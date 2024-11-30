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
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu_keyboard")]])

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

# Message Handler for Admin Commands or Stages
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
            f"ID: {user_id}\n"
            f"Name: {message.from_user.first_name}\n"
            f"Username: @{message.from_user.username or 'N/A'}\n"
            f"Referrals: {referral_list}\n"
            f"Issue: {issue}"
        )

        for admin_id in Config.ADMIN_IDS:
            await bot.send_message(
                admin_id,
                f"📩 **New Support Request:**\n\n{user_details}\n\n"
                f"Reply with /reply `{user_id}` <message> to respond."
            )

        db.set_user_stage(user_id, None)
        await message.reply("✅ Your support request has been submitted. Admin will contact you soon.", reply_markup=main_menu_keyboard())

# Admin Commands Handler
@bot.on_message(filters.command(['reply','broadcast','stats']) & filters.user(Config.ADMIN_IDS))
async def handle_admin_commands(_, message: Message):
    command = message.command[0].lower()
    await message.reply(f"⚙️ Executing command: `{command}`. Please use appropriate bot functions.")

@bot.on_message(filters.private & filters.command('broadcast'))
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
        except Exception as e:
            print(e)

    await message.reply(f"📢 Broadcast sent to `{count}` users.")

# Bot Startup
print(f"🚀 Starting {Config.BOT_USERNAME}...")
bot.run()
