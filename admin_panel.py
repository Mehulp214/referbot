from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from database import Database

db = Database(Config.MONGO_URI)

# Define commands that only admins can use
def admin_only(func):
    async def wrapper(client, message: Message):
        if message.from_user.id not in Config.ADMIN_IDS:
            await message.reply("🚫 You are not authorized to use this command.")
            return
        return await func(client, message)
    return wrapper

# Admin Panel Commands
@Client.on_message(filters.command("stats") & filters.private)
@admin_only
async def stats(_, message: Message):
    total_users, total_withdrawals = db.get_stats()
    await message.reply(
        f"📊 **Bot Statistics**\n\n"
        f"👤 Total Users: {total_users}\n"
        f"💰 Total Withdrawals: {total_withdrawals} {Config.DEFAULT_CURRENCY}"
    )

@Client.on_message(filters.command("ban") & filters.private)
@admin_only
async def ban(_, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: `/ban <user_id>`")
        return

    user_id = int(message.command[1])
    db.ban_user(user_id)
    await message.reply(f"🚫 User `{user_id}` has been banned.")

@Client.on_message(filters.command("unban") & filters.private)
@admin_only
async def unban(_, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: `/unban <user_id>`")
        return

    user_id = int(message.command[1])
    db.unban_user(user_id)
    await message.reply(f"✅ User `{user_id}` has been unbanned.")

@Client.on_message(filters.command("add_balance") & filters.private)
@admin_only
async def add_balance(_, message: Message):
    if len(message.command) < 3:
        await message.reply("Usage: `/add_balance <user_id> <amount>`")
        return

    user_id = int(message.command[1])
    amount = int(message.command[2])
    db.update_balance(user_id, amount)
    await message.reply(f"💰 Added `{amount} {Config.DEFAULT_CURRENCY}` to user `{user_id}`.")

@Client.on_message(filters.command("deduct_balance") & filters.private)
@admin_only
async def deduct_balance(_, message: Message):
    if len(message.command) < 3:
        await message.reply("Usage: `/deduct_balance <user_id> <amount>`")
        return

    user_id = int(message.command[1])
    amount = int(message.command[2])
    db.update_balance(user_id, -amount)
    await message.reply(f"💸 Deducted `{amount} {Config.DEFAULT_CURRENCY}` from user `{user_id}`.")

@Client.on_message(filters.command("broadcast") & filters.private)
@admin_only
async def broadcast(_, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: `/broadcast <message>`")
        return

    text = message.text.split(" ", 1)[1]
    users = db.db.users.find({})
    count = 0

    for user in users:
        try:
            await _.send_message(user["_id"], text)
            count += 1
        except Exception:
            pass

    await message.reply(f"📢 Broadcast sent to `{count}` users.")

@Client.on_message(filters.command("user_info") & filters.private)
@admin_only
async def user_info(_, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: `/user_info <user_id>`")
        return

    user_id = int(message.command[1])
    user = db.get_user(user_id)
    if not user:
        await message.reply(f"❌ User `{user_id}` not found.")
        return

    referrals = user.get("referrals", [])
    await message.reply(
        f"👤 **User Info**\n\n"
        f"🆔 ID: {user['_id']}\n"
        f"💰 Balance: {user['balance']} {Config.DEFAULT_CURRENCY}\n"
        f"🏦 Wallet: {user['wallet'] or 'Not Set'}\n"
        f"👥 Referrals: {len(referrals)}\n"
        f"🚫 Banned: {'Yes' if user['is_banned'] else 'No'}"
    )

@Client.on_message(filters.command("maintenance") & filters.private)
@admin_only
async def maintenance(_, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: `/maintenance <on/off>`")
        return

    mode = message.command[1].lower()
    if mode == "on":
        db.db.settings.update_one({}, {"$set": {"maintenance": True}})
        await message.reply("⚙️ Maintenance mode is now ON.")
    elif mode == "off":
        db.db.settings.update_one({}, {"$set": {"maintenance": False}})
        await message.reply("⚙️ Maintenance mode is now OFF.")
    else:
        await message.reply("Invalid mode! Use `on` or `off`.")

