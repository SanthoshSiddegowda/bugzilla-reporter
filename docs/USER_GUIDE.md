# Bugzilla Report API - User Guide

A service that automatically fetches team bug reports from Bugzilla and posts status updates to Google Chat.

## Quick Start

The API provides two main endpoints:

### 1. Status Check
```
GET /
```
Returns API status. Use this to verify the service is running.

### 2. Bug Report Generation
```
GET /current-day-status
```

#### Parameters:
- `notify_team` (optional): Team name to fetch report for (default: "os")
- `google_chat_webhook` (optional): Custom Google Chat webhook URL

#### Example Usage:

1. Default Report (OS Team):
```
GET /current-day-status
```

2. Custom Team Report:
```
GET /current-day-status?notify_team=mobile
```

3. Custom Team with Custom Webhook:
```
GET /current-day-status?notify_team=web&google_chat_webhook=YOUR_WEBHOOK_URL
```

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