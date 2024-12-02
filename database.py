
#(©)CodeXBotz




import pymongo, os
from config import Config

dbclient = pymongo.MongoClient(Config.MONGO_URI)
database = dbclient["REFER_START"]


user_data = database['users']


import pymongo
from config import Config

# Initialize the MongoDB client and connect to the database
dbclient = pymongo.MongoClient(Config.MONGO_URI)
database = dbclient["REFER_START"]

# Accessing the collection 'users'
user_data = database['users']


# Check if a user is present in the database
async def present_user(user_id: int):
    found = user_data.find_one({'_id': user_id})
    return bool(found)


# Add a new user to the database
# async def add_user(user_id: int):
#     if not await present_user(user_id):
#         user_data.insert_one({'_id': user_id, 'balance': 0, 'referral_count': 0})
#     return
async def add_user(user_id: int):
    if not await present_user(user_id):
        user_data.insert_one({
            '_id': user_id,
            'balance': 0,  # Default balance
            'referral_count': 0  # Default referral count
        })
    return


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
# async def update_balance(user_id: int, amount: int):
#     user = user_data.find_one({'_id': user_id})
#     if user:
#         new_balance = user['balance'] + amount
#         user_data.update_one({'_id': user_id}, {'$set': {'balance': new_balance}})
#     return


# # Update the referral count of a user
# async def update_referral_count(user_id: int):
#     user = user_data.find_one({'_id': user_id})
#     if user:
#         new_count = user['referral_count'] + 1
#         user_data.update_one({'_id': user_id}, {'$set': {'referral_count': new_count}})
#     return


# # Get a user's balance
# async def get_balance(user_id: int):
#     user = user_data.find_one({'_id': user_id})  # Use the present_user function to check if the user exists
#     if user:
#         return user.get('balance', 0)  # Get balance or default to 0 if not set
#     return 0 

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


# Store a temporary referral for a user
async def set_temp_referral(user_id: int, referral_id: str):
    temp_referrals.update_one(
        {'_id': user_id},
        {'$set': {'referrer_id': referral_id}},
        upsert=True  # Create document if it doesn't exist
    )
    return


# Retrieve the temporary referral for a user
async def get_temp_referral(user_id: int):
    temp_referral = temp_referrals.find_one({'_id': user_id})
    if temp_referral:
        return temp_referral.get('referrer_id')
    return None


# Clear the temporary referral for a user
async def clear_temp_referral(user_id: int):
    temp_referrals.delete_one({'_id': user_id})
    return


