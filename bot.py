from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
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


# Back to Menu Keyboard
def back_button_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]])

@bot.on_message(filters.command(["stats", "user_info", "reply"]) & filters.user(Config.ADMIN_IDS))
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
            referrer = db.users.find_one({"user_id": ref_id})

            if referrer:  # Valid referrer
                db.add_referral(ref_id, user_id)
                db.update_balance(ref_id, Config.REFERRAL_REWARD)

                # Notify referrer
                try:
                    await bot.send_message(
                        ref_id,
                        f"🎉 **Good News!**\n"
                        f"👤 User `{message.from_user.mention}` joined using your referral link.\n"
                        f"💰 Referral bonus of `{Config.REFERRAL_REWARD} {Config.DEFAULT_CURRENCY}` credited to your account!"
                    )
                except Exception:
                    pass  # Skip notification if referrer has blocked the bot or is unreachable

    # Check Maintenance Mode
    if db.is_maintenance_mode():
        await message.reply("🚧 The bot is under maintenance. Please try again later.")
        return

    # Send Start Message
    start_text = db.get_start_text() or f"👋 Welcome to {Config.BOT_NAME}! Earn rewards by referring others."
    await message.reply(start_text, reply_markup=main_menu_keyboard())


# Handle Main Menu Button
@bot.on_callback_query(filters.regex("main_menu"))
async def main_menu_callback(_, callback_query):
    await callback_query.message.edit_text("🏠 **Main Menu:**", reply_markup=main_menu_keyboard())


# Callback Queries for Other Buttons
@bot.on_callback_query(filters.regex("balance"))
async def balance_callback(_, callback_query):
    user_id = callback_query.from_user.id
    balance = db.get_balance(user_id)
    await callback_query.message.edit_text(
        f"👛 **Your Balance:**\n\n`{balance} {Config.DEFAULT_CURRENCY}`",
        reply_markup=back_button_keyboard()
    )


@bot.on_callback_query(filters.regex("statistics"))
async def statistics_callback(_, callback_query):
    user_id = callback_query.from_user.id
    total_referrals = len(db.get_referrals(user_id))
    balance = db.get_balance(user_id)
    await callback_query.message.edit_text(
        f"📊 **Your Statistics:**\n\n"
        f"👥 Total Referrals: {total_referrals}\n"
        f"💰 Balance: {balance} {Config.DEFAULT_CURRENCY}",
        reply_markup=back_button_keyboard()
    )


@bot.on_callback_query(filters.regex("referral_link"))
async def referral_link_callback(_, callback_query):
    user_id = callback_query.from_user.id
    referral_link = f"https://t.me/{Config.BOT_USERNAME}?start={user_id}"
    await callback_query.message.edit_text(
        f"🔗 **Your Referral Link:**\n\n`{referral_link}`\n\n"
        f"Share this link with friends to earn rewards!",
        reply_markup=back_button_keyboard()
    )


@bot.on_callback_query(filters.regex("my_referrals"))
async def my_referrals_callback(_, callback_query):
    user_id = callback_query.from_user.id
    referrals = db.get_referrals(user_id)
    referral_list = "\n".join([f"👤 {ref_id}" for ref_id in referrals]) or "No referrals yet."
    await callback_query.message.edit_text(
        f"👥 **Your Referrals:**\n\n{referral_list}",
        reply_markup=back_button_keyboard()
    )


@bot.on_callback_query(filters.regex("set_wallet"))
async def set_wallet_callback(_, callback_query):
    await callback_query.message.edit_text(
        "💳 **Set Wallet Address:**\n\nPlease reply with your wallet address to set it.",
        reply_markup=back_button_keyboard()
    )
    db.set_user_stage(callback_query.from_user.id, "SET_WALLET")


@bot.on_callback_query(filters.regex("withdraw"))
async def withdraw_callback(_, callback_query):
    user_id = callback_query.from_user.id
    balance = db.get_balance(user_id)

    if balance < Config.MIN_WITHDRAW_AMOUNT:
        await callback_query.message.edit_text(
            f"❌ You need at least `{Config.MIN_WITHDRAW_AMOUNT} {Config.DEFAULT_CURRENCY}` to withdraw.",
            reply_markup=back_button_keyboard()
        )
        return

    wallet = db.get_wallet(user_id)
    if not wallet:
        await callback_query.message.edit_text(
            "❌ Please set your wallet address first.",
            reply_markup=back_button_keyboard()
        )
        return

    db.request_withdrawal(user_id, balance)
    admin_ids = Config.ADMIN_IDS
    withdrawal_channel = Config.WITHDRAWAL_CHANNEL_ID

    # Notify withdrawal channel
    await bot.send_message(
        withdrawal_channel,
        f"💸 **New Withdrawal Request:**\n\n"
        f"👤 User ID: `{user_id}`\n"
        f"💰 Amount: `{balance} {Config.DEFAULT_CURRENCY}`\n"
        f"💳 Wallet: `{wallet}`"
    )

    # Notify admins
    for admin_id in admin_ids:
        await bot.send_message(
            admin_id,
            f"💸 **New Withdrawal Request:**\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"💰 Amount: `{balance} {Config.DEFAULT_CURRENCY}`\n"
            f"💳 Wallet: `{wallet}`"
        )

    db.update_balance(user_id, -balance)
    await callback_query.message.edit_text(
        "✅ Your withdrawal request has been sent.",
        reply_markup=back_button_keyboard()
    )


# Support Callback
@bot.on_callback_query(filters.regex("support"))
async def support_callback(_, callback_query):
    user_id = callback_query.from_user.id
    await callback_query.message.edit_text(
        "📩 **Support Request:**\n\nPlease describe your issue. Our admin will get back to you shortly.",
        reply_markup=back_button_keyboard()
    )
    db.set_user_stage(user_id, "SUPPORT")


# Message Handler for Setting Wallet and Support
@bot.on_message(filters.text & filters.private)
async def handle_text(_, message: Message):
    user_id = message.from_user.id
    user_stage = db.get_user_stage(user_id)

    if user_stage == "SET_WALLET":
        wallet = message.text.strip()
        db.set_wallet(user_id, wallet)
        db.set_user_stage(user_id, None)
        await message.reply("✅ Your wallet address has been set.", reply_markup=main_menu_keyboard())
    elif user_stage == "SUPPORT":
        issue = message.text.strip()
        referrals = db.get_referrals(user_id)
        referral_list = ", ".join(map(str, referrals)) or "No referrals"
        user_details = (
            f"👤 **User Details:**\n"
            f"ID: `{user_id}`\n"
            f"Name: `{message.from_user.first_name}`\n"
            f"Username: @{message.from_user.username or 'N/A'}\n"
            f"Referrals: {referral_list}\n"
            f"Issue: {issue}"
        )

        for admin_id in Config.ADMIN_IDS:
            await bot.send_message(
                admin_id,
                f"📩 **New Support Request:**\n\n{user_details}\n\n"
                f"Reply with `/reply {user_id} <message>` to respond."
            )

        db.set_user_stage(user_id, None)
        await message.reply("✅ Your support request has been submitted. Admin will contact you soon.", reply_markup=main_menu_keyboard())
    else:
        await message.reply("⚙️ Use the buttons to navigate.", reply_markup=main_menu_keyboard())


# Bot Startup
print(f"🚀 Starting {Config.BOT_USERNAME}...")
bot.run()
