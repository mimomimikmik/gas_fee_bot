import pyrebase
from config import Config
from datetime import datetime, timedelta

class FirebaseService:
    def __init__(self):
        self.firebase = pyrebase.initialize_app(Config.FIREBASE_CONFIG)
        self.db = self.firebase.database()
    
    def get_user(self, user_id):
        return self.db.child("users").child(str(user_id)).get().val()
    
    def create_user(self, user_id, username):
        user_data = {
            "id": user_id,
            "username": username,
            "is_paid": False,
            "subscription_expiry": None,
            "alerts": {},
            "notification_settings": {
                "low_threshold": Config.DEFAULT_LOW_THRESHOLD,
                "high_threshold": Config.DEFAULT_HIGH_THRESHOLD,
                "notification_frequency": Config.FREE_USER_UPDATE_INTERVAL
            },
            "created_at": datetime.now().isoformat()
        }
        self.db.child("users").child(str(user_id)).set(user_data)
        return user_data
    
    def update_user(self, user_id, updates):
        self.db.child("users").child(str(user_id)).update(updates)
    
    def add_alert(self, user_id, alert_name, threshold, condition):
        alerts = self.get_user(user_id).get("alerts", {})
        
        if len(alerts) >= Config.FREE_USER_MAX_ALERTS and not self.is_paid_user(user_id):
            raise Exception("Free users can only have up to 3 alerts")
        
        new_alert = {
            "threshold": threshold,
            "condition": condition,  # 'above' or 'below'
            "last_triggered": None,
            "created_at": datetime.now().isoformat()
        }
        
        self.db.child("users").child(str(user_id)).child("alerts").child(alert_name).set(new_alert)
    
    def remove_alert(self, user_id, alert_name):
        self.db.child("users").child(str(user_id)).child("alerts").child(alert_name).remove()
    
    def is_paid_user(self, user_id):
        user = self.get_user(user_id)
        if not user:
            return False
        
        if user.get("is_paid", False):
            expiry = user.get("subscription_expiry")
            if expiry and datetime.fromisoformat(expiry) > datetime.now():
                return True
            else:
                # Subscription expired
                self.db.child("users").child(str(user_id)).update({
                    "is_paid": False,
                    "subscription_expiry": None
                })
        return False
    
    def activate_subscription(self, user_id, tx_hash, duration_seconds=Config.SUBSCRIPTION_DURATION):
        expiry_date = datetime.now() + timedelta(seconds=duration_seconds)
        
        self.db.child("users").child(str(user_id)).update({
            "is_paid": True,
            "subscription_expiry": expiry_date.isoformat(),
            "last_payment_tx": tx_hash,
            "notification_settings": {
                "notification_frequency": Config.PAID_USER_UPDATE_INTERVAL
            }
        })
    
    def update_wallet_address(self, new_address):
        self.db.child("config").child("payment_wallet").set(new_address)
        return new_address
    
    def get_wallet_address(self):
        return self.db.child("config").child("payment_wallet").get().val() or Config.PAYMENT_WALLET_ADDRESS