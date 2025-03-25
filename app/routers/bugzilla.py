from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
import requests
from bs4 import BeautifulSoup
import os
from typing import List, Dict, Any, Tuple, Optional
from app.services.google_chat import GoogleChatService
from app.services.bitbucket import BitbucketAPI
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

router = APIRouter(prefix="/bugzilla", tags=["bugzilla"])

# Get environment variables with validation
BUGZILLA_EMAIL = os.getenv('BUGZILLA_EMAIL')
BUGZILLA_PASSWORD = os.getenv('BUGZILLA_PASSWORD')
BUGZILLA_URL = os.getenv('BUGZILLA_URL')
GOOGLE_CHAT_WEBHOOK = os.getenv('GOOGLE_CHAT_WEBHOOK')

# Validate critical environment variables
if not BUGZILLA_URL:
    print("WARNING: BUGZILLA_URL environment variable is not set!")
    BUGZILLA_URL = "https://bugzilla.bizom.in"  # Fallback default
    print(f"Using default BUGZILLA_URL: {BUGZILLA_URL}")

REPORT_URL = f"{BUGZILLA_URL}/report.cgi"


def get_session_with_login():
    """
    Create and return an authenticated session for Bugzilla
    
    Returns:
        requests.Session: Authenticated session
        
    Raises:
        HTTPException: If login fails
    """
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

def process_csv_response(response: requests.Response) -> List[Dict[str, Any]]:
    """
    Process CSV response from Bugzilla into a list of dictionaries
    
    Args:
        response: HTTP response containing CSV data
        
    Returns:
        List of dictionaries representing bugs
    """
    # Process CSV data
    csv_data = [[cell.strip().strip('"') for cell in row.split(',')] 
               for row in response.text.strip().split('\n')]
    
    if not csv_data or len(csv_data) <= 1:  # Only headers or empty
        return []
        
    headers = csv_data[0]
    bugs = []
    
    # Convert rows to dictionaries
    for row in csv_data[1:]:
        if len(row) == len(headers):
            bug_dict = {headers[i]: row[i] for i in range(len(headers))}
            bugs.append(bug_dict)
    
    return bugs

def get_chat_service(webhook_url: Optional[str] = None) -> Tuple[GoogleChatService, str]:
    """
    Get Google Chat service with appropriate webhook URL
    
    Args:
        webhook_url: Optional custom webhook URL
        
    Returns:
        Tuple of (GoogleChatService, webhook_type)
        
    Raises:
        HTTPException: If no webhook URL is available
    """
    chat_url = webhook_url or GOOGLE_CHAT_WEBHOOK
    if not chat_url:
        raise HTTPException(
            status_code=400,
            detail="Google Chat webhook URL not configured"
        )
    
    webhook_type = "custom" if webhook_url else "default"
    return GoogleChatService(chat_url, BUGZILLA_URL), webhook_type

def format_response(
    result: Dict[str, Any], 
    chat_posted: bool, 
    webhook_type: str
) -> Dict[str, Any]:
    """
    Format standard API response
    
    Args:
        result: Result data
        chat_posted: Whether notification was posted to chat
        webhook_type: Type of webhook used
        
    Returns:
        Formatted response dictionary
    """
    return {
        "status": "success",
        "data": result,
        "posted_to_chat": chat_posted,
        "webhook_used": webhook_type if chat_posted else "none"
    }

@router.get("/get-priority-bug-miss")
async def get_priority_bug_report(
    notify_team: str = "OS", 
    google_chat_webhook: str = None,
    skip_chat: bool = False
)-> dict:
    """
    Get Priority miss report for a specific team and optionally notify via Google Chat.

    Args:
        notify_team (str): Team to notify (default: "OS")
        google_chat_webhook (str, optional): Custom webhook URL for Google Chat notifications
        skip_chat (bool): Flag to skip sending notification to Google Chat (default: False)

    Returns:
        dict: Dictionary containing:
            - status (str): Operation status
            - data (dict): SLA miss report details including team, bugs list, and count
            - posted_to_chat (bool): Whether notification was sent to Google Chat
            - webhook_used (str): Type of webhook used ('custom', 'default', or 'none')

    Raises:
        HTTPException: If there are errors during API requests or processing
    """
    try:
        session = get_session_with_login()

        params = {
            "bug_severity": ["blocker", "critical"],
            "bug_status": ["UNCONFIRMED", "CONFIRMED", "NEEDS_INFO", "IN_PROGRESS", "IN_PROGRESS_DEV", "UNDER_REVIEW", "RE-OPENED"],
            "chfield": "[Bug creation]",
            "chfieldto": "-1D",
            "priority": ["Highest", "High", "Normal", "Low", "Lowest", "---"],
            "product": ["BizomWeb", "ELL", "Mobile App", "OneView DIY"],
            "version": notify_team,
            "action": "wrap",
            "ctype": "csv"
        }
        
        response = session.get(f"{BUGZILLA_URL}/buglist.cgi", params=params)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch report: {response.text}"
            )
            
        bugs = process_csv_response(response)
        
        if not bugs:
            return {
                "status": "success",
                "data": "No SLA miss bugs found",
                "posted_to_chat": False,
                "webhook_used": "none"
            }
                
        # Format the data for return
        result = {
            "team": notify_team,
            "bugs": bugs,
            "count": len(bugs)
        }
        
        # Post to Google Chat if needed
        chat_posted = False
        webhook_type = "none"
        if not skip_chat and bugs:
            chat_service, webhook_type = get_chat_service(google_chat_webhook)
            chat_service.send_priority_bug_notification(result, notify_team)
            chat_posted = True
            
        return format_response(result, chat_posted, webhook_type)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

