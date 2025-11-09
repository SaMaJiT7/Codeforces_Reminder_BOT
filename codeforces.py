from telegram.ext import Application
import requests
from requests.exceptions import HTTPError
import datetime
from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.ext import CommandHandler, Updater, CallbackContext, ApplicationBuilder , ContextTypes, CallbackQueryHandler
from typing import List, Dict
import json, os
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import httpx
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import shlex
import secrets
from telegram import BotCommand
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

load_dotenv()

Internal_API_KEY = os.getenv("INTERNAL_API_KEY")

FASTAPI_SERVER_URL = os.getenv("FASTAPI_SERVER_URL")


# --- PERSISTENT STORAGE FOR USER PREFERENCES ---
Preferences_FILE = "user_prefs.json"
TOKENS_FILE = "user_tokens.json"
USERS_FILE = "subscribed_users.json"
REMINDED_FILE = "reminded_contests.json"

def load_prefs():
    """Loads user preferences from a JSON file when the bot starts."""
    try:
        # 1. Check if the file exists
        if not os.path.exists(Preferences_FILE):
            return {}  # Return an empty dict if the file doesn't exist

        # 2. Open and load the file
        with open(Preferences_FILE, "r") as f:
            data = json.load(f)
            
            # 3. JSON saves all keys as strings. We must convert them
            #    back to integers for user_ids.
            return {int(k): v for k, v in data.items()}
            
    except json.JSONDecodeError:
        # This happens if the file is empty or corrupted
        print(f"Warning: {Preferences_FILE} is empty or corrupt. Starting fresh.")
        return {}
    except Exception as e:
        print(f"Error loading preferences: {e}")
        return {}

def save_prefs(prefs):
    with open(Preferences_FILE, "w") as f:
        json.dump(prefs, f)


# --- Generic Set Functions (For Users & Reminders) ---
def load_set_from_file(filename: str) -> set:
    """Loads a set from a JSON file."""
    if not os.path.exists(filename):
        return set()  # Return an empty set if no file
    try:
        with open(filename, "r") as f:
            data_list = json.load(f)
            return set(data_list)  # Convert the loaded list back to a set
    except (json.JSONDecodeError, TypeError):
        print(f"Warning: Could not decode {filename}. Starting fresh.")
        return set()
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return set()

def save_set_to_file(data_set: set, filename: str):
    """Saves a set to a JSON file."""
    try:
        with open(filename, "w") as f:
            data_list = list(data_set)  # Convert the set to a list for JSON
            json.dump(data_list, f, indent=4)
    except Exception as e:
        print(f"Error saving {filename}: {e}")


user_prefs = load_prefs()
subscribed_users = load_set_from_file(USERS_FILE)
reminded_contests = load_set_from_file(REMINDED_FILE)


