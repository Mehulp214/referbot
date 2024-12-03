import os

class Config:
    API_ID = int(os.getenv("API_ID", 13216322))
    API_HASH = os.getenv("API_HASH", "15e5e632a8a0e52251ac8c3ccbe462c7")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "7610980882:AAESQYI9Ca1pWSobokw1-S-QkVfTrja-Xdk")
    #MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://referandearn:Qwerty_1234@cluster0.dasly.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    MONGO_URI="mongodb+srv://new-user_31:Qwerty_1234@cluster0.7vbmd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "5993556795").split(",")))  # Admin Telegram IDs
    BOT_USERNAME = os.getenv("BOT_USERNAME", "referexamplebot")
    DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "USD")
    WITHDRAWAL_CHANNEL = os.getenv("WITHDRAWAL_CHANNEL", "-1002493977004")  # Channel ID
    REFERRAL_REWARD=5
