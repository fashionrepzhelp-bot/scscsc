#!/usr/bin/env python3
"""
Utility script to generate a new Solana keypair for the app wallet
and save it to a JSON file.
"""

import json
import base58
from solders.keypair import Keypair

def generate_keypair():
    """Generate a new Solana keypair and save to file"""
    # Generate a new keypair
    keypair = Keypair()
    
    # Get the secret key as bytes
    secret_key = bytes(keypair)
    
    # Convert to base58 string for storage
    secret_key_b58 = base58.b58encode(secret_key).decode('utf-8')
    
    # Get the public key
    public_key = str(keypair.pubkey())
    
    # Create keypair dictionary
    keypair_dict = {
        "secret_key": secret_key_b58,
        "public_key": public_key
    }
    
    # Save to file
    with open("app_keypair.json", "w") as f:
        json.dump(keypair_dict, f, indent=2)
    
    print("✅ New keypair generated and saved to app_keypair.json")
    print(f"Public Key: {public_key}")
    print("⚠️  IMPORTANT: Keep this file secure and never share the secret key!")
    print("⚠️  For production, use environment variables instead of files")

if __name__ == "__main__":
    generate_keypair()
