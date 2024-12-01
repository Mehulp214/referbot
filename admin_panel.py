# from pyrogram import Client, filters
# from pyrogram.types import Message
# from database import Database
# import os

# # Bot setup

# API_ID = int(os.getenv("API_ID", 13216322))
# API_HASH = os.getenv("API_HASH", "15e5e632a8a0e52251ac8c3ccbe462c7")
# BOT_TOKEN = os.getenv("BOT_TOKEN", "7610980882:AAESQYI9Ca1pWSobokw1-S-QkVfTrja-Xdk")
# MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://referandearn:Qwerty_1234@cluster0.dasly.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
# ADMIN_ID = list(map(int, os.getenv("ADMIN_ID", "5993556795").split(",")))  # Admin Telegram IDs

# app = Client("refer_and_earn_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# # Database instance
# db = Database(MONGO_URI)

# # Admin ID (replace with your ID)
# ADMIN_ID = 5993556795


# # Helper function to restrict commands to admin only
# def is_admin(func):
#     async def wrapper(client: Client, message: Message):
#         if message.from_user.id == ADMIN_ID:
#             await func(client, message)
#         else:
#             await message.reply("🚫 You are not authorized to use this command.")
#     return wrapper


# @app.on_message(filters.command("stats") & filters.private)
# @is_admin
# async def stats(client: Client, message: Message):
#     user_count = db.get_user_count()
#     total_balance = db.get_total_balance()
#     total_withdrawals, total_amount = db.get_withdrawal_stats()
#     await message.reply_text(f"📊 Stats:\n"
#                              f"👤 Total Users: {user_count}\n"
#                              f"💰 Total Balance: {total_balance}\n"
#                              f"✅ Completed Withdrawals: {total_withdrawals}\n"
#                              f"💵 Total Withdrawn: {total_amount}")


# @app.on_message(filters.command("add_channel") & filters.private)
# @is_admin
# async def add_channel(client: Client, message: Message):
#     args = message.text.split(maxsplit=1)
#     if len(args) > 1:
#         channel_id = args[1]
#         db.add_to_array("fsub_channels", channel_id)
#         await message.reply_text(f"✅ Channel {channel_id} added to FSub list.")
#     else:
#         await message.reply_text("❌ Please provide a channel ID.")


# @app.on_message(filters.command("remove_channel") & filters.private)
# @is_admin
# async def remove_channel(client: Client, message: Message):
#     args = message.text.split(maxsplit=1)
#     if len(args) > 1:
#         channel_id = args[1]
#         db.remove_from_array("fsub_channels", channel_id)
#         await message.reply_text(f"✅ Channel {channel_id} removed from FSub list.")
#     else:
#         await message.reply_text("❌ Please provide a channel ID.")


# @app.on_message(filters.command("set_currency") & filters.private)
# @is_admin
# async def set_currency(client: Client, message: Message):
#     args = message.text.split(maxsplit=1)
#     if len(args) > 1:
#         currency = args[1].upper()
#         db.update_setting("currency", currency)
#         await message.reply_text(f"✅ Currency set to {currency}.")
#     else:
#         await message.reply_text("❌ Please provide a currency code.")


# @app.on_message(filters.command("set_refer_amount") & filters.private)
# @is_admin
# async def set_refer_amount(client: Client, message: Message):
#     args = message.text.split(maxsplit=1)
#     try:
#         amount = int(args[1])
#         db.update_setting("referral_reward", amount)
#         await message.reply_text(f"✅ Referral amount set to {amount}.")
#     except (IndexError, ValueError):
#         await message.reply_text("❌ Please provide a valid amount.")


# @app.on_message(filters.command("set_withdraw_amount") & filters.private)
# @is_admin
# async def set_withdraw_amount(client: Client, message: Message):
#     args = message.text.split(maxsplit=1)
#     try:
#         amount = int(args[1])
#         db.update_setting("min_withdraw_amount", amount)
#         await message.reply_text(f"✅ Minimum withdrawal amount set to {amount}.")
#     except (IndexError, ValueError):
#         await message.reply_text("❌ Please provide a valid amount.")


# @app.on_message(filters.command("broadcast") & filters.private)
# @is_admin
# async def broadcast(client: Client, message: Message):
#     args = message.text.split(maxsplit=1)
#     if len(args) > 1:
#         text = args[1]
#         users = db.users.find()
#         for user in users:
#             try:
#                 await client.send_message(user["user_id"], text)
#             except Exception:
#                 pass
#         await message.reply_text("✅ Broadcast sent.")
#     else:
#         await message.reply_text("❌ Please provide a message to broadcast.")


