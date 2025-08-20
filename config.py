import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot Token
    TELEGRAM_TOKEN = os.getenv('8242252342:AAE8hb-Jgj_bFiSIcC989CHt6ROky1Ev298')
    
    # Etherscan API
    ETHERSCAN_API_KEY = os.getenv('CKBY8HQHE9C2U3UPTIFTSAWBSFH12B2VMM')
    ETHERSCAN_URL = "https://etherscan.io/"
    
    # Firebase Configuration
    FIREBASE_CONFIG = {
        "apiKey": os.getenv('AIzaSyAoUHEs64wnq-4ucNfDWdDhoU-NzWUMiCs'),
        "authDomain": os.getenv('gasfeebot.firebaseapp.com'),
        "databaseURL": os.getenv('https://gasfeebot-default-rtdb.asia-southeast1.firebasedatabase.app'),
        "projectId": os.getenv('gasfeebot'),
        "storageBucket": os.getenv('gasfeebot.firebasestorage.app'),
        "messagingSenderId": os.getenv('740873908859'),
        "appId": os.getenv('1:740873908859:web:54a743a97746f4ddfa68de')
    }
    
    # Payment Wallet Address (can be changed dynamically)
    PAYMENT_WALLET_ADDRESS = os.getenv('PAYMENT_WALLET_ADDRESS', '0xc9055E28b2773661B45DC8D39823bebAF7260E0b')
    
    # Subscription Settings
    SUBSCRIPTION_PRICE_ETH = 0.01  # 0.01 ETH per month
    SUBSCRIPTION_DURATION = 30 * 24 * 60 * 60  # 30 days in seconds
    
    # Notification Thresholds
    DEFAULT_LOW_THRESHOLD = 30  # gwei
    DEFAULT_HIGH_THRESHOLD = 100  # gwei
    
    # Free tier limits
    FREE_USER_MAX_ALERTS = 3
    FREE_USER_UPDATE_INTERVAL = 3600  # 1 hour in seconds
    PAID_USER_UPDATE_INTERVAL = 300  # 5 minutes in seconds