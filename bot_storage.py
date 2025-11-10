import os
import json
import redis

# --- Connect to Redis ---
# Render will automatically provide this environment variable
REDIS_URL = os.environ.get("REDIS_URL")

if not REDIS_URL:
    print("WARNING: REDIS_URL not found. Defaulting to localhost.")
    REDIS_URL = "redis://localhost:6379"

try:
    # This (r) is your one connection to the Redis database
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
    print("Connected to Redis successfully!")
except redis.exceptions.ConnectionError as e: # type: ignore
    print(f"FATAL: Could not connect to Redis. {e}")
    print("Bot will not be able to save or load any data.")
    # In a real app, you might exit, but here we'll let it continue
    # so you can see other errors.
    r = None # Set to None so other functions don't crash

# --- Keys for your data ---
# This is like naming your files
PREFS_KEY = "user_prefs"
SUBSCRIBERS_KEY = "subscribed_users"
REMINDED_KEY = "reminded_contests"


# --- Preference Functions (for user_prefs) ---
def load_prefs():
    """Loads user preferences (a dict) from Redis."""
    if not r: return {} # No connection
    try:
        prefs_raw = r.hgetall(PREFS_KEY)
        prefs = {}
        for user_id, prefs_json in prefs_raw.items(): # type: ignore
            prefs[int(user_id)] = json.loads(prefs_json)
        return prefs
    except Exception as e:
        print(f"Error loading prefs from Redis: {e}")
        return {}

def save_prefs(prefs_dict):
    """Saves the entire user preferences dict to Redis."""
    if not r: return
    try:
        pipe = r.pipeline()
        pipe.delete(PREFS_KEY) # Delete old hash
        if prefs_dict:
            # Convert values to JSON strings for storage
            for user_id, prefs_list in prefs_dict.items():
                pipe.hset(PREFS_KEY, str(user_id), json.dumps(prefs_list))
            pipe.execute()
    except Exception as e:
        print(f"Error saving prefs to Redis: {e}")

# --- Set Functions (for subscribers and reminders) ---
def load_set_from_file(redis_key: str) -> set:
    """Loads a set from Redis."""
    if not r: return set()
    try:
        return r.smembers(redis_key) # type: ignore
    except Exception as e:
        print(f"Error loading set {redis_key} from Redis: {e}")
        return set()

def add_to_set_file(item, redis_key: str):
    """Adds a single item to a set in Redis."""
    if not r: return
    try:
        r.sadd(redis_key, str(item))
    except Exception as e:
        print(f"Error adding to set {redis_key}: {e}")

def remove_from_set_file(item, redis_key: str):
    """Removes a single item from a set in Redis."""
    if not r: return
    try:
        r.srem(redis_key, str(item))
    except Exception as e:
        print(f"Error removing from set {redis_key}: {e}")

def is_in_set_file(item, redis_key: str) -> bool:
    """Checks if an item is in a set in Redis."""
    if not r: return False
    try:
        return r.sismember(redis_key, str(item)) # type: ignore
    except Exception as e:
        print(f"Error checking set {redis_key}: {e}")
        return False