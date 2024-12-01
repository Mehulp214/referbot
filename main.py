from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from database import Database
import os 

# Bot Configurations
API_ID = int(os.getenv("API_ID", 13216322))
API_HASH = os.getenv("API_HASH", "15e5e632a8a0e52251ac8c3ccbe462c7")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7610980882:AAESQYI9Ca1pWSobokw1-S-QkVfTrja-Xdk")
MONGO_URI = "mongodb+srv://referandearn:Qwerty_1234@cluster0.dasly.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "refer_bot_2"
ADMIN_ID = 5993556795  # Replace with your Telegram User ID



FORCE_MSG="JOIN OUR CHANNELS"
START_MSG="JOIN OUR CHANNELS"

@Bot.on_message(filters.command('start') & filters.private & subscribed)
async def start_command(client: Client, message: Message):
    id = message.from_user.id
    if not await present_user(id):
        try:
            await add_user(id)
        except:
            pass
    text = message.text
    reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("😊 About Me", callback_data = "about"),
                    InlineKeyboardButton("🔒 Close", callback_data = "close")
                ]
            ]
        )
        await message.reply_text(
            text = START_MSG.format(
                first = message.from_user.first_name,
                last = message.from_user.last_name,
                username = None if not message.from_user.username else '@' + message.from_user.username,
                mention = message.from_user.mention,
                id = message.from_user.id
            ),
            reply_markup = reply_markup,
            disable_web_page_preview = True,
            quote = True
        )
        return

# Channels for Force Subscription
FORCE_SUB_CHANNELS = [-1002493977004]  # Add channel IDs here

# Initialize the bot
app = Client("ForceSubBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

FORCE_MSG="JOIN OUR CHANNELS"


# Helper Function to Check Subscription
async def is_subscribed(filter, client, update):
    if not FORCE_SUB_CHANNEL:
        return True
    
    user_id = update.from_user.id
    if user_id in ADMINS:
        return True

    for channel_id in FORCE_SUB_CHANNEL:
        try:
            member = await client.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
                return False  # If the user is not a member of any channel, return False
        except UserNotParticipant:
            return False  # If the user is not a member of any channel, return False

    return True  # If the loop completes without returning False, return True

subscribed = filters.create(is_subscribed)

# Start Command with Force Subscription
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

@Client.on_message(filters.command("start") & filters.private)
async def not_joined(client: Client, message: Message):
    buttons = []

    for channel_id in FORCE_SUB_CHANNELS:
        try:
            invite_link = await client.export_chat_invite_link(channel_id)
            buttons.append([InlineKeyboardButton("Join Channel", url=invite_link)])
        except Exception as e:
            print(f"Error generating invite link for channel {channel_id}: {e}")

    try:
        buttons.append(
            [InlineKeyboardButton(
                text='Try Again',
                url=f"https://t.me/{client.username}?start={message.command[1]}" if len(message.command) > 1 else f"https://t.me/{client.username}?start"
            )]
        )
    except IndexError:
        pass

    try:
        sent_message = await message.reply(
        text=FORCE_MSG.format(
            first=message.from_user.first_name,
            last=message.from_user.last_name,
            username=None if not message.from_user.username else '@' + message.from_user.username,
            mention=message.from_user.mention,
            id=message.from_user.id
        ),
        reply_markup=InlineKeyboardMarkup(buttons),
        quote=True,
        disable_web_page_preview=True
    )
    except Exception as e:
        print(f"Error while sending message: {e}")



# Run the bot
if __name__ == "__main__":
    app.run()
