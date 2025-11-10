import os
import json
import secrets
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from google_auth_oauthlib.flow import Flow
from dotenv import load_dotenv

# --- Import your new storage file ---
import server_storage

load_dotenv()

# --- Config (from .env) ---
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
Internal_API_KEY = os.getenv("INTERNAL_API_KEY")
FASTAPI_SERVER_URL = os.getenv("FASTAPI_SERVER_URL")

# --- Config (Hardcoded) ---
SCOPES = [
    "https.www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly"
]
# This MUST be your public server URL (from Render, not localhost)
REDIRECT_URL = f"{FASTAPI_SERVER_URL}/oauth2callback"

app = FastAPI()

# --- DELETED REDUNDANT CODE ---
# The Redis connection (r) and KEY definitions
# are now correctly handled inside server_storage.py
# ------------------------------

def create_flow():
    """Creates a new Google OAuth Flow instance."""
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
    )

@app.get("/")
async def root():
    return {"message": "Codeforces Bot Auth Server is running."}

@app.get("/connect")
# --- FIX: Changed user_id: str to user_id: int to match the bot ---
async def connect(token: str, user_id: int):
    # Use the storage function
    server_storage.save_pending_auth(token, user_id)
    
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
    token = params.get("state")

    # Use the storage function
    user_id_int = server_storage.pop_pending_auth(token)

    if not user_id_int:
        return HTMLResponse(content="<h1>Error: Invalid or expired auth token.</h1><p>Please try connecting from Telegram again.</p>")

    flow = create_flow()
    flow.redirect_uri = REDIRECT_URL
    
    try:
        flow.fetch_token(code=code)
    except Exception as e:
        print(f"Error fetching token for user {user_id_int}: {e}")
        return HTMLResponse(content="<h1>Error: Failed to fetch token from Google.</h1>")

    creds = flow.credentials
    
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri, # type: ignore
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes
    }
    
    # Use the storage function
    server_storage.save_token_for_user(user_id_int, token_data)
    
    print(f"✅ [AUTH SUCCESS] Token saved for user: {user_id_int}")
    return HTMLResponse(content="<h2>✅ Google Calendar connected!</h2><p>You can close this tab.</p>")

# --- FIX: Renamed endpoint to /get-user-token to match bot ---
@app.get("/get-user-token")
async def get_single_token(user_id: int, x_api_key: str = Header(None)):
    if x_api_key != Internal_API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # Use the storage function
    token_data = server_storage.load_tokens().get(user_id)

    if not token_data:
        raise HTTPException(status_code=404, detail="Token not found")

    return token_data