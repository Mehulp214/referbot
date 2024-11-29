from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
from database import Database

db = Database(Config.MONGO_URI)

# Initialize Bot
bot = Client(
    "ReferAndEarnBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
)


# Define commands that only admins can use
def admin_only(func):
    async def wrapper(client, message: Message):
        if message.from_user.id not in Config.ADMIN_IDS:
            await message.reply("🚫 You are not authorized to use this command.")
            return
        return await func(client, message)
    return wrapper


# Main Menu Keyboard
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👛 Balance", callback_data="balance"),
         InlineKeyboardButton("📊 Statistics", callback_data="statistics")],
        [InlineKeyboardButton("🔗 Referral Link", callback_data="referral_link"),
         InlineKeyboardButton("👥 My Referrals", callback_data="my_referrals")],
        [InlineKeyboardButton("💳 Set Wallet", callback_data="set_wallet"),
         InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("📩 Support", callback_data="support")]
    ])


# Admin Panel Commands
@bot.on_message(filters.command("stats") & filters.private)
@admin_only
async def stats(_, message: Message):
    total_users, total_withdrawals = db.get_stats()
    await message.reply(
        f"📊 **Bot Statistics**\n\n"
        f"👤 Total Users: {total_users}\n"
        f"💰 Total Withdrawals: {total_withdrawals} {db.get_setting('DEFAULT_CURRENCY')}"
    )


@bot.on_message(filters.command("set") & filters.private)
@admin_only
async def set_config(_, message: Message):
    if len(message.command) < 3:
        await message.reply("Usage: `/set <setting> <value>`\nExample: `/set MIN_WITHDRAW_AMOUNT 10`")
        return

    setting, value = message.command[1], " ".join(message.command[2:])
    db.set_setting(setting, value)
    await message.reply(f"✅ Setting `{setting}` updated to `{value}`.")


@bot.on_message(filters.command("broadcast") & filters.private)
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
            await bot.send_message(user["_id"], text)
            count += 1
        except Exception:
            pass

    await message.reply(f"📢 Broadcast sent to `{count}` users.")


# Start Command
@bot.on_message(filters.command("start") & filters.private)
async def start_command(_, message: Message):
    user_id = message.from_user.id

    # Extract referral ID if provided
    ref_id = message.text.split(" ", 1)[1] if len(message.text.split()) > 1 else None

    # Add user and handle referral
    is_new_user = db.add_user(user_id)
    if is_new_user:
        if ref_id and ref_id.isdigit() and int(ref_id) != user_id:
            ref_id = int(ref_id)
            referrer = db.get_user(ref_id)

            if referrer:  # Valid referrer
                db.add_referral(ref_id, user_id)
                referral_reward = int(db.get_setting("REFERRAL_REWARD", default=10))
                db.update_balance(ref_id, referral_reward)

                # Notify referrer
                try:
                    await bot.send_message(
                        ref_id,
                        f"🎉 **Good News!**\n"
                        f"👤 User `{message.from_user.mention}` joined using your referral link.\n"
                        f"💰 Referral bonus of `{referral_reward} {db.get_setting('DEFAULT_CURRENCY')}` credited to your account!"
                    )
                except Exception:
                    pass  # Skip notification if referrer has blocked the bot or is unreachable

    # Check Maintenance Mode
    if db.get_setting("MAINTENANCE_MODE", default="off") == "on":
        await message.reply("🚧 The bot is under maintenance. Please try again later.")
        return

    # Send Start Message
    start_text = db.get_setting("START_MESSAGE", default="👋 Welcome to the bot!")
    await message.reply(start_text, reply_markup=main_menu_keyboard())


# Callback Queries for Main Menu Buttons
@bot.on_callback_query(filters.regex("balance"))
async def balance_callback(_, callback_query):
    user_id = callback_query.from_user.id
    balance = db.get_balance(user_id)
    await callback_query.message.edit_text(
        f"👛 **Your Balance:**\n\n`{balance} {db.get_setting('DEFAULT_CURRENCY')}`",
        reply_markup=main_menu_keyboard()
    )


@bot.on_callback_query(filters.regex("withdraw"))
async def withdraw_callback(_, callback_query):
    user_id = callback_query.from_user.id
    balance = db.get_balance(user_id)
    min_withdraw = int(db.get_setting("MIN_WITHDRAW_AMOUNT", default=10))

    if balance < min_withdraw:
        await callback_query.message.edit_text(
            f"❌ You need at least `{min_withdraw} {db.get_setting('DEFAULT_CURRENCY')}` to withdraw.",
            reply_markup=main_menu_keyboard()
        )
        return

    wallet = db.get_wallet(user_id)
    if not wallet:
        await callback_query.message.edit_text(
            "❌ Please set your wallet address first.",
            reply_markup=main_menu_keyboard()
        )
        return

    withdrawal_channel = db.get_setting("WITHDRAWAL_CHANNEL_ID")
    db.request_withdrawal(user_id, balance)

    # Notify withdrawal channel
    if withdrawal_channel:
        await bot.send_message(
            int(withdrawal_channel),
            f"💸 **New Withdrawal Request:**\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"💰 Amount: `{balance} {db.get_setting('DEFAULT_CURRENCY')}`\n"
            f"💳 Wallet: `{wallet}`"
        )

    db.update_balance(user_id, -balance)
    await callback_query.message.edit_text(
        "✅ Your withdrawal request has been sent.",
        reply_markup=main_menu_keyboard()
    )


# Support Callback
@bot.on_callback_query(filters.regex("support"))
async def support_callback(_, callback_query):
    user_id = callback_query.from_user.id
    await callback_query.message.edit_text(
        "📩 **Support Request:**\n\nPlease describe your issue. Our admin will get back to you shortly.",
        reply_markup=main_menu_keyboard()
    )
    db.set_user_stage(user_id, "SUPPORT")


# Bot Startup
print(f"🚀 Starting {Config.BOT_USERNAME}...")
bot.run()
