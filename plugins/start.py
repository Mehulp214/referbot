import asyncio
import os
from datetime import datetime
from bot import marimo as app
from config import *
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram import filters
from pyromod import Client
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from pyromod.helpers import ikb

 
from database import *




#======================================KEYBOARD INLINE --------------------+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def main_key():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👛 Balance", callback_data="check_balance"),
            InlineKeyboardButton("📊 Statistics", callback_data="statistics")
        ],
        [
            InlineKeyboardButton("🔗 Referral Link", callback_data="referral_link"),
            InlineKeyboardButton("👥 My Referrals", callback_data="my_referrals")
        ],
        [
            InlineKeyboardButton("💳 Set Wallet", callback_data="set_wallet"),
            InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")
        ],
        [
            InlineKeyboardButton("📩 Support", callback_data="support")
        ]
    ])

#BACK BUTTON function
def back_key():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ])

FORCE_SUB_CHANNELS=get_fsub_channels()
print(get_fsub_channels())
# Helper Function to Check Subscription
async def check_subscription(client, user_id):
    FORCE_SUB_CHANNELS=get_fsub_channels()
    for channel_id in FORCE_SUB_CHANNELS:
        try:
            member = await client.get_chat_member(channel_id, user_id)
            if member.status not in [
                ChatMemberStatus.OWNER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.MEMBER,
            ]:
                return False
        except UserNotParticipant:
            return False
        except Exception as e:
            print(f"Error checking subscription: {e}")
            return False
    return True


# Middleware: Enforce subscription before proceeding
async def force_subscription(client, message):
    user_id = message.from_user.id
    if user_id in ADMIN_IDS:  # Skip subscription check for admins
        return True
    if not await check_subscription(client, user_id):
        buttons = []
        FORCE_SUB_CHANNELS=get_fsub_channels()
        for channel_id in FORCE_SUB_CHANNELS:
            try:
                invite_link = await client.export_chat_invite_link(channel_id)
                buttons.append([InlineKeyboardButton("Join Channel", url=invite_link)])
            except Exception as e:
                print(f"Error creating invite link for {channel_id}: {e}")
        buttons.append(
            [InlineKeyboardButton("Check Subscription ✅", callback_data="check_subscription")]
        )
        await message.reply(
            FORCE_MSG, reply_markup=InlineKeyboardMarkup(buttons), quote=True
        )
        return False
    return True



# Command: Start
@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    referral_code = None

    # Extract referral code from the start command
    if len(message.text.split()) > 1:
        referral_code = message.text.split()[1]

    # Check if user is already registered
    if await present_user(user_id):
        await message.reply(
            "You are already registered and cannot be referred by anyone."
        )
    else:
         
        # Register new user and process referral
        if referral_code and referral_code != str(user_id):
            if await present_user(int(referral_code)):  # Ensure referrer exists
                await set_temp_referral(user_id, int(referral_code))  # Temporarily store referral
            else:
                await message.reply("Invalid referral code. Proceeding without a referrer.")
        await add_user(user_id)
        
    # Enforce force subscription
    if not await force_subscription(client, message):
        return

    # Send start message
    await temp_main_menu(client, message)
    

# Temporary main menu
async def temp_main_menu(client: Client, message: Message):
    user_id = message.from_user.id
    if not await check_subscription(client, user_id):
        await message.reply("You must join all required channels first.")
        return
    referrer_id = await get_temp_referral(user_id)
    if referrer_id:
        user_data = ud.find_one({'_id': user_id})  # Fetch user data explicitly
        if user_data and not user_data.get("referrer_id"):  # Reward only if no referrer is set
            await update_referral_count(referrer_id)
            print(referrer_id)
            await update_balance(int(referrer_id), 10)  # Reward the referrer with 10 units
            #await set_temp_referral(user_id, None)  # Clear temporary referral data
            await add_user(user_id, referrer_id=referrer_id)  # Set referrer for the user

    await message.reply(
        MAIN_MENU_MSG,
        reply_markup=main_key()
    )


# Callback: Main Menu
@app.on_callback_query(filters.regex("main_menu"))
async def main_menu_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    if not await check_subscription(client, user_id):
        await callback_query.answer(
            "You must join all required channels first.", show_alert=True
        )
        return

    # Check if a referral reward is pending
    referrer_id = await get_temp_referral(user_id)
    if referrer_id:
        user_data = ud.find_one({'_id': user_id})  # Fetch user data explicitly
        if user_data and not user_data.get("referrer_id"):  # Reward only if no referrer is set
            await update_referral_count(referrer_id)
            await update_balance(int(referrer_id), 10)  # Reward the referrer with 10 units
            await set_temp_referral(user_id, None)  # Clear temporary referral data
            await add_user(user_id, referrer_id=referrer_id)  # Set referrer for the user

    # Show main menu message
    await callback_query.answer("Main menu loaded!")

    # Edit message with main menu
    await callback_query.message.edit_text(
        MAIN_MENU_MSG,
        reply_markup=main_key()
    )



