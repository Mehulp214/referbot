import pymongo
import asyncio
from datetime import datetime
from bot import marimo as app
from pyrogram import filters
from pyromod import listen
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from config import *
from database import *

dbclient = pymongo.MongoClient(Config.MONGO_URI)
database_name = dbclient["REFER_START"]

# Main admin panel
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

# Callback query handler for the admin panel
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
        await fsub_manage_callback(client, callback)

# Fsub Management Panel
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
    await callback.message.edit("Fsub Channel Management:", reply_markup=keyboard)



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


@app.on_callback_query(filters.regex("^(add_fsub|remove_fsub|view_fsub)$"))
async def handle_fsub_action(client, callback: CallbackQuery):
    action = callback.data

    if action == "add_fsub":
        await callback.message.edit("Send the channel ID to add:")
        try:
            user_response = await app.listen(callback.message.chat.id, timeout=60)
            channel_id = user_response.text.strip()
            add_fsub_channel(channel_id)
            await callback.message.reply(f"Channel ID {channel_id} added successfully!")
        except asyncio.TimeoutError:
            await callback.message.reply("Timeout! No input received.")

    elif action == "remove_fsub":
        await callback.message.edit("Send the channel ID to remove:")
        try:
            user_response = await app.listen(callback.message.chat.id, timeout=60)
            channel_id = user_response.text.strip()
            remove_fsub_channel(channel_id)
            await callback.message.reply(f"Channel ID {channel_id} removed successfully!")
        except asyncio.TimeoutError:
            await callback.message.reply("Timeout! No input received.")

    elif action == "view_fsub":
        channels = get_fsub_channels()
        if channels:
            channel_list = "\n".join(channels)
            await callback.message.reply(f"List of Fsub Channels:\n{channel_list}")
        else:
            await callback.message.reply("No fsub channels found.")



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
