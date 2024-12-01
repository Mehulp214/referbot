from pymongo import MongoClient


class Database:
    def __init__(self, mongo_uri):
        self.client = MongoClient(mongo_uri)
        self.db = self.client["ReferAndEarnBot"]  # Database name
        self.users = self.db["users"]
        self.admin_config = self.db["admin_config"]
        self.withdrawals = self.db["withdrawals"]

        # Initialize admin config if not present
        if not self.admin_config.find_one():
            self.admin_config.insert_one({
                "start_text": "👋 Welcome to our Refer & Earn Bot! Earn rewards by referring others.",
                "currency": "USD",
                "maintenance_mode": False,
                "min_withdraw_amount": 10,
                "referral_reward": 10,
                "fsub_channels": [],
                "withdrawal_channel_id": None
            })

    # User Management
    def add_user(self, user_id, name):
        if not self.users.find_one({"user_id": user_id}):
            self.users.insert_one({
                "user_id": user_id,
                "name": name,
                "balance": 0,
                "wallet": None,
                "referrals": [],
                "is_banned": False
            })
            return True
        return False

    def get_user_info(self, user_id):
        return self.users.find_one({"user_id": user_id})

    def update_balance(self, user_id, amount):
        self.users.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": amount}}
        )

    def set_wallet(self, user_id, wallet):
        self.users.update_one(
            {"user_id": user_id},
            {"$set": {"wallet": wallet}}
        )

    def ban_user(self, user_id):
        self.users.update_one({"user_id": user_id}, {"$set": {"is_banned": True}})

    def unban_user(self, user_id):
        self.users.update_one({"user_id": user_id}, {"$set": {"is_banned": False}})

    def get_referrals(self, user_id):
        user = self.get_user_info(user_id)
        return user["referrals"] if user else []

    def add_referral(self, referrer_id, referral_id):
        self.users.update_one(
            {"user_id": referrer_id},
            {"$addToSet": {"referrals": referral_id}}
        )
        self.update_balance(referrer_id, self.get_setting("referral_reward"))

    # Admin Config Management
    def get_setting(self, key):
        config = self.admin_config.find_one()
        return config.get(key) if config else None

    def update_setting(self, key, value):
        self.admin_config.update_one(
            {}, {"$set": {key: value}}
        )

    def add_to_array(self, key, value):
        self.admin_config.update_one(
            {}, {"$addToSet": {key: value}}
        )

    def remove_from_array(self, key, value):
        self.admin_config.update_one(
            {}, {"$pull": {key: value}}
        )

    # Stats
    def get_user_count(self):
        return self.users.count_documents({})

    def get_total_balance(self):
        return sum(user["balance"] for user in self.users.find())

    def get_withdrawal_stats(self):
        total_withdrawals = self.withdrawals.count_documents({"status": "completed"})
        total_amount = sum(
            withdrawal["amount"] for withdrawal in self.withdrawals.find({"status": "completed"})
        )
        return total_withdrawals, total_amount
