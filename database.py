
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
# Create a new collection for storing referrals separately
referrals_collection = database['referrals']


bot_stats=database['withdrawls']
# Access the collection for fsub channels
fsub_collection = database['fsub_channels']


# Function to get the list of fsub channels
def get_fsub_channels():
    return [doc["channel_id"] for doc in fsub_collection.find()]

# Function to add an fsub channel
def add_fsub_channel(channel_id: str):
    if not fsub_collection.find_one({"channel_id": channel_id}):
        fsub_collection.insert_one({"channel_id": channel_id})
        # Update the static list
        global FORCE_SUB_CHANNELS
        FORCE_SUB_CHANNELS = get_fsub_channels()

# Function to remove an fsub channel
def remove_fsub_channel(channel_id: str):
    fsub_collection.delete_one({"channel_id": channel_id})
    # Update the static list
    global FORCE_SUB_CHANNELS
    FORCE_SUB_CHANNELS = get_fsub_channels()


# Function to get the list of fsub channels
def get_fsub_channels():
    return [doc["channel_id"] for doc in fsub_collection.find()]

# Check if a user is present in the database
async def present_user(user_id: int):
    found = user_data.find_one({'_id': user_id})
    return bool(found)



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
        referrer_id = int(referrer_id)  # Ensure referrer_id is an integer

    # Check if user already exists in the database
    if not await present_user(user_id):
        # Insert new user
        user_data.insert_one({
            '_id': user_id,
            'balance': 0,
            'referral_count': 0,
            'referrer_id': referrer_id,
            'wallet_address': None,
            'referred_at': get_ist_time(),  # Referral timestamp in IST
            'name': name or "Unknown",  # Save name if provided, otherwise "Unknown"
            'referrals': []  # Initialize empty referral list
        })
        print(f"New user added: {user_id} with referrer_id: {referrer_id} and name: {name}")

        # If a referrer exists, add the referral record
        if referrer_id:
            referral_data = {
                'user_id': user_id,
                'timestamp': get_ist_time()  # Referral timestamp in IST
            }
            user_data.update_one(
                {'_id': referrer_id},
                {
                    '$push': {'referrals': referral_data},  # Add referred user to referrer's list
                    '$inc': {'referral_count': 1}  # Increase referrer’s referral count
                }
            )
            print(f"Referral added for referrer_id {referrer_id}: {referral_data}")

    else:
        # If the user exists but doesn't have a referrer, set their referrer_id (no need to push referrals)
        user = user_data.find_one({'_id': user_id})
        if not user.get('referrer_id') and referrer_id:
            user_data.update_one(
                {'_id': user_id},
                {'$set': {'referrer_id': referrer_id}}
            )
            print(f"User {user_id} referrer_id updated to {referrer_id}")

    return

# Function to add withdrawal for a user and update statistics
async def add_withdrawal(user_id: int, amount: int):
    # Validate input
    if amount <= 0:
        return "Invalid withdrawal amount."

    # Ensure 'total_withdrawals' exists for the user
    user = user_data.find_one({"_id": user_id})
    if not user:
        return f"User {user_id} not found."
    
    if not user.get("total_withdrawals"):
        # If 'total_withdrawals' field does not exist, initialize it
        user_data.update_one(
            {"_id": user_id},
            {"$set": {"total_withdrawals": 0}},  # Initialize it to 0
            upsert=True
        )

    # Update the user's total withdrawals
    user_data.update_one(
        {"_id": user_id},
        {"$inc": {"total_withdrawals": amount}},  # Increment the user's total withdrawals
        upsert=True  # Create document if user doesn't exist
    )

    # Update the global total withdrawals
    bot_stats.update_one(
        {"_id": "stats"},
        {"$inc": {"total_withdrawals": amount}},  # Increment the global total withdrawals
        upsert=True  # Create the 'stats' document if it doesn't exist
    )

    return f"Successfully added withdrawal of {amount} for user {user_id}."


# Function to update the global total withdrawals in the database
async def update_total_withdrawals(amount: int):
    bot_stats.update_one(
        {"_id": "stats"},
        {"$inc": {"total_withdrawals": amount}},  # Increment global total withdrawals
        upsert=True  # Create the 'stats' document if it doesn't exist
    )

# Function to get the total withdrawals for a specific user
async def get_user_withdrawals(user_id: int):
    user = user_data.find_one({"_id": user_id})
    if user:
        return user.get("total_withdrawals", 0)  # Return the user's total withdrawals or 0 if not set
    return 0

# Function to fetch the global total withdrawals
async def get_total_withdrawals():
    # Fetch the global total withdrawals from the bot_stats collection
    stats = bot_stats.find_one({"_id": "stats"})
    if stats:
        return stats.get("total_withdrawals", 0)  # Return global total withdrawals
    return 0  # Return 0 if the global stats document is not found

# Function to set a specific total withdrawals value globally (for reset or setting purposes)
async def set_total_withdrawals(total: int):
    bot_stats.update_one(
        {"_id": "stats"},
        {"$set": {"total_withdrawals": total}},  # Set the total withdrawals to the specified value
        upsert=True  # Create the 'stats' document if it doesn't exist
    )




# Function to get the referral list for a specific user
async def get_referral_list(user_id: int):
    user = user_data.find_one({'_id': user_id})
    if user and 'referrals' in user:
        referrals = user['referrals']
        referral_details = []
        
        for ref in referrals:
            ref_id = ref.get("user_id")
            timestamp = ref.get("timestamp")
            
            # Fetch the referred user's name
            ref_user = user_data.find_one({'_id': ref_id})
            ref_name = ref_user.get('name', 'Unknown') if ref_user else 'Unknown'
            
            referral_details.append({
                "user_id": ref_id,
                "name": ref_name,
                "timestamp": timestamp
            })

        return referral_details  # Returns a list of referred users with names and timestamps

    return []



