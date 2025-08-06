# Phantom Wallet Telegram Bot

This is a Telegram bot that integrates with Phantom Solana wallet to allow users to connect their wallets and transfer funds.

## Features

- Secure wallet connection via Phantom Universal Links
- Fund transfer functionality with user confirmation
- Session management with HMAC signatures
- Rate limiting for transfers
- Error handling and user notifications

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables**:
   Create a `.env` file with the following variables:
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_BOT_USERNAME=your_bot_username
   PHANTOM_APP_ID=your_phantom_app_id
   CALLBACK_BASE_URL=https://yourdomain.com
   SESSION_SECRET=your_random_session_secret
   APP_PUBLIC_KEY=your_app_public_key
   APP_SECRET_KEY=your_app_secret_key
   ```

3. **Configure Redis** (optional but recommended for production):
   ```env
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   REDIS_PASSWORD=
   ```

4. **Configure transaction parameters** (optional):
   ```env
   FEE_LAMPORTS=5000
   MIN_TRANSFER_AMOUNT=1000000
   RATE_LIMIT_WINDOW=3600
   RATE_LIMIT_MAX_TRANSFERS=3
   ```

## Usage

1. **Start the bot**:
   ```bash
   python main.py
   ```

2. **Interact with the bot**:
   - Send `/start` to begin
   - Click "Connect Phantom Wallet" to connect your wallet
   - Follow the Phantom app prompts to connect
   - After connection, you'll receive a message with your wallet balance
   - Click "Transfer All Funds" to initiate a transfer
   - Follow the Phantom app prompts to sign the transaction

## Security

- All sessions are validated using HMAC signatures
- Rate limiting prevents excessive transfers
- Private keys are never stored in the code or session data
- All Phantom callbacks are validated before processing
- HTTPS is required for all endpoints

## Technical Stack

- python-telegram-bot for Telegram interface
- Flask for HTTPS callback endpoints
- solana library for blockchain interactions
- Redis for session storage
- Proper error handling for network/bot issues

## Implementation Details

### Wallet Connection Flow

1. User clicks "Connect Phantom" button in Telegram
2. Bot generates a Phantom deep link using universal link format:
   `https://phantom.app/ul/v1/connect?app_url={callback}&dapp_key={app_id}&session={session_id}`
3. User opens Phantom app and connects their wallet
4. Phantom redirects to the HTTPS callback URL with public key and session data
5. The callback endpoint validates the session and stores the wallet public key
6. User is redirected back to Telegram bot with confirmation

### Fund Transfer Functionality

1. After connection, user can initiate fund transfer
2. Bot creates Solana transaction to move ALL user funds minus fees
3. Transaction is sent to Phantom via deep link for signing:
   `https://phantom.app/ul/v1/signAndSendTransaction?transaction={encoded_tx}&session={session_id}&app_url={callback_url}&dapp_key={app_id}`
4. User signs transaction in Phantom app
5. Phantom sends signed transaction back to the callback
6. Bot submits transaction to Solana network and confirms it
7. User gets success notification in Telegram

## Important Notes

- This implementation requires a public HTTPS endpoint for Phantom callbacks
- For development/testing, you can use ngrok to expose your local server
- Never automatically transfer funds without explicit user approval
- Store private keys securely using environment variables or a secure vault
