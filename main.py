import asyncio
import os
from bot import app
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram import filters
from pyromod import Client
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
# from database import (
#     user_data as ud,
#     add_user,
#     del_user,
#     full_userbase,
#     present_user,
#     update_balance,
#     update_referral_count,
#     get_balance,
#     clear_temp_referral,
#     set_temp_referral,
#     get_temp_referral,
#     get_referral_list
# )
from database import *
ud=user_data


# Bot Configurations
API_ID = int(os.getenv("API_ID", 13216322))
API_HASH = os.getenv("API_HASH", "15e5e632a8a0e52251ac8c3ccbe462c7")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7610980882:AAESQYI9Ca1pWSobokw1-S-QkVfTrja-Xdk")
ADMIN_IDS = [5993556795]  # Replace with your Telegram User IDs

FORCE_MSG = "You must join our channels to use this bot."
START_MSG = "Welcome, {first}!"
MAIN_MENU_MSG = "WELCOME TO MENU"

# Channels for Force Subscription
FORCE_SUB_CHANNELS = [-1002493977004]  # Add channel IDs here


# Initialize the bot
app = Client("ForceSubBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


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


# Helper Function to Check Subscription
async def check_subscription(client, user_id):
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
#@app.on_message(filters.command("set_wallet") & filters.private)
#async def set_wallet_command(client: Client, message):
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
    response = await client.listen(callback_query.message.chat.id, timeout=300)  # 5 minutes timeout
    
    # Handle cancellation
    if response.text.lower() == "cancel":
        await response.reply_text("Wallet update cancelled.")
        return

    # Update wallet address
    new_wallet = response.text.strip()
    await update_wallet(user_id, new_wallet)
    await response.reply_text(f"Your wallet address has been updated to:\n`{new_wallet}`")
    await main_menu_callback(client,callback_query)
    
# Handle unknown button presses
@app.on_callback_query(filters.regex("cancel"))
async def cancel_button(client: Client, callback_query):
    await callback_query.answer("Action cancelled.", show_alert=True)
    await main_menu_callback(client,callback_query)

# Callback: Withdraw
@app.on_callback_query(filters.regex("withdraw"))
async def withdraw_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    balance = await get_balance(user_id)
    if balance < 50:  # Minimum balance to withdraw
        await callback_query.message.edit_text(
            "You need at least 50 units to withdraw.",
            reply_markup=back_key()
        )
    else:
        await callback_query.message.edit_text(
            "Please provide your wallet address for the withdrawal.",
            reply_markup=back_key()
        )
        # Handle withdrawal logic and balance deduction as needed



# Callback: Statistics
@app.on_callback_query(filters.regex("statistics"))
async def statistics_callback(client: Client, callback_query: CallbackQuery):
    user_count = await ud.count_documents({})  # Count all users
    await callback_query.message.edit_text(
        f"Total users using this bot: {user_count}",
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


# Command to View Balance
@app.on_message(filters.command("users") & filters.private & filters.user(ADMIN_IDS))
async def get_users(client: Client, message: Message):
    users = await full_userbase()
    await message.reply(f"There are {len(users)} users using this bot.")


# Broadcast Command
@app.on_message(filters.command("broadcast") & filters.private & filters.user(ADMIN_IDS))
async def broadcast_message(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply("Reply to a message to broadcast.")
        return

    users = await full_userbase()
    total = len(users)
    successful, blocked, deleted, unsuccessful = 0, 0, 0, 0

    pls_wait = await message.reply("<i>Broadcasting Message... This will take some time.</i>")
    for user_id in users:
        try:
            await message.reply_to_message.copy(user_id)
            successful += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await message.reply_to_message.copy(user_id)
            successful += 1
        except UserIsBlocked:
            await del_user(user_id)
            blocked += 1
        except InputUserDeactivated:
            await del_user(user_id)
            deleted += 1
        except Exception:
            unsuccessful += 1

    status = f"""<b>Broadcast Completed</b>
Total: {total}
Successful: {successful}
Blocked: {blocked}
Deleted: {deleted}
Failed: {unsuccessful}"""
    await pls_wait.edit(status)


@app.on_message(filters.command("add_balance") & filters.private)
async def add_command(client: Client, message: Message):
    user_id = message.from_user.id
    await update_balance(1932612943, 100)
    print(user_id)

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




@app.on_message(filters.command("refer_list") & filters.user(ADMIN_IDS))
async def refer_list_command(client: Client, message: Message):
    # Ensure the admin is sending a valid user_id to view referrals
    try:
        # Extract user_id from the command text (e.g., /refer_list 1234567890)
        user_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.reply("Please provide a valid user ID.\nUsage: /refer_list <user_id>")
        return

    # Fetch referral count for the specified user
    ref_count = ud.count_documents({"referrer_id": user_id})
    
    # Fetch detailed referral information for the specified user
    referred_users = list(ud.find({"referrer_id": user_id}))
    referral_details = []

    # Add numbering and timestamp
    for index, user in enumerate(referred_users, 1):  # Start numbering from 1
        referred_user_id = user['_id']
        
        # Fetch the referred user's name using Pyrogram
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
            f"{index}. User ID: `{referred_user_id}`, Name: **{full_name}**, \nReferred On: **{timestamp}**, \n[Profile Link](tg://user?id={referred_user_id})\n"
        )

    referral_details_text = "\n".join(referral_details) if referral_details else "No referrals yet."
    f_name=user_info.first_name + (" " + user_info.last_name if user_info.last_name else "")
    # Send the response to the admin
    await message.reply(
        f"Admin, you are viewing the referrals of user with ID: `{user_id}`-**{f_name}**.\n\nReferral Count: {ref_count}\n\nReferral Details:\n{referral_details_text}",
        disable_web_page_preview=True  # Avoid link previews
    )



import pymongo
from config import Config
dbclient = pymongo.MongoClient(Config.MONGO_URI)
database_name = dbclient["REFER_START"]

@app.on_message(filters.command("drop") & filters.private)
async def drop(client: Client, message: Message):
    # Drop the database using the client
    dbclient.drop_database(database_name)
    await message.reply("Database dropped.")
    print("DB DROPPED")


# Run the bot
if __name__ == "__main__":
    app.run()
