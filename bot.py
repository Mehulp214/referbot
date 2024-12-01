from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import random, string
from database import Database
from admin_panel import app,MONGO_URI,ADMIN_IDS

db = Database(MONGO_URI)
ADMIN_IDS = ADMIN_ID

def generate_referral_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))



def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("📊 Statistics", callback_data="statistics")],
        [InlineKeyboardButton("🔗 My Referral Link", callback_data="referral_link")],
        [InlineKeyboardButton("🤝 My Referrals", callback_data="my_referrals")],
        [InlineKeyboardButton("🏦 Set Wallet", callback_data="set_wallet")],
        [InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("📞 Support", callback_data="support")]
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

# # Helper function to generate random referral codes
# def generate_referral_code():
#     return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

# Notify admins about new user
async def notify_admins_about_user(user):
    for admin_id in ADMIN_IDS:
        try:
            await app.send_message(
                admin_id,
                f"🚀 New User Joined:\n"
                f"👤 Name: {user['name']}\n"
                f"🆔 ID: {user['user_id']}\n"
                f"🔗 Referral: {user.get('referrer', 'None')}"
            )
        except Exception:
            pass

# Notify referrer about new referral
async def notify_referrer(referrer_id, referral_name):
    try:
        await app.send_message(
            referrer_id,
            f"🎉 Someone joined using your referral link!\n"
            f"👤 Name: {referral_name}"
        )
    except Exception:
        pass

# # Main menu keyboard
# def main_menu():
#     return InlineKeyboardMarkup([
#         [InlineKeyboardButton("💰 Balance", callback_data="balance")],
#         [InlineKeyboardButton("📊 Statistics", callback_data="statistics")],
#         [InlineKeyboardButton("🔗 My Referral Link", callback_data="referral_link")],
#         [InlineKeyboardButton("🤝 My Referrals", callback_data="my_referrals")],
#         [InlineKeyboardButton("🏦 Set Wallet", callback_data="set_wallet")],
#         [InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")],
#         [InlineKeyboardButton("📞 Support", callback_data="support")]
#     ])

# # Start command
# @app.on_message(filters.command("start") & filters.private)
# async def start(client: Client, message: Message):
#     user_id = message.from_user.id
#     name = message.from_user.first_name
#     ref_code = message.text.split(" ")[1] if len(message.text.split()) > 1 else None

#     user = db.get_user_info(user_id)
#     if not user:
#         referral_code = generate_referral_code()
#         referrer_id = db.get_user_id_by_referral_code(ref_code) if ref_code else None
#         db.add_user(user_id, name, referral_code, referrer_id)
        
#         # Notify admins and referrer
#         await notify_admins_about_user({"user_id": user_id, "name": name, "referrer": ref_code})
#         if referrer_id:
#             await notify_referrer(referrer_id, name)

#     await message.reply(f"👋 Welcome, {name}!\nUse the menu below to navigate.", reply_markup=main_menu())

# Balance handler
@app.on_callback_query(filters.regex("balance"))
async def balance(client: Client, callback_query):
    user_id = callback_query.from_user.id
    balance = db.get_user_balance(user_id)
    await callback_query.message.edit_text(f"💰 Your Balance: {balance} {db.get_setting('currency')}", reply_markup=main_menu())

# Statistics handler
@app.on_callback_query(filters.regex("statistics"))
async def statistics(client: Client, callback_query):
    user_id = callback_query.from_user.id
    referrals = db.get_user_referrals(user_id)
    await callback_query.message.edit_text(f"📊 Statistics:\n"
                                           f"🔗 Referrals: {len(referrals)}\n"
                                           f"💰 Balance: {db.get_user_balance(user_id)} {db.get_setting('currency')}", reply_markup=main_menu())

# Referral link handler
@app.on_callback_query(filters.regex("referral_link"))
async def referral_link(client: Client, callback_query):
    user_id = callback_query.from_user.id
    referral_code = db.get_user_referral_code(user_id)
    await callback_query.message.edit_text(f"🔗 Your Referral Link:\nhttps://t.me/{app.me.username}?start={referral_code}", reply_markup=main_menu())

# My referrals handler
@app.on_callback_query(filters.regex("my_referrals"))
async def my_referrals(client: Client, callback_query):
    user_id = callback_query.from_user.id
    referrals = db.get_user_referrals(user_id)
    await callback_query.message.edit_text(f"🤝 Your Referrals:\n" + "\n".join(referrals) if referrals else "You have no referrals yet.", reply_markup=main_menu())

# Set wallet handler
@app.on_callback_query(filters.regex("set_wallet"))
async def set_wallet(client: Client, callback_query):
    await callback_query.message.edit_text("🏦 Send your wallet address to set it.")

    @app.on_message(filters.text & filters.private)
    async def receive_wallet(client: Client, message: Message):
        wallet = message.text
        db.update_wallet(message.from_user.id, wallet)
        await message.reply("✅ Wallet updated!", reply_markup=main_menu())
        app.remove_handler(receive_wallet)

# Withdraw handler
@app.on_callback_query(filters.regex("withdraw"))
async def withdraw(client: Client, callback_query):
    user_id = callback_query.from_user.id
    balance = db.get_user_balance(user_id)
    min_withdraw_amount = db.get_setting("min_withdraw_amount")

    if balance < min_withdraw_amount:
        await callback_query.message.edit_text(f"❌ Minimum withdrawal amount is {min_withdraw_amount} {db.get_setting('currency')}.", reply_markup=main_menu())
    else:
        await callback_query.message.edit_text("📤 Send the amount you want to withdraw.")

        @app.on_message(filters.text & filters.private)
        async def receive_withdraw(client: Client, message: Message):
            try:
                amount = int(message.text)
                if amount > balance:
                    await message.reply("❌ Insufficient balance.", reply_markup=main_menu())
                else:
                    wallet = db.get_user_wallet(user_id)
                    if not wallet:
                        await message.reply("❌ Please set your wallet first.", reply_markup=main_menu())
                        return

                    db.update_balance(user_id, -amount)
                    db.add_withdraw_request(user_id, amount)
                    
                    # Notify withdrawal channel and admins
                    withdrawal_details = f"📤 Withdrawal Request:\n👤 User: {message.from_user.first_name}\n🆔 ID: {user_id}\n💵 Amount: {amount}\n🏦 Wallet: {wallet}"
                    await app.send_message(db.get_setting("withdraw_channel"), withdrawal_details)
                    for admin_id in ADMIN_IDS:
                        await app.send_message(admin_id, withdrawal_details)

                    await message.reply("✅ Withdrawal request sent!", reply_markup=main_menu())
                    app.remove_handler(receive_withdraw)
            except ValueError:
                await message.reply("❌ Please enter a valid amount.")

# Support handler
@app.on_callback_query(filters.regex("support"))
async def support(client: Client, callback_query):
    await callback_query.message.edit_text("📞 Send your message, document, or image for support.")

    @app.on_message(filters.private & (filters.text | filters.document | filters.photo))
    async def receive_support(client: Client, message: Message):
        for admin_id in ADMIN_IDS:
            await message.copy(admin_id)
        await message.reply("✅ Your message has been sent to support!", reply_markup=main_menu())
        app.remove_handler(receive_support)

# if __name__ == "__main__":
#     app.run()

if __name__ == "__main__":
    app.run()

