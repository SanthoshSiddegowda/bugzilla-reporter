# Bitzilla Developer Guide

## Introduction

This developer guide provides detailed technical information for developers working on the Bitzilla Report API project. It covers the architecture, implementation details, and development workflows to help you understand, maintain, and extend the codebase.

## Architecture Overview

Bitzilla is built using FastAPI, a modern Python web framework optimized for API development. The application follows a modular architecture with clear separation of concerns:

```
bugzilla/
├── app/                   # Application code
│   ├── main.py            # FastAPI application entry point
│   ├── routers/           # API endpoint definitions
│   │   ├── bugzilla.py    # Bugzilla-related endpoints
│   │   └── bitbucket.py   # Bitbucket-related endpoints
│   └── services/          # Business logic and external integrations
│       ├── bitbucket.py   # Bitbucket API client
│       └── google_chat.py # Google Chat notification service
├── doc/                   # Documentation
├── requirements.txt       # Python dependencies
└── .env.example          # Environment variable template
```

### Key Components

1. **FastAPI Application (main.py)**
   - Initializes the FastAPI application
   - Configures application metadata from environment variables
   - Validates required environment variables
   - Registers routers for different API endpoints

2. **Routers**
   - Define API endpoints and handle HTTP requests
   - Implement request validation and error handling
   - Coordinate between services to fulfill requests

3. **Services**
   - Encapsulate business logic and external API interactions
   - Provide reusable functionality for routers
   - Handle authentication and data formatting

## Development Environment Setup

### Prerequisites

- Python 3.8 or higher
- Access to Bugzilla and Bitbucket instances
- Google Chat webhook URL for notifications

### Installation Steps

1. Clone the repository

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example`:
   ```
   APP_NAME=Bitzilla
   APP_DESC="BitZilla is a bug tracking system..."
   APP_VERSION=1.0.0

   BUGZILLA_EMAIL=your_email@example.com
   BUGZILLA_PASSWORD=your_password
   BUGZILLA_URL=your_bugzilla_url

   GOOGLE_CHAT_WEBHOOK=your_chat_url

   BITBUCKET_USERNAME=your_bitbucket_username
   BITBUCKET_PASSWORD=your_bitbucket_password
   BITBUCKET_URL=https://api.bitbucket.org/2.0
   ```

5. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

6. Access the API documentation at `http://localhost:8000/docs`

## Implementation Details

### Authentication Mechanisms

#### Bugzilla Authentication

The application uses session-based authentication with Bugzilla through the `get_session_with_login()` function in `bugzilla.py`. This function:

1. Creates a new requests session
2. Retrieves the login page to get CSRF tokens
3. Submits login credentials
4. Maintains the authenticated session for subsequent requests

Key implementation details:
```python
def get_session_with_login():
    """Create and return an authenticated session for Bugzilla"""
    try:
        session = requests.Session()
        # Get the login page first to get the token
        login_page = session.get(f"{BUGZILLA_URL}/report.cgi")
        # Parse the login page to extract the token
        # Submit login credentials
        # Return authenticated session
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")
```

#### Bitbucket Authentication

Bitbucket authentication uses basic authentication with the provided username and app password. The BitbucketAPI class handles authentication in its constructor:

```python
class BitbucketAPI:
    def __init__(self, username: str, app_password: str, workspace: str):
        self.auth = (username, app_password)
        self.workspace = workspace
        self.api_base = "https://api.bitbucket.org/2.0"
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
```

### Data Processing

#### Bugzilla Data Extraction

The application uses BeautifulSoup to parse HTML responses from Bugzilla, as the Bugzilla instance may not provide a modern REST API. Key functions include:

- `parse_bug_table`: Extracts bug data from HTML tables
- `get_priority_bug_miss`: Identifies priority bugs that missed SLA
- `get_current_day_status`: Retrieves current day bug status by team

#### Google Chat Notifications

The GoogleChatService class formats and sends notifications to Google Chat using webhook URLs. It supports multiple notification formats:

- Bug status reports
- Priority bug miss notifications
- SLA missed bug reports
- Open PR notifications

Each notification type has a dedicated method that formats the data into Google Chat's card format.

## Extending the Application

### Adding New Endpoints

To add a new endpoint:

