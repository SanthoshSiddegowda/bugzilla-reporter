import os
from fastapi import FastAPI
from dotenv import load_dotenv
from app.routers import bugzilla, bitbucket

# Load environment variables
load_dotenv()

title = os.getenv('APP_NAME', 'Bitzilla Report API')
description = os.getenv('APP_DESC', 'API for generating reports from Bugzilla and Bitbucket')
version = os.getenv('APP_VERSION', '0.0.1')

# Initialize FastAPI app with environment variables for title, description, and version
app = FastAPI(
    title=title,
    description=description,
    version=version
)

# Validate environment variables
required_vars = [
    'BUGZILLA_EMAIL',
    'BUGZILLA_PASSWORD',
    'BUGZILLA_URL',
    'GOOGLE_CHAT_WEBHOOK',
    'BITBUCKET_USERNAME', 
    'BITBUCKET_PASSWORD', 
    'BITBUCKET_URL'
]

missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Include routers
app.include_router(bugzilla.router)
app.include_router(bitbucket.router)

@app.get("/")
async def root():
    """Root endpoint that returns API information"""
    return {
        "status": "active",
        "message": f"Hello World! I am {title}",
        "version": version
    }