# @app.on_message(filters.command("user_info") & filters.private)
# @is_admin
# async def user_info(client: Client, message: Message):
#     args = message.text.split(maxsplit=1)
#     try:
#         user_id = int(args[1])
#         user = db.get_user_info(user_id)
#         if user:
#             await message.reply_text(f"👤 User Info:\n"
#                                      f"ID: {user['user_id']}\n"
#                                      f"Name: {user['name']}\n"
#                                      f"Balance: {user['balance']}\n"
#                                      f"Referrals: {user['referrals']}")
#         else:
#             await message.reply_text("❌ User not found.")
#     except (IndexError, ValueError):
#         await message.reply_text("❌ Please provide a valid user ID.")


# @app.on_message(filters.command("add_balance") & filters.private)
# @is_admin
# async def add_balance(client: Client, message: Message):
#     args = message.text.split(maxsplit=2)
#     try:
#         user_id = int(args[1])
#         amount = int(args[2])
#         db.update_balance(user_id, amount)
#         await message.reply_text(f"✅ Added {amount} to user {user_id}'s balance.")
#     except (IndexError, ValueError):
#         await message.reply_text("❌ Please provide valid user ID and amount.")


# @app.on_message(filters.command("remove_balance") & filters.private)
# @is_admin
# async def remove_balance(client: Client, message: Message):
#     args = message.text.split(maxsplit=2)
#     try:
#         user_id = int(args[1])
#         amount = int(args[2])
#         db.update_balance(user_id, -amount)
#         await message.reply_text(f"✅ Removed {amount} from user {user_id}'s balance.")
#     except (IndexError, ValueError):
#         await message.reply_text("❌ Please provide valid user ID and amount.")


# @app.on_message(filters.command("maintenance") & filters.private)
# @is_admin
# async def maintenance(client: Client, message: Message):
#     args = message.text.split(maxsplit=1)
#     if len(args) > 1 and args[1].lower() in ["on", "off"]:
#         mode = args[1].lower() == "on"
#         db.update_setting("maintenance_mode", mode)
#         await message.reply_text(f"✅ Maintenance mode set to {args[1].upper()}.")
#     else:
#         await message.reply_text("❌ Use 'on' or 'off'.")




# if __name__ == "__main__":
#     app.run()

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import random, string
from database import Database
import os

# Bot setup
API_ID = int(os.getenv("API_ID", 13216322))
API_HASH = os.getenv("API_HASH", "15e5e632a8a0e52251ac8c3ccbe462c7")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7610980882:AAESQYI9Ca1pWSobokw1-S-QkVfTrja-Xdk")
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://referandearn:Qwerty_1234@cluster0.dasly.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
ADMIN_ID = list(map(int, os.getenv("ADMIN_ID", "5993556795").split(",")))  # Admin Telegram IDs

ADMIN_ID=5993556795
app = Client("refer_and_earn_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# Database instance
db = Database(MONGO_URI)

# Helper function to restrict commands to admin only
def is_admin(func):
    async def wrapper(client: Client, message: Message):
        if message.from_user.id == ADMIN_ID:
            await func(client, message)
        else:
            await message.reply("🚫 You are not authorized to use this command.")
    return wrapper


# Admin commands
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


# User functions
def generate_referral_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Balance", callback_data="balance"),
            InlineKeyboardButton("📊 Statistics", callback_data="statistics"),
        ],
        [
            InlineKeyboardButton("🔗 Referral Link", callback_data="referral_link"),
            InlineKeyboardButton("🤝 Referrals", callback_data="my_referrals"),
        ],
        [
            InlineKeyboardButton("🏦 Wallet", callback_data="set_wallet"),
            InlineKeyboardButton("📤 Withdraw", callback_data="withdraw"),
        ],
        [
            InlineKeyboardButton("📞 Support", callback_data="support")
        ]
    ])


@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    ref_code = message.text.split(" ")[1] if len(message.text.split()) > 1 else None

    if not db.get_user_info(user_id):
        referral_code = generate_referral_code()
        referrer_id = db.get_user_id_by_referral_code(ref_code) if ref_code else None
        db.add_user(user_id, name, referral_code, referrer_id)
    await message.reply("👋 Welcome!", reply_markup=main_menu())

# Balance handler
@app.on_callback_query(filters.regex("balance"))
async def balance(client: Client, callback_query):
    user_id = callback_query.from_user.id
    balance = db.get_total_balance(user_id)
    await callback_query.message.edit_text(
        f"💰 Your Balance: {balance} {db.get_setting('currency')}",
        reply_markup=main_menu()
    )


# Statistics handler

@app.on_callback_query(filters.regex("statistics"))
async def statistics(client: Client, callback_query):
    user_id = callback_query.from_user.id
    referrals = db.get_user_referrals(user_id)
    balance = db.get_user_balance(user_id)
    await callback_query.message.edit_text(
        f"📊 Your Stats:\n"
        f"👥 Referrals: {referrals}\n"
        f"💰 Balance: {balance} {db.get_setting('currency')}",
        reply_markup=main_menu()
    )



