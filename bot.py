import requests
import telegram
from telegram.ext import Updater, CommandHandler
import firebase_admin
from firebase_admin import db

# Config
TELEGRAM_TOKEN = "8242252342:AAE8hb-Jgj_bFiSIcC989CHt6ROky1Ev298"
ETHERSCAN_API_KEY = "CKBY8HQHE9C2U3UPTIFTSAWBSFH12B2VMM"
FIREBASE_URL = "https://gasfeebot-default-rtdb.asia-southeast1.firebasedatabase.app/"

# Init Firebase
cred = firebase_admin.credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_URL})

# Fetch Gas Fee from Etherscan
def get_gas_fee():
    url = f"https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey={ETHERSCAN_API_KEY}"
    response = requests.get(url).json()
    return int(response["result"]["ProposeGasPrice"])

# Bot Commands
def start(update, context):
    update.message.reply_text("🚀 **Gas Fee Alert Bot**\n\n/subscribe_free - Dapat notif gas fee murah 1x/hari\n/upgrade_vip - Notif real-time + analisis!")

def subscribe_free(update, context):
    user_id = update.message.chat_id
    db.reference(f"users/{user_id}").set({"tier": "free"})
    update.message.reply_text("✅ Anda berhasil subscribe! Kami akan mengingatkan Anda saat gas fee < 10 gwei.")

def upgrade_vip(update, context):
    user_id = update.message.chat_id
    db.reference(f"users/{user_id}").set({"tier": "vip"})
    update.message.reply_text("💎 **UPGRADE VIP BERHASIL!**\n\nBayar 5 USDT ke alamat ini: 0x123...\nKirim bukti ke @admin.")

# Check Gas Fee Every 1 Hour
def check_gas(context):
    gas = get_gas_fee()
    if gas < 10:
        users = db.reference("users").get()
        for user_id, data in users.items():
            context.bot.send_message(user_id, f"🚀 **Gas Fee ETH {gas} gwei!** Waktu terbaik untuk transaksi!")

# Main
updater = Updater(TELEGRAM_TOKEN)  # Removed use_context=True
updater.dispatcher.add_handler(CommandHandler("start", start))
updater.dispatcher.add_handler(CommandHandler("subscribe_free", subscribe_free))
updater.dispatcher.add_handler(CommandHandler("upgrade_vip", upgrade_vip))

# Schedule gas check
job_queue = updater.job_queue
job_queue.run_repeating(check_gas, interval=3600, first=0)

updater.start_polling()
updater.idle()