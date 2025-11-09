# Codeforces Reminder Bot 🤖

## 🗂️  Description

The Codeforces Reminder Bot is a Telegram bot designed to help competitive programmers stay on top of their contest schedule. It integrates with Google Calendar to provide personalized reminders for upcoming contests on the Codeforces platform. This project is perfect for programmers who want to stay organized and focused on their coding goals.

The bot is built using Python and leverages popular libraries like python-telegram-bot and FastAPI to provide a seamless experience. With its user-friendly interface and robust features, the Codeforces Reminder Bot is an essential tool for any competitive programmer.

## ✨ Key Features

### Core Features

* **Contest Reminders**: Receive notifications for upcoming contests on Codeforces
* **Google Calendar Integration**: Connect your Google Calendar to schedule events and reminders
* **User-Friendly Interface**: Interact with the bot using simple commands like `/start`, `/setprefs`, and `/nextcontest`

### Bot Commands

* `/start`: Initialize the bot and start using it
* `/setprefs`: Configure your preferences for contest reminders
* `/nextcontest`: Get information about the next contest
* `/connectauth`: Connect your Google Calendar account
* `/addevent`: Add a contest event to your Google Calendar

## start of the Bot
![Bot - Start](images/start.jpg)


## nextcontest of the Bot
![Bot - nextcontest](images/nextcontest.jpg)
![Bot - nextcontest2](images/nextcontest2.jpg)

## connectauth of the Bot
![Bot - nextcontest](images/auth.jpg)

## addevent of the Bot
![Bot - nextcontest](images/event_add.jpg)
![Bot - nextcontest](images/event_add_2.jpg)




## 🛠️ Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white&style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white&style=for-the-badge)
![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-008000?logo=telegram&logoColor=white&style=for-the-badge)
![Google Calendar API](https://img.shields.io/badge/Google%20Calendar%20API-4285F4?logo=google-calendar&logoColor=white&style=for-the-badge)
![Codeforces API](https://img.shields.io/badge/Codeforces%20API-0059B3?logo=codeforces&logoColor=white&style=for-the-badge)

## ⚙️ Setup Instructions

To run the project locally, follow these steps:

* Clone the repository: `git clone https://github.com/SaMaJiT7/Codeforces_Reminder_BOT.git`
* Install dependencies: `pip install -r requirements.txt`
* Set environment variables for Google Calendar API and Codeforces API
* Run the server: `uvicorn server:app --host 0.0.0.0 --port 8000`
* Run the bot: `python codeforces.py`

## 📈 GitHub Actions

This repository uses GitHub Actions to automate testing and deployment. The workflow is triggered on push events to the main branch and runs the following jobs:

* **Linting**: Checks for code style and syntax errors
* **Testing**: Runs unit tests and integration tests
* **Deployment**: Deploys the bot to a production environment

```mermaid
graph TD;
  push-->linting;
  push-->testing;
  push-->deployment;
```



<br><br>
<div align="center">
<img src="https://avatars.githubusercontent.com/u/139092138?v=4" width="120" />
<h3>SAMAJIT NANDI</h3>
<p>No information available.</p>
</div>
<br>
<p align="right">
<img src="https://gitfull.vercel.app/appLogo.png" width="20"/>  <a href="https://gitfull.vercel.app">Made by GitFull</a>
</p>
    