# Referral link handler
@app.on_callback_query(filters.regex("referral_link"))
async def referral_link(client: Client, callback_query):
    user_id = callback_query.from_user.id
    bot_info = await client.get_me()
    referral_code = db.get_user_referral_code(user_id)

    if referral_code:
        referral_link = f"https://t.me/{bot_info.username}?start={referral_code}"
        await callback_query.message.edit_text(
            f"🔗 Your Referral Link: {referral_link}",
            reply_markup=main_menu()
        )
    else:
        await callback_query.message.edit_text(
            "❌ You don't have a referral code. Please contact support.",
            reply_markup=main_menu()
        )



# Referrals handler
@app.on_callback_query(filters.regex("my_referrals"))
async def my_referrals(client: Client, callback_query):
    user_id = callback_query.from_user.id
    referrals = db.get_referrals(user_id)
    if referrals:
        referrals_text = "\n".join([f"{i + 1}. {ref}" for i, ref in enumerate(referrals)])
    else:
        referrals_text = "❌ You don't have any referrals yet."
    await callback_query.message.edit_text(
        f"🤝 Your Referrals:\n\n{referrals_text}",
        reply_markup=main_menu()
    )





# Withdraw handler
@app.on_callback_query(filters.regex("withdraw"))
async def withdraw(client: Client, callback_query):
    user_id = callback_query.from_user.id
    balance = db.get_user_balance(user_id)
    min_withdraw = db.get_setting("min_withdraw_amount")
    if balance >= min_withdraw:
        db.withdraw(user_id, balance)
        await callback_query.message.edit_text("✅ Withdrawal successful!", reply_markup=main_menu())
    else:
        await callback_query.message.edit_text(f"❌ Your balance is less than the minimum withdrawal amount ({min_withdraw}).", reply_markup=main_menu())

# Support handler
# Support handler
@app.on_callback_query(filters.regex("support"))
async def support(client: Client, callback_query):
    """
    Handles the support button click. Prompts the user to type a message for the admin.
    """
    user_id = callback_query.from_user.id
    db.update_setting(f"user_support_mode_{user_id}", True)  # Set user in support mode
    await callback_query.message.edit_text(
        "📩 Please type your message for the admin. They will respond as soon as possible.\n"
        "If you'd like to exit support mode, type /cancel.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
        ])
    )


@app.on_message(filters.text & filters.private)
async def handle_support_or_wallet(client: Client, message: Message):
    """
    Handles support messages or wallet input based on the user's current mode.
    """
    user_id = message.from_user.id
    user_support_mode = db.get_setting2(f"user_support_mode_{user_id}")

    if user_support_mode:
        # Send support message to admin
        await client.send_message(
            ADMIN_ID, 
            f"📩 Support message from {user_id}:\n\n{message.text}"
        )
        await message.reply_text("✅ Your message has been sent to the admin.")
        db.update_setting2(f"user_support_mode_{user_id}", False)  # Exit support mode

    elif db.get_setting2(f"user_wallet_mode_{user_id}"):
        # Handle wallet input
        wallet = message.text.strip()
        valid_starts = ["0x", "bc1", "ltc", "bnb"]  # Add more valid prefixes
        if any(wallet.startswith(prefix) for prefix in valid_starts) and len(wallet) > 10:
            db.set_wallet(user_id, wallet)
            await message.reply_text("✅ Wallet set successfully!")
            db.update_setting2(f"user_wallet_mode_{user_id}", False)  # Exit wallet mode
        else:
            await message.reply_text(
                "❌ Invalid wallet address. Please ensure it starts with a valid prefix (e.g., 0x, bc1) "
                "and is properly formatted."
            )
    else:
        await message.reply_text(
            "⚠️ Please use the buttons from the menu to access features."
        )


# Set wallet handler
@app.on_callback_query(filters.regex("set_wallet"))
async def set_wallet(client: Client, callback_query):
    """
    Prompts the user to enter their wallet address.
    """
    user_id = callback_query.from_user.id
    db.update_setting2(f"user_wallet_mode_{user_id}", True)  # Set user in wallet mode
    await callback_query.message.edit_text(
        "💳 Please enter your wallet address.\n"
        "If you'd like to exit, type /cancel.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
        ])
    )


# Cancel handler to exit modes
@app.on_message(filters.command("cancel") & filters.private)
async def cancel_mode(client: Client, message: Message):
    """
    Cancels any active modes (support or wallet entry).
    """
    user_id = message.from_user.id
    db.update_setting2(f"user_support_mode_{user_id}", False)
    db.update_setting2(f"user_wallet_mode_{user_id}", False)
    await message.reply_text("❌ Operation cancelled.", reply_markup=main_menu())



if __name__ == "__main__":
    app.run()


