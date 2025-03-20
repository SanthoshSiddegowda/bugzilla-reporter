# Bugzilla Report API Documentation

## Overview
The Bugzilla Report API is a service that automates the process of fetching bug reports from Bugzilla and posting them to Google Chat. It provides real-time status updates for team bug tracking and open pull request monitoring.

## Features
- Automated bug status reporting
- Open pull request tracking
- Google Chat integration
- Team-specific reports
- Real-time data fetching
- IST timezone support
- Customizable webhooks
- Author-based PR filtering

## Technical Details

### Base URL
```
https://your-api-domain.com
```

### Authentication
The API uses Bugzilla credentials, Bitbucket credentials, and Google Chat webhooks for authentication. These are configured via environment variables.

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
    "message": "Hello World! I am Bizom Report API"
}
```

#### 2. Bug Report Generation
```http
GET /current-day-status
```

**Query Parameters**:
| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| notify_team | No | "OS" | Team name to generate report for |
| google_chat_webhook | No | ENV value | Custom Google Chat webhook URL |
| skip_chat | No | false | Whether to skip sending notification |

**Example Requests**:
```http
# Basic request
GET /current-day-status

# With team specification
GET /current-day-status?notify_team=Mobile

# With custom webhook
GET /current-day-status?notify_team=Web&google_chat_webhook=https://chat.googleapis.com/v1/spaces

# Skip chat notification
GET /current-day-status?skip_chat=true
```

#### 3. Open Pull Requests
```http
GET /open-prs
```

**Query Parameters**:
| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| authors | No | None | Filter PRs by authors (comma-separated) |
| webhook_url | No | ENV value | Custom Google Chat webhook URL |
| skip_chat | No | false | Whether to skip sending notification |

**Example Requests**:
```http
# All open PRs
GET /open-prs

# Filter by authors
GET /open-prs?authors=laxmikanthtd,sumithhegde

# With custom webhook
GET /open-prs?webhook_url=https://chat.googleapis.com/v1/spaces
```

### Response Formats

#### Bug Report Success Response:
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

#### Open PRs Success Response:
```json
{
    "status": "success",
    "data": [...],
    "posted_to_chat": true,
    "webhook_used": "default"
}
```

### Error Handling

| Status Code | Description | Resolution |
|-------------|-------------|------------|
| 200 | Success | Report generated and posted |
| 400 | Bad Request | Check team name or webhook URL |
| 401 | Authentication Failed | Check Bugzilla/Bitbucket credentials |
| 500 | Server Error | Check logs for details |

### Implementation Notes

1. **Environment Setup**
   ```bash
   # Required environment variables
   BUGZILLA_EMAIL=your_email
   BUGZILLA_PASSWORD=your_password
   BUGZILLA_URL=https://bugzilla.example.com
   BITBUCKET_USERNAME=your_username
   BITBUCKET_PASSWORD=your_app_password
   BITBUCKET_URL=https://bitbucket.org
   GOOGLE_CHAT_WEBHOOK=your_webhook_url
   ```

2. **Webhook Configuration**
   - Supports custom webhooks per request
   - Falls back to environment variable if not provided
   - Validates webhook URL before use
   - Requires proper Google Chat space permissions

3. **Data Processing**
   - Fetches real-time data from Bugzilla
   - Processes bug statuses and counts
   - Handles case-insensitive team names
   - Formats data for Google Chat
   - Processes PR data from Bitbucket

### Best Practices

1. **Error Handling**
   - Implement proper error monitoring
   - Log all API responses
   - Set up alerts for failed requests
   - Use descriptive error messages

2. **Security**
   - Use HTTPS for all requests
   - Keep webhook URLs confidential
   - Rotate credentials periodically
   - Monitor for unauthorized access
   - Store sensitive data in environment variables

3. **Performance**
   - Cache responses when possible
   - Implement rate limiting
   - Monitor response times
   - Use async operations for I/O

4. **Maintenance**
   - Regular credential updates
   - Webhook validation
   - Log rotation
   - Status monitoring
   - Team name validation

## Support

For technical support or feature requests:
1. Open a GitHub issue
2. Contact the development team
3. Check the logs for detailed error messages
4. Verify environment variables
5. Check team name case sensitivity

## Security Considerations

1. **API Security**
   - Use HTTPS only
   - Implement rate limiting
   - Validate all inputs
   - Monitor for suspicious activity
   - Sanitize error messages

2. **Data Protection**
   - Encrypt sensitive data
   - Use secure environment variables
   - Regular security audits
   - Access control monitoring
   - Secure credential storage

3. **Compliance**
   - Follow data protection guidelines
   - Maintain audit logs
   - Regular security reviews
   - Monitor access patterns
   - Implement proper error handling 