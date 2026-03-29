import urllib.parse
import base64
import os
from config import PHANTOM_APP_ID, CALLBACK_BASE_URL

class PhantomUtils:
    @staticmethod
    def generate_connect_url(session_id):
        """Generate official Phantom connect deep link"""
        if not PHANTOM_APP_ID or not CALLBACK_BASE_URL:
            raise ValueError("Phantom app ID or callback URL not configured")
            
        # CORRECT PARAMETERS FOR PHANTOM V1:
        params = {
            "app_url": CALLBACK_BASE_URL,
            "dapp_encryption_public_key": PHANTOM_APP_ID, # MUST be your Public Key
            "redirect_link": f"{CALLBACK_BASE_URL}/connect?session_id={session_id}",
            "cluster": "mainnet-beta"
        }
        
        query = urllib.parse.urlencode(params)
        return f"https://phantom.app?{query}"
        
    @staticmethod
    def generate_sign_transaction_url(transaction_message, session_id):
        """Generate official Phantom sign transaction deep link"""
        if not PHANTOM_APP_ID or not CALLBACK_BASE_URL:
            raise ValueError("Phantom app ID or callback URL not configured")
            
        # Encode transaction
        encoded_tx = base64.urlsafe_b64encode(transaction_message).decode('utf-8')
        
        params = {
            "transaction": encoded_tx,
            "session": session_id,
            "dapp_encryption_public_key": PHANTOM_APP_ID,
            "redirect_link": f"{CALLBACK_BASE_URL}/sign?session_id={session_id}"
        }
        
        query = urllib.parse.urlencode(params)
        return f"https://phantom.app?{query}"

    @staticmethod
    def validate_connect_callback(session_id, public_key):
        if not session_id or not public_key:
            return False, "Missing parameters"
        return True, "Valid"
