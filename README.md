# BitZilla Report Bot

A FastAPI service that automatically fetches team bug reports from Bugzilla and open pull requests from Bitbucket, posting status updates to Google Chat.

## Features

- Fetches real-time bug status from Bugzilla
- Tracks open pull requests from Bitbucket
- Posts formatted reports to Google Chat
- Shows bug counts by status
- Author-based PR filtering
- Team-specific reports
- Secure credential handling
- Customizable webhooks

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the root directory with the following variables:

```bash
# Bugzilla Configuration
BUGZILLA_EMAIL=your_bugzilla_email@example.com
BUGZILLA_PASSWORD=your_bugzilla_password
BUGZILLA_URL=https://bugzilla.example.com

# Bitbucket Configuration
BITBUCKET_USERNAME=your_bitbucket_username
BITBUCKET_PASSWORD=your_bitbucket_app_password
BITBUCKET_URL=https://bitbucket.org

# Google Chat Configuration
GOOGLE_CHAT_WEBHOOK=your_webhook_url
```

3. Run the service:

```bash
uvicorn app.main:app --reload
```

## API Endpoints

### 1. Health Check
```http
GET /
```
Returns API status and version information.

### 2. Bug Report Generation
```http
GET /current-day-status
```
Generates and posts bug status reports for specified teams.

Parameters:
- `notify_team`: Team name (default: "OS")
- `google_chat_webhook`: Custom webhook URL (optional)
- `skip_chat`: Skip notification (default: false)

### 3. Open Pull Requests
```http
GET /open-prs
```
Fetches and posts open pull request information.

Parameters:
- `authors`: Filter by authors (comma-separated)
- `webhook_url`: Custom webhook URL (optional)
- `skip_chat`: Skip notification (default: false)

## Development

### Project Structure
```
bugzilla/
├── app/
│   ├── main.py              # FastAPI application
│   └── services/
│       ├── bitbucket.py     # Bitbucket API service
│       └── google_chat.py   # Google Chat service
├── docs/
│   ├── USER_GUIDE.md        # User documentation
│   └── DETAILED_GUIDE.md    # Technical documentation
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

### Adding New Features
1. Create new service in `app/services/`
2. Add endpoints in `app/main.py`
3. Update documentation in `docs/`
4. Add tests in `tests/`

## 🚨 Security Notice

This application requires sensitive credentials and API keys. Never commit the actual `.env` file to version control. Use `.env.example` as a template and create your own `.env` file with your credentials.

### Security Best Practices
- Use HTTPS for all API calls
- Rotate credentials periodically
- Monitor for unauthorized access
- Keep webhook URLs confidential
- Store sensitive data in environment variables
- Implement proper error handling
- Sanitize error messages
- Monitor access patterns

## Support

For technical support or feature requests:
1. Open a GitHub issue
2. Contact the development team
3. Check the logs for detailed error messages
4. Verify environment variables
5. Check team name case sensitivity

## License

This project is licensed under the MIT License - see the LICENSE file for details.
    