import os
import json
import redis

# --- Connect to Redis ---
# Render will automatically provide this environment variable
REDIS_URL = os.environ.get("REDIS_URL")

if not REDIS_URL:
    print("WARNING (Server): REDIS_URL not found. Defaulting to localhost.")
    REDIS_URL = "redis://localhost:6379"

try:
    # This (r) is your one connection to the Redis database
    # decode_responses=True makes it return strings, not bytes
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
    print("Connected to Redis (Server) successfully!")
except redis.exceptions.ConnectionError as e: # type: ignore
    print(f"FATAL (Server): Could not connect to Redis. {e}")
    r = None # Set to None so other functions don't crash

# --- We will store all data in Redis Hashes ---
TOKENS_KEY = "user_tokens"
PENDING_KEY = "pending_auth"

def load_tokens():
    """Loads all user tokens from Redis."""
    if not r: return {}
    try:
        tokens_raw = r.hgetall(TOKENS_KEY)
        tokens = {}
        for user_id, token_json in tokens_raw.items(): # type: ignore
            tokens[int(user_id)] = json.loads(token_json)
        return tokens
    except Exception as e:
        print(f"Error loading tokens from Redis: {e}")
        return {}

def save_token_for_user(user_id, token_data):
    """Saves a single user's token to Redis."""
    if not r: return
    try:
        r.hset(TOKENS_KEY, str(user_id), json.dumps(token_data))
    except Exception as e:
        print(f"Error saving token to Redis: {e}")

def load_pending():
    """Loads all pending auths from Redis."""
    if not r: return {}
    try:
        pending_raw = r.hgetall(PENDING_KEY)
        # Keys are strings (tokens), values are int (user_ids)
        return {token: int(user_id) for token, user_id in pending_raw.items()} # type: ignore
    except Exception as e:
        print(f"Error loading pending auths from Redis: {e}")
        return {}

def save_pending_auth(token, user_id):
    """Saves a single pending auth token to Redis."""
    if not r: return
    try:
        # Use r.set() instead of hset() for a simple key:value with expiry
        # 900 seconds = 15 minutes
        r.set(f"{PENDING_KEY}:{token}", str(user_id), ex=900)
    except Exception as e:
        print(f"Error saving pending auth to Redis: {e}")

def pop_pending_auth(token):
    """Retrieves and deletes a pending auth token from Redis."""
    if not r: return None
    try:
        # Use r.get() to fetch the key
        key = f"{PENDING_KEY}:{token}"
        user_id = r.get(key)
        
        if user_id:
            r.delete(key) # Delete the key
            return int(user_id) # type: ignore
        return None
    except Exception as e:
        print(f"Error popping pending auth from Redis: {e}")
        return None