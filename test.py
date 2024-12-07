# from pyrogram import Client, filters


from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from database import (
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
import asyncio
import os

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

    # Extract referral code from start command
    if len(message.text.split()) > 1:
        referral_code = message.text.split()[1]
        if referral_code and referral_code != str(user_id):
            await set_temp_referral(user_id, referral_code)  # Store referral temporarily

    # Check if the user is already in the database
    if not await present_user(user_id):
        await add_user(user_id)

    if not await force_subscription(client, message):
        return

    # Reply with the start message
    await message.reply(
        START_MSG.format(first=message.from_user.first_name),
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Main Menu", callback_data="main_menu")]]
        ),
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
        await update_referral_count(referrer_id)
        await update_balance(int(referrer_id), 10)  # Reward the referrer with 10 units
        print(referrer_id)
        print(type(int(referrer_id)))
        await set_temp_referral(user_id, None)  # Clear temporary referral data

    # Show main menu message
    await callback_query.message.edit_text(
        MAIN_MENU_MSG,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Check Balance", callback_data="check_balance")]]
        ),
    )


# Command: Balance
@app.on_message(filters.command("balance") & filters.private)
async def balance_command(client: Client, message: Message):
    if not await force_subscription(client, message):
        return

    user_id = message.from_user.id
    balance = await get_balance(user_id)
    await message.reply(f"Your current balance is: {balance} units.")


# Callback: Check Balance
@app.on_callback_query(filters.regex("check_balance"))
async def check_balance_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    balance = await get_balance(user_id)
    await callback_query.answer(f"Your current balance is: {balance} units.", show_alert=True)


# Callback: Check Subscription
@app.on_callback_query(filters.regex("check_subscription"))
async def check_subscription_callback(client: Client, callback_query):
    user_id = callback_query.from_user.id
    if await check_subscription(client, user_id):
        await callback_query.answer("Thank you for subscribing!", show_alert=True)
        await callback_query.message.delete()
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


# Run the bot
if __name__ == "__main__":
    app.run()


# from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
# from config import Config
# from database import Database

# db = Database(Config.MONGO_URI)

# # Initialize Bot
# bot = Client(
#     "ReferAndEarnBot",
#     api_id=Config.API_ID,
#     api_hash=Config.API_HASH,
#     bot_token=Config.BOT_TOKEN,
# )


# # Define commands that only admins can use
# def admin_only(func):
#     async def wrapper(client, message: Message):
#         if message.from_user.id not in Config.ADMIN_IDS:
#             await message.reply("🚫 You are not authorized to use this command.")
#             return
#         return await func(client, message)
#     return wrapper


# # Main Menu Keyboard
# def main_menu_keyboard():
#     return InlineKeyboardMarkup([
#         [InlineKeyboardButton("👛 Balance", callback_data="balance"),
#          InlineKeyboardButton("📊 Statistics", callback_data="statistics")],
#         [InlineKeyboardButton("🔗 Referral Link", callback_data="referral_link"),
#          InlineKeyboardButton("👥 My Referrals", callback_data="my_referrals")],
#         [InlineKeyboardButton("💳 Set Wallet", callback_data="set_wallet"),
#          InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
#         [InlineKeyboardButton("📩 Support", callback_data="support")]
#     ])


# # Admin Panel Commands
# @bot.on_message(filters.command("stats") & filters.private)
# @admin_only
# async def stats(_, message: Message):
#     total_users, total_withdrawals = db.get_stats()
#     await message.reply(
#         f"📊 **Bot Statistics**\n\n"
#         f"👤 Total Users: {total_users}\n"
#         f"💰 Total Withdrawals: {total_withdrawals} {db.get_setting('DEFAULT_CURRENCY')}"
#     )


# @bot.on_message(filters.command("set") & filters.private)
# @admin_only
# async def set_config(_, message: Message):
#     if len(message.command) < 3:
#         await message.reply("Usage: `/set <setting> <value>`\nExample: `/set MIN_WITHDRAW_AMOUNT 10`")
#         return

#     setting, value = message.command[1], " ".join(message.command[2:])
#     db.set_setting(setting, value)
#     await message.reply(f"✅ Setting `{setting}` updated to `{value}`.")


# @bot.on_message(filters.command("broadcast") & filters.private)
# @admin_only
# async def broadcast(_, message: Message):
#     if len(message.command) < 2:
#         await message.reply("Usage: `/broadcast <message>`")
#         return

