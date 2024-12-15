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




# Withdrawal Functionality
@app.on_callback_query(filters.regex("withdraw"))
async def withdraw_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user = await client.get_users(user_id)
    username = user.username or "No Username"
    full_name = user.first_name + (" " + user.last_name if user.last_name else "")
    balance = await get_balance(user_id)

    if balance < 50:  # Minimum balance to withdraw
        await callback_query.message.edit_text(
            "You need at least 50 units to withdraw.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
            ])
        )
        return

    # Ask user for withdrawal amount
    await callback_query.message.edit_text(
        f"Your balance: {balance} units\n\nEnter the withdrawal amount (minimum 50):",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
        ])
    )

    try:
        response = await client.listen(callback_query.message.chat.id, timeout=150)  # Wait for user input
        if response.text and response.text.lower() == "cancel":
            await callback_query.message.reply_text("**Withdrawal process canceled.**")
            return

        amount = int(response.text)  # Convert user input to integer
        if amount < 50 or amount > balance:
            await callback_query.message.reply_text(
                "Invalid amount! Ensure it is at least 50 and does not exceed your balance.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
                ])
            )
            return

        # Ask user for wallet address
        await callback_query.message.reply_text(
            "Please provide your wallet address:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
            ])
        )
        wallet_response = await client.listen(callback_query.message.chat.id, timeout=150)
        if wallet_response.text and wallet_response.text.lower() == "cancel":
            await callback_query.message.reply_text("**Withdrawal process canceled.**")
            return

        wallet_address = wallet_response.text
        payout_channel = "@YourPayoutChannel"  # Replace with your payout channel

        # Deduct balance and create withdrawal request
        await update_balance(user_id, -amount)
        timestamp = get_ist_time()
        withdrawal_request = (
            f"**New Withdrawal Request**\n\n"
            f"User ID: `{user_id}`\n"
            f"Username: @{username}\n"
            f"Full Name: {full_name}\n"
            f"Amount: {amount} units\n"
            f"Wallet Address: {wallet_address}\n"
            f"Time: {timestamp}\n"
            f"Payout Channel: {payout_channel}"
        )

        # Notify user, admins, and payout channel
        await callback_query.message.reply_text(
            f"Your withdrawal request has been created:\n\n{withdrawal_request}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
            ])
        )
        for admin_id in ADMIN_IDS:
            await client.send_message(chat_id=admin_id, text=withdrawal_request)

        await client.send_message(chat_id=payout_channel, text=withdrawal_request)

        # Update withdrawal statistics in the database
        await add_withdrawal(user_id, amount)  # This function updates the user's withdrawal record
        await update_total_withdrawals(amount)  # This function updates the global total withdrawals

    except asyncio.TimeoutError:
        await callback_query.message.reply_text(
            "⏳ **Withdrawal process timed out. Please try again.**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
            ])
        )
    except ValueError:
        await callback_query.message.reply_text(
            "Invalid input! Please enter a numeric value for the withdrawal amount.",
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

# Callback: Set Wallet
@app.on_callback_query(filters.regex("set_wallet"))
async def set_wallet_command(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.message.from_user.id
    
    # Get the current wallet address
    old_wallet = await get_wallet(user_id)
    if old_wallet:
        await callback_query.message.reply_text(
            f"Your current wallet address is:\n`{old_wallet}`\n\nPlease provide a new wallet address below:",
            reply_markup=ikb([[("Cancel", "cancel")]])
        )
    else:
        await callback_query.message.reply_text(
            "You don't have a wallet address set. Please provide a wallet address below:",
            reply_markup=ikb([[("Cancel", "cancel")]])
        )

    # Wait for the user's response
    response = await client.listen(callback_query.message.chat.id, timeout=60)  # 5 minutes timeout
    
    # Handle cancellation
    if response.text.lower() == "cancel":
        await response.reply_text("Wallet update cancelled.")
        return

    # Update wallet address
    new_wallet = response.text.strip()
    await update_wallet(user_id, new_wallet)
    await response.reply_text(f"Your wallet address has been updated to:\n`{new_wallet}` \n\n /start again to Update ")
    
    
# Handle unknown button presses
@app.on_callback_query(filters.regex("cancel"))
async def cancel_button(client: Client, callback_query):
    await callback_query.answer("Action cancelled.", show_alert=True)
    await main_menu_callback(client,callback_query)





@app.on_callback_query(filters.regex("statistics"))
async def statistics_callback(client: Client, callback_query: CallbackQuery):
    # Get total users count
    users = await full_userbase()
    user_count =len(users)  # Count all users
    
    # Fetch total withdrawal amount
    total_withdrawals = await get_total_withdrawals()  # This function gets the total withdrawal from bot_stats
    
    # Prepare individual withdrawal amounts
    withdrawal_data = []
    user_docs = ud.find()
    for user in user_docs:
        user_id = user['_id']
        individual_withdrawal = await get_user_withdrawals(user_id)  # This function gets the withdrawal amount for each user
        withdrawal_data.append(f"User {user_id}: {individual_withdrawal} amount withdrawn")
    
    # Format the statistics message
    withdrawal_message = "\n".join(withdrawal_data) if withdrawal_data else "No withdrawals found."
    
    # Send the statistics message with total and individual withdrawal amounts
    await callback_query.message.edit_text(
        f"Total users using this bot: {user_count}\n"
        f"Total withdrawal amount across all users: {total_withdrawals}\n\n"
        f"Individual withdrawal amounts:\n{withdrawal_message}",
        reply_markup=back_key()
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



 





