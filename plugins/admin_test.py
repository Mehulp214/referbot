import pymongo
import asyncio
from datetime import datetime
from bot import marimo as app
from pyrogram import filters
from pyromod import listen
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from config import *
from database import *

dbclient = pymongo.MongoClient(Config.MONGO_URI)
database_name = dbclient["REFER_START"]

# Main admin panel
# @app.on_message(filters.command("admin_panel") & filters.user(ADMIN_IDS))
# async def admin_panel(client, message: Message):
#     keyboard = InlineKeyboardMarkup([
#         [
#             InlineKeyboardButton("Manage Fsub Channels", callback_data="manage_fsub")#manage_fsub
#         ],
#         [
#             InlineKeyboardButton("View Referrals", callback_data="view_referrals"),
#             InlineKeyboardButton("Add Balance", callback_data="add_balance")
#         ],
#         [
#             InlineKeyboardButton("Broadcast", callback_data="broadcast"),
#             InlineKeyboardButton("Check Balance", callback_data="check_balance")
#         ]
#     ])
#     await message.reply("Welcome to the Admin Panel. Choose an action:", reply_markup=keyboard)

# # Callback query handler for the admin panel
# @app.on_callback_query()
# async def admin_callback_handler(client, callback_query: CallbackQuery):
#     data = callback_query.data

#     if data == "view_referrals":
#         await handle_view_referrals(client, callback_query)
#     elif data == "add_balance":
#         await handle_add_balance(client, callback_query)
#     elif data == "broadcast":
#         await handle_broadcast(client, callback_query)
#     elif data == "check_balance":
#         await handle_check_balance(client, callback_query)
#     elif data == "back_to_admin_panel":
#         await admin_panel(client, callback_query.message)
#     elif data == "manage_fsub":
#         await fsub_manage_callback(client, callback_query)


# async def add_fsub(client, callback_query):
#     await callback_query.message.reply_text("Send the channel ID to add:")
#     print(get_fsub_channels())
#     try:
#         response = await app.listen(callback_query.message.chat.id, timeout=60)
#         channel_id = response.text.strip()
#         add_fsub_channel(int(channel_id))  # Call function to add channel
#         await callback_query.message.reply_text(f"Channel ID {channel_id} added successfully!")
#     except asyncio.TimeoutError:
#         await callback_query.message.reply_text("Timeout! No input received.")
        
# ## Fsub Management Panel
# async def fsub_manage_callback(client, callback: CallbackQuery):
#     keyboard = InlineKeyboardMarkup([
#         [
#             InlineKeyboardButton("Add Fsub Channel", callback_data="add_fsub"),
#             InlineKeyboardButton("Remove Fsub Channel", callback_data="remove_fsub")
#         ],
#         [
#             InlineKeyboardButton("View Fsub Channels", callback_data="action:view_fsub"),
#             InlineKeyboardButton("Back to Admin Panel", callback_data="back_to_admin_panel")
#         ]
#     ])
#     await callback.message.edit_text("Fsub Channel Management:", reply_markup=keyboard)

# async def remove_fsub(client, callback_query):
#     await callback_query.message.reply_text("Send the channel ID to remove:")
#     try:
#         response = await app.listen(callback_query.message.chat.id, timeout=60)
#         channel_id = response.text.strip()
#         remove_fsub_channel(int(channel_id))  # Call function to add channel
#         await callback_query.message.reply_text(f"Channel ID {channel_id} removed successfully!")
#     except asyncio.TimeoutError:
#         await callback_query.message.reply_text("Timeout! No input received.")

# @app.on_callback_query()
# async def admin_callback_handler(client, callback_query: CallbackQuery):
#     data = callback_query.data

#     if data == "add_fsub":
#         await add_fsub(client, callback_query)
#     elif data == "remove_fsub":
#         await remove_fsub(client, callback_query)


