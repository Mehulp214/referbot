from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from database import add_user, del_user, full_userbase, present_user
import asyncio
import os

# Bot Configurations
API_ID = int(os.getenv("API_ID", 13216322))
API_HASH = os.getenv("API_HASH", "15e5e632a8a0e52251ac8c3ccbe462c7")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7610980882:AAESQYI9Ca1pWSobokw1-S-QkVfTrja-Xdk")
ADMIN_IDS = [5993556795]  # Replace with your Telegram User IDs

FORCE_MSG = "You must join our channels to use this bot."
START_MSG = "Welcome, {first}!"

# Channels for Force Subscription
FORCE_SUB_CHANNELS = [-1002493977004]  # Add channel IDs here

# Initialize the bot
app = Client("ForceSubBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Helper Function to Check Subscription
async def is_subscribed(client, user_id):
    if not FORCE_SUB_CHANNELS:
        return True

    for channel_id in FORCE_SUB_CHANNELS:
        try:
            member = await client.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
                return False
        except Exception:
            return False
    return True

# Middleware to Enforce Subscription
async def enforce_subscription(client, message):
    if await is_subscribed(client, message.from_user.id):
        return True

    buttons = []
    for channel_id in FORCE_SUB_CHANNELS:
        try:
            invite_link = await client.export_chat_invite_link(channel_id)
            buttons.append([InlineKeyboardButton("Join Channel", url=invite_link)])
        except Exception as e:
            print(f"Error generating invite link for channel {channel_id}: {e}")

    buttons.append([InlineKeyboardButton("Try Again", callback_data="check_subscription")])
    await message.reply(
        text=FORCE_MSG,
        reply_markup=InlineKeyboardMarkup(buttons),
        quote=True
    )
    return False

# Start Command
@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    if not await enforce_subscription(client, message):
        return

    user_id = message.from_user.id
    if not await present_user(user_id):
        try:
            await add_user(user_id)
        except Exception as e:
            print(f"Error adding user {user_id}: {e}")

    reply_markup = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("😊 About Me", callback_data="about"),
            InlineKeyboardButton("🔒 Close", callback_data="close")
        ]]
    )
    await message.reply_text(
        text=START_MSG.format(first=message.from_user.first_name),
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

# Get Users Command
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

# Run the bot
if __name__ == "__main__":
    app.run()