#WITHDRAWAL FUNCTIONALITY------------------------------------------------------------------------------------------------------------------------------------
import asyncio

cancelled_users = {}  # Stores users who clicked cancel

# Automatically remove user from cancelled_users after 60 seconds
async def remove_cancelled_user(user_id):
    await asyncio.sleep(60)
    cancelled_users.pop(user_id, None)  # Remove user ID after 60 seconds

@app.on_callback_query(filters.regex("withdraw"))
async def withdraw_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    if user_id in cancelled_users:
        await callback_query.answer("❌ You recently cancelled. Please try again later!", show_alert=True)
        return

    balance = await get_balance(user_id)

    if balance < 50:
        await callback_query.message.reply_text(
            "❌ You need at least 50 units to withdraw.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
            ])
        )
        return

    wallet = await get_wallet(user_id)

    if not wallet:
        await request_wallet(client, callback_query, user_id)
        return

    # ✅ FIX: Instead of resending this message, proceed with confirmation
    await callback_query.message.reply_text(
        f"💼 Your wallet address:\n`{wallet}`\n\nIs this correct?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Yes, proceed", callback_data="proceed_withdrawal")],
            [InlineKeyboardButton("❌ No, change it", callback_data="change_wallet")]
        ])
    )

@app.on_callback_query(filters.regex("change_wallet"))
async def change_wallet_callback(client: Client, callback_query: CallbackQuery):
    """Handles wallet change request."""
    await request_wallet(client, callback_query, callback_query.from_user.id)

@app.on_callback_query(filters.regex("proceed_withdrawal"))
async def proceed_withdrawal(client: Client, callback_query: CallbackQuery):
    """Proceeds with withdrawal after wallet confirmation."""
    user_id = callback_query.from_user.id

    if user_id in cancelled_users:
        await callback_query.answer("❌ You recently cancelled. Please try again later!", show_alert=True)
        return

    balance = await get_balance(user_id)

    await callback_query.message.reply_text(
        f"💰 **Your balance: {balance} units**\n\nEnter the withdrawal amount (minimum 50):",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ])
    )

    response = await client.listen(callback_query.message.chat.id, timeout=150)

    if response.text.lower() in ("cancel", "back", "exit"):
        cancelled_users[user_id] = True
        asyncio.create_task(remove_cancelled_user(user_id))

        await callback_query.message.reply_text(
            "❌ **Withdrawal cancelled.**\nReturning to main menu...",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
            ])
        )
        return

    amount = int(response.text)
    if amount < 50 or amount > balance:
        await callback_query.message.reply_text(
            "❌ **Invalid amount!** Ensure it's at least 50 and does not exceed your balance."
        )
        return

    wallet_address = await get_wallet(user_id)
    payout_channel = "@YourPayoutChannel"

    await update_balance(user_id, -amount)
    await add_withdrawal(user_id, amount)
    await update_total_withdrawals(amount)
    timestamp = get_ist_time()

    withdrawal_request = (
        f"✅ **New Withdrawal Request**\n\n"
        f"👤 User ID: `{user_id}`\n"
        f"💵 Amount: {amount} units\n"
        f"💼 Wallet: `{wallet_address}`\n"
        f"🕒 Time: {timestamp}\n"
        f"📢 Payout Channel: {payout_channel}"
    )

    await callback_query.message.reply_text(
        f"✅ **Your withdrawal request has been submitted!**\n\n{withdrawal_request}"
    )

    for admin_id in ADMIN_IDS:
        await client.send_message(chat_id=admin_id, text=withdrawal_request)

    await client.send_message(chat_id=payout_channel, text=withdrawal_request)

@app.on_callback_query(filters.regex("cancel"))
async def cancel_button(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    cancelled_users[user_id] = True
    asyncio.create_task(remove_cancelled_user(user_id))

    await callback_query.message.reply_text("❌ **Action cancelled.**")
    await callback_query.message.reply_text(
        "Returning to main menu...",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
        ])
    )




# Callback: Check Balance
@app.on_callback_query(filters.regex("check_balance"))
async def check_balance_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    balance = await get_balance(user_id)
    await callback_query.answer(f"Your current balance is: {balance} units.", show_alert=True)
    await callback_query.message.edit_text(
        f"Your current balance is: {balance} units.",
        reply_markup=back_key()
    )