@app.on_message(filters.command("admin_panel") & filters.user(ADMIN_IDS))
async def admin_panel(client, message: Message):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Manage Fsub Channels", callback_data="manage_fsub")
        ],
        [
            InlineKeyboardButton("View Referrals", callback_data="view_referrals"),
            InlineKeyboardButton("Add Balance", callback_data="add_balance")
        ],
        [
            InlineKeyboardButton("Broadcast", callback_data="broadcast"),
            InlineKeyboardButton("Check Balance", callback_data="check_balance")
        ]
    ])
    await message.reply("Welcome to the Admin Panel. Choose an action:", reply_markup=keyboard)

async def add_fsub(client, callback_query):
    await callback_query.message.reply_text("Send the channel ID to add:")
    try:
        response = await app.listen(callback_query.message.chat.id, timeout=60)
        channel_id = response.text.strip()
        add_fsub_channel(int(channel_id))  # Call function to add channel
        await callback_query.message.reply_text(f"Channel ID {channel_id} added successfully!")
    except asyncio.TimeoutError:
        await callback_query.message.reply_text("Timeout! No input received.")

async def remove_fsub(client, callback_query):
    await callback_query.message.reply_text(f"Send the channel ID to remove: \n\n {get_fsub_channels()}\n FROM THESE CHANNEL ONLY")
    try:
        response = await app.listen(callback_query.message.chat.id, timeout=60)
        channel_id = response.text.strip()
        remove_fsub_channel(int(channel_id))  # Call function to remove channel
        await callback_query.message.reply_text(f"Channel ID {channel_id} removed successfully!")
    except asyncio.TimeoutError:
        await callback_query.message.reply_text("Timeout! No input received.")


async def view_fsub(client, callback_query):
    try:
        dynamic_channels = get_fsub_channels()
        static_channels = FORCE_SUB_CHANNELS
        all_channels = list(set(dynamic_channels + static_channels))

        channel_details = []
        c=0
        for channel_id in all_channels:
           try:
                chat = await client.get_chat(channel_id)  # Fetch channel details
                invite_link = chat.invite_link or await client.export_chat_invite_link(channel_id)
                c=c+1
                channel_details.append(f"{c}. [{chat.title}]({invite_link})")
            except Exception as e:
                print(f"Error fetching details for {channel_id}: {e}")
                channel_details.append(f"Channel ID: {channel_id}")

        formatted_message = "These are the Force Sub channels:\n\n" + "\n".join(channel_details)
        await callback_query.message.reply_text(
            formatted_message, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )
    except Exception as e:
        print(f"Error in view_fsub: {e}")
        await callback_query.message.reply_text("An error occurred while fetching Force Sub channels.")


async def fsub_manage_callback(client, callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Add Fsub Channel", callback_data="add_fsub"),
            InlineKeyboardButton("Remove Fsub Channel", callback_data="remove_fsub")
        ],
        [
            InlineKeyboardButton("View Fsub Channels", callback_data="view_fsub"),
            InlineKeyboardButton("Back to Admin Panel", callback_data="back_to_admin_panel")
        ]
    ])
    await callback.message.edit_text("Fsub Channel Management:", reply_markup=keyboard)

@app.on_callback_query()
async def admin_callback_handler(client, callback_query: CallbackQuery):
    data = callback_query.data

    if data == "view_referrals":
        await handle_view_referrals(client, callback_query)
    elif data == "add_balance":
        await handle_add_balance(client, callback_query)
    elif data == "broadcast":
        await handle_broadcast(client, callback_query)
    elif data == "check_balance":
        await handle_check_balance(client, callback_query)
    elif data == "back_to_admin_panel":
        await admin_panel(client, callback_query.message)
    elif data == "manage_fsub":
        await fsub_manage_callback(client, callback_query)
    elif data == "add_fsub":
        await add_fsub(client, callback_query)
    elif data == "remove_fsub":
        await remove_fsub(client, callback_query)
    elif data == "view_fsub":
        await view_fsub(client, callback_query)


