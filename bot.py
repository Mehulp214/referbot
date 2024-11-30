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


# Forced Subscription Check
async def check_fsub(user_id):
    fsub_channels = db.get_fsub_channels()
    for channel in fsub_channels:
        try:
            member = await bot.get_chat_member(channel, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False, channel
        except Exception:
            return False, channel
    return True, None


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
                db.update_balance(ref_id, db.get_setting("referral_reward"))

                # Notify referrer
                try:
                    await bot.send_message(
                        ref_id,
                        f"🎉 **Good News!**\n"
                        f"👤 User `{message.from_user.mention}` joined using your referral link.\n"
                        f"💰 Referral bonus credited to your account!"
                    )
                except Exception:
                    pass  # Skip notification if referrer has blocked the bot or is unreachable

    # Check Maintenance Mode
    if db.is_maintenance_mode():
        await message.reply("🚧 The bot is under maintenance. Please try again later.")
        return

    # Check Forced Subscription
    is_member, channel = await check_fsub(user_id)
    if not is_member:
        await message.reply(
            f"📢 **Please join our channel first to use the bot!**\n\n"
            f"👉 [Join Channel](https://t.me/{channel})",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Joined", callback_data="check_fsub")]
            ]),
            disable_web_page_preview=True
        )
        return

    # Send Start Message
    start_text = db.get_start_text() or "👋 Welcome! Start earning rewards by referring others."
    await message.reply(start_text, reply_markup=main_menu_keyboard())


# Handle "Joined" Button
@bot.on_callback_query(filters.regex("check_fsub"))
async def joined_callback(_, callback_query):
    user_id = callback_query.from_user.id
    is_member, channel = await check_fsub(user_id)

    if is_member:
        await callback_query.message.edit_text("✅ You have successfully joined! Use the menu below:", reply_markup=main_menu_keyboard())
    else:
        await callback_query.answer("❌ You must join the required channels first.", show_alert=True)


# Callback Queries for Menu Buttons
@bot.on_callback_query(filters.regex("balance"))
async def balance_callback(_, callback_query):
    user_id = callback_query.from_user.id
    balance = db.get_balance(user_id)
    currency = db.get_setting("default_currency")
    await callback_query.message.edit_text(
        f"👛 **Your Balance:**\n\n`{balance} {currency}`",
        reply_markup=back_button_keyboard()
    )


@bot.on_callback_query(filters.regex("statistics"))
async def statistics_callback(_, callback_query):
    user_id = callback_query.from_user.id
    total_referrals = len(db.get_referrals(user_id))
    balance = db.get_balance(user_id)
    currency = db.get_setting("default_currency")
    await callback_query.message.edit_text(
        f"📊 **Your Statistics:**\n\n"
        f"👥 Total Referrals: {total_referrals}\n"
        f"💰 Balance: {balance} {currency}",
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


# Other callback queries for "My Referrals," "Set Wallet," etc., remain the same


# Bot Startup
print(f"🚀 Starting {Config.BOT_USERNAME}...")
bot.run()
