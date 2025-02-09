import pymongo
import config as Config
import asyncio
import os
from datetime import datetime
from bot import marimo as app
#from config import *
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram import filters
from pyromod import Client
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from pyromod.helpers import ikb
from plugins.start import back_key, main_menu_callback


dbclient = pymongo.MongoClient(Config.MONGO_URI)
database_name = dbclient["REFER_START"]

@app.on_message(filters.command("drop") & filters.private)
async def drop(client: Client, message: Message):
    # Drop the database using the client
    dbclient.drop_database(database_name)
    await message.reply("Database dropped.")
    print("DB DROPPED")

# from config import *
# from database import *
# #-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# @app.on_message(filters.command("refer_list") & filters.user(ADMIN_IDS))
# async def refer_list_command(client: Client, message: Message):
#     # Ensure the admin is sending a valid user_id to view referrals
#     try:
#         # Extract user_id from the command text (e.g., /refer_list 1234567890)
#         user_id = int(message.text.split()[1])
#     except (IndexError, ValueError):
#         await message.reply("Please provide a valid user ID.\nUsage: /refer_list <user_id>")
#         return

#     # Fetch referral count for the specified user
#     ref_count = ud.count_documents({"referrer_id": user_id})
    
#     # Fetch detailed referral information for the specified user
#     referred_users = list(ud.find({"referrer_id": user_id}))
#     referral_details = []

#     # Add numbering and timestamp
#     for index, user in enumerate(referred_users, 1):  # Start numbering from 1
#         referred_user_id = user['_id']
        
#         # Fetch the referred user's name using Pyrogram
#         try:
#             user_info = await client.get_users(referred_user_id)
#             full_name = user_info.first_name + (" " + user_info.last_name if user_info.last_name else "")
#         except Exception as e:
#             full_name = "Unknown"
        
#         # Get the timestamp from the referral document (it's in the 'referrals' array)
#         referral = next((r for r in user.get('referrals', []) if r['user_id'] == referred_user_id), None)
#         timestamp = referral.get('timestamp', 'Unknown date') if referral else 'Unknown date'

#         # Format the timestamp (if needed, you can convert it to a readable string)
#         referral_details.append(
#             f"{index}. User ID: `{referred_user_id}`, Name: **{full_name}**, \nReferred On: **{timestamp}**, \n[Profile Link](tg://user?id={referred_user_id})\n"
#         )

#     referral_details_text = "\n".join(referral_details) if referral_details else "No referrals yet."
#     f_name=user_info.first_name + (" " + user_info.last_name if user_info.last_name else "")
#     # Send the response to the admin
#     await message.reply(
#         f"Admin, you are viewing the referrals of user with ID: `{user_id}`-**{f_name}**.\n\nReferral Count: {ref_count}\n\nReferral Details:\n{referral_details_text}",
#         disable_web_page_preview=True  # Avoid link previews
#     )

# #------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# @app.on_message(filters.command("add_balance") & filters.private)
# async def add_command(client: Client, message: Message):
#     #user_id = message.from_user.id
#     try:
#         # Extract user_id from the command text (e.g., /refer_list 1234567890)
#         user_id = int(message.text.split()[1])
#         temp_amount = int(message.text.split()[2])
#         await update_balance(user_id, temp_amount)
#         print(user_id)
#         user = await client.get_users(user_id)
#         full_name = user.first_name
#         if user.last_name:
#             full_name += f" {user.last_name}"
#         await message.reply(f"{temp_amount} credited to user {user_id} - {full_name}")
#     except (IndexError, ValueError):
#         await message.reply("Please provide a valid user ID.\nUsage: /add_balance <user_id> <amount>")
#         return

# #---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# # Command to total users
# @app.on_message(filters.command("users") & filters.private & filters.user(ADMIN_IDS))
# async def get_users(client: Client, message: Message):
#     users = await full_userbase()
#     await message.reply(f"There are {len(users)} users using this bot.")

# #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# # Broadcast Command
# @app.on_message(filters.command("broadcast") & filters.private & filters.user(ADMIN_IDS))
# async def broadcast_message(client: Client, message: Message):
#     if not message.reply_to_message:
#         await message.reply("Reply to a message to broadcast.")
#         return

#     users = await full_userbase()
#     total = len(users)
#     successful, blocked, deleted, unsuccessful = 0, 0, 0, 0

#     pls_wait = await message.reply("<i>Broadcasting Message... This will take some time.</i>")
#     for user_id in users:
#         try:
#             await message.reply_to_message.copy(user_id)
#             successful += 1
#         except FloodWait as e:
#             await asyncio.sleep(e.value)
#             await message.reply_to_message.copy(user_id)
#             successful += 1
#         except UserIsBlocked:
#             await del_user(user_id)
#             blocked += 1
#         except InputUserDeactivated:
#             await del_user(user_id)
#             deleted += 1
#         except Exception:
#             unsuccessful += 1

#     status = f"""<b>Broadcast Completed</b>
# Total: {total}
# Successful: {successful}
# Blocked: {blocked}
# Deleted: {deleted}
# Failed: {unsuccessful}"""
#     await pls_wait.edit(status)
# #----------------------------------------------------------------------------------------------------------------------------------------------------------------


# @app.on_message(filters.command("check_balance") & filters.user(ADMIN_IDS))
# async def check_balance(client: Client, message: Message):
#     try:
#         # Check if the command has an argument (user ID)
#         if len(message.text.split()) < 2:
#             await message.reply("Please provide a user ID after the command.")
#             return
#         user_id = int(message.text.split()[1])  # Get user ID from the message
#         balance = await get_balance(user_id)  # Assuming you have a function to get the balance
#          # Send the balance information as a reply to the message
#         await message.reply(f"User's current balance is: {balance} units.")
#     except ValueError:
#         # Handle the case where the user ID is not a valid integer
#         await message.reply("Invalid user ID. Please provide a valid number.")
#     except Exception as e:
#         # Handle any other exceptions
#         await message.reply(f"An error occurred: {str(e)}")
