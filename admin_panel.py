from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, ReplyKeyboardButton
from database import Database
import os

# Environment Variables
API_ID = int(os.getenv("API_ID", 13216322))
API_HASH = os.getenv("API_HASH", "15e5e632a8a0e52251ac8c3ccbe462c7")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7610980882:AAESQYI9Ca1pWSobokw1-S-QkVfTrja-Xdk")
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://referandearn:Qwerty_1234@cluster0.dasly.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "5993556795").split(",")))  # Admin IDs as a comma-separated string
WITHDRAW_CHANNEL = int(os.getenv("WITHDRAW_CHANNEL", -1002493977004))  # Withdrawal notification channel

# Initialize bot and database
app = Client("refer_and_earn_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)
db = Database(MONGO_URI)

# Global dictionary to track user states
user_states = {}  # Dictionary to track user states
ADMIN_IDS=[5993556795]

# Helper Functions
def is_admin(func):
    async def wrapper(client: Client, message: Message):
        if message.from_user.id in ADMIN_IDS:
            await func(client, message)
        else:
            await message.reply("🚫 You are not authorized to use this command.")
    return wrapper


# Main Menu (Updated to ReplyKeyboardMarkup)
def main_menu():
    return ReplyKeyboardMarkup([
        [ReplyKeyboardButton("💰 Balance"), ReplyKeyboardButton("📊 Statistics")],
        [ReplyKeyboardButton("🔗 Referral Link"), ReplyKeyboardButton("🤝 Referrals")],
        [ReplyKeyboardButton("🏦 Set Wallet"), ReplyKeyboardButton("📤 Withdraw")],
        [ReplyKeyboardButton("📞 Support")]
    ], resize_keyboard=True)


# Bot Commands
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    ref_code = message.text.split(" ")[1] if len(message.text.split()) > 1 else None

    # Add user to database if not exists
    if not db.get_user_info(user_id):
        referral_code = db.generate_referral_code()
        referrer_id = db.get_user_id_by_referral_code(ref_code) if ref_code else None
        db.add_user(user_id, name, referral_code, referrer_id)

    await message.reply("👋 Welcome to the Refer and Earn Bot!", reply_markup=main_menu())


@app.on_callback_query(filters.regex("balance"))
async def balance(client, callback_query):
    user_id = callback_query.from_user.id
    balance = db.get_user_balance(user_id)
    await callback_query.message.edit_text(
        f"💰 Your Balance: {balance} {db.get_setting('currency')}",
        reply_markup=main_menu()
    )


@app.on_callback_query(filters.regex("statistics"))
async def statistics(client, callback_query):
    user_id = callback_query.from_user.id
    referrals = db.get_user_referrals(user_id)
    balance = db.get_user_balance(user_id)
    await callback_query.message.edit_text(
        f"📊 Your Stats:\n"
        f"👥 Referrals: {referrals}\n"
        f"💰 Balance: {balance} {db.get_setting('currency')}",
        reply_markup=main_menu()
    )


@app.on_callback_query(filters.regex("referral_link"))
async def referral_link(client, callback_query):
    user_id = callback_query.from_user.id
    referral_code = db.get_user_referral_code(user_id)
    if referral_code:
        bot_info = await client.get_me()  # Get bot username dynamically
        referral_link = f"https://t.me/{bot_info.username}?start={referral_code}"
        await callback_query.message.edit_text(
            f"🔗 Your Referral Link: {referral_link}",
            reply_markup=main_menu()  # To keep navigation consistent
        )
    else:
        await callback_query.message.edit_text(
            "❌ You do not have a referral code yet. Contact support for assistance.",
            reply_markup=main_menu()
        )


@app.on_callback_query(filters.regex("referrals"))
async def referrals(client, callback_query):
    user_id = callback_query.from_user.id
    referrals = db.get_referrals(user_id)
    referrals_text = "\n".join([f"{i+1}. {ref['name']} (ID: {ref['id']})" for i, ref in enumerate(referrals)]) or "❌ No referrals yet."
    await callback_query.message.edit_text(
        f"🤝 Your Referrals:\n\n{referrals_text}",
        reply_markup=main_menu()
    )


@app.on_callback_query(filters.regex("set_wallet"))
async def set_wallet(client, callback_query):
    user_id = callback_query.from_user.id
    await callback_query.message.edit_text(
        "💼 Please enter your wallet address:",
        reply_markup=ReplyKeyboardMarkup([
            [ReplyKeyboardButton("Cancel")]
        ], resize_keyboard=True)
    )

    # Change state to awaiting wallet input
    user_states[user_id] = "awaiting_wallet"


@app.on_message(filters.private)
async def collect_wallet(client, message):
    user_id = message.from_user.id
    if user_states.get(user_id) == "awaiting_wallet":
        wallet_address = message.text.strip()
        db.set_wallet(user_id, wallet_address)
        user_states.pop(user_id)  # Clear state
        await message.reply(f"✅ Your wallet address has been updated to: {wallet_address}", reply_markup=main_menu())
    


@app.on_callback_query(filters.regex("cancel_set_wallet"))
async def cancel_set_wallet(client, callback_query):
    user_id = callback_query.from_user.id
    user_states.pop(user_id, None)  # Remove state if exists
    await callback_query.message.edit_text("❌ Wallet setting canceled.", reply_markup=main_menu())


@app.on_callback_query(filters.regex("withdraw"))
async def withdraw(client, callback_query):
    user_id = callback_query.from_user.id
    balance = db.get_user_balance(user_id)
    min_withdraw = db.get_setting("min_withdraw_amount")
    referrals = db.get_user_referrals(user_id)

    if balance >= min_withdraw:
        db.withdraw(user_id, balance)
        # Notify withdrawal channel
        withdraw_details = f"👤 User: {callback_query.from_user.first_name}\n" \
                           f"🆔 ID: {user_id}\n" \
                           f"💰 Amount: {balance}\n" \
                           f"👥 Referrals: {referrals}"
        await app.send_message(WITHDRAW_CHANNEL, withdraw_details)
        await callback_query.message.edit_text("✅ Withdrawal successful!", reply_markup=main_menu())
    else:
        await callback_query.message.edit_text(
            f"❌ Your balance is less than the minimum withdrawal amount ({min_withdraw}).",
            reply_markup=main_menu()
        )


# Admin Commands and Other Functionality
# Your remaining admin and other bot commands remain unchanged...


# Admin Commands
@app.on_message(filters.command("broadcast") & filters.private)
@is_admin
async def broadcast(client, message):
    text = message.text.split(maxsplit=1)[1]
    users = db.get_all_users()
    for user in users:
        try:
            await client.send_message(user["user_id"], text)
        except Exception:
            pass
    await message.reply("✅ Broadcast sent.")


@app.on_message(filters.command("stats") & filters.private)
@is_admin
async def stats(client, message):
    total_users = db.get_user_count()
    total_balance = db.get_total_balance()
    await message.reply(f"📊 Stats:\n👥 Total Users: {total_users}\n💰 Total Balance: {total_balance}")


@app.on_message(filters.command("user_info") & filters.private)
@is_admin
async def user_info(client, message):
    user_id = int(message.text.split()[1])
    user = db.get_user_info(user_id)
    if user:
        referrals = db.get_user_referrals(user_id)
        await message.reply(f"👤 User Info:\n🆔 ID: {user['user_id']}\n💰 Balance: {user['balance']}\n👥 Referrals: {referrals}")
    else:
        await message.reply("❌ User not found.")


@app.on_message(filters.command("add_balance") & filters.private)
@is_admin
async def add_balance(client, message):
    user_id, amount = map(int, message.text.split()[1:])
    db.update_balance(user_id, amount)
    await message.reply(f"✅ Added {amount} to user {user_id}'s balance.")


@app.on_message(filters.command("remove_balance") & filters.private)
@is_admin
async def remove_balance(client, message):
    user_id, amount = map(int, message.text.split()[1:])
    db.update_balance(user_id, -amount)
    await message.reply(f"✅ Removed {amount} from user {user_id}'s balance.")


if __name__ == "__main__":
    app.run()