def get_upcoming_contests():

    API_URL = "https://codeforces.com/api/contest.list"
    params = {'gym': 'false'}
    
    # This header identifies your script. This is the fix.
    headers = {
        'User-Agent': 'MyCodeforcesBot/1.0'
    }

    try:
        response = requests.get(API_URL, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "OK":
            print("API reported an error, not 'OK'.")
            return None  # <-- FIX 1: Return None, not a string

        contests = data["result"]
        
        # Use a list comprehension (square brackets) to create the list directly
        upcoming_contests = [c for c in contests if c["phase"] == "BEFORE"]
        
        contests_sorted = sorted(upcoming_contests, key=lambda x: x['startTimeSeconds'])
        return contests_sorted[:10] # Success! Return the list

    except HTTPError as http_err:
        if http_err.response.status_code == 400:
            print(f"Error 400: Bad Request. Check your API parameters.")
            try:
                print(f"Details: {http_err.response.json()}")
            except requests.exceptions.JSONDecodeError:
                print(f"Details: {http_err.response.text}")
        else:
            print(f"An HTTP error occurred: {http_err}")
            
    except requests.exceptions.JSONDecodeError:
        print("Failed to decode the response as JSON.")
        
    except Exception as err:
        print(f"A non-HTTP error occurred: {err}")
        
    return None  # <-- FIX 2: Return None on ANY exception


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users_id  = update.effective_user.id # type: ignore
    subscribed_users.add(users_id)
    save_set_to_file(subscribed_users, USERS_FILE)
    
    # --- FIX: Changed command names to match your handlers ---
    welcome_text = (
    "👋 *Hi there!* I'm your **Codeforces Reminder Bot** 🤖\n\n"
    "Here’s what I can do for you:\n"
    "📅 /nextcontest – See upcoming Codeforces contests\n"
    "🎯 /setprefs Div.2 Div.4 – Choose which contest divisions you want reminders for\n"
    "🔗 /connectauth – Connect your Google Calendar to auto-add contests\n"
    "⏰ /addevent – Manually add a custom event or reminder\n\n"
    "Let’s make sure you *never miss a contest again!* 🚀"
    )
    
    await update.message.reply_text(  # type: ignore
        welcome_text,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

async def setprefs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if not update.effective_user or not update.message:
        return  # Safety: avoid NoneType errors

    user_id  = update.effective_user.id   #type: ignore
    prefs = context.args or []

    if not prefs:
        await update.message.reply_text("Please Provide at least any preference (e.g., Div.2, Div.3).")  # type: ignore
        return
    
    
    user_prefs[user_id] = prefs # type: ignore
    save_prefs(user_prefs)

    await update.message.reply_text(f"Preferences Saved! You will now recieve contest for Divisions: {', '.join(prefs)}") # type: ignore


async def nextcontest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id # type: ignore
    contests = get_upcoming_contests()

    # --- THIS IS THE SAFETY CHECK ---
    # If the API call failed, 'contests' will be None.
    # This 'if' block stops the function and prevents the crash.
    if contests is None:
        await update.message.reply_text("Sorry, I couldn't fetch the contest data. Please try again later.") # type: ignore
        return  # Stop the function
    # --------------------------------

    prefs = user_prefs.get(user_id, []) # type: ignore

    if prefs:
        contests = [c for c in contests if any(div in c["name"] for div in prefs)] # type: ignore

    if not contests:
        await update.message.reply_text("No upcoming contests found according to your preferences.") # type: ignore
        return
    
    
    # --- FIX 1: Send the header ONCE, before the loop ---
    await update.message.reply_text("🏁 Upcoming Contests:") # type: ignore
    
    # --- THIS IS THE LOOP ---
    # It just builds the 'msg' string
    for c in contests:
        #FIX 2: Build the message from scratch ---
        start_time = datetime.fromtimestamp(c['startTimeSeconds']).strftime("%a, %d %b %Y at %I:%M %p") # type: ignore
        msg = (
            f"• *{c['name']}*\n"
            f"  🕒 Start Time: {start_time}\n"
            f"  Duration: {c['durationSeconds']//3600} hrs\n"
            f"  🔗 Link: https://codeforces.com/contests/{c['id']}"
        )

        button = InlineKeyboardButton(
            text="Add to Google Calender",
            callback_data=f"add_{c['id']}" 
        )

        #keyboard creation
        keyboard = InlineKeyboardMarkup(
            [[button]]
        )
        
        await update.message.reply_text(msg,reply_markup=keyboard,parse_mode="Markdown") #type: ignore
    
    # --- END OF THE LOOP ---



async def handle_to_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # type: ignore

    try:
        data = query.data # type: ignore
        user_id = query.from_user.id # type: ignore
        print(f"Callback triggered: {data} from {user_id}")

        if not data.startswith("add_"): # type: ignore
            return

        contest_id = data.split("_")[1] # type: ignore
        creds = await get_creds_for_user(user_id)
        if not creds:
            await query.message.reply_text("Please authenticate with /connectauth first.") # type: ignore
            return

        contests = get_upcoming_contests()
        if not contests:
            await query.message.reply_text("Couldn’t fetch contests.") # type: ignore
            return

        contest_to_add = next((c for c in contests if str(c["id"]) == contest_id), None)
        if not contest_to_add:
            await query.message.reply_text("Contest not found.") # type: ignore
            return

        summary = contest_to_add["name"]
        tz = await get_user_timezone(user_id)
        start_dt = datetime.fromtimestamp(contest_to_add['startTimeSeconds'])
        end_dt = start_dt + timedelta(seconds=contest_to_add['durationSeconds'])

        event_body = {
            'summary': summary,
            'start': {'dateTime': start_dt.isoformat(), 'timeZone': tz},
            'end': {'dateTime': end_dt.isoformat(), 'timeZone': tz},
        }

        service = build('calendar', 'v3', credentials=creds)

        def insert_event():
            return service.events().insert(calendarId='primary', body=event_body).execute()

        print("Inserting event...")
        await asyncio.to_thread(insert_event)
        print("✅ Event added!")

        await query.edit_message_text(f"✅ Event '{summary}' added to your calendar!") # type: ignore

    except Exception as e:
        print(f" ERROR in handle_to_button: {e}")
        import traceback
        traceback.print_exc()
        await query.message.reply_text("⚠️ Something went wrong.") # type: ignore









#Setting the Reminder Scheduler
async def send_reminders(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    contests = get_upcoming_contests()

    # Safety check: Stop if the API call failed
    if contests is None:
        print("send_reminders: Failed to fetch contests, skipping run.")
        return
    
    now = datetime.now().timestamp() # type: ignore

    for c in contests: # type: ignore
        start_time = c["startTimeSeconds"]
        Time_left = start_time - now


        if 0 < Time_left <= 1800 and c["id"] not in reminded_contests: #30 minutes before the contest
            for user_id in subscribed_users:
                prefs = user_prefs.get(user_id, []) # type: ignore

                if prefs  and not any(div in c["name"] for div in prefs):
                    continue

                try:
                    await bot.send_message(
                        chat_id = user_id,
                        text=f"⏰ Reminder: *{c['name']}* starts in 30 minutes!\nJoin here: https://codeforces.com/contests",
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    print(f"Failed to send Reminde to {user_id}: {e}")

            # --- FIX 4 (SPAM): Add contest to the set so we don't send again ---
            reminded_contests.add(c['id'])
            save_set_to_file(reminded_contests, REMINDED_FILE)


async def connectgoogle_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id # type: ignore
    token = secrets.token_urlsafe(16)

    # Send both the token and user_id to your server
    auth_url = f"{FASTAPI_SERVER_URL}/connect?token={token}&user_id={user_id}"

    text = (
        "🗓️ *Connect your Google Calendar!*\n\n"
        "Click the button below to securely connect your calendar account.\n\n"
        f"[🔗 Connect Google Calendar]({auth_url})"
    )
    
    
    print(f"[INFO] User {user_id} started calendar connection with token {token}")

    await update.message.reply_text( #type: ignore
        text,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

async def get_creds_for_user(user_id: int):

    headers = {"X-API-KEY": Internal_API_KEY}
    Params = {"user_id": user_id}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{FASTAPI_SERVER_URL}/get_user_tokens", headers=headers, params=Params ,timeout=10.0) # type: ignore
            response.raise_for_status()

            token_data = response.json()
            return Credentials(**token_data)
        
        except httpx.HTTPStatusError as http_err:
            # This catches 4xx and 5xx errors
            if http_err.response.status_code == 404:
                print(f"Token not found for user {user_id}")
            else:
                print(f"HTTP error from token server: {http_err}")
            return None
            
        except httpx.RequestError as e:
            # This catches network errors (connection, timeout, etc.)
            print(f"Failed to connect to token server: {e}")
            return None
        except Exception as e:
            # Catch any other unexpected errors
            print(f"An unknown error occurred: {e}")
            return None
        

#setting the timezone of the user
async def get_user_timezone(user_id: int):
    creds = await get_creds_for_user(user_id)

    if not creds:
        print(f"No creds for user {user_id}, defaulting to UTC.")
        return "UTC"
    try:
        service = build('calendar', 'v3', credentials=creds)
        # 3. Define the slow, blocking code you want to run
        def get_calendar_from_google():
            # This .execute() call is what freezes your bot
            return service.calendars().get(calendarId='primary').execute()
        # 4. Run the blocking code in a separate thread
        # This is the key fix. The 'await' pauses this function,
        # but the rest of your bot keeps running.
        calendar_data = await asyncio.to_thread(get_calendar_from_google)

        time_zone = calendar_data.get('timeZone', 'UTC')
        return time_zone
    
    except Exception as e:
        print(f"Error getting timezone for {user_id}: {e}")
        return "UTC"  # Always default to UTC on any error
        
# Command to add event to Google Calendar
async def add_event_to_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id  # type: ignore

    creds = await get_creds_for_user(user_id)

    if not creds:
        print(f"❌ User {user_id} not authenticated.")
        await update.message.reply_text("Please authenticate your Google Account /connectauth to use this feature.")  # type: ignore
        return
    
    
    # 2. Check if any arguments were provided at all
    if not context.args:
        await update.message.reply_text(  # type: ignore
            "Usage:\n/add_event <event_title> <start_time>\n\n"
            "Example:\n/add_event \"Codeforces Round\" \"2025-11-10T10:00:00\""
        )
        return
    
    # 3. Parse arguments using shlex (This is the main fix)
    # --- INDENTATION FIXED HERE ---
    try:
        args_string = " ".join(context.args)
        # 3. shlex.split() now correctly parses the string with quotes
        parsed_args = shlex.split(args_string)
    except ValueError:
        await update.message.reply_text("Error: Mismatched quotes in your command.") # type: ignore
        return
    # ----------------------------

    if len(parsed_args) < 2:
        await update.message.reply_text( # type: ignore
            "Usage:\n/add_event <event_title> <start_time>\n\n"
            "Example:\n/add_event \"Codeforces Round\" \"2025-11-10T10:00:00\""
        )
        return

    summary = parsed_args[0]
    start_time_str = parsed_args[1]

    # 5. Build the Google Calendar event
    try:
        timeZone_user = await get_user_timezone(user_id)
        # Try to parse the time string to make sure it's valid
        # We assume a 1-hour duration for this example
        start_dt = datetime.fromisoformat(start_time_str) # type: ignore
        end_dt = start_dt + timedelta(hours=1) # type: ignore
        
        # This is the format Google API needs
        event_body = {
            'summary': summary,
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': timeZone_user,
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': timeZone_user,
            },
        }

    except ValueError:
        await update.message.reply_text( #type:ignore
            "Error: Invalid time format. Please use ISO format:\n"
            "YYYY-MM-DDTHH:MM:SS"
        )
        return
    
    
    # 6. Insert the event
    try:
        # Build the Google Calendar service
        service = build('calendar', 'v3', credentials=creds)
        
        # Define the blocking function
        def insert_event_to_google():
            return service.events().insert(calendarId='primary', body=event_body).execute()

        # Run it with asyncio.to_thread to prevent freezing
        await asyncio.to_thread(insert_event_to_google)
        
        await update.message.reply_text(f"✅ Event '{summary}' added to your calendar!") # type: ignore
        
        
    except Exception as e:
        print(f"Failed to add event for {user_id}: {e}")
        # This could fail if the token expired.
        await update.message.reply_text("❌ Sorry, I couldn't add the event. Please try to /auth again.") # type: ignore


async def post_init(application: Application):
    """
    This function runs *after* the bot is initialized
    but *before* polling starts.
    """
    print("Setting bot commands...")
    commands = [
        BotCommand("start", "Subscribe to notifications"),
        BotCommand("nextcontest", "Show upcoming contests"),
        BotCommand("setprefs", "Set your preferred divisions"),
        BotCommand("connectauth", "Connect your Google Calendar"),
        BotCommand("addevent", "Manually add an event"),
    ]
    
    try:
        await application.bot.set_my_commands(commands) # type: ignore
        print("Bot commands set successfully.")
    except Exception as e:
        print(f"Failed to set bot commands: {e}")






def main():
    # 1. Make sure "TELEGRAM_TOKEN" matches your .env file
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        print("Error: TELEGRAM_TOKEN not found in environment variables!")
        return

    # 2. Removed the extra dot "..post_init"
    application = (
        ApplicationBuilder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    ) # type: ignore

    application.add_handler(CommandHandler("start", start))
    
    # 3. Fixed "setpref" -> "setprefs"
    application.add_handler(CommandHandler("setprefs", setprefs))
    
    # 4. Fixed "NextContest" -> "nextcontest"
    application.add_handler(CommandHandler("nextcontest", nextcontest))

    application.add_handler(CommandHandler("connectauth", connectgoogle_auth))
    application.add_handler(CommandHandler("addevent", add_event_to_calendar))
    application.add_handler(CallbackQueryHandler(handle_to_button))
    
    # --- SCHEDULE THE JOB ---
    job_queue = application.job_queue
    job_queue.run_repeating(send_reminders, interval=900) # type: ignore

    print("CF Bot is Running with the reminders...")
    application.run_polling() # type: ignore

if __name__ == "__main__":
    main()

