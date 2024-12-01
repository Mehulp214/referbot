from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from database import add_user, del_user, full_userbase, present_user, update_balance, update_referral_count, get_balance
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




# Generate Referral Link
async def generate_referral_link(user_id):
    bot_info = await client.get_me()
    bot_username = bot_info.username
    referral_code = str(user_id)
    return f"https://t.me/{bot_username}?start={referral_code}"

# Middleware to Enforce Subscription
async def enforce_subscription(client: Client, message: Message):
    if await is_subscribed(client, message.from_user.id):
        return True

    buttons = []
    for channel_id in FORCE_SUB_CHANNELS:
        try:
            invite_link = await client.export_chat_invite_link(channel_id)
            buttons.append([InlineKeyboardButton("Join Channel", url=invite_link)])
        except Exception as e:
            print(f"Error generating invite link for channel {channel_id}: {e}")

    bot_info = await client.get_me()
    bot_username = bot_info.username
    buttons.append([InlineKeyboardButton("SUBSCRIBED ✅✅", url=f"https://t.me/{bot_username}?start={referral_code}")])
    await message.reply(
        text=FORCE_MSG,
        reply_markup=InlineKeyboardMarkup(buttons),
        quote=True
    )
    return False

# Check Referral and Update Balance
async def check_and_update_referral(client: Client, user_id, referral_code):
    if referral_code:
        if user_id != int(referral_code):  # Avoid self-referral
            # Update balance for referrer
            await update_referral_count(referral_code)
            await update_balance(referral_code, 10)  # Reward the referrer with 10 units
            print(f"Referral successful for user {referral_code}, credited 10 units.")

# Start Command
@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    referral_code = None

    # Check for referral code in /start command
    if len(message.text) > 7:
        referral_code = message.text.split(" ", 1)[1]

    # If the user doesn't exist in the database, add them
    if not await present_user(user_id):
        await add_user(user_id)

    await check_and_update_referral(client, user_id, referral_code)

    # Generate the referral link for the user
    referral_link = await generate_referral_link(user_id)

    # Send start message with referral link
    reply_markup = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("😊 About Me", callback_data="about"),
            InlineKeyboardButton("🔒 Close", callback_data="close"),
            InlineKeyboardButton("Get Your Referral Link", url=referral_link)
        ]]
    )

    await message.reply_text(
        text=START_MSG.format(first=message.from_user.first_name),
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

# Command to View Balance
@app.on_message(filters.command("balance") & filters.private)
async def balance_command(client: Client, message: Message):
    user_id = message.from_user.id
    user_data = await present_user(user_id)
    if user_data:
        balance = user_data.get('balance', 0)
        await message.reply(f"Your current balance: {balance} units.")
    else:
        await message.reply("You are not registered yet. Please start by joining the channels.")


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
