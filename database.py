# import pymongo
# import random
# import string


# class Database:
#     def __init__(self, mongo_uri):
#         self.client = pymongo.MongoClient(mongo_uri)
#         self.db = self.client["refer_and_earn_bot"]

#         # Collections
#         self.users = self.db["users"]
#         self.settings = self.db["settings"]

#         # Default settings
#         if not self.settings.find_one({"key": "currency"}):
#             self.settings.insert_one({"key": "currency", "value": "USD"})
#         if not self.settings.find_one({"key": "min_withdraw_amount"}):
#             self.settings.insert_one({"key": "min_withdraw_amount", "value": 10})

#     # User Management
#     def add_user(self, user_id, name, referral_code, referrer_id=None):
#         if not self.users.find_one({"user_id": user_id}):
#             self.users.insert_one({
#                 "user_id": user_id,
#                 "name": name,
#                 "balance": 0,
#                 "referral_code": referral_code,
#                 "referrer_id": referrer_id,
#                 "referrals": [],
#                 "wallet": None
#             })
#             if referrer_id:
#                 self.add_referral(referrer_id, user_id)

#     def get_user_info(self, user_id):
#         return self.users.find_one({"user_id": user_id})

#     def get_user_balance(self, user_id):
#         user = self.get_user_info(user_id)
#         return user["balance"] if user else 0

#     def update_balance(self, user_id, amount):
#         self.users.update_one({"user_id": user_id}, {"$inc": {"balance": amount}})

#     def set_wallet(self, user_id, wallet_address):
#         self.users.update_one({"user_id": user_id}, {"$set": {"wallet": wallet_address}})

#     # Referral Management
#     def generate_referral_code(self):
#         return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

#     def get_user_id_by_referral_code(self, referral_code):
#         user = self.users.find_one({"referral_code": referral_code})
#         return user["user_id"] if user else None

#     def add_referral(self, referrer_id, referral_id):
#         self.users.update_one({"user_id": referrer_id}, {"$push": {"referrals": referral_id}})
#         referral_amount = int(self.get_setting("referral_amount", default=1))
#         self.update_balance(referrer_id, referral_amount)

#     def get_user_referrals(self, user_id):
#         user = self.get_user_info(user_id)
#         return len(user["referrals"]) if user else 0

#     def get_referrals(self, user_id):
#         user = self.get_user_info(user_id)
#         if not user:
#             return []
#         referrals = [
#             self.get_user_info(referral_id) for referral_id in user["referrals"]
#         ]
#         return [{"id": ref["user_id"], "name": ref["name"]} for ref in referrals if ref]

#     # Withdraw Management
#     def withdraw(self, user_id, amount):
#         self.users.update_one({"user_id": user_id}, {"$set": {"balance": 0}})
#         # Log withdrawal (optional)

#     # Settings Management
#     def get_setting(self, key, default=None):
#         setting = self.settings.find_one({"key": key})
#         return setting["value"] if setting else default

#     def update_setting(self, key, value):
#         self.settings.update_one({"key": key}, {"$set": {"value": value}}, upsert=True)

#     # Stats
#     def get_user_count(self):
#         return self.users.count_documents({})

#     def get_total_balance(self):
#         return sum(user["balance"] for user in self.users.find())

#     def get_all_users(self):
#         return list(self.users.find())

#     def get_user_referral_code(self, user_id):
#         user = self.get_user_info(user_id)
#         return user["referral_code"] if user else None


#(©)CodeXBotz




import pymongo, os
from main import MONGO_URI, DB_NAME


dbclient = pymongo.MongoClient(DB_URI)
database = dbclient[DB_NAME]


user_data = database['users']



async def present_user(user_id : int):
    found = user_data.find_one({'_id': user_id})
    return bool(found)

async def add_user(user_id: int):
    user_data.insert_one({'_id': user_id})
    return

async def full_userbase():
    user_docs = user_data.find()
    user_ids = []
    for doc in user_docs:
        user_ids.append(doc['_id'])
        
    return user_ids

async def del_user(user_id: int):
    user_data.delete_one({'_id': user_id})
    return
