# Bugzilla Report API Documentation

## Overview
The Bugzilla Report API is a service that automates the process of fetching bug reports from Bugzilla and posting them to Google Chat. It provides real-time status updates for team bug tracking.

## Features
- Automated bug status reporting
- Google Chat integration
- Team-specific reports
- Real-time data fetching
- IST timezone support
- Customizable webhooks

## Technical Details

### Base URL
```
https://your-api-domain.com
```

### Authentication
The API uses Bugzilla credentials and Google Chat webhooks for authentication. These are configured via environment variables.

### Endpoints

#### 1. Health Check
```http
GET /
```
**Purpose**: Verify API service status

**Response**:
```json
{
    "status": "active",
    "message": "Hello World! I am Bugzilla Report API"
}
```

#### 2. Bug Report Generation
```http
GET /current-day-status
```

**Query Parameters**:
| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| notify_team | No | "os" | Team name to generate report for |
| google_chat_webhook | No | ENV value | Custom Google Chat webhook URL |

**Example Requests**:
```http
# Basic request
GET /current-day-status

# With team specification
GET /current-day-status?notify_team=os

# With custom webhook
GET /current-day-status?notify_team=os&google_chat_webhook=https://chat.googleapis.com/v1/spaces
```

### Google Chat Message Format

```
🐞 BUGZILLA STATUS REPORT - OS TEAM
📅 28 Mar 2024 | 10:30 AM IST
─────────────────────────

• UNCONFIRMED: 5
• CONFIRMED: 10
• IN_PROGRESS: 8
• IN_PROGRESS_DEV: 3
• NEEDS_INFO: 2
• UNDER_REVIEW: 4
• RE-OPENED: 1

📊 TOTAL ACTIVE ISSUES: 33

🔗 View Full Report
```

### Error Handling

| Status Code | Description | Resolution |
|-------------|-------------|------------|
| 200 | Success | Report generated and posted |
| 401 | Authentication Failed | Check Bugzilla credentials |
| 404 | Team Not Found | Verify team name |
| 500 | Server Error | Check logs for details |

### Implementation Notes

1. **Environment Setup**
   ```bash
   # Required environment variables
   BUGZILLA_EMAIL=your_email
   BUGZILLA_PASSWORD=your_password
   BUGZILLA_URL=https://bugzilla.example.com
   GOOGLE_CHAT_WEBHOOK_URL=https://chat.googleapis.com/v1/spaces
   GOOGLE_CHAT_SPACE_ID=your_space_id
   GOOGLE_CHAT_KEY=your_key
   GOOGLE_CHAT_TOKEN=your_token
   REPORT_SAVED_ID=your_report_id
   ```

2. **Webhook Configuration**
   - Format: `{GOOGLE_CHAT_WEBHOOK_URL}/{SPACE_ID}/messages?key={KEY}&token={TOKEN}`
   - Requires proper Google Chat space permissions
   - Supports custom webhooks per request

3. **Data Processing**
   - Fetches real-time data from Bugzilla
   - Processes bug statuses and counts
   - Formats data for Google Chat
   - Handles timezone conversion to IST

### Best Practices

1. **Error Handling**
   - Implement proper error monitoring
   - Log all API responses
   - Set up alerts for failed requests

2. **Security**
   - Use HTTPS for all requests
   - Keep webhook URLs confidential
   - Rotate credentials periodically
   - Monitor for unauthorized access

3. **Performance**
   - Cache responses when possible
   - Implement rate limiting
   - Monitor response times

4. **Maintenance**
   - Regular credential updates
   - Webhook validation
   - Log rotation
   - Status monitoring

## Support

For technical support or feature requests:
1. Open a GitHub issue
2. Contact the development team
3. Check the logs for detailed error messages

## Security Considerations

1. **API Security**
   - Use HTTPS only
   - Implement rate limiting
   - Validate all inputs
   - Monitor for suspicious activity

2. **Data Protection**
   - Encrypt sensitive data
   - Use secure environment variables
   - Regular security audits
   - Access control monitoring

3. **Compliance**
   - Follow data protection guidelines
   - Maintain audit logs
   - Regular security reviews 