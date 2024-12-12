from pyrogram import Client, idle
from config import *
from pyromod import Client as modClient

# Initialize a subclass of pyrogram.Client
class Zoro(Client):
    def __init__(self):
        # Initialize the bot (pyrogram.Client)
        self.bot: modClient = modClient(
            "Zoro", 
            api_id=API_ID, 
            api_hash=API_HASH, 
            bot_token=BOT_TOKEN, 
            plugins=dict(root="plugins")  # Specify the plugins folder
        )

    async def start_bot(self):
        # Start the bot using the pyrogram client
        await self.start()
        print(f"@{self.me.username} is alive now!")

    async def stop(self):
        # Stop the bot
        await self.stop()
        print("Bot is dead now")
        
    async def start_up(self):
        # Start the bot and idle
        await self.start_bot()
        await idle()  # Keep the bot running until you stop it

# Create an instance of the Zoro bot
marimo = Zoro()

# Start the bot
marimo.run()
