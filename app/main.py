from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import requests
import pandas as pd
from dotenv import load_dotenv
import os
from typing import List
from bs4 import BeautifulSoup
from app.services.bitbucket import BitbucketAPI
from app.services.google_chat import GoogleChatService

# Load environment variables
load_dotenv()

app = FastAPI(title="Bugzilla Report API")

# Get credentials from environment variables
BUGZILLA_EMAIL = os.getenv('BUGZILLA_EMAIL')
BUGZILLA_PASSWORD = os.getenv('BUGZILLA_PASSWORD')
BUGZILLA_URL = os.getenv('BUGZILLA_URL')
BITBUCKET_USERNAME = os.getenv('BITBUCKET_USERNAME')
BITBUCKET_PASSWORD = os.getenv('BITBUCKET_PASSWORD')
BITBUCKET_URL = os.getenv('BITBUCKET_URL')

GOOGLE_CHAT_WEBHOOK = os.getenv('GOOGLE_CHAT_WEBHOOK')

# Validate environment variables
required_vars = [
    'BUGZILLA_EMAIL', 'BUGZILLA_PASSWORD', 'BUGZILLA_URL',
    'GOOGLE_CHAT_WEBHOOK',
    'BITBUCKET_USERNAME', 'BITBUCKET_PASSWORD', 'BITBUCKET_URL'
]

missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Remove hardcoded URL
REPORT_URL = f"{BUGZILLA_URL}/report.cgi"

def get_session_with_login():
    try:
        session = requests.Session()
        print(f"Attempting login to: {BUGZILLA_URL}")
        
        # Get the login page first to get the token
        login_page = session.get(
            f"{BUGZILLA_URL}/report.cgi",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "text/html,application/xhtml+xml"
            }
        )
        
        # Parse the login page
        soup = BeautifulSoup(login_page.text, 'html.parser')
        
        # Get both login token and forgot password token
        login_token = soup.find('input', {'name': 'Bugzilla_login_token'})
        token = soup.find('input', {'id': 'token'})
        
        if not login_token or not token:
            raise HTTPException(
                status_code=500,
                detail="Could not find required tokens"
            )
        
        # Prepare login data with all required tokens
        login_data = {
            "Bugzilla_login": BUGZILLA_EMAIL.strip(),
            "Bugzilla_password": BUGZILLA_PASSWORD.strip(),
            "Bugzilla_login_token": login_token['value'],
            "token": token['value'],
            "GoAheadAndLogIn": "Log in",
            "Bugzilla_remember": "on",
            "Bugzilla_restrictlogin": "off"
        }
        
        # Submit login form with proper headers
        login_response = session.post(
            f"{BUGZILLA_URL}/report.cgi",
            data=login_data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Mozilla/5.0",
                "Accept": "text/html,application/xhtml+xml",
                "Origin": BUGZILLA_URL,
                "Referer": f"{BUGZILLA_URL}/report.cgi"
            },
            allow_redirects=True
        )
        
        print(f"Login response status: {login_response.status_code}")
        print(f"Cookies received: {session.cookies.get_dict()}")
        
        # Verify login success
        if "The username or password you entered is not valid" in login_response.text:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )
            
        if "Bugzilla_login" not in session.cookies:
            raise HTTPException(
                status_code=401,
                detail="Login failed - no session cookie received"
            )
        
        return session
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Login failed: {str(e)}"
        )

@app.get("/")
async def root():
    """Root endpoint that returns API information"""
    return {
        "status": "active",
        "message": "Hello World! I am Bizom Report API"
    }

