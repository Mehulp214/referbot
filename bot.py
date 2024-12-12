from pyrogram import Client, idle
from config import *
from pyromod import Client as modClient

# Initialize a subclass of pyrogram.Client
class Zoro(Client):
    def __init__(self):
        self.bot: modClient = modClient(  # Using pyromod.Client here
            "Zoro",
            API_ID,
            API_HASH,
            plugins=dict(root="plugins"),
            bot_token=BOT_TOKEN
        )
        # self.user: Client = Client(  # Using pyrogram.Client for the user bot
        #     "Luffy",
        #     API_ID,
        #     API_HASH,
        #     session_string=SESSION,
        # )

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
