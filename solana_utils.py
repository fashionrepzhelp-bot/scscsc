from solana.rpc.api import Client
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.message import Message
from solders.transaction import Transaction
from solders.keypair import Keypair
import base64
import json
import os
import base58
from config import SOLANA_RPC_URL, FEE_LAMPORTS, MIN_TRANSFER_AMOUNT

class SolanaUtils:
    def __init__(self):
        """Initialize Solana RPC client and app keypair"""
        self.client = Client(SOLANA_RPC_URL)
        
        # Load app keypair from environment variables
        secret_key_b58 = os.getenv("APP_SECRET_KEY")
        if secret_key_b58:
            secret_key_bytes = base58.b58decode(secret_key_b58)
            self.app_keypair = Keypair.from_bytes(secret_key_bytes)
        else:
            self.app_keypair = None
        
    def get_user_balance(self, public_key_str):
        """Get user balance in lamports"""
        try:
            pubkey = Pubkey.from_string(public_key_str)
            response = self.client.get_balance(pubkey)
            return response.value
        except Exception as e:
            raise Exception(f"Failed to get balance: {str(e)}")
            
    def create_transfer_transaction(self, from_pubkey_str, to_pubkey_str):
        """Create a transfer transaction for all funds minus fees"""
        try:
            # Convert string public keys to Pubkey objects
            from_pubkey = Pubkey.from_string(from_pubkey_str)
            to_pubkey = Pubkey.from_string(to_pubkey_str)
            
            # Get user's balance
            balance = self.get_user_balance(from_pubkey_str)
            
            # Calculate transfer amount (all funds minus fees)
            if balance <= FEE_LAMPORTS:
                raise Exception("Insufficient balance for transfer fees")
                
            transfer_amount = balance - FEE_LAMPORTS
            
            # Check minimum transfer amount
            if transfer_amount < MIN_TRANSFER_AMOUNT:
                raise Exception(f"Transfer amount too small. Minimum is {MIN_TRANSFER_AMOUNT} lamports.")
            
            # Create transfer instruction
            instruction = transfer(
                TransferParams(
                    from_pubkey=from_pubkey,
                    to_pubkey=to_pubkey,
                    lamports=transfer_amount
                )
            )
            
            # Get latest blockhash
            blockhash_response = self.client.get_latest_blockhash()
            blockhash = blockhash_response.value.blockhash
            
            # Create message
            message = Message.new_with_blockhash(
                [instruction],
                blockhash,
                from_pubkey
            )
            
            return message, transfer_amount
        except Exception as e:
            raise Exception(f"Failed to create transfer transaction: {str(e)}")
            
    def submit_signed_transaction(self, signature):
        """Submit a signed transaction to the Solana network"""
        try:
            # Decode the base64 signature
            tx_bytes = base64.urlsafe_b64decode(signature)
            
            # Submit transaction
            tx_response = self.client.send_raw_transaction(tx_bytes)
            tx_signature = tx_response.value
            
            # Wait for confirmation
            self.client.confirm_transaction(tx_signature)
            
            # Check transaction status
            status_response = self.client.get_signature_statuses([tx_signature])
            status = status_response.value[0]
            
            if status is None:
                raise Exception("Transaction status not found")
                
            if status.err is not None:
                raise Exception(f"Transaction failed: {status.err}")
                
            return tx_signature
        except Exception as e:
            raise Exception(f"Failed to submit transaction: {str(e)}")
            
    def get_transaction_status(self, tx_signature):
        """Get the status of a transaction"""
        try:
            status_response = self.client.get_signature_statuses([tx_signature])
            status = status_response.value[0]
            
            if status is None:
                return None
                
            return {
                "confirmed": status.confirmation_status is not None,
                "err": status.err,
                "slot": status.slot
            }
        except Exception as e:
            raise Exception(f"Failed to get transaction status: {str(e)}")
