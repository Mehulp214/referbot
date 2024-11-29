import os

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    MONGO_URI = os.getenv("MONGO_URI", "YOUR_MONGO_URI_HERE")
    ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "123456789").split(",")))  # Admin Telegram IDs
    BOT_USERNAME = os.getenv("BOT_USERNAME", "YourBotUsername")
    DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "USD")
    WITHDRAWAL_CHANNEL = os.getenv("WITHDRAWAL_CHANNEL", "-1001234567890")  # Channel ID
