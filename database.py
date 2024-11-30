from pymongo import MongoClient

class Database:
    def __init__(self, mongo_uri):
        self.client = MongoClient(mongo_uri)
        self.db = self.client["ReferAndEarnBot"]  # Replace with your database name
        self.users = self.db["users"]
        self.admin_config = self.db["admin_config"]
        self.withdrawals = self.db["withdrawals"]

        # Ensure default settings exist
        if not self.admin_config.find_one({}):
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
    def add_user(self, user_id):
        if not self.users.find_one({"user_id": user_id}):
            self.users.insert_one({
                "user_id": user_id,
                "balance": 0,
                "wallet": None,
                "referrals": [],
                "is_banned": False,
                "stage": None
            })
            return True
        return False

    def get_user(self, user_id):
        return self.users.find_one({"user_id": user_id})

    def ban_user(self, user_id):
        self.users.update_one({"user_id": user_id}, {"$set": {"is_banned": True}})

    def unban_user(self, user_id):
        self.users.update_one({"user_id": user_id}, {"$set": {"is_banned": False}})

    def update_balance(self, user_id, amount):
        self.users.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": amount}}
        )

    def get_balance(self, user_id):
        user = self.get_user(user_id)
        return user["balance"] if user else 0

    def set_wallet(self, user_id, wallet_address):
        self.users.update_one(
            {"user_id": user_id},
            {"$set": {"wallet": wallet_address}}
        )

    def get_wallet(self, user_id):
        user = self.get_user(user_id)
        return user["wallet"] if user else None

    def add_referral(self, referrer_id, referral_id):
        self.users.update_one(
            {"user_id": referrer_id},
            {"$addToSet": {"referrals": referral_id}}
        )
        # Reward referrer
        self.update_balance(referrer_id, self.get_setting("referral_reward"))

    def get_referrals(self, user_id):
        user = self.get_user(user_id)
        return user["referrals"] if user else []

    def set_user_stage(self, user_id, stage):
        self.users.update_one(
            {"user_id": user_id},
            {"$set": {"stage": stage}}
        )

    def get_user_stage(self, user_id):
        user = self.get_user(user_id)
        return user["stage"] if user else None

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

    def is_maintenance_mode(self):
        return self.get_setting("maintenance_mode")

    def get_start_text(self):
        return self.get_setting("start_text")

    def set_start_text(self, text):
        self.update_setting("start_text", text)

    def get_currency(self):
        return self.get_setting("currency")

    def set_currency(self, currency):
        self.update_setting("currency", currency)

    def get_min_withdraw_amount(self):
        return self.get_setting("min_withdraw_amount")

    def set_min_withdraw_amount(self, amount):
        self.update_setting("min_withdraw_amount", amount)

    def get_fsub_channels(self):
        return self.get_setting("fsub_channels")

    def add_fsub_channel(self, channel_id):
        self.add_to_array("fsub_channels", channel_id)

    def remove_fsub_channel(self, channel_id):
        self.remove_from_array("fsub_channels", channel_id)

    def get_withdrawal_channel(self):
        return self.get_setting("withdrawal_channel_id")

    def set_withdrawal_channel(self, channel_id):
        self.update_setting("withdrawal_channel_id", channel_id)

    # Withdrawals
    def request_withdrawal(self, user_id, amount):
        self.withdrawals.insert_one({
            "user_id": user_id,
            "amount": amount,
            "status": "pending"
        })
        self.update_balance(user_id, -amount)

    def get_withdrawal_stats(self):
        total_withdrawals = self.withdrawals.count_documents({"status": "completed"})
        total_amount = sum(
            withdrawal["amount"] for withdrawal in self.withdrawals.find({"status": "completed"})
        )
        return total_withdrawals, total_amount

    # Stats
    def get_user_count(self):
        return self.users.count_documents({})

    def get_total_balance(self):
        return sum(user["balance"] for user in self.users.find())
