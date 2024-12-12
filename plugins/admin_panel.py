import pymongo
import config as Config
dbclient = pymongo.MongoClient(Config.MONGO_URI)
database_name = dbclient["REFER_START"]

@app.on_message(filters.command("drop") & filters.private)
async def drop(client: Client, message: Message):
    # Drop the database using the client
    dbclient.drop_database(database_name)
    await message.reply("Database dropped.")
    print("DB DROPPED")