# Callback: Referral Link
@app.on_callback_query(filters.regex("referral_link"))
async def referral_link_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    referral_link = f"https://t.me/{client.me.username}?start={user_id}"
    await callback_query.message.edit_text(
        f"Share this referral link to earn rewards:\n\n{referral_link}",
        reply_markup=back_key()
    )

from pyromod.helpers import ikb 
import asyncio
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

import asyncio

cancelled_users = {}  # Stores users who clicked cancel

# Automatically remove user from cancelled_users after 60 seconds
async def remove_cancelled_user(user_id):
    await asyncio.sleep(60)
    cancelled_users.pop(user_id, None)  # Remove user ID after 60 seconds


@app.on_callback_query(filters.regex("set_wallet"))
async def set_wallet_command(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    if user_id in cancelled_users:
        await callback_query.answer("❌ You recently cancelled. Please try again later!", show_alert=True)
        return

    old_wallet = await get_wallet(user_id)

    if old_wallet:
        await callback_query.message.reply_text(
            f"Your current wallet address is:\n`{old_wallet}`\n\nIs this correct?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Yes, it's correct", callback_data="confirm_wallet")],
                [InlineKeyboardButton("❌ No, change it", callback_data="change_wallet")]
            ])
        )
    else:
        await request_wallet(client, callback_query, user_id)


@app.on_callback_query(filters.regex("change_wallet"))
async def change_wallet(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    if user_id in cancelled_users:
        await callback_query.answer("❌ You recently cancelled. Please try again later!", show_alert=True)
        return

    await request_wallet(client, callback_query, user_id)


async def request_wallet(client: Client, callback_query: CallbackQuery, user_id: int):
    cancel_words = ("cancel", "back", "exit")

    await callback_query.message.edit_text(
        "Please provide your new wallet address below (or type 'cancel' to stop):",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ])
    )

    try:
        response = await client.listen(callback_query.message.chat.id, timeout=60)

        # If user cancels, store ID and remove after 60s
        if response.text.lower() in cancel_words:
            cancelled_users[user_id] = True
            asyncio.create_task(remove_cancelled_user(user_id))  # Remove after 60 seconds

            await callback_query.message.edit_text("❌ Action cancelled. Returning to main menu...")
            await main_menu_callback(client, callback_query)
            return

        if user_id in cancelled_users:
            await response.reply_text("❌ You cancelled the process. Please try again later!")
            return

        new_wallet = response.text.strip()
        await update_wallet(user_id, new_wallet)

        await response.reply_text(f"✅ Your wallet has been updated to:\n`{new_wallet}`\n\nUse /start to refresh.")

    except asyncio.TimeoutError:
        await callback_query.message.edit_text(
            "⏳ **Wallet update timed out. Returning to main menu...**"
        )

    await main_menu_callback(client, callback_query)


@app.on_callback_query(filters.regex("cancel"))
async def cancel_button(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    cancelled_users[user_id] = True  # Store user ID in cancelled list
    asyncio.create_task(remove_cancelled_user(user_id))  # Auto remove after 60 seconds

    await callback_query.answer("❌ Action cancelled.", show_alert=True)
    await main_menu_callback(client, callback_query)




# Cancel handler
# @app.on_callback_query(filters.regex("cancel"))
# async def cancel_button(client: Client, callback_query: CallbackQuery):
#     user_id = callback_query.from_user.id
#     user_states.pop(user_id, None) 
#     await callback_query.message.edit_text(
#         "Action cancelled",
#         reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Main Menu", callback_data="main_menu")]])
#     )





@app.on_callback_query(filters.regex("statistics"))
async def stats_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Fetch the user's total withdrawals
    user_withdrawals = await get_user_withdrawals(user_id)
    
    # Fetch the global total withdrawals
    global_withdrawals = await get_total_withdrawals()

    # Fetch total users in the system
    total_users = await full_userbase()

    # Prepare the statistics message
    stats_message = (
        f"**Statistics**\n\n"
        f"**Your Withdrawals**: {user_withdrawals} units\n"
        f"**Total Global Withdrawals**: {global_withdrawals} units\n"
        f"**Total Users**: {len(total_users)} users in the system"
    )

    # Send the statistics to the user
    await callback_query.message.edit_text(
        stats_message,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
        ])
    )




# Callback: Check Subscription
@app.on_callback_query(filters.regex("check_subscription"))
async def check_subscription_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    if await check_subscription(client, user_id):
        await callback_query.answer("Thank you for subscribing!", show_alert=True)
        #await callback_query.message.delete()
        await main_menu_callback(client, callback_query)
    else:
        await callback_query.answer(
            "You still need to join the required channels.", show_alert=True
        )


  

