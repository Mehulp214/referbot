from pymongo import MongoClient
from datetime import datetime


class Database:
    def __init__(self, mongo_uri):
        self.client = MongoClient(mongo_uri)
        self.db = self.client['refer_and_earn']
        self.users = self.db['users']
        self.settings = self.db['settings']
        self.withdrawals = self.db['withdrawals']

    # User-related operations
    def get_user_info(self, user_id):
        return self.users.find_one({"user_id": user_id})

    def add_user(self, user_id, name, referral_code, referrer_id=None):
        user_data = {
            "user_id": user_id,
            "name": name,
            "referral_code": referral_code,
            "referrer_id": referrer_id,
            "balance": 0,
            "referrals": [],
            "wallet": None
        }
        self.users.insert_one(user_data)

        if referrer_id:
            self.users.update_one(
                {"user_id": referrer_id},
                {"$push": {"referrals": {"id": user_id, "name": name}}}
            )

    def get_user_id_by_referral_code(self, referral_code):
        user = self.users.find_one({"referral_code": referral_code})
        return user["user_id"] if user else None

    def get_user_balance(self, user_id):
        user = self.get_user_info(user_id)
        return user["balance"] if user else 0

    def update_balance(self, user_id, amount):
        self.users.update_one({"user_id": user_id}, {"$inc": {"balance": amount}})

    def withdraw(self, user_id, amount):
        self.users.update_one({"user_id": user_id}, {"$inc": {"balance": -amount}})

    def get_referrals(self, user_id):
        user = self.get_user_info(user_id)
        return user.get("referrals", []) if user else []

    # Statistics
    def get_user_count(self):
        return self.users.count_documents({})

    def get_total_balance(self):
        return sum(user["balance"] for user in self.users.find())

    # Settings-related operations
    def update_setting(self, key, value):
        self.settings.update_one({"key": key}, {"$set": {"value": value}}, upsert=True)

    def get_setting(self, key):
        setting = self.settings.find_one({"key": key})
        return setting["value"] if setting else None

    def log_withdrawal(self, user_id, amount):
        self.withdrawals.insert_one({
            "user_id": user_id,
            "amount": amount,
            "timestamp": datetime.utcnow()
        })
