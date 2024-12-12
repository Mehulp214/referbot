from pyrogram import Client, idle
from config import *
from pyromod import Client as modClient

# Initialize a subclass of pyrogram.Client
from pyrogram import Client, idle
from config import *
from pyromod import Client as modClient

# Initialize a subclass of pyrogram.Client
class Zoro(modClient):
    def __init__(self):
        # Initialize modClient (pyromod.Client)
        super().__init__(  # Using pyromod.Client constructor
            "Zoro",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="plugins")  # Specify the plugins folder
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

# Ensure the plugins are loaded and check if there is an issue
# print("Starting bot...")
# marimo.run()

        
   
