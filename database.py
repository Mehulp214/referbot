from pymongo import MongoClient
from config import Config

class Database:
    def __init__(self, mongo_uri):
        self.client = MongoClient(mongo_uri)
        self.db = self.client["ReferAndEarnBot"]
        self.users = self.db["users"]
        self.admin_config = self.db["admin_config"]
        self.withdrawals = self.db["withdrawals"]

        # Initialize Admin Config if not present
        if not self.admin_config.find_one():
            self.admin_config.insert_one({
                "start_text": "👋 Welcome to our Refer & Earn Bot! Earn rewards by referring others.",
                "currency": "USD",
                "maintenance_mode": False,
                "min_withdraw_amount": 10,
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
                "stage": None  # For specific user actions
            })
            return True
        return False

    def get_balance(self, user_id):
        user = self.users.find_one({"user_id": user_id})
        return user["balance"] if user else 0

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

    def get_wallet(self, user_id):
        user = self.users.find_one({"user_id": user_id})
        return user["wallet"] if user else None

    def set_user_stage(self, user_id, stage):
        self.users.update_one(
            {"user_id": user_id},
            {"$set": {"stage": stage}}
        )

    def get_user_stage(self, user_id):
        user = self.users.find_one({"user_id": user_id})
        return user["stage"] if user else None

    def get_referrals(self, user_id):
        user = self.users.find_one({"user_id": user_id})
        return user["referrals"] if user else []

    def add_referral(self, referrer_id, referral_id):
        self.users.update_one(
            {"user_id": referrer_id},
            {"$addToSet": {"referrals": referral_id}}
        )
        # Reward referrer
        self.update_balance(referrer_id, Config.REFERRAL_REWARD)

    # Admin Config Management
    def get_start_text(self):
        config = self.admin_config.find_one()
        return config.get("start_text") if config else None

    def set_start_text(self, text):
        self.admin_config.update_one(
            {}, {"$set": {"start_text": text}}
        )

    def get_currency(self):
        config = self.admin_config.find_one()
        return config.get("currency") if config else "USD"

    def set_currency(self, currency):
        self.admin_config.update_one(
            {}, {"$set": {"currency": currency}}
        )

    def is_maintenance_mode(self):
        config = self.admin_config.find_one()
        return config.get("maintenance_mode", False)

    def set_maintenance_mode(self, status):
        self.admin_config.update_one(
            {}, {"$set": {"maintenance_mode": status}}
        )

    def get_min_withdraw_amount(self):
        config = self.admin_config.find_one()
        return config.get("min_withdraw_amount", 10)

    def set_min_withdraw_amount(self, amount):
        self.admin_config.update_one(
            {}, {"$set": {"min_withdraw_amount": amount}}
        )

    def get_fsub_channels(self):
        config = self.admin_config.find_one()
        return config.get("fsub_channels", [])

    def add_fsub_channel(self, channel_id):
        self.admin_config.update_one(
            {}, {"$addToSet": {"fsub_channels": channel_id}}
        )

    def remove_fsub_channel(self, channel_id):
        self.admin_config.update_one(
            {}, {"$pull": {"fsub_channels": channel_id}}
        )

    def get_withdrawal_channel(self):
        config = self.admin_config.find_one()
        return config.get("withdrawal_channel_id")

    def set_withdrawal_channel(self, channel_id):
        self.admin_config.update_one(
            {}, {"$set": {"withdrawal_channel_id": channel_id}}
        )

    # Withdrawals
    def request_withdrawal(self, user_id, amount):
        self.withdrawals.insert_one({
            "user_id": user_id,
            "amount": amount,
            "status": "pending"
        })

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

