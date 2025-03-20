# Bugzilla Report API - User Guide

A service that automatically fetches team bug reports from Bugzilla and posts status updates to Google Chat.

## Quick Start

The API provides three main endpoints:

### 1. Status Check
```
GET /
```
Returns API status. Use this to verify the service is running.

Response:
```json
{
    "status": "active",
    "message": "Hello World! I am Bizom Report API"
}
```

### 2. Bug Report Generation
```
GET /current-day-status
```

#### Parameters:
- `notify_team` (optional): Team name to fetch report for (default: "OS")
- `google_chat_webhook` (optional): Custom Google Chat webhook URL
- `skip_chat` (optional): Whether to skip sending notification to Google Chat (default: false)

#### Example Usage:

1. Default Report (OS Team):
```
GET /current-day-status
```

2. Custom Team Report:
```
GET /current-day-status?notify_team=Mobile
```

3. Custom Team with Custom Webhook:
```
GET /current-day-status?notify_team=Web&google_chat_webhook=YOUR_WEBHOOK_URL
```

4. Skip Chat Notification:
```
GET /current-day-status?skip_chat=true
```

### 3. Open Pull Requests
```
GET /open-prs
```

#### Parameters:
- `authors` (optional): Filter PRs by authors (comma-separated)
- `webhook_url` (optional): Custom Google Chat webhook URL
- `skip_chat` (optional): Whether to skip sending notification to Google Chat (default: false)

#### Example Usage:

1. All Open PRs:
```
GET /open-prs
```

2. Filter by Authors:
```
GET /open-prs?authors=laxmikanthtd,sumithhegde
```

3. Custom Webhook:
```
GET /open-prs?webhook_url=YOUR_WEBHOOK_URL
```

## Response Formats

### Success Response (Bug Report):
```json
{
    "status": "success",
    "data": {
        "TeamName": {
            "UNCONFIRMED": 5,
            "CONFIRMED": 3,
            "IN_PROGRESS": 2,
            "IN_PROGRESS_DEV": 1,
            "NEEDS_INFO": 0,
            "UNDER_REVIEW": 1,
            "RE-OPENED": 0
        }
    },
    "posted_to_chat": true,
    "webhook_used": "default"
}
```

### Success Response (Open PRs):
```json
{
    "status": "success",
    "data": [...],
    "posted_to_chat": true,
    "webhook_used": "default"
}
```

### Error Response:
```json
{
    "detail": "Error message here"
}
```

## Common Errors

1. Team Not Found (400):
   - Verify the team name exists in Bugzilla
   - Team names are case-insensitive
   - Available teams will be listed in the error message

2. Authentication Failed (401):
   - Check if Bugzilla credentials are valid
   - Ensure you have access to the report

3. Google Chat Error (500):
   - Verify webhook URL is valid
   - Check Google Chat space permissions

4. Missing Configuration (400):
   - Ensure all required environment variables are set
   - Check webhook URL configuration

## Environment Variables

Required environment variables:
- `BUGZILLA_EMAIL`
- `BUGZILLA_PASSWORD`
- `BUGZILLA_URL`
- `GOOGLE_CHAT_WEBHOOK`
- `BITBUCKET_USERNAME`
- `BITBUCKET_PASSWORD`
- `BITBUCKET_URL`

## Best Practices

1. Use consistent team names as defined in Bugzilla
2. Schedule reports at regular intervals
3. Verify webhook URLs before use
4. Monitor for error responses
5. Use `skip_chat=true` when testing to avoid unnecessary notifications

## Need Help?

Contact the development team for:
- Adding new teams
- Webhook configuration
- Access issues
- Feature requests

## Security Note

- Do not share webhook URLs publicly
- Use HTTPS for all requests
- Keep API endpoint URLs confidential
- Store sensitive credentials in environment variables

## Report Format

The Google Chat message includes:
- Team name
- Current date and time (IST)
- Bug counts by status:
  - UNCONFIRMED
  - CONFIRMED
  - IN_PROGRESS
  - IN_PROGRESS_DEV
  - NEEDS_INFO
  - UNDER_REVIEW
  - RE-OPENED
- Total active issues
- Link to full Bugzilla report

## Response Format

Success Response:
```json
{
    "status": "success",
    "message": "Report posted to Google Chat"
}
```

Error Response:
```json
{
    "detail": "Error message here"
}
```

## Common Errors

1. Team Not Found (404):
   - Verify the team name exists in Bugzilla
   - Team names are case-insensitive

2. Authentication Failed (401):
   - Check if Bugzilla credentials are valid
   - Ensure you have access to the report

3. Google Chat Error (500):
   - Verify webhook URL is valid
   - Check Google Chat space permissions

## Best Practices

1. Use consistent team names as defined in Bugzilla
2. Schedule reports at regular intervals
3. Verify webhook URLs before use
4. Monitor for error responses

## Need Help?

Contact the development team for:
- Adding new teams
- Webhook configuration
- Access issues
- Feature requests

## Security Note

- Do not share webhook URLs publicly
- Use HTTPS for all requests
- Keep API endpoint URLs confidential 