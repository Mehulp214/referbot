import asyncio
import os
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from database import (
    user_data as ud,
    add_user,
    del_user,
    full_userbase,
    present_user,
    update_balance,
    update_referral_count,
    get_balance,
    clear_temp_referral,
    set_temp_referral,
    get_temp_referral,
)


# Bot Configurations
API_ID = int(os.getenv("API_ID", 13216322))
API_HASH = os.getenv("API_HASH", "15e5e632a8a0e52251ac8c3ccbe462c7")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7610980882:AAESQYI9Ca1pWSobokw1-S-QkVfTrja-Xdk")
ADMIN_IDS = [5993556795]  # Replace with your Telegram User IDs

FORCE_MSG = "You must join our channels to use this bot."
START_MSG = "Welcome, {first}!"
MAIN_MENU_MSG = "WELCOME TO MENU"

# Channels for Force Subscription
FORCE_SUB_CHANNELS = [-1002493977004]  # Add channel IDs here

# Initialize the bot
app = Client("ForceSubBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


# Helper Function to Check Subscription
async def check_subscription(client, user_id):
    for channel_id in FORCE_SUB_CHANNELS:
        try:
            member = await client.get_chat_member(channel_id, user_id)
            if member.status not in [
                ChatMemberStatus.OWNER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.MEMBER,
            ]:
                return False
        except UserNotParticipant:
            return False
        except Exception as e:
            print(f"Error checking subscription: {e}")
            return False
    return True
    await temp_main_menu(client,message)


# Middleware: Enforce subscription before proceeding
async def force_subscription(client, message):
    user_id = message.from_user.id
    if user_id in ADMIN_IDS:  # Skip subscription check for admins
        return True
    if not await check_subscription(client, user_id):
        buttons = []
        for channel_id in FORCE_SUB_CHANNELS:
            try:
                invite_link = await client.export_chat_invite_link(channel_id)
                buttons.append([InlineKeyboardButton("Join Channel", url=invite_link)])
            except Exception as e:
                print(f"Error creating invite link for {channel_id}: {e}")
        buttons.append(
            [InlineKeyboardButton("Check Subscription ✅", callback_data="check_subscription")]
        )
        await message.reply(
            FORCE_MSG, reply_markup=InlineKeyboardMarkup(buttons), quote=True
        )
        return False
    return True


# Command: Start
# Command: Start
@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    referral_code = None

    # Extract referral code from the start command
    if len(message.text.split()) > 1:
        referral_code = message.text.split()[1]

    # Check if user is already registered
    if await present_user(user_id):
        await message.reply(
            "You are already registered and cannot be referred by anyone."
        )
    else:
        # If not registered, allow referral if a valid referral code is provided
        if referral_code and referral_code != str(user_id):
            if await present_user(int(referral_code)):  # Ensure the referrer exists
                await update_referral_count(referral_code)  # Increment referral count
                await update_balance(int(referral_code), 10)  # Reward the referrer
                await add_user(user_id, referrer_id=int(referral_code))  # Add the new user with a referrer
            else:
                await message.reply("Invalid referral code. Proceeding without a referrer.")
                await add_user(user_id)  # Add the new user without a referrer
        else:
            # No referral code or invalid referral code
            await add_user(user_id)

    # Enforce force subscription
    if not await force_subscription(client, message):
        return

    # Send start message
    await temp_main_menu(client, message)
    # await message.reply(
    #     START_MSG.format(first=message.from_user.first_name),
    #     reply_markup=InlineKeyboardMarkup(
    #         [[InlineKeyboardButton("Main Menu", callback_data="main_menu")]]
    #     ),
    # )

#temporary main menu
async def temp_main_menu(client: Client, message: Message):
    user_id = message.from_user.id
    if not await check_subscription(client, user_id):
        await message.reply("You must join all required channels first.")
        return
    referrer_id = await get_temp_referral(user_id)
    if referrer_id:
        user_data = ud.find_one({'_id': user_id})  # Fetch user data explicitly
        if user_data and not user_data.get("referrer_id"):  # Reward only if no referrer is set
            await update_referral_count(referrer_id)
            await update_balance(int(referrer_id), 10)  # Reward the referrer with 10 units
            print(referrer_id)
            await set_temp_referral(user_id, None)  # Clear temporary referral data
            await add_user(user_id, referrer_id=referrer_id)  # Set referrer for the user
        else:
            print(f"User {user_id} already has a referrer set: {user_data['referrer_id']}")

    await message.reply(
        MAIN_MENU_MSG,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Check Balance", callback_data="check_balance")]]
        ),
    )

