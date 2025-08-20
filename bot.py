import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from firebase_service import FirebaseService
from etherscan_service import EtherscanService
from payment_processor import PaymentProcessor
from config import Config
import threading
import time
from datetime import datetime

# Initialize services
firebase = FirebaseService()
etherscan = EtherscanService()
payment_processor = PaymentProcessor("https://mainnet.infura.io/v3/f5fb0ce9013649b5a08e1c5e56355516")

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name
    
    # Check if user exists
    existing_user = firebase.get_user(user_id)
    if not existing_user:
        firebase.create_user(user_id, username)
        existing_user = firebase.get_user(user_id)
    
    is_paid = firebase.is_paid_user(user_id)
    
    message = (
        f"👋 Hello {username}!\n\n"
        "I'm Ethereum Gas Fee Notifier Bot. I can alert you when gas prices reach certain thresholds.\n\n"
        f"Your current status: {'💰 PAID USER' if is_paid else '🎉 FREE USER'}\n\n"
        "Commands:\n"
        "/current - Get current gas prices\n"
        "/setalert - Set a new gas price alert\n"
        "/myalerts - View your current alerts\n"
        "/subscribe - Upgrade to paid version\n"
        "/help - Show this help message"
    )
    
    update.message.reply_text(message)

def current_gas(update: Update, context: CallbackContext):
    try:
        prices = etherscan.get_gas_prices()
        message = (
            "⛽ Current Ethereum Gas Prices (Gwei):\n\n"
            f"🐢 Safe: {prices['safe']}\n"
            f"🚗 Proposed: {prices['propose']}\n"
            f"🚀 Fast: {prices['fast']}\n\n"
            f"Base Fee: {prices['suggestBaseFee']}"
        )
        update.message.reply_text(message)
    except Exception as e:
        update.message.reply_text(f"❌ Error getting gas prices: {str(e)}")

