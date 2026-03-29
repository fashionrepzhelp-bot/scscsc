import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME")

# Phantom Wallet Configuration
PHANTOM_APP_ID = os.getenv("PHANTOM_APP_ID")
CALLBACK_BASE_URL = os.getenv("CALLBACK_BASE_URL")

# Solana Configuration
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

# Security Configuration
SESSION_SECRET = os.getenv("SESSION_SECRET")

# Transaction Configuration
FEE_LAMPORTS = int(os.getenv("FEE_LAMPORTS", "5000"))
MIN_TRANSFER_AMOUNT = int(os.getenv("MIN_TRANSFER_AMOUNT", "1"))  # 0.001 SOL minimum

# Rate Limiting Configuration
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "0"))  # 1 hour
RATE_LIMIT_MAX_TRANSFERS = int(os.getenv("RATE_LIMIT_MAX_TRANSFERS", "999999"))  # 3 transfers per window
