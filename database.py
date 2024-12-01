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
            # Update the referrer's referrals list
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
        self.log_withdrawal(user_id, amount)

    def set_wallet(self, user_id, wallet_address):
        self.users.update_one({"user_id": user_id}, {"$set": {"wallet": wallet_address}})

    def get_referrals(self, user_id):
        user = self.get_user_info(user_id)
        return user.get("referrals", []) if user else []

    # Added to match the bot's function calls
    def get_user_referrals(self, user_id):
        return len(self.get_referrals(user_id))

    # Statistics operations
    def get_user_count(self):
        return self.users.count_documents({})

    def get_total_balance(self):
        result = self.users.aggregate([{"$group": {"_id": None, "total": {"$sum": "$balance"}}}])
        return next(result, {}).get("total", 0)

    def get_withdrawal_stats(self):
        total_withdrawals = self.withdrawals.count_documents({})
        result = self.withdrawals.aggregate([{"$group": {"_id": None, "total": {"$sum": "$amount"}}}])
        total_amount = next(result, {}).get("total", 0)
        return total_withdrawals, total_amount

    # Settings-related operations
    def update_setting(self, key, value):
        self.settings.update_one({"key": key}, {"$set": {"value": value}}, upsert=True)

    def get_setting(self, key):
        setting = self.settings.find_one({"key": key})
        return setting["value"] if setting else None

    def add_to_array(self, key, value):
        self.settings.update_one({"key": key}, {"$addToSet": {"value": value}}, upsert=True)

    def remove_from_array(self, key, value):
        self.settings.update_one({"key": key}, {"$pull": {"value": value}})

    # Withdrawal logging
    def log_withdrawal(self, user_id, amount):
        self.withdrawals.insert_one({
            "user_id": user_id,
            "amount": amount,
            "timestamp": datetime.utcnow()
        })
