from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from database import Database
import os 

# Bot Configurations
API_ID = int(os.getenv("API_ID", 13216322))
API_HASH = os.getenv("API_HASH", "15e5e632a8a0e52251ac8c3ccbe462c7")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7610980882:AAESQYI9Ca1pWSobokw1-S-QkVfTrja-Xdk")
MONGO_URI = "mongodb+srv://referandearn:Qwerty_1234@cluster0.dasly.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "refer_bot_2"
ADMIN_ID = 5993556795  # Replace with your Telegram User ID






# Channels for Force Subscription
FORCE_SUB_CHANNELS = [-1002493977004]  # Add channel IDs here

# Initialize the bot
app = Client("ForceSubBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


# Helper Function to Check Subscription
async def is_user_subscribed(client, user_id):
    unsubscribed_channels = []
    for channel_id in FORCE_SUB_CHANNELS:
        try:
            member = await client.get_chat_member(channel_id, user_id)
            if member.status not in ("member", "administrator", "creator"):
                unsubscribed_channels.append(channel_id)
        except Exception as e:
            print(f"Error checking subscription for channel {channel_id}: {e}")
            unsubscribed_channels.append(channel_id)
    return unsubscribed_channels


# Start Command with Force Subscription
@app.on_message(filters.command("start") & filters.private)
async def start(client: Client, message: Message):
    user_id = message.from_user.id
    unsubscribed_channels = await is_user_subscribed(client, user_id)

    if unsubscribed_channels:
        # Generate dynamic buttons for unsubscribed channels
        buttons = []
        for channel_id in unsubscribed_channels:
            try:
                invite_link = await client.export_chat_invite_link(channel_id)
                buttons.append([InlineKeyboardButton("Join Channel", url=invite_link)])
            except Exception as e:
                print(f"Error generating invite link for channel {channel_id}: {e}")

        # Add a "Try Again" button
        buttons.append([
            InlineKeyboardButton(
                "✅ I've Subscribed",
                callback_data="check_subscription"
            )
        ])

        await message.reply(
            "Please join all the channels below to use this bot:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        # User is subscribed to all channels, proceed
        await message.reply(
            "Welcome! 🎉 You have successfully subscribed to all required channels. Enjoy using the bot!"
        )


# Callback Query Handler to Recheck Subscription
@app.on_callback_query(filters.regex("check_subscription"))
async def verify_subscription(client, query):
    user_id = query.from_user.id
    unsubscribed_channels = await is_user_subscribed(client, user_id)

    if unsubscribed_channels:
        # User still hasn't subscribed to all channels
        buttons = []
        for channel_id in unsubscribed_channels:
            try:
                invite_link = await client.export_chat_invite_link(channel_id)
                buttons.append([InlineKeyboardButton("Join Channel", url=invite_link)])
            except Exception as e:
                print(f"Error generating invite link for channel {channel_id}: {e}")

        buttons.append([
            InlineKeyboardButton(
                "✅ I've Subscribed",
                callback_data="check_subscription"
            )
        ])

        await query.message.edit_text(
            "You're still not subscribed to all required channels. Please complete the subscription:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        # User has subscribed to all channels
        await query.message.edit_text(
            "Thank you for subscribing! You can now use the bot. 🎉"
        )


# Run the bot
if __name__ == "__main__":
    app.run()
