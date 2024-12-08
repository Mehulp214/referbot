import os
from pyrogram import Client, filters
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