def set_alert(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = firebase.get_user(user_id)
    
    if not user:
        update.message.reply_text("Please /start the bot first")
        return
    
    is_paid = firebase.is_paid_user(user_id)
    alerts = user.get("alerts", {})
    
    if len(alerts) >= Config.FREE_USER_MAX_ALERTS and not is_paid:
        update.message.reply_text(
            f"❌ Free users can only have {Config.FREE_USER_MAX_ALERTS} alerts. "
            "Upgrade to paid for unlimited alerts."
        )
        return
    
    if not context.args or len(context.args) < 2:
        update.message.reply_text(
            "Usage: /setalert <name> <threshold> [above|below]\n\n"
            "Example:\n"
            "/setalert cheap 30 below - Alert when gas is below 30 gwei\n"
            "/setalert expensive 100 above - Alert when gas is above 100 gwei\n\n"
            "Default condition is 'below'"
        )
        return
    
    alert_name = context.args[0]
    try:
        threshold = int(context.args[1])
    except ValueError:
        update.message.reply_text("Threshold must be a number")
        return
    
    condition = context.args[2].lower() if len(context.args) > 2 else "below"
    if condition not in ["above", "below"]:
        update.message.reply_text("Condition must be 'above' or 'below'")
        return
    
    try:
        firebase.add_alert(user_id, alert_name, threshold, condition)
        update.message.reply_text(
            f"✅ Alert '{alert_name}' set!\n"
            f"I will notify you when gas is {condition} {threshold} gwei"
        )
    except Exception as e:
        update.message.reply_text(f"❌ Error setting alert: {str(e)}")

def my_alerts(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = firebase.get_user(user_id)
    
    if not user:
        update.message.reply_text("Please /start the bot first")
        return
    
    alerts = user.get("alerts", {})
    is_paid = firebase.is_paid_user(user_id)
    
    if not alerts:
        update.message.reply_text("You don't have any alerts set. Use /setalert to create one.")
        return
    
    message = ["🔔 Your Gas Price Alerts:"]
    for name, alert in alerts.items():
        message.append(
            f"- {name}: Notify when gas is {alert['condition']} {alert['threshold']} gwei"
        )
    
    message.append(f"\nStatus: {'💰 PAID USER' if is_paid else '🎉 FREE USER'}")
    message.append(f"Alerts: {len(alerts)}/{'∞' if is_paid else Config.FREE_USER_MAX_ALERTS}")
    
    keyboard = [
        [InlineKeyboardButton("Remove Alert", callback_data="remove_alert")],
    ]
    
    update.message.reply_text(
        "\n".join(message),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def remove_alert_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    user_id = query.from_user.id
    user = firebase.get_user(user_id)
    
    if not user:
        query.edit_message_text("Please /start the bot first")
        return
    
    alerts = user.get("alerts", {})
    if not alerts:
        query.edit_message_text("You don't have any alerts to remove")
        return
    
    # Create a button for each alert to remove
    keyboard = []
    for name in alerts.keys():
        keyboard.append([InlineKeyboardButton(f"Remove {name}", callback_data=f"remove_{name}")])
    
    keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
    
    query.edit_message_text(
        "Select an alert to remove:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def process_remove_alert(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    
    if data == "cancel":
        query.edit_message_text("Alert removal cancelled")
        return
    
    alert_name = data.replace("remove_", "")
    
    try:
        firebase.remove_alert(user_id, alert_name)
        query.edit_message_text(f"✅ Alert '{alert_name}' removed successfully")
    except Exception as e:
        query.edit_message_text(f"❌ Error removing alert: {str(e)}")

def subscribe(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = firebase.get_user(user_id)
    
    if not user:
        update.message.reply_text("Please /start the bot first")
        return
    
    if firebase.is_paid_user(user_id):
        update.message.reply_text("You already have an active subscription!")
        return
    
    wallet_address = firebase.get_wallet_address()
    
    message = (
        "💰 Upgrade to Paid Version\n\n"
        "Benefits:\n"
        "- Unlimited gas price alerts\n"
        "- More frequent updates (every 5 minutes)\n"
        "- Priority support\n\n"
        f"Price: {Config.SUBSCRIPTION_PRICE_ETH} ETH per month\n\n"
        f"Send payment to:\n`{wallet_address}`\n\n"
        "After payment, send me the transaction hash with the command:\n"
        "/paid <tx_hash>"
    )
    
    update.message.reply_text(message, parse_mode="Markdown")

def paid(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = firebase.get_user(user_id)
    
    if not user:
        update.message.reply_text("Please /start the bot first")
        return
    
    if firebase.is_paid_user(user_id):
        update.message.reply_text("You already have an active subscription!")
        return
    
    if not context.args:
        update.message.reply_text("Please provide your transaction hash: /paid <tx_hash>")
        return
    
    tx_hash = context.args[0]
    
    try:
        # Try to validate immediately
        is_valid, message = payment_processor.validate_payment(user_id, tx_hash)
        
        if is_valid:
            firebase.activate_subscription(user_id, tx_hash)
            update.message.reply_text(
                "✅ Payment verified! Your subscription is now active.\n\n"
                "You now have access to:\n"
                "- Unlimited gas price alerts\n"
                "- More frequent updates\n"
                "- Priority support"
            )
        else:
            # If not immediately found, start monitoring
            update.message.reply_text(
                f"⏳ Payment not immediately found. I'll keep checking for the next few minutes.\n\n"
                f"Reason: {message}"
            )
            
            # In a real implementation, you'd set up a proper background task
            # This is a simplified version
            def monitor_payment():
                time.sleep(300)  # Wait 5 minutes
                is_valid, message = payment_processor.validate_payment(user_id, tx_hash)
                if is_valid:
                    firebase.activate_subscription(user_id, tx_hash)
                    context.bot.send_message(
                        chat_id=user_id,
                        text="✅ Payment verified! Your subscription is now active."
                    )
                else:
                    context.bot.send_message(
                        chat_id=user_id,
                        text=f"❌ Payment not verified after 5 minutes. Please try again or contact support.\n\nError: {message}"
                    )
            
            threading.Thread(target=monitor_payment).start()
    
    except Exception as e:
        update.message.reply_text(f"❌ Error processing payment: {str(e)}")

def help_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🛠️ Help\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/current - Get current gas prices\n"
        "/setalert <name> <threshold> [above|below] - Set a new gas price alert\n"
        "/myalerts - View your current alerts\n"
        "/subscribe - Upgrade to paid version\n"
        "/paid <tx_hash> - Submit your payment transaction\n"
        "/help - Show this help message"
    )

def check_alerts(context: CallbackContext):
    """Background job to check alerts for all users"""
    try:
        # Get current gas prices
        prices = etherscan.get_gas_prices()
        current_gas = prices['propose']  # Using proposed gas price for alerts
        
        # Get all users (in a real app, you'd paginate or use a more efficient method)
        all_users = firebase.db.child("users").get().val() or {}
        
        for user_id, user_data in all_users.items():
            try:
                alerts = user_data.get("alerts", {})
                if not alerts:
                    continue
                
                # Check user's notification frequency
                last_notified = user_data.get("last_notified", 0)
                notification_freq = user_data.get("notification_settings", {}).get(
                    "notification_frequency", 
                    Config.PAID_USER_UPDATE_INTERVAL if firebase.is_paid_user(user_id) 
                    else Config.FREE_USER_UPDATE_INTERVAL
                )
                
                if time.time() - last_notified < notification_freq:
                    continue
                
                # Check each alert
                for alert_name, alert in alerts.items():
                    threshold = alert["threshold"]
                    condition = alert["condition"]
                    last_triggered = alert.get("last_triggered")
                    
                    triggered = False
                    message = ""
                    
                    if condition == "below" and current_gas <= threshold:
                        triggered = True
                        message = f"🔔 Gas Alert: {alert_name}\nCurrent gas is {current_gas} gwei (below {threshold} gwei)"
                    elif condition == "above" and current_gas >= threshold:
                        triggered = True
                        message = f"🔔 Gas Alert: {alert_name}\nCurrent gas is {current_gas} gwei (above {threshold} gwei)"
                    
                    if triggered:
                        # Check if we've already notified for this condition recently
                        if last_triggered and (time.time() - last_triggered) < 3600:  # 1 hour cooldown
                            continue
                        
                        # Send notification
                        context.bot.send_message(
                            chat_id=user_id,
                            text=message
                        )
                        
                        # Update last triggered time
                        firebase.db.child("users").child(user_id).child("alerts").child(alert_name).update({
                            "last_triggered": time.time()
                        })
                        
                        # Update last notified time for user
                        firebase.db.child("users").child(user_id).update({
                            "last_notified": time.time()
                        })
            
            except Exception as e:
                logger.error(f"Error processing alerts for user {user_id}: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error in alert checking job: {str(e)}")

def error_handler(update: Update, context: CallbackContext):
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.message:
        update.message.reply_text("An error occurred. Please try again later.")

def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater(Config.TELEGRAM_TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Register command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("current", current_gas))
    dp.add_handler(CommandHandler("setalert", set_alert))
    dp.add_handler(CommandHandler("myalerts", my_alerts))
    dp.add_handler(CommandHandler("subscribe", subscribe))
    dp.add_handler(CommandHandler("paid", paid))
    dp.add_handler(CommandHandler("help", help_command))
    
    # Callback handlers
    dp.add_handler(CallbackQueryHandler(remove_alert_callback, pattern="^remove_alert$"))
    dp.add_handler(CallbackQueryHandler(process_remove_alert, pattern="^remove_"))
    dp.add_handler(CallbackQueryHandler(process_remove_alert, pattern="^cancel$"))
    
    # Log all errors
    dp.add_error_handler(error_handler)

    # Start background job to check alerts
    job_queue = updater.job_queue
    job_queue.run_repeating(check_alerts, interval=300, first=0)  # Check every 5 minutes

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()