import logging
import threading
import asyncio
import os

# Import configuration
from config import TELEGRAM_BOT_TOKEN, PHANTOM_APP_ID, CALLBACK_BASE_URL

# Import services
from callback_service import app as flask_app
from telegram_bot import PhantomWalletBot

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def validate_configuration():
    """Validate that all required configuration values are set"""
    missing_configs = []
    
    if not TELEGRAM_BOT_TOKEN:
        missing_configs.append("TELEGRAM_BOT_TOKEN")
        
    if not PHANTOM_APP_ID:
        missing_configs.append("PHANTOM_APP_ID")
        
    if not CALLBACK_BASE_URL or CALLBACK_BASE_URL == "https://yourdomain.com":
        missing_configs.append("CALLBACK_BASE_URL")
        
    if not os.getenv("SESSION_SECRET"):
        missing_configs.append("SESSION_SECRET")
        
    if not os.getenv("APP_PUBLIC_KEY"):
        missing_configs.append("APP_PUBLIC_KEY")
        
    if missing_configs:
        raise ValueError(f"Missing required configuration: {', '.join(missing_configs)}")

def run_flask_app():
    """Run the Flask app"""
    flask_app.run(host="0.0.0.0", port=443, ssl_context='adhoc', threaded=True)

if __name__ == "__main__":
    try:
        # Validate configuration
        validate_configuration()
        
        # Start Flask service in a separate thread
        flask_thread = threading.Thread(target=run_flask_app)
        flask_thread.daemon = True
        flask_thread.start()
        
        # Start Telegram bot
        bot = PhantomWalletBot()
        bot.run()
        
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        print(f"❌ Configuration error: {str(e)}")
        print("Please set the required environment variables in the .env file")
    except Exception as e:
        logger.error(f"Failed to start services: {str(e)}")
        print(f"❌ Failed to start services: {str(e)}")