# View referrals handler
async def handle_view_referrals(client, callback_query):
    await callback_query.message.reply(
        "Please enter the user ID to view referrals or type 'cancel' to go back.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back_to_admin_panel")]])
    )
    try:
        response = await client.listen(callback_query.message.chat.id, timeout=120)
        if response.text.lower() == "cancel":
            await callback_query.message.reply("Action canceled.")
            return
        user_id = int(response.text)
        ref_count = user_data.count_documents({"referrer_id": user_id})
        referred_users = list(user_data.find({"referrer_id": user_id}))
        referral_details = []
        for index, user in enumerate(referred_users, 1):
            referred_user_id = user['_id']
            try:
                user_info = await client.get_users(referred_user_id)
                full_name = user_info.first_name + (" " + user_info.last_name if user_info.last_name else "")
            except Exception:
                full_name = "Unknown"
            referral_details.append(
                f"{index}. User ID: {referred_user_id}, Name: **{full_name}**\n"
            )
        referral_details_text = "\n".join(referral_details) if referral_details else "No referrals yet."
        await callback_query.message.reply(
            f"Referral Count: {ref_count}\n\nReferral Details:\n{referral_details_text}",
            disable_web_page_preview=True
        )
    except asyncio.TimeoutError:
        await callback_query.message.reply("Timeout. No input received.")

# Add balance handler
async def handle_add_balance(client, callback_query):
    await callback_query.message.reply(
        "Please enter the user ID and amount to add (use - for subtract), separated by a space (e.g., 12345 100), or type 'cancel' to go back.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back_to_admin_panel")]])
    )
    try:
        response = await client.listen(callback_query.message.chat.id, timeout=120)
        if response.text.lower() == "cancel":
            await callback_query.message.reply("Action canceled.")
            return
        user_id, temp_amount = map(int, response.text.split())
        await update_balance(user_id, temp_amount)
        user = await client.get_users(user_id)
        full_name = user.first_name + (" " + user.last_name if user.last_name else "")
        await callback_query.message.reply(f"{temp_amount} credited to user {user_id} - {full_name}.")
    except (ValueError, asyncio.TimeoutError):
        await callback_query.message.reply("Invalid input or timeout.")

# Broadcast handler
async def handle_broadcast(client, callback_query):
    await callback_query.message.reply(
        "Please reply to a message to broadcast it to all users.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back_to_admin_panel")]])
    )
    try:
        response = await client.listen(callback_query.message.chat.id, timeout=120)
        if not response.reply_to_message:
            await callback_query.message.reply("You need to reply to a message for broadcasting.")
            return
        users = await full_userbase()
        successful, blocked, deleted, unsuccessful = 0, 0, 0, 0
        for user_id in users:
            try:
                await response.reply_to_message.copy(user_id)
                successful += 1
            except UserIsBlocked:
                await del_user(user_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(user_id)
                deleted += 1
            except Exception:
                unsuccessful += 1
        await callback_query.message.reply(
            f"Broadcast completed.\nSuccessful: {successful}\nBlocked: {blocked}\nDeleted: {deleted}\nFailed: {unsuccessful}"
        )
    except asyncio.TimeoutError:
        await callback_query.message.reply("Timeout. No input received.")






# Check balance handler
async def handle_check_balance(client, callback_query):
    await callback_query.message.reply(
        "Please enter the user ID to check balance or type 'cancel' to go back.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back_to_admin_panel")]])
    )
    try:
        response = await client.listen(callback_query.message.chat.id, timeout=120)
        if response.text.lower() == "cancel":
            await callback_query.message.reply("Action canceled.")
            return
        user_id = int(response.text)
        balance = await get_balance(user_id)
        await callback_query.message.reply(f"User's current balance: {balance} units.")
    except (ValueError, asyncio.TimeoutError):
        await callback_query.message.reply("Invalid input or timeout.")
