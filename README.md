Codeforces Reminder & Google Calendar Bot

A comprehensive Telegram bot that sends Codeforces contest reminders, allows users to filter by division, and automatically adds contests to their Google Calendar.

This project uses a secure, two-part system:

A Telegram Bot (codeforces.py) that handles all user interaction.

A FastAPI Server (server.py) that manages the secure Google OAuth2 flow and acts as a "token vault" for user credentials.

Features

Contest Notifications: A background job runs every 15 minutes to check for contests starting soon.

Google Calendar Integration:

Securely connect a Google account using /connectauth.
![Bot Preview - auth](images/auth.jpg)

Add contests to your calendar with a single click using inline buttons.

Manually add custom events with /addevent.
![Bot Preview - eventadd](images/event_add.jpg)
![Bot Preview - eventadd2](images/event_add_2.jpg)

NEXT CONTEST DETAILS:
![Bot Preview - nextcontest](images/nextcontest.jpg)
![Bot Preview - nextcontest2](images/nextcontest2.jpg)


Subscribe from reminders (/start).
![Bot Preview - start](images/start.jpg)

Set preferred divisions (e.g., "Div. 2") with /setprefs.

Persistent Storage: Uses JSON files to save user preferences, subscriptions, and Google tokens. No data is lost on restart.

Tech Stack

Bot: python-telegram-bot

Server: fastapi, uvicorn

Google API: google-api-python-client, google-auth-oauthlib

HTTP Client: httpx (for bot-to-server communication)

Scheduling: apscheduler

Environment: python-dotenv

Data: json, shlex, secrets

Setup & Installation

Follow these steps to run the bot locally.

1. Clone the Repository

git clone [https://github.com/SaMaJiT7/Codeforces_Reminder_BOT.git](https://github.com/SaMaJiT7/Codeforces_Reminder_BOT.git)
cd Codeforces_Reminder_BOT


2. Create requirements.txt

Create a file named requirements.txt and paste this in:

python-telegram-bot
python-dotenv
requests
google-api-python-client
google-auth-oauthlib
fastapi
uvicorn[standard]
httpx
apscheduler


3. Install Dependencies

pip install -r requirements.txt


4. Create Your Secret Files

This project uses a .gitignore file to keep all secret keys off of GitHub. You will need to create these files yourself.

A. Create .env file
In the root folder, create a .env file for all your API keys:

TELEGRAM_TOKEN=123456:ABC...xyz
INTERNAL_API_KEY=a-very-long-and-random-password
FASTAPI_SERVER_URL=[http://127.0.0.1:8000](http://127.0.0.1:8000)


TELEGRAM_TOKEN: Get this from BotFather on Telegram.

INTERNAL_API_KEY: Make up a long, random password. The bot and server use this to trust each other.

B. Create client_secrets.json
This file is for Google OAuth and is used by server.py.

Go to the Google Cloud Console.

Create a new project.

Enable the "Google Calendar API" in the "Library".

Go to "Credentials" and "Create Credentials" > "OAuth client ID".

Select "Web application".

Under "Authorized redirect URIs", add your server's callback URL.

For local testing with uvicorn: http://127.0.0.1:8000/oauth2callback

For testing with ngrok: https://<your-ngrok-url>.ngrok-free.app/oauth2callback

Click "Create", then download the JSON credentials.

Rename the downloaded file to client_secrets.json and place it in your project folder.

5. Run the Project

You must run both the server and the bot in two separate terminals.

Terminal 1: Run the FastAPI Server

uvicorn server:app --reload


(This will run the server on http://127.0.0.1:8000)

Terminal 2: Run the Telegram Bot

python codeforces.py


Bot Commands

Command

Description

/start

Subscribe to notifications.

/nextcontest

Show upcoming contests with "Add to Calendar" buttons.

/stats <handle>

Get a user's Codeforces rating and rank.

/setprefs <Div. 1>

Set your preferred divisions (e.g., /setprefs Div. 2 Div. 3).

/connectauth

Connect your Google Calendar.

/addevent "<Title>" "<Time>"

Manually add an event (e.g., /addevent "My Event" "2025-11-10T10:00:00").

/unsubscribe

Stop all notifications.

/help

Show this help message.