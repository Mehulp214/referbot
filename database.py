
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
async def add_user(user_id: int):
    if not await present_user(user_id):
        user_data.insert_one({'_id': user_id, 'balance': 0, 'referral_count': 0})
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
async def update_balance(user_id: int, amount: int):
    user = user_data.find_one({'_id': user_id})
    if user:
        new_balance = user['balance'] + amount
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
        return user['balance']
    return 0


# # Check if a user is present in the database
# async def present_user(user_id):
#     return await db.users.find_one({"user_id": user_id}) is not None

# # Get the full list of users
# async def full_userbase():
#     return [user["user_id"] for user in await db.users.find({}).to_list(length=None)]

# async def present_user(user_id : int):
#     found = user_data.find_one({'_id': user_id})
#     return bool(found)

# async def add_user(user_id: int):
#     user_data.insert_one({'_id': user_id})
#     return

# async def full_userbase():
#     user_docs = user_data.find()
#     user_ids = []
#     for doc in user_docs:
#         user_ids.append(doc['_id'])
        
#     return user_ids

# async def del_user(user_id: int):
#     user_data.delete_one({'_id': user_id})
#     return