@app.get("/current-day-status")
async def getCurrentDayStatus(
    notify_team: str = "OS", 
    google_chat_webhook: str = None,
    skip_chat: bool = False
) -> dict:
    """
    Get current day's bug status for all teams and optionally notify via Google Chat.
    
    Args:
        notify_team: Team to notify (default: "OS")
        google_chat_webhook: Optional custom webhook URL for Google Chat notifications
        skip_chat: Whether to skip sending notification to Google Chat
        
    Returns:
        dict: Status counts for each team and notification status
    """
    try:
        session = get_session_with_login()
        
        params = {
            "bug_severity": ["blocker", "critical", "major", "normal", "minor", "trivial"],
            "bug_status": ["UNCONFIRMED", "CONFIRMED", "NEEDS_INFO", "IN_PROGRESS", 
                          "IN_PROGRESS_DEV", "UNDER_REVIEW", "RE-OPENED"],
            "chfield": "[Bug creation]",
            "chfieldto": "Now",
            "priority": ["Highest", "High", "Normal", "Low", "Lowest", "---"],
            "product": ["BizomWeb", "Mobile App"],
            "x_axis_field": "version",
            "y_axis_field": "bug_status",
            "format": "table",
            "action": "wrap",
            "ctype": "csv"
        }

        response = session.get(REPORT_URL, params=params)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch report: {response.text}"
            )
        
        # Process CSV data
        csv_data = [[cell.strip().strip('"') for cell in row.split(',')] 
                   for row in response.text.strip().split('\n')]
        
        headers = csv_data[0]
        teams = headers[1:]
        
        # Create case-insensitive team mapping
        team_mapping = {team.lower(): team for team in teams}
        
        result = {
            team: {
                row[0]: int(row[team_index])
                for row in csv_data[1:]
            }
            for team_index, team in enumerate(teams, 1)
        }
        
        chat_posted = False
        if not skip_chat:
            chat_url = google_chat_webhook or GOOGLE_CHAT_WEBHOOK
            if not chat_url:
                raise HTTPException(
                    status_code=400,
                    detail="Google Chat webhook URL not configured"
                )
            
            # Get the correct case version of the team name
            team_key = notify_team.lower()
            if team_key not in team_mapping:
                raise HTTPException(
                    status_code=400,
                    detail=f"Team '{notify_team}' not found in the report. Available teams: {', '.join(teams)}"
                )
            
            chat_service = GoogleChatService(chat_url)
            chat_service.send_team_notification(result, team_mapping[team_key])
            chat_posted = True
        
        return {
            "status": "success",
            "data": result,
            "posted_to_chat": chat_posted,
            "webhook_used": "custom" if google_chat_webhook else "default" if chat_posted else "none"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

@app.get("/open-prs")
async def get_all_prs(
    authors: str = Query(
        None, 
        description="Filter PRs by authors (comma-separated, e.g., 'laxmikanthtd,sumithhegde')"
    ),
    webhook_url: str = Query(
        None,
        description="Optional custom Google Chat webhook URL. If not provided, default webhook will be used."
    ),
    skip_chat: bool = Query(
        False,
        description="Set to true to skip posting to Google Chat"
    )
):
    """Get all open PRs across repositories"""
    try:
        if not BITBUCKET_USERNAME or not BITBUCKET_PASSWORD:
            raise HTTPException(
                status_code=500,
                detail="Bitbucket credentials not configured"
            )
            
        # Initialize Bitbucket API client
        bitbucket = BitbucketAPI(
            username=BITBUCKET_USERNAME,
            app_password=BITBUCKET_PASSWORD,
            workspace="bizom"
        )
        
        # Get all open PRs with optional author filter
        prs = bitbucket.get_all_open_prs(authors)
        
        # Post to Google Chat by default unless skip_chat is True
        chat_posted = False
        if not skip_chat:
            message = bitbucket.format_prs_for_chat(prs)
            payload = {"text": message}
            
            # Use provided webhook URL or fall back to default
            chat_url = webhook_url or GOOGLE_CHAT_WEBHOOK
            
            response = requests.post(chat_url, json=payload)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to post to Google Chat: {response.text}"
                )
            chat_posted = True
        
        return {
            "status": "success",
            "data": prs,
            "posted_to_chat": chat_posted,
            "webhook_used": "custom" if webhook_url else "default" if chat_posted else "none"
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        ) 