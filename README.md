# Bugzilla Report Bot

A FastAPI service that automatically fetches team bug reports from Bugzilla and posts status updates to Google Chat.

## Features

- Fetches real-time bug status from Bugzilla
- Posts formatted reports to Google Chat
- Shows bug counts by status
- Automatic IST timezone conversion
- Secure credential handling

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the root directory with the following variables:

```bash
BUGZILLA_EMAIL=your_bugzilla_email@example.com
BUGZILLA_PASSWORD=your_bugzilla_password
BUGZILLA_URL=https://bugzilla.mozilla.org
GOOGLE_CHAT_WEBHOOK_URL=https://chat.googleapis.com/v1/spaces/
GOOGLE_CHAT_SPACE_ID=your_space_id
GOOGLE_CHAT_KEY=your_key   
```

3. Run the service:

```bash
uvicorn app.main:app --reload
```

## 🚨 Security Notice

This application requires sensitive credentials and API keys. Never commit the actual `.env` file to version control. Use `.env.example` as a template and create your own `.env` file with your credentials.
    