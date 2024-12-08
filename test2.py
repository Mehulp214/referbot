import asyncio
import os
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from database import (
    user_data as ud,
    add_user,
    del_user,
    full_userbase,
    present_user,
    update_balance,
    update_referral_count,
    get_balance,
    clear_temp_referral,
    set_temp_referral,
    get_temp_referral,
)

# Bot Configurations
API_ID = int(os.getenv("API_ID", 13216322))
API_HASH = os.getenv("API_HASH", "15e5e632a8a0e52251ac8c3ccbe462c7")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7610980882:AAESQYI9Ca1pWSobokw1-S-QkVfTrja-Xdk")
ADMIN_IDS = [5993556795]

FORCE_SUB_CHANNELS = [-1002493977004]  # Add channel IDs here
FORCE_MSG = "You must join our channels to use this bot."
START_MSG = "Welcome, {first}!"
MAIN_MENU_MSG = "WELCOME TO MENU"

# Initialize the bot
app = Client("ForceSubBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


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
        await message.reply("You are already registered and cannot be referred by anyone.")
    else:
        # Register new user and process referral
        if referral_code and referral_code != str(user_id):
            if await present_user(int(referral_code)):  # Ensure referrer exists
                await set_temp_referral(user_id, int(referral_code))  # Temporarily store referral
            else:
                await message.reply("Invalid referral code. Proceeding without a referrer.")
        await add_user(user_id)

    # Enforce force subscription
    if not await check_subscription(client, user_id):
        buttons = [
            [InlineKeyboardButton("Join Channel", url=await client.export_chat_invite_link(FORCE_SUB_CHANNELS[0]))],
            [InlineKeyboardButton("Check Subscription ✅", callback_data="check_subscription")]
        ]
        await message.reply(FORCE_MSG, reply_markup=InlineKeyboardMarkup(buttons))
        return

    # Redirect to the main menu
    await main_menu(client, message)


# Function: Main Menu
async def main_menu(client: Client, message: Message):
    await message.reply(
        MAIN_MENU_MSG,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Check Balance", callback_data="check_balance")]]
        ),
    )


# Callback: Check Subscription
@app.on_callback_query(filters.regex("check_subscription"))
async def check_subscription_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if await check_subscription(client, user_id):
        # Process referral rewards if valid subscription
        referrer_id = await get_temp_referral(user_id)
        if referrer_id:
            await update_referral_count(referrer_id)
            await update_balance(referrer_id, 10)  # Reward referrer
            await set_temp_referral(user_id, None)
            await add_user(user_id, referrer_id=referrer_id)
        await callback_query.answer("Thank you for subscribing!", show_alert=True)
        await main_menu(client, callback_query.message)
    else:
        await callback_query.answer("You still need to join the required channels.", show_alert=True)


# Callback: Check Balance
@app.on_callback_query(filters.regex("check_balance"))
async def check_balance_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    balance = await get_balance(user_id)
    await callback_query.answer(f"Your current balance is: {balance} units.", show_alert=True)


# Admin Commands
@app.on_message(filters.command("users") & filters.private & filters.user(ADMIN_IDS))
async def get_users(client: Client, message: Message):
    users = await full_userbase()
    await message.reply(f"There are {len(users)} users using this bot.")


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


if __name__ == "__main__":
    app.run()