@router.get("/current-day-status")
async def get_current_day_bug_count(
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
        webhook_type = "none"
        if not skip_chat:
            chat_service, webhook_type = get_chat_service(google_chat_webhook)
            
            # Get the correct case version of the team name
            team_key = notify_team.lower()
            if team_key not in team_mapping:
                raise HTTPException(
                    status_code=400,
                    detail=f"Team '{notify_team}' not found in the report. Available teams: {', '.join(teams)}"
                )
            
            chat_service.send_current_day_bug_notification(result, team_mapping[team_key])
            chat_posted = True
        
        return format_response(result, chat_posted, webhook_type)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


@router.get("/get-sla-missed-bugs")
async def get_sla_missed_bugs_report(
    notify_team: str = "OS", 
    google_chat_webhook: str = None,
    days: int = 3,
    skip_chat: bool = False
)-> dict:
    """
    Get SLA missed bugs report (last 3 days) for a specific team and optionally notify via Google Chat.

    Args:
        notify_team (str): Team to notify (default: "OS")
        google_chat_webhook (str, optional): Custom webhook URL for Google Chat notifications
        days (int): Number of days to look back (default: 3)
        skip_chat (bool): Flag to skip sending notification to Google Chat (default: False)

    Returns:
        dict: Dictionary containing:
            - status (str): Operation status
            - data (dict): Recent bugs report details including team, bugs list, and count
            - posted_to_chat (bool): Whether notification was sent to Google Chat
            - webhook_used (str): Type of webhook used ('custom', 'default', or 'none')

    Raises:
        HTTPException: If there are errors during API requests or processing
    """
    try:
        session = get_session_with_login()

        params = {
            "bug_severity": ["blocker", "critical", "major", "normal", "minor", "trivial"],
            "bug_status": ["UNCONFIRMED", "CONFIRMED", "NEEDS_INFO", "IN_PROGRESS", "IN_PROGRESS_DEV", "UNDER_REVIEW", "RE-OPENED"],
            "chfield": "[Bug creation]",
            "chfieldto": f"-{days}d" if days else "-3d",  # Default 3 days if not specified
            "component": ["API", "Aqua", "Backend", "Bourbon", "Cross Platform", "Custom Feature", 
                         "Distiman", "MDM (Changes)", "MDM (New)", "RetailerApp", 
                         "Templates (Changes)", "Templates (New)", "UI", "Windows Phone"],
            "priority": ["Highest", "High", "Normal", "Low", "Lowest", "---"],
            "product": ["BizomWeb", "Mobile App"],
            "version": notify_team,
            "action": "wrap",
            "ctype": "csv"
        }
        
        response = session.get(f"{BUGZILLA_URL}/buglist.cgi", params=params)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch report: {response.text}"
            )
            
        bugs = process_csv_response(response)
        
        if not bugs:
            return {
                "status": "success",
                "data": "No SLA Miss bugs found",
                "posted_to_chat": False,
                "webhook_used": "none"
            }
                
        # Format the data for return
        result = {
            "team": notify_team,
            "bugs": bugs,
            "count": len(bugs)
        }
        
        # Post to Google Chat if needed
        chat_posted = False
        webhook_type = "none"
        if not skip_chat and bugs:
            chat_service, webhook_type = get_chat_service(google_chat_webhook)
            chat_service.send_sla_missed_bugs_notification(result, notify_team)
            chat_posted = True
            
        return format_response(result, chat_posted, webhook_type)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )