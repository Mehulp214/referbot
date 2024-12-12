
#(©)CodeXBotz
import pymongo
import asyncio
from datetime import datetime
from bot import marimo as app
from pyrogram import filters



import pymongo
import config as Config

# Initialize the MongoDB client and connect to the database
dbclient = pymongo.MongoClient(Config.MONGO_URI)
database = dbclient["REFER_START"]

# Accessing the collection 'users'
user_data = database['users']
temp_referrals = database['temp_referrals'] 

bot_stats=database['withdrawls']
# Access the collection for fsub channels
fsub_collection = database['fsub_channels']

# Function to add a new fsub channel
def add_fsub_channel(channel_id: str):
    if not fsub_collection.find_one({"channel_id": channel_id}):
        fsub_collection.insert_one({"channel_id": channel_id})

# Function to remove an fsub channel
def remove_fsub_channel(channel_id: str):
    fsub_collection.delete_one({"channel_id": channel_id})

# Function to get the list of fsub channels
def get_fsub_channels():
    return [doc["channel_id"] for doc in fsub_collection.find()]

# Check if a user is present in the database
async def present_user(user_id: int):
    found = user_data.find_one({'_id': user_id})
    return bool(found)

#================================================================================================================================
# async def add_user(user_id: int, referrer_id: int = None):
#     if referrer_id:
#         referrer_id = int(referrer_id)  # Ensure it's stored as an integer

#     if not await present_user(user_id):
#         user_data.insert_one({
#             '_id': user_id,
#             'balance': 0,
#             'referral_count': 0,
#             'referrer_id': referrer_id,
#             'wallet_address': None
#         })
#     else:
#         user = user_data.find_one({'_id': user_id})
#         if not user.get('referrer_id') and referrer_id:
#             user_data.update_one(
#                 {'_id': user_id},
#                 {'$set': {'referrer_id': referrer_id}}
#             )
#     return

#-==============================-=-=-=--=-=-=-=-=-=-=-=-=-=-=-=-=-=-=--=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-========================-----------------============

# Get the full list of users (user IDs)
async def full_userbase():
    user_docs = user_data.find()
    user_ids = [doc['_id'] for doc in user_docs]
    return user_ids



# Delete a user from the database
async def del_user(user_id: int):
    user_data.delete_one({'_id': user_id})
    return


# Update the balance of a user
async def update_balance(user_id: int, amount: int):
    user = user_data.find_one({'_id': user_id})
    if user:
        new_balance = user.get('balance', 0) + amount  # Default to 0 if balance is missing
        user_data.update_one({'_id': user_id}, {'$set': {'balance': new_balance}})
    return


# Update the referral count of a user
async def update_referral_count(user_id: int):
    user = user_data.find_one({'_id': user_id})
    if user:
        new_count = user['referral_count'] + 1
        user_data.update_one({'_id': user_id}, {'$set': {'referral_count': new_count}})
    return


# Get a user's balance
async def get_balance(user_id: int):
    user = user_data.find_one({'_id': user_id})
    if user:
        return user.get('balance', 0)  # Get balance or default to 0 if not set
    return 0

#GET A referral count
async def get_referral_count(user_id: int):
    user = user_data.find_one({'_id': user_id})
    if user:
        return user.get('referral_count', 0)  # Get balance or default to 0 if not set
    return 0


# Set a temporary referral
async def set_temp_referral(user_id: int, referrer_id: str):
    temp_referrals.update_one(
        {'_id': user_id},
        {'$set': {'referrer_id': referrer_id}},
        upsert=True
    )
    return

# Clear a temporary referral
async def clear_temp_referral(user_id: int):
    temp_referrals.delete_one({'_id': user_id})
    return

async def get_temp_referral(user_id: int):
    temp_referral = temp_referrals.find_one({'_id': user_id})
    if temp_referral:
        return temp_referral.get('referrer_id')
    return None

# Update the wallet address for a user
async def update_wallet(user_id: int, wallet_address: str):
    user_data.update_one({'_id': user_id}, {'$set': {'wallet_address': wallet_address}})
    return

# Get the wallet address of a user
async def get_wallet(user_id: int):
    user = user_data.find_one({'_id': user_id})
    return user.get('wallet_address') if user else None


# Get a leaderboard sorted by referrals or balance
async def get_leaderboard(sort_by='referral_count', limit=10):
    top_users = user_data.find().sort(sort_by, -1).limit(limit)
    leaderboard = [{'user_id': user['_id'], sort_by: user.get(sort_by, 0)} for user in top_users]
    return leaderboard



from datetime import datetime
import pytz

# Function to get the current time in IST
def get_ist_time():
    # Define Indian Standard Time timezone (UTC +5:30)
    ist = pytz.timezone('Asia/Kolkata')
    # Get the current time in UTC and convert to IST
    return datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')  # Format: YYYY-MM-DD HH:MM:SS

async def add_user(user_id: int, referrer_id: int = None, name: str = None):
    if referrer_id:
        referrer_id = int(referrer_id)  # Ensure it's stored as an integer

    # Check if user already exists in the database
    if not await present_user(user_id):
        # Insert new user with referral timestamp and name
        user_data.insert_one({
            '_id': user_id,
            'balance': 0,
            'referral_count': 0,
            'referrer_id': referrer_id,
            'wallet_address': None,
            'referred_at': get_ist_time(),  # Add referral timestamp in IST
            'name': name or "Unknown"  # Save the name if provided, default to "Unknown"
        })
        print(f"New user added: {user_id} with referrer_id: {referrer_id} and name: {name}")

        # If a referrer exists, add the referral record
        if referrer_id:
            referral_data = {
                'user_id': user_id,
                'timestamp': get_ist_time()  # Add referral timestamp in IST
            }
            user_data.update_one(
                {'_id': referrer_id},
                {'$push': {'referrals': referral_data}},
                upsert=True
            )
            print(f"Referral added for referrer_id {referrer_id}: {referral_data}")

    else:
        # If user exists and doesn't have a referrer, set the referrer_id and add timestamp
        user = user_data.find_one({'_id': user_id})
        if not user.get('referrer_id') and referrer_id:
            timestamp = get_ist_time()  # Get current timestamp in IST
            user_data.update_one(
                {'_id': user_id},
                {
                    '$set': {'referrer_id': referrer_id},
                    '$push': {'referrals': {'user_id': user_id, 'timestamp': timestamp}}  # Add referral timestamp
                }
            )
            print(f"User {user_id} referrer_id updated to {referrer_id} with timestamp: {timestamp}")

    return

async def add_withdrawal(user_id: int, amount: int):
    # Validate input
    if amount <= 0:
        return "Invalid withdrawal amount."

    # Update user's total withdrawals
    user_data.update_one(
        {"_id": user_id},
        {"$inc": {"total_withdrawals": amount}},  # Increment user-specific total
        upsert=True  # Create document if not exists
    )

    # Update global total withdrawals
    bot_stats.update_one(
        {"_id": "stats"},
        {"$inc": {"total_withdrawals": amount}}
    )

    return f"Successfully added withdrawal of {amount} for user {user_id}."

async def get_user_withdrawals(user_id: int):
    user = user_data.find_one({"_id": user_id})
    return user.get("total_withdrawals", 0) if user else 0

async def get_total_withdrawals():
    stats = bot_stats.find_one({"_id": "stats"})
    return stats.get("total_withdrawals", 0) if stats else 0


# Function to get the referral list for a specific user
async def get_referral_list(user_id: int):
    pass

