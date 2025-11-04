from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi import Header, HTTPException
from google_auth_oauthlib.flow import Flow
import json, os

app = FastAPI()

CLIENT_ID  = "837036947469-hupbt93evofo4p2k4kduk0etgl9j9e2q.apps.googleusercontent.com"
CLIENT_SECRET = "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"
REDIRECT_URL = "https://arlo-supertragic-nonprogressively.ngrok-free.dev/oauth2callback"
SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly"
]

Internal_API_KEY = "PryKUMZn_hupbt93evofo4p_internal_CFBOT_26420"


TOKENS_FILE = "user_tokens.json"
user_tokens = {}


# It temporarily maps the random token to the user_id
pending_auth = {}

def load_tokens():
    """Loads user tokens from a JSON file."""
    try:
        if not os.path.exists(TOKENS_FILE):
            return {}
        with open(TOKENS_FILE, "r") as f:
            data = json.load(f)
            return {int(k): v for k, v in data.items()}
    except Exception as e:
        print(f"Error loading tokens: {e}")
        return {}

def save_tokens(tokens_dict):
    """Saves the user tokens dictionary to a JSON file."""
    try:
        with open(TOKENS_FILE, "w") as f:
            json.dump(tokens_dict, f, indent=4)
    except Exception as e:
        print(f"Error saving tokens: {e}")

user_tokens = load_tokens()
print("Loaded tokens on startup:", user_tokens) # Safe, only you can see this in your terminal

@app.get("/")
async def root():
    return {"message": "Server is running."}

def create_flow():
    return Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URL],
            }
        },
        scopes=SCOPES
    ) # type: ignore


@app.get("/connect")
async def connect(token: str, user_id: str):
    pending_auth[token] = user_id


    flow = create_flow()
    flow.redirect_uri = REDIRECT_URL

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=token
    )

    return RedirectResponse(auth_url)


@app.get("/oauth2callback")
async def oauth2callback(request: Request):
    params = dict(request.query_params)
    code = params.get("code")

    # 1. Get the token back from Google
    token = params.get("state")

    # 2. Find the user_id by looking up the token
    # .pop() gets the ID and deletes the token (it's single-use)
    user_id_int = pending_auth.pop(token, None)

    if not user_id_int:
        return HTMLResponse(content="<h1>Error: Invalid or expired token.</h1>")

    
    # 4. Exchange the code for credentials
    flow = create_flow()
    flow.redirect_uri = REDIRECT_URL
    
    try:
        flow.fetch_token(code=code)
    except Exception as e:
        print(f"Error fetching token for user {user_id_int}: {e}")
        return HTMLResponse(content="<h1>Error: Failed to fetch token from Google.</h1>")

    creds = flow.credentials

    # 5. ATOMIC READ-MODIFY-WRITE
    # This is the correct logic from your post
    current_tokens = load_tokens()

    current_tokens[user_id_int] = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri, # type: ignore
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes
    }

    save_tokens(current_tokens)

    # --- ADD THIS LINE ---
    print(f"✅ [AUTH SUCCESS] Token saved for user: {user_id_int}")
    # ---------------------

    # 6. Send success message
    html = """
    <h2>✅ Google Calendar connected successfully!</h2>
    <p>You can close this tab and return to Telegram now.</p>
    """
    return HTMLResponse(content=html)


@app.get("/get_user_tokens")
async def get_single_token(user_id: int, x_api_key: str = Header(None)):

    if x_api_key != Internal_API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    user_tokens = load_tokens()
    token_data = user_tokens.get(user_id) # Use int key

    if not token_data:
        raise HTTPException(status_code=404, detail="Token not found")

    # 3. Return ONLY that one user's token
    return token_data