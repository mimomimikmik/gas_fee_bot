import requests
from telegram.ext import Application, CommandHandler
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
async def start(update, context):
    await update.message.reply_text("🚀 **Gas Fee Alert Bot**\n\n/subscribe_free - Dapat notif gas fee murah 1x/hari\n/upgrade_vip - Notif real-time + analisis!")

async def subscribe_free(update, context):
    user_id = update.message.chat_id
    db.reference(f"users/{user_id}").set({"tier": "free"})
    await update.message.reply_text("✅ Anda berhasil subscribe! Kami akan mengingatkan Anda saat gas fee < 10 gwei.")

async def upgrade_vip(update, context):
    user_id = update.message.chat_id
    db.reference(f"users/{user_id}").set({"tier": "vip"})
    await update.message.reply_text("💎 **UPGRADE VIP BERHASIL!**\n\nBayar 5 USDT ke alamat ini: 0x123...\nKirim bukti ke @admin.")

# Check Gas Fee Every 1 Hour
async def check_gas(context):
    gas = get_gas_fee()
    if gas < 10:
        users = db.reference("users").get() or {}
        for user_id, data in users.items():
            await context.bot.send_message(int(user_id), f"🚀 **Gas Fee ETH {gas} gwei!** Waktu terbaik untuk transaksi!")

# Main
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("subscribe_free", subscribe_free))
    app.add_handler(CommandHandler("upgrade_vip", upgrade_vip))
    
    # Schedule gas check (only works if PTB installed with [job-queue])
    job_queue = app.job_queue
    if job_queue:  # Check if JobQueue is available
        job_queue.run_repeating(check_gas, interval=3600, first=0)
    else:
        print("Warning: JobQueue not available. Install with 'pip install \"python-telegram-bot[job-queue]\"'")
    
    app.run_polling()

if __name__ == "__main__":
    main()