1. Identify the appropriate router (bugzilla.py or bitbucket.py)
2. Add a new function with the FastAPI route decorator
3. Implement the endpoint logic

Example:
```python
@router.get("/new-endpoint")
async def new_endpoint(
    param: str = Query(None, description="Parameter description"),
    webhook_url: str = Query(None, description="Optional custom Google Chat webhook URL"),
    skip_chat: bool = Query(False, description="Set to true to skip posting to Google Chat")
):
    # Implementation
    result = process_data(param)
    
    # Send notification if needed
    if not skip_chat:
        chat_service = GoogleChatService(webhook_url or GOOGLE_CHAT_WEBHOOK)
        chat_service.send_notification(result)
        
    return {"result": result, "notification_sent": not skip_chat}
```

### Adding New Services

To add a new service:

1. Create a new file in the services directory
2. Implement the service class with required methods
3. Import and use the service in the appropriate router

Example:
```python
# app/services/new_service.py
class NewService:
    def __init__(self, config_param):
        self.config_param = config_param
        
    def process_data(self, input_data):
        # Implementation
        return processed_data
```

### Error Handling Best Practices

The application uses FastAPI's HTTPException for error handling. Follow these patterns:

```python
# For client errors (4xx)
if not data:
    raise HTTPException(
        status_code=404,
        detail="No data found"
    )

# For server errors (5xx)
try:
    result = process_data()
except Exception as e:
    raise HTTPException(
        status_code=500,
        detail=f"Processing failed: {str(e)}"
    )
```

## Testing

### Manual Testing

For manual testing:

1. Start the application with `uvicorn app.main:app --reload`
2. Use the Swagger UI at `http://localhost:8000/docs` to test endpoints
3. Verify responses and notifications

### Future Automated Testing

When implementing automated tests:

1. Create a `tests` directory
2. Use pytest for writing tests
3. Mock external services (Bugzilla, Bitbucket, Google Chat)

Example test structure:
```
tests/
├── conftest.py           # Test fixtures
├── test_bugzilla.py      # Tests for Bugzilla endpoints
├── test_bitbucket.py     # Tests for Bitbucket endpoints
└── test_services/        # Tests for services
    ├── test_bitbucket.py
    └── test_google_chat.py
```

## Deployment

### Production Deployment

For production deployment:

1. Set up a production environment with proper security measures
2. Use a production ASGI server like Uvicorn with Gunicorn
3. Set up environment variables securely

Example Gunicorn deployment:
```bash
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker Deployment

A Dockerfile could be created for containerized deployment:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Check your Bugzilla and Bitbucket credentials in the .env file
   - Verify that the Bugzilla and Bitbucket instances are accessible

2. **Missing Environment Variables**
   - Ensure all required variables are set in your .env file
   - Check for typos in variable names

3. **API Rate Limiting**
   - Implement retry logic for external API calls
   - Add exponential backoff for repeated requests

4. **HTML Parsing Issues**
   - If Bugzilla's HTML structure changes, update the parsing logic
   - Add more robust error handling for HTML parsing

### Debugging Tips

1. Enable FastAPI's debug mode for detailed error information
2. Use logging to track application flow and API interactions
3. Check the application logs for error messages and stack traces

## Performance Optimization

1. **Caching**
   - Consider adding caching for frequently accessed data
   - Use Redis or a similar in-memory store for caching

2. **Asynchronous Processing**
   - Leverage FastAPI's async capabilities for I/O-bound operations
   - Use background tasks for notifications

3. **Connection Pooling**
   - Reuse HTTP connections when making multiple requests to the same service

## Security Considerations

1. **Environment Variables**
   - Never commit .env files to version control
   - Use a secure method to manage production secrets

2. **Authentication**
   - Regularly rotate API keys and passwords
   - Use app passwords or tokens instead of main account credentials

3. **Input Validation**
   - Validate all user inputs using FastAPI's type hints and validation
   - Sanitize data before using it in queries or templates

## Contributing Guidelines

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Bugzilla API Documentation](https://bugzilla.readthedocs.io/en/latest/api/)
- [Bitbucket API Documentation](https://developer.atlassian.com/cloud/bitbucket/rest/intro/)
- [Google Chat API Documentation](https://developers.google.com/chat/api/guides/message-formats)