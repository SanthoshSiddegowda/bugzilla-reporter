# Bitzilla Report API Documentation

## Overview

The Bitzilla Report API is a FastAPI-based application that integrates with Bugzilla and Bitbucket to provide automated reporting and notifications for engineering teams. It helps teams track bugs, SLA misses, and other important metrics through Google Chat notifications.

## Features

- **Bugzilla Integration**: Authenticates with Bugzilla and retrieves bug reports
- **Priority Bug Tracking**: Identifies and reports on high-priority bugs
- **SLA Monitoring**: Tracks bugs that have missed SLA deadlines
- **Current Day Status**: Provides daily bug status reports
- **Google Chat Notifications**: Sends automated notifications to team channels
- **Bitbucket Integration**: Connects with Bitbucket for repository information

## Environment Setup

The application requires several environment variables to be set:

```
BUGZILLA_EMAIL=your_bugzilla_email
BUGZILLA_PASSWORD=your_bugzilla_password
BUGZILLA_URL=https://your_bugzilla_instance
GOOGLE_CHAT_WEBHOOK=your_google_chat_webhook_url
BITBUCKET_USERNAME=your_bitbucket_username
BITBUCKET_PASSWORD=your_bitbucket_password
BITBUCKET_URL=https://your_bitbucket_instance
```

A `.env.example` file is provided in the root directory as a template.

## API Endpoints

### Bugzilla Endpoints

#### GET /bugzilla/get-priority-bug-miss

Returns priority bug misses for a specific team and optionally sends a notification to Google Chat.

**Query Parameters:**
- `notify_team` (string, default: "OS"): Team to notify
- `google_chat_webhook` (string, optional): Custom webhook URL
- `skip_chat` (boolean, default: false): Skip sending notification

#### GET /bugzilla/current-day-status

Returns the current day's bug status for all teams and optionally sends a notification.

**Query Parameters:**
- `notify_team` (string, default: "OS"): Team to notify
- `google_chat_webhook` (string, optional): Custom webhook URL
- `skip_chat` (boolean, default: false): Skip sending notification

#### GET /bugzilla/get-sla-missed-bugs

Returns SLA missed bugs report for a specific team and optionally sends a notification.

**Query Parameters:**
- `notify_team` (string, default: "OS"): Team to notify
- `google_chat_webhook` (string, optional): Custom webhook URL
- `days` (integer, default: 3): Number of days to look back
- `skip_chat` (boolean, default: false): Skip sending notification

### Bitbucket Endpoints

#### GET /bitbucket/open-prs

Returns all open pull requests across repositories and optionally sends a notification to Google Chat.

**Query Parameters:**
- `authors` (string, optional): Filter PRs by authors (comma-separated, e.g., 'laxmikanthtd,sumithhegde')
- `webhook_url` (string, optional): Custom webhook URL for Google Chat notifications
- `skip_chat` (boolean, default: false): Skip sending notification

## Authentication

The application uses session-based authentication with Bugzilla, handling login tokens and cookies automatically. For Bitbucket, it uses basic authentication with the provided credentials.

## Notification System

The Google Chat notification system formats and sends messages to team channels with information about bugs, SLA misses, and daily status reports. Custom webhooks can be provided per request to send notifications to different channels.

The notification system supports several message formats:

- **Current Day Bug Status**: Shows a breakdown of bugs by status for a specific team
- **Priority Bug Notifications**: Highlights high-priority bugs that have missed SLA deadlines
- **SLA Missed Bugs**: Reports on all bugs that have missed their SLA deadlines
- **Open Pull Requests**: Lists all open PRs in Bitbucket, optionally filtered by author

All notifications include direct links to the relevant Bugzilla bugs or Bitbucket pull requests for easy access.

## Project Structure

```
bugzilla/
├── app/
│   ├── main.py              # FastAPI application
│   ├── routers/
│   │   ├── bugzilla.py      # Bugzilla API endpoints
│   │   └── bitbucket.py     # Bitbucket API endpoints
│   └── services/
│       ├── bitbucket.py     # Bitbucket API service
│       └── google_chat.py   # Google Chat service
├── doc/
│   └── README.md            # This documentation
├── requirements.txt         # Python dependencies
└── README.md               # Project overview
```

## Running the Application

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up environment variables (create a `.env` file based on `.env.example`)

3. Run the FastAPI application:
   ```
   uvicorn app.main:app --reload
   ```

4. Access the API documentation at `http://localhost:8000/docs`

5. Use the API endpoints with appropriate query parameters as documented above

## Error Handling

The application includes comprehensive error handling for:
- Authentication failures
- API request failures
- Missing environment variables
- Invalid team names
- Empty report results

Errors are returned as HTTP exceptions with appropriate status codes and detailed messages.