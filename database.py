from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

class Database:
    def __init__(self, mongo_uri):
        self.client = MongoClient(mongo_uri)
        self.db = self.client["refer_and_earn"]  # Database name
        self.users = self.db["users"]  # Collection for users
        self.settings = self.db["settings"]  # Collection for app settings

        # Ensure indexes
        self.users.create_index("user_id", unique=True)
        self.users.create_index("referral_code", unique=True)

        # Default settings
        if not self.settings.find_one({"_id": "config"}):
            self.settings.insert_one({
                "_id": "config",
                "currency": "USD",
                "referral_reward": 10,
                "min_withdraw_amount": 50,
                "maintenance_mode": False,
                "fsub_channels": []
            })

    # User management
    def add_user(self, user_id, name, referral_code, referrer_id=None):
        user_data = {
            "user_id": user_id,
            "name": name,
            "balance": 0,
            "referrals": 0,
            "referral_code": referral_code,
            "referrer_id": referrer_id,
            "wallet": None
        }
        try:
            self.users.insert_one(user_data)
            if referrer_id:
                self.users.update_one({"user_id": referrer_id}, {"$inc": {"balance": self.get_setting("referral_reward"), "referrals": 1}})
        except DuplicateKeyError:
            pass

    def get_user_info(self, user_id):
        return self.users.find_one({"user_id": user_id})

    def get_user_balance(self, user_id):
        user = self.get_user_info(user_id)
        return user["balance"] if user else 0

    def get_user_id_by_referral_code(self, referral_code):
        user = self.users.find_one({"referral_code": referral_code})
        return user["user_id"] if user else None

    def get_user_referrals(self, user_id):
        return self.users.find({"referrer_id": user_id}).count()

    def set_wallet(self, user_id, wallet_address):
        self.users.update_one({"user_id": user_id}, {"$set": {"wallet": wallet_address}})

    def update_balance(self, user_id, amount):
        self.users.update_one({"user_id": user_id}, {"$inc": {"balance": amount}})

    # Referral statistics
    def get_referrals(self, user_id):
        referrals = self.users.find({"referrer_id": user_id}, {"user_id": 1, "name": 1})
        return [{"id": ref["user_id"], "name": ref["name"]} for ref in referrals]

    # Withdrawal
    def withdraw(self, user_id, amount):
        self.update_balance(user_id, -amount)
        # Add any additional processing logic here if needed

    # Global statistics
    def get_user_count(self):
        return self.users.count_documents({})

    def get_total_balance(self):
        return self.users.aggregate([{"$group": {"_id": None, "total": {"$sum": "$balance"}}}]).next().get("total", 0)

    def get_withdrawal_stats(self):
        # Adjust if you maintain separate withdrawals
        total_withdrawals = 0
        total_amount = 0
        return total_withdrawals, total_amount

    # Settings management
    def get_setting(self, key):
        config = self.settings.find_one({"_id": "config"})
        return config.get(key) if config else None

    def update_setting(self, key, value):
        self.settings.update_one({"_id": "config"}, {"$set": {key: value}})

    def add_to_array(self, key, value):
        self.settings.update_one({"_id": "config"}, {"$addToSet": {key: value}})

    def remove_from_array(self, key, value):
        self.settings.update_one({"_id": "config"}, {"$pull": {key: value}})
