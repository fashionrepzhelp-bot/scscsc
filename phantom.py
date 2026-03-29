import urllib.parse
import base64
import os
from config import PHANTOM_APP_ID, CALLBACK_BASE_URL

class PhantomUtils:
    @staticmethod
    def generate_connect_url(session_id):
        """Generate official Phantom connect deep link"""
        # PHANTOM REQUIRES THESE EXACT PARAMETER NAMES
        params = {
            "app_url": CALLBACK_BASE_URL,
            "dapp_encryption_public_key": PHANTOM_APP_ID, # Now it gets the 7kok... key
            "redirect_link": f"{CALLBACK_BASE_URL}/connect?session_id={session_id}",
            "cluster": "mainnet-beta"
        }
        
        query = urllib.parse.urlencode(params)
        return f"https://phantom.app?{query}"
        
    @staticmethod
    def generate_sign_transaction_url(transaction_message, session_id):
        """Generate official Phantom sign transaction deep link"""
        # Encode the transaction for the deep link
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
        return (True, "Valid") if session_id and public_key else (False, "Missing params")
