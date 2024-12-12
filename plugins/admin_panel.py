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

dbclient = pymongo.MongoClient(Config.MONGO_URI)
database_name = dbclient["REFER_START"]

@app.on_message(filters.command("drop") & filters.private)
async def drop(client: Client, message: Message):
    # Drop the database using the client
    dbclient.drop_database(database_name)
    await message.reply("Database dropped.")
    print("DB DROPPED")