@app.on_callback_query(filters.regex("my_referrals"))
async def my_referrals_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Fetch referral count synchronously
    ref_count = ud.count_documents({"referrer_id": user_id})
    
    # Fetch detailed referral information
    referred_users = list(ud.find({"referrer_id": user_id}))
    referral_details = []

    # Add numbering and timestamp
    for index, user in enumerate(referred_users, 1):  # Start numbering from 1
        referred_user_id = user['_id']
        
        # Fetch the referred user's name from the main user data collection (ud)
        try:
            user_info = await client.get_users(referred_user_id)
            full_name = user_info.first_name + (" " + user_info.last_name if user_info.last_name else "")
        except Exception as e:
            full_name = "Unknown"
        
        # Get the timestamp from the referral document (it's in the 'referrals' array)
        referral = next((r for r in user.get('referrals', []) if r['user_id'] == referred_user_id), None)
        timestamp = referral.get('timestamp', 'Unknown date') if referral else 'Unknown date'

        # Format the timestamp (if needed, you can convert it to a readable string)
        referral_details.append(
            f"{index}. User ID: `{referred_user_id}`, Name: **{full_name}**, \n Referred On: **{timestamp}**, \n [Profile Link](tg://user?id={referred_user_id})\n"
        )

    referral_details_text = "\n".join(referral_details) if referral_details else "No referrals yet."

    # Send the response to the user
    await callback_query.message.edit_text(
        f"You have successfully referred **{ref_count} users**.\n\nReferral Details:\n{referral_details_text}",
        reply_markup=back_key(),
        disable_web_page_preview=True  # Avoid link previews
    )






# Callback for Support Request
@app.on_callback_query(filters.regex("support"))
async def support_request(client: Client, callback_query: CallbackQuery):
    await callback_query.message.reply_text(
        "Please send your message or a screenshot with a caption to submit a support request.\n\n"
        "Type 'cancel' at any time to cancel the request."
    )
    try:
        # Wait for user response
        response = await client.listen(callback_query.message.chat.id, timeout=150)  # Wait for 5 minutes
        if response.text and response.text.lower() == "cancel":
            await callback_query.message.reply_text("**Support request canceled.**")
            return

        # Collect and process the support request
        user_id = response.from_user.id
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if response.photo:
            # Handle photo with caption
            photo = response.photo.file_id
            caption = response.caption or "No caption provided."
            for admin_id in ADMIN_IDS:
                await client.send_photo(
                    chat_id=admin_id,
                    photo=photo,
                    caption=f"**New Support Request**:\n\nUser ID: `{user_id}`\nTime: {timestamp}\nCaption: **{caption}**",
                    reply_markup=ikb([[("Reply to User", f"reply_{user_id}")]])
                )
            await callback_query.message.reply_text("Your support request has been submitted successfully!")
        else:
            # Handle text-only support request
            message_text = response.text or "No message provided."
            for admin_id in ADMIN_IDS:
                await client.send_message(
                    chat_id=admin_id,
                    text=f"New Support Request:\n\nUser ID: `{user_id}`\nTime: {timestamp}\nMessage: **{message_text}**",
                    reply_markup=ikb([[("Reply to User", f"reply_{user_id}")]])
                )
            await callback_query.message.reply_text("**Your support request has been submitted successfully!**")

    except TimeoutError:
        # Handle timeout and inform the user
        await callback_query.message.reply_text(
            "⏳ **Support request timed out.**\n\nYou did not respond in time. Please try again.",
            reply_markup=ikb([[("Back to Main Menu", "main_menu")]])
        )

# Admin Reply Handler
@app.on_callback_query(filters.regex(r"reply_(\d+)"))
async def admin_reply(client: Client, callback_query: CallbackQuery):
    user_id = int(callback_query.data.split("_")[1])
    await callback_query.message.reply_text("Please type your reply to the user:")
    
    try:
        # Wait for admin response
        response = await client.listen(callback_query.message.chat.id, timeout=150)  # Wait for 5 minutes
        if response.text and response.text.lower() == "cancel":
            await callback_query.message.reply_text("Reply canceled.")
            return

        reply_text = response.text or "No reply provided."
        await client.send_message(
            chat_id=user_id,
            text=f"Admin has sent you a Reply:\n\n**{reply_text}**"
        )
        await callback_query.message.reply_text("Reply sent to the user successfully.")
    except TimeoutError:
        # Handle timeout for admin reply
        await callback_query.message.reply_text(
            "⏳ **Reply timed out.**\n\nYou did not respond in time. Please try again.",
            reply_markup=ikb([[("Back to Main Menu", "main_menu")]])
        )



 





