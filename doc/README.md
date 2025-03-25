# Bitzilla Developer Guide

## Project Overview

Bitzilla is a FastAPI-based application that integrates with Bugzilla and Bitbucket to provide automated reporting and notifications for engineering teams. This developer guide will help you understand the project structure, setup process, and how to extend the application.

## Project Structure

```
bugzilla/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── routers/
│   │   ├── bugzilla.py      # Bugzilla API endpoints
│   │   └── bitbucket.py     # Bitbucket API endpoints
│   └── services/
│       ├── bitbucket.py     # Bitbucket API service
│       └── google_chat.py   # Google Chat service
├── doc/
│   └── README.md            # This developer guide
├── requirements.txt         # Python dependencies
└── README.md               # Project overview
```

## Setup and Installation

### Prerequisites

- Python 3.8 or higher
- Access to Bugzilla and Bitbucket instances
- Google Chat webhook URL for notifications

### Environment Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file based on `.env.example` with your credentials

## Core Components

### FastAPI Application (main.py)

The main application initializes FastAPI, loads environment variables, and includes the routers for Bugzilla and Bitbucket endpoints.

### Routers

#### Bugzilla Router (routers/bugzilla.py)

Handles endpoints related to Bugzilla:
- `/bugzilla/get-priority-bug-miss`: Retrieves priority bug misses
- `/bugzilla/current-day-status`: Gets current day bug status
- `/bugzilla/get-sla-missed-bugs`: Retrieves SLA missed bugs

#### Bitbucket Router (routers/bitbucket.py)

Handles endpoints related to Bitbucket:
- `/bitbucket/open-prs`: Retrieves open pull requests

### Services

#### Bitbucket Service (services/bitbucket.py)

Provides methods to interact with the Bitbucket API:
- Authentication with Bitbucket
- Retrieving repositories
- Fetching open pull requests

#### Google Chat Service (services/google_chat.py)

Handles formatting and sending notifications to Google Chat:
- Formatting bug reports
- Sending notifications with different layouts
- Handling webhook URLs

## Authentication

### Bugzilla Authentication

The application uses session-based authentication with Bugzilla, handling login tokens and cookies automatically through the `get_session_with_login()` function in the Bugzilla router.

### Bitbucket Authentication

Bitbucket authentication uses basic authentication with the provided username and app password.

## Extending the Application

### Adding New Endpoints

To add a new endpoint:
1. Identify the appropriate router (bugzilla.py or bitbucket.py)
2. Add a new function with the FastAPI route decorator
3. Implement the endpoint logic

Example:
```python
@router.get("/new-endpoint")
async def new_endpoint(param: str = Query(None)):
    # Implementation
    return {"result": "data"}
```

### Adding New Services

To add a new service:
1. Create a new file in the services directory
2. Implement the service class with required methods
3. Import and use the service in the appropriate router

## Error Handling

The application uses FastAPI's HTTPException for error handling. Common patterns include:

```python
if not data:
    raise HTTPException(
        status_code=404,
        detail="No data found"
    )
```

## Testing

Currently, the project does not have automated tests. When implementing tests:

1. Create a `tests` directory
2. Use pytest for writing tests
3. Mock external services (Bugzilla, Bitbucket, Google Chat)

## Deployment

The application can be deployed using various methods:

1. **Docker**: Create a Dockerfile and deploy as a container
2. **Serverless**: Deploy as a serverless function (AWS Lambda, Google Cloud Functions)
3. **Traditional hosting**: Deploy on a server with a WSGI server like Gunicorn

Example Gunicorn deployment:
```
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Troubleshooting

### Common Issues

1. **Authentication Failures**: Check your Bugzilla and Bitbucket credentials in the .env file
2. **Missing Environment Variables**: Ensure all required variables are set
3. **API Rate Limiting**: Implement retry logic for external API calls

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Bugzilla API Documentation](https://bugzilla.readthedocs.io/en/latest/api/)
- [Bitbucket API Documentation](https://developer.atlassian.com/cloud/bitbucket/rest/intro/)