import redis
import json
import uuid
import hashlib
import hmac
import time
from config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD, SESSION_SECRET, RATE_LIMIT_WINDOW, RATE_LIMIT_MAX_TRANSFERS

class SessionManager:
    def __init__(self):
        """Initialize Redis connection"""
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True
        )
        
    def create_session(self, user_id, action):
        """Create a new session with HMAC signature"""
        session_id = str(uuid.uuid4())
        timestamp = int(time.time())
        
        session_data = {
            "user_id": user_id,
            "action": action,
            "timestamp": timestamp
        }
        
        # Create HMAC signature for session validation
        signature = self._generate_session_token(session_data)
        session_data["signature"] = signature
        
        # Store session in Redis with expiration (1 hour)
        self.redis_client.setex(
            f"session:{session_id}",
            3600,
            json.dumps(session_data)
        )
        
        return session_id, session_data
        
    def validate_session(self, session_id, data):
        """Validate session using HMAC signature"""
        # Retrieve session from Redis
        session_json = self.redis_client.get(f"session:{session_id}")
        if not session_json:
            return False, "Session not found"
            
        session_data = json.loads(session_json)
        
        # Check if session has expired (1 hour)
        timestamp = session_data.get("timestamp", 0)
        if int(time.time()) - timestamp > 3600:
            self.redis_client.delete(f"session:{session_id}")
            return False, "Session expired"
        
        # Verify HMAC signature
        expected_signature = session_data.get("signature")
        if not expected_signature:
            return False, "Invalid session data"
            
        # Remove signature from data before validating
        data_to_verify = data.copy()
        if "signature" in data_to_verify:
            del data_to_verify["signature"]
            
        actual_signature = self._generate_session_token(data_to_verify)
        
        if not hmac.compare_digest(expected_signature, actual_signature):
            return False, "Invalid session signature"
            
        return True, session_data
        
    def _generate_session_token(self, data):
        """Generate HMAC signature for session data"""
        if not SESSION_SECRET:
            raise ValueError("SESSION_SECRET not configured")
            
        message = json.dumps(data, sort_keys=True).encode()
        return hmac.new(
            SESSION_SECRET.encode(),
            message,
            hashlib.sha256
        ).hexdigest()
        
    def store_wallet_connection(self, session_id, public_key):
        """Store wallet public key in session"""
        session_json = self.redis_client.get(f"session:{session_id}")
        if not session_json:
            return False
            
        session_data = json.loads(session_json)
        session_data["public_key"] = public_key
        
        # Update session in Redis
        self.redis_client.setex(
            f"session:{session_id}",
            3600,
            json.dumps(session_data)
        )
        
        return True
        
    def increment_transfer_count(self, user_id):
        """Increment transfer count for rate limiting"""
        key = f"transfer_limit:{user_id}"
        current_count = self.redis_client.get(key)
        
        if current_count is None:
            # First transfer in window, set with expiration
            self.redis_client.setex(key, RATE_LIMIT_WINDOW, 1)
            return 1
        else:
            # Increment count
            new_count = self.redis_client.incr(key)
            return int(new_count)
            
    def check_transfer_limit(self, user_id):
        """Check if user has exceeded transfer limit"""
        key = f"transfer_limit:{user_id}"
        current_count = self.redis_client.get(key)
        
        if current_count is None:
            return True  # No transfers yet
            
        return int(current_count) < RATE_LIMIT_MAX_TRANSFERS
        
    def get_session_data(self, session_id):
        """Retrieve session data without validation"""
        session_json = self.redis_client.get(f"session:{session_id}")
        if not session_json:
            return None
            
        return json.loads(session_json)
        
    def delete_session(self, session_id):
        """Delete session from Redis"""
        self.redis_client.delete(f"session:{session_id}")
