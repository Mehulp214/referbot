from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from database import Database
from bot import bot

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
        await message.reply("Usage: /ban <user_id>")
        return

    user_id = int(message.command[1])
    db.ban_user(user_id)
    await message.reply(f"🚫 User {user_id} has been banned.")

@Client.on_message(filters.command("unban") & filters.private)
@admin_only
async def unban(_, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /unban <user_id>")
        return

    user_id = int(message.command[1])
    db.unban_user(user_id)
    await message.reply(f"✅ User {user_id} has been unbanned.")

@Client.on_message(filters.command("add_balance") & filters.private)
@admin_only
async def add_balance(_, message: Message):
    if len(message.command) < 3:
        await message.reply("Usage: /add_balance <user_id> <amount>")
        return

    user_id = int(message.command[1])
    amount = int(message.command[2])
    db.update_balance(user_id, amount)
    await message.reply(f"💰 Added {amount} {Config.DEFAULT_CURRENCY} to user {user_id}.")

@Client.on_message(filters.command("deduct_balance") & filters.private)
@admin_only
async def deduct_balance(_, message: Message):
    if len(message.command) < 3:
        await message.reply("Usage: /deduct_balance <user_id> <amount>")
        return

    user_id = int(message.command[1])
    amount = int(message.command[2])
    db.update_balance(user_id, -amount)
    await message.reply(f"💸 Deducted {amount} {Config.DEFAULT_CURRENCY} from user {user_id}.")

@bot.on_message(filters.private & filters.command('broadcast'))
@admins_only
async def broadcast(_, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /broadcast <message>")
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

    await message.reply(f"📢 Broadcast sent to {count} users.")

@Client.on_message(filters.command("user_info") & filters.private)
@admin_only
async def user_info(_, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /user_info <user_id>")
        return

    user_id = int(message.command[1])
    user = db.get_user(user_id)
    if not user:
        await message.reply(f"❌ User {user_id} not found.")
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
        await message.reply("Usage: /maintenance <on/off>")
        return

    mode = message.command[1].lower()
    if mode == "on":
        db.db.settings.update_one({}, {"$set": {"maintenance": True}})
        await message.reply("⚙️ Maintenance mode is now ON.")
    elif mode == "off":
        db.db.settings.update_one({}, {"$set": {"maintenance": False}})
        await message.reply("⚙️ Maintenance mode is now OFF.")
    else:
        await message.reply("Invalid mode! Use on or off.")





# Admin Commands

@Client.on_message(filters.command("set_min_withdraw") & filters.private)
@admin_only
async def set_min_withdraw(_, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /set_min_withdraw <amount>")
        return

    amount = int(message.command[1])
    db.update_setting("min_withdraw", amount)
    await message.reply(f"✅ Minimum withdrawal amount set to {amount}.")

@Client.on_message(filters.command("set_currency") & filters.private)
@admin_only
async def set_currency(_, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /set_currency <currency>")
        return

    currency = message.command[1]
    db.update_setting("default_currency", currency)
    await message.reply(f"✅ Default currency set to {currency}.")

@Client.on_message(filters.command("set_referral_reward") & filters.private)
@admin_only
async def set_referral_reward(_, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /set_referral_reward <amount>")
        return

    reward = int(message.command[1])
    db.update_setting("referral_reward", reward)
    await message.reply(f"✅ Referral reward set to {reward}.")

@Client.on_message(filters.command("set_withdraw_channel") & filters.private)
@admin_only
async def set_withdraw_channel(_, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /set_withdraw_channel <channel_id>")
        return

    channel_id = int(message.command[1])
    db.update_setting("withdraw_channel", channel_id)
    await message.reply(f"✅ Withdrawal channel set to {channel_id}.")

@Client.on_message(filters.command("set_start_message") & filters.private)
@admin_only
async def set_start_message(_, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /set_start_message <message>")
        return

    start_message = message.text.split(" ", 1)[1]
    db.update_setting("start_message", start_message)
    await message.reply(f"✅ Start message updated.")

@Client.on_message(filters.command("add_fsub") & filters.private)
@admin_only
async def add_fsub(_, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /add_fsub <channel_id>")
        return

    channel_id = int(message.command[1])
    db.add_to_array("fsub_channels", channel_id)
    await message.reply(f"✅ Channel {channel_id} added to forced subscription.")

@Client.on_message(filters.command("remove_fsub") & filters.private)
@admin_only
async def remove_fsub(_, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /remove_fsub <channel_id>")
        return

    channel_id = int(message.command[1])
    db.remove_from_array("fsub_channels", channel_id)
    await message.reply(f"✅ Channel {channel_id} removed from forced subscription.")


this is admin_panel.py


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
                        f"👤 User {message.from_user.mention} joined using your referral link.\n"
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
        f"👛 **Your Balance:**\n\n{balance} {currency}",
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
        f"🔗 **Your Referral Link:**\n\n{referral_link}\n\n"
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
            f"❌ You need at least {Config.MIN_WITHDRAW_AMOUNT} {Config.DEFAULT_CURRENCY} to withdraw.",
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
        f"👤 User ID: {user_id}\n"
        f"💰 Amount: {balance} {Config.DEFAULT_CURRENCY}\n"
        f"💳 Wallet: {wallet}"
    )

    # Notify admins
    for admin_id in admin_ids:
        await bot.send_message(
            admin_id,
            f"💸 **New Withdrawal Request:**\n\n"
            f"👤 User ID: {user_id}\n"
            f"💰 Amount: {balance} {Config.DEFAULT_CURRENCY}\n"
            f"💳 Wallet: {wallet}"
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
                f"Reply with /reply {user_id} <message> to respond."
            )

        db.set_user_stage(user_id, None)
        await message.reply("✅ Your support request has been submitted. Admin will contact you soon.", reply_markup=main_menu_keyboard())
    else:
        pass


# Bot Startup
print(f"🚀 Starting {Config.BOT_USERNAME}...")
bot.run()
