from pyrogram import Client, filters
from pyrogram.types import Message
from database import Database
import os

# Bot setup

API_ID = int(os.getenv("API_ID", 13216322))
API_HASH = os.getenv("API_HASH", "15e5e632a8a0e52251ac8c3ccbe462c7")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7610980882:AAESQYI9Ca1pWSobokw1-S-QkVfTrja-Xdk")
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://referandearn:Qwerty_1234@cluster0.dasly.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
ADMIN_ID = list(map(int, os.getenv("ADMIN_ID", "5993556795").split(",")))  # Admin Telegram IDs

app = Client("refer_and_earn_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# Database instance
db = Database(MONGO_URI)

# Admin ID (replace with your ID)
#ADMIN_ID = 123456789


# Helper function to restrict commands to admin only
def is_admin(func):
    async def wrapper(client: Client, message: Message):
        if message.from_user.id == ADMIN_ID:
            await func(client, message)
        else:
            await message.reply("🚫 You are not authorized to use this command.")
    return wrapper


@app.on_message(filters.command("stats") & filters.private)
@is_admin
async def stats(client: Client, message: Message):
    user_count = db.get_user_count()
    total_balance = db.get_total_balance()
    total_withdrawals, total_amount = db.get_withdrawal_stats()
    await message.reply_text(f"📊 Stats:\n"
                             f"👤 Total Users: {user_count}\n"
                             f"💰 Total Balance: {total_balance}\n"
                             f"✅ Completed Withdrawals: {total_withdrawals}\n"
                             f"💵 Total Withdrawn: {total_amount}")


@app.on_message(filters.command("add_channel") & filters.private)
@is_admin
async def add_channel(client: Client, message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        channel_id = args[1]
        db.add_to_array("fsub_channels", channel_id)
        await message.reply_text(f"✅ Channel {channel_id} added to FSub list.")
    else:
        await message.reply_text("❌ Please provide a channel ID.")


@app.on_message(filters.command("remove_channel") & filters.private)
@is_admin
async def remove_channel(client: Client, message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        channel_id = args[1]
        db.remove_from_array("fsub_channels", channel_id)
        await message.reply_text(f"✅ Channel {channel_id} removed from FSub list.")
    else:
        await message.reply_text("❌ Please provide a channel ID.")


@app.on_message(filters.command("set_currency") & filters.private)
@is_admin
async def set_currency(client: Client, message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        currency = args[1].upper()
        db.update_setting("currency", currency)
        await message.reply_text(f"✅ Currency set to {currency}.")
    else:
        await message.reply_text("❌ Please provide a currency code.")


@app.on_message(filters.command("set_refer_amount") & filters.private)
@is_admin
async def set_refer_amount(client: Client, message: Message):
    args = message.text.split(maxsplit=1)
    try:
        amount = int(args[1])
        db.update_setting("referral_reward", amount)
        await message.reply_text(f"✅ Referral amount set to {amount}.")
    except (IndexError, ValueError):
        await message.reply_text("❌ Please provide a valid amount.")


@app.on_message(filters.command("set_withdraw_amount") & filters.private)
@is_admin
async def set_withdraw_amount(client: Client, message: Message):
    args = message.text.split(maxsplit=1)
    try:
        amount = int(args[1])
        db.update_setting("min_withdraw_amount", amount)
        await message.reply_text(f"✅ Minimum withdrawal amount set to {amount}.")
    except (IndexError, ValueError):
        await message.reply_text("❌ Please provide a valid amount.")


@app.on_message(filters.command("broadcast") & filters.private)
@is_admin
async def broadcast(client: Client, message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        text = args[1]
        users = db.users.find()
        for user in users:
            try:
                await client.send_message(user["user_id"], text)
            except Exception:
                pass
        await message.reply_text("✅ Broadcast sent.")
    else:
        await message.reply_text("❌ Please provide a message to broadcast.")


@app.on_message(filters.command("user_info") & filters.private)
@is_admin
async def user_info(client: Client, message: Message):
    args = message.text.split(maxsplit=1)
    try:
        user_id = int(args[1])
        user = db.get_user_info(user_id)
        if user:
            await message.reply_text(f"👤 User Info:\n"
                                     f"ID: {user['user_id']}\n"
                                     f"Name: {user['name']}\n"
                                     f"Balance: {user['balance']}\n"
                                     f"Referrals: {user['referrals']}")
        else:
            await message.reply_text("❌ User not found.")
    except (IndexError, ValueError):
        await message.reply_text("❌ Please provide a valid user ID.")


@app.on_message(filters.command("add_balance") & filters.private)
@is_admin
async def add_balance(client: Client, message: Message):
    args = message.text.split(maxsplit=2)
    try:
        user_id = int(args[1])
        amount = int(args[2])
        db.update_balance(user_id, amount)
        await message.reply_text(f"✅ Added {amount} to user {user_id}'s balance.")
    except (IndexError, ValueError):
        await message.reply_text("❌ Please provide valid user ID and amount.")


@app.on_message(filters.command("remove_balance") & filters.private)
@is_admin
async def remove_balance(client: Client, message: Message):
    args = message.text.split(maxsplit=2)
    try:
        user_id = int(args[1])
        amount = int(args[2])
        db.update_balance(user_id, -amount)
        await message.reply_text(f"✅ Removed {amount} from user {user_id}'s balance.")
    except (IndexError, ValueError):
        await message.reply_text("❌ Please provide valid user ID and amount.")


@app.on_message(filters.command("maintenance") & filters.private)
@is_admin
async def maintenance(client: Client, message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) > 1 and args[1].lower() in ["on", "off"]:
        mode = args[1].lower() == "on"
        db.update_setting("maintenance_mode", mode)
        await message.reply_text(f"✅ Maintenance mode set to {args[1].upper()}.")
    else:
        await message.reply_text("❌ Use 'on' or 'off'.")


if __name__ == "__main__":
    app.run()