#     text = message.text.split(" ", 1)[1]
#     users = db.db.users.find({})
#     count = 0

#     for user in users:
#         try:
#             await bot.send_message(user["_id"], text)
#             count += 1
#         except Exception:
#             pass

#     await message.reply(f"📢 Broadcast sent to `{count}` users.")


# # Start Command
# @bot.on_message(filters.command("start") & filters.private)
# async def start_command(_, message: Message):
#     user_id = message.from_user.id

#     # Extract referral ID if provided
#     ref_id = message.text.split(" ", 1)[1] if len(message.text.split()) > 1 else None

#     # Add user and handle referral
#     is_new_user = db.add_user(user_id)
#     if is_new_user:
#         if ref_id and ref_id.isdigit() and int(ref_id) != user_id:
#             ref_id = int(ref_id)
#             referrer = db.get_user(ref_id)

#             if referrer:  # Valid referrer
#                 db.add_referral(ref_id, user_id)
#                 referral_reward = int(db.get_setting("REFERRAL_REWARD", default=10))
#                 db.update_balance(ref_id, referral_reward)

#                 # Notify referrer
#                 try:
#                     await bot.send_message(
#                         ref_id,
#                         f"🎉 **Good News!**\n"
#                         f"👤 User `{message.from_user.mention}` joined using your referral link.\n"
#                         f"💰 Referral bonus of `{referral_reward} {db.get_setting('DEFAULT_CURRENCY')}` credited to your account!"
#                     )
#                 except Exception:
#                     pass  # Skip notification if referrer has blocked the bot or is unreachable

#     # Check Maintenance Mode
#     if db.get_setting("MAINTENANCE_MODE", default="off") == "on":
#         await message.reply("🚧 The bot is under maintenance. Please try again later.")
#         return

#     # Send Start Message
#     start_text = db.get_setting("START_MESSAGE", default="👋 Welcome to the bot!")
#     await message.reply(start_text, reply_markup=main_menu_keyboard())


# # Callback Queries for Main Menu Buttons
# @bot.on_callback_query(filters.regex("balance"))
# async def balance_callback(_, callback_query):
#     user_id = callback_query.from_user.id
#     balance = db.get_balance(user_id)
#     await callback_query.message.edit_text(
#         f"👛 **Your Balance:**\n\n`{balance} {db.get_setting('DEFAULT_CURRENCY')}`",
#         reply_markup=main_menu_keyboard()
#     )


# @bot.on_callback_query(filters.regex("withdraw"))
# async def withdraw_callback(_, callback_query):
#     user_id = callback_query.from_user.id
#     balance = db.get_balance(user_id)
#     min_withdraw = int(db.get_setting("MIN_WITHDRAW_AMOUNT", default=10))

#     if balance < min_withdraw:
#         await callback_query.message.edit_text(
#             f"❌ You need at least `{min_withdraw} {db.get_setting('DEFAULT_CURRENCY')}` to withdraw.",
#             reply_markup=main_menu_keyboard()
#         )
#         return

#     wallet = db.get_wallet(user_id)
#     if not wallet:
#         await callback_query.message.edit_text(
#             "❌ Please set your wallet address first.",
#             reply_markup=main_menu_keyboard()
#         )
#         return

#     withdrawal_channel = db.get_setting("WITHDRAWAL_CHANNEL_ID")
#     db.request_withdrawal(user_id, balance)

#     # Notify withdrawal channel
#     if withdrawal_channel:
#         await bot.send_message(
#             int(withdrawal_channel),
#             f"💸 **New Withdrawal Request:**\n\n"
#             f"👤 User ID: `{user_id}`\n"
#             f"💰 Amount: `{balance} {db.get_setting('DEFAULT_CURRENCY')}`\n"
#             f"💳 Wallet: `{wallet}`"
#         )

#     db.update_balance(user_id, -balance)
#     await callback_query.message.edit_text(
#         "✅ Your withdrawal request has been sent.",
#         reply_markup=main_menu_keyboard()
#     )


# # Support Callback
# @bot.on_callback_query(filters.regex("support"))
# async def support_callback(_, callback_query):
#     user_id = callback_query.from_user.id
#     await callback_query.message.edit_text(
#         "📩 **Support Request:**\n\nPlease describe your issue. Our admin will get back to you shortly.",
#         reply_markup=main_menu_keyboard()
#     )
#     db.set_user_stage(user_id, "SUPPORT")


# # Bot Startup
# print(f"🚀 Starting {Config.BOT_USERNAME}...")
# bot.run()
