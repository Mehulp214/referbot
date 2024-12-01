from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database

# Bot Configurations
API_ID = int(os.getenv("API_ID", 13216322))
API_HASH = os.getenv("API_HASH", "15e5e632a8a0e52251ac8c3ccbe462c7")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7610980882:AAESQYI9Ca1pWSobokw1-S-QkVfTrja-Xdk")
MONGO_URI = "mongodb+srv://referandearn:Qwerty_1234@cluster0.dasly.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "refer_bot_2"
ADMIN_ID = 5993556795  # Replace with your Telegram User ID

# Force Subscription Channels
CHANNELS = ["@Channel1", "@Channel2", "@Channel3"]

# Initialize Bot and Database
app = Client("ReferAndEarnBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
db = Database(MONGO_URI, DB_NAME)

# Helper Function: Check Subscription
async def check_subscription(user_id):
    unsubscribed_channels = []
    for channel in CHANNELS:
        try:
            member = await app.get_chat_member(channel, user_id)
            if member.status not in ("member", "administrator", "creator"):
                unsubscribed_channels.append(channel)
        except:
            unsubscribed_channels.append(channel)
    return unsubscribed_channels

# Start Command
@app.on_message(filters.command("start") & filters.private)
async def start(bot, message):
    user_id = message.from_user.id
    referrer_id = message.text.split(" ")[1] if len(message.text.split()) > 1 else None

    # Add user to database
    db.add_user(user_id, referrer_id)

    # Check subscription status
    unsubscribed_channels = await check_subscription(user_id)
    if unsubscribed_channels:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Subscribe to {channel}", url=f"https://t.me/{channel.replace('@', '')}")]
            for channel in unsubscribed_channels
        ] + [[InlineKeyboardButton("✅ I've Subscribed to All", callback_data="check_subscription")]])
        
        await message.reply(
            "Please subscribe to the channels below to use the bot:",
            reply_markup=keyboard
        )
        return

    # Send referral link
    ref_link = f"https://t.me/{app.me.username}?start={user_id}"
    await message.reply(
        f"Welcome to the Refer and Earn Bot!\n\n"
        f"Your referral link: {ref_link}\n\n"
        f"Invite friends and earn rewards!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Share Referral Link", url=f"https://t.me/share/url?url={ref_link}")]
        ])
    )

# Callback Query Handler for Subscription Check
@app.on_callback_query(filters.regex("check_subscription"))
async def verify_subscription(bot, query):
    user_id = query.from_user.id
    unsubscribed_channels = await check_subscription(user_id)
    if unsubscribed_channels:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Subscribe to {channel}", url=f"https://t.me/{channel.replace('@', '')}")]
            for channel in unsubscribed_channels
        ] + [[InlineKeyboardButton("✅ I've Subscribed to All", callback_data="check_subscription")]])
        
        await query.message.edit_text(
            "You're not subscribed to all required channels. Please complete the subscription:",
            reply_markup=keyboard
        )
        return

    await query.message.edit_text("Thank you for subscribing! You can now use the bot.")

# Broadcast Command (Admin Only)
@app.on_message(filters.command("broadcast") & filters.user(ADMIN_ID))
async def broadcast(bot, message):
    if len(message.command) < 2:
        await message.reply("Usage: /broadcast <message>")
        return

    text = message.text.split(None, 1)[1]
    users = db.get_all_users()
    success, failed = 0, 0
    for user in users:
        try:
            await bot.send_message(user["_id"], text)
            success += 1
        except:
            failed += 1

    await message.reply(f"Broadcast completed: {success} success, {failed} failed.")

# Run the Bot
app.run()
