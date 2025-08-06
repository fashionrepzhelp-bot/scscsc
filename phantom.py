import urllib.parse
import base64
from config import PHANTOM_APP_ID, CALLBACK_BASE_URL

class PhantomUtils:
    @staticmethod
    def generate_connect_url(session_id):
        """Generate Phantom connect deep link"""
        if not PHANTOM_APP_ID or not CALLBACK_BASE_URL:
            raise ValueError("Phantom app ID or callback URL not configured")
            
        # Build connection URL according to Phantom Universal Link format
        redirect_uri = f"{CALLBACK_BASE_URL}/connect"
        connect_url = (
            f"https://phantom.app/ul/v1/connect?"
            f"app_url={urllib.parse.quote(redirect_uri)}&"
            f"dapp_key={PHANTOM_APP_ID}&"
            f"session={session_id}"
        )
        
        return connect_url
        
    @staticmethod
    def generate_sign_transaction_url(transaction_message, session_id):
        """Generate Phantom sign transaction deep link"""
        if not PHANTOM_APP_ID or not CALLBACK_BASE_URL:
            raise ValueError("Phantom app ID or callback URL not configured")
            
        # Serialize and encode transaction message
        tx_bytes = bytes(transaction_message.serialize())
        encoded_tx = base64.urlsafe_b64encode(tx_bytes).decode('utf-8')
        
        # Build sign transaction URL according to Phantom Universal Link format
        redirect_uri = f"{CALLBACK_BASE_URL}/sign"
        sign_url = (
            f"https://phantom.app/ul/v1/signAndSendTransaction?"
            f"transaction={urllib.parse.quote(encoded_tx)}&"
            f"session={session_id}&"
            f"app_url={urllib.parse.quote(redirect_uri)}&"
            f"dapp_key={PHANTOM_APP_ID}"
        )
        
        return sign_url
        
    @staticmethod
    def validate_connect_callback(session_id, public_key):
        """Validate connect callback parameters"""
        # Basic validation - session_id and public_key should not be empty
        if not session_id or not public_key:
            return False, "Missing required parameters"
            
        return True, "Valid callback parameters"
        
    @staticmethod
    def validate_sign_callback(session_id, signature):
        """Validate sign callback parameters"""
        # Basic validation - session_id and signature should not be empty
        if not session_id or not signature:
            return False, "Missing required parameters"
            
        return True, "Valid callback parameters"