# Callback: Main Menu
@app.on_callback_query(filters.regex("main_menu"))
async def main_menu_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    if not await check_subscription(client, user_id):
        await callback_query.answer(
            "You must join all required channels first.", show_alert=True
        )
        return

    # Check if a referral reward is pending
    referrer_id = await get_temp_referral(user_id)
    if referrer_id:
        user_data = ud.find_one({'_id': user_id})  # Fetch user data explicitly
        if user_data and not user_data.get("referrer_id"):  # Reward only if no referrer is set
            await update_referral_count(referrer_id)
            await update_balance(int(referrer_id), 10)  # Reward the referrer with 10 units
            print(referrer_id)
            await set_temp_referral(user_id, None)  # Clear temporary referral data
            await add_user(user_id, referrer_id=referrer_id)  # Set referrer for the user
        else:
            print(f"User {user_id} already has a referrer set: {user_data['referrer_id']}")

    # Show main menu message
    await callback_query.message.edit_text(
        MAIN_MENU_MSG,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Check Balance", callback_data="check_balance")]]
        ),
    )




# Command: Balance
@app.on_message(filters.command("balance") & filters.private)
async def balance_command(client: Client, message: Message):
    if not await force_subscription(client, message):
        return

    user_id = message.from_user.id
    balance = await get_balance(user_id)
    await message.reply(f"Your current balance is: {balance} units.")


# Callback: Check Balance
@app.on_callback_query(filters.regex("check_balance"))
async def check_balance_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    balance = await get_balance(user_id)
    await callback_query.answer(f"Your current balance is: {balance} units.", show_alert=True)


# Callback: Check Subscription
@app.on_callback_query(filters.regex("check_subscription"))
async def check_subscription_callback(client: Client, callback_query):
    user_id = callback_query.from_user.id
    if await check_subscription(client, user_id):
        await callback_query.answer("Thank you for subscribing!", show_alert=True)
        await callback_query.message.delete()
    else:
        await callback_query.answer(
            "You still need to join the required channels.", show_alert=True
        )


# Command to View Balance
@app.on_message(filters.command("users") & filters.private & filters.user(ADMIN_IDS))
async def get_users(client: Client, message: Message):
    users = await full_userbase()
    await message.reply(f"There are {len(users)} users using this bot.")


# Broadcast Command
@app.on_message(filters.command("broadcast") & filters.private & filters.user(ADMIN_IDS))
async def broadcast_message(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply("Reply to a message to broadcast.")
        return

    users = await full_userbase()
    total = len(users)
    successful, blocked, deleted, unsuccessful = 0, 0, 0, 0

    pls_wait = await message.reply("<i>Broadcasting Message... This will take some time.</i>")
    for user_id in users:
        try:
            await message.reply_to_message.copy(user_id)
            successful += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await message.reply_to_message.copy(user_id)
            successful += 1
        except UserIsBlocked:
            await del_user(user_id)
            blocked += 1
        except InputUserDeactivated:
            await del_user(user_id)
            deleted += 1
        except Exception:
            unsuccessful += 1

    status = f"""<b>Broadcast Completed</b>
Total: {total}
Successful: {successful}
Blocked: {blocked}
Deleted: {deleted}
Failed: {unsuccessful}"""
    await pls_wait.edit(status)


@app.on_message(filters.command("add_balance") & filters.private)
async def add_command(client: Client, message: Message):
    user_id = message.from_user.id
    await update_balance(1932612943, 100)
    print(user_id)

#--------------==========================================================================================================================================================
import pymongo
from config import Config
dbclient = pymongo.MongoClient(Config.MONGO_URI)
database_name = dbclient["REFER_START"]
@app.on_message(filters.command("drop") & filters.private)
async def drop(client: Client, message: Message):
    # Drop the database using the client
    dbclient.drop_database(database_name)
    await message.reply("Database dropped.")
    print("DB DROPPED")

#========================================================================================================================================================================
    
# Run the bot
if __name__ == "__main__":
    app.run()
