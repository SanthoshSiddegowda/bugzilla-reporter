from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import requests
from bs4 import BeautifulSoup
import pandas as pd
from dotenv import load_dotenv
import os
from datetime import datetime
import pytz
from app.services.google_chat import post_qa_status_to_chat
from app.config import BUGZILLA_URL, GOOGLE_CHAT_WEBHOOK, BITBUCKET_USERNAME, BITBUCKET_PASSWORD, BITBUCKET_URL
from typing import List
from app.services.bitbucket import BitbucketAPI

# Load environment variables
load_dotenv()

app = FastAPI(title="Bugzilla Report API")

# Get credentials from environment variables
BUGZILLA_EMAIL = os.getenv('BUGZILLA_EMAIL')
BUGZILLA_PASSWORD = os.getenv('BUGZILLA_PASSWORD')
BUGZILLA_URL = os.getenv('BUGZILLA_URL')

# Construct Google Chat webhook URL from components
GOOGLE_CHAT_WEBHOOK_URL = os.getenv('GOOGLE_CHAT_WEBHOOK_URL')
GOOGLE_CHAT_SPACE_ID = os.getenv('GOOGLE_CHAT_SPACE_ID')
GOOGLE_CHAT_KEY = os.getenv('GOOGLE_CHAT_KEY')
GOOGLE_CHAT_TOKEN = os.getenv('GOOGLE_CHAT_TOKEN')

GOOGLE_CHAT_WEBHOOK = f"{GOOGLE_CHAT_WEBHOOK_URL}/{GOOGLE_CHAT_SPACE_ID}/messages?key={GOOGLE_CHAT_KEY}&token={GOOGLE_CHAT_TOKEN}"

REPORT_SAVED_ID = os.getenv('REPORT_SAVED_ID')

# Validate environment variables
required_vars = [
    'BUGZILLA_EMAIL', 'BUGZILLA_PASSWORD', 'BUGZILLA_URL',
    'GOOGLE_CHAT_WEBHOOK_URL', 'GOOGLE_CHAT_SPACE_ID',
    'GOOGLE_CHAT_KEY', 'GOOGLE_CHAT_TOKEN', 'REPORT_SAVED_ID',
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

def post_to_google_chat(teams_data, team_name: str, google_chat_webhook: str):
    team_data = next((team for team in teams_data if team['team'].lower() == team_name.lower()), None)
    
    if not team_data:
        print(f"{team_name} team data not found")
        return
    
    # Get current date in IST
    ist_timezone = pytz.timezone('Asia/Kolkata')
    ist_time = datetime.now(ist_timezone)
    datetime_str = ist_time.strftime('%d %b %Y | %I:%M %p IST')
    
    # Construct Bugzilla report URL
    report_url = (
        f"{BUGZILLA_URL}/report.cgi?"
        f"bug_severity=blocker&bug_severity=critical&bug_severity=major&"
        f"bug_severity=normal&bug_severity=minor&bug_severity=trivial&"
        f"bug_status=UNCONFIRMED&bug_status=CONFIRMED&bug_status=NEEDS_INFO&"
        f"bug_status=IN_PROGRESS&bug_status=IN_PROGRESS_DEV&bug_status=UNDER_REVIEW&"
        f"bug_status=RE-OPENED&"
        f"product=BizomWeb&product=Mobile%20App&"
        f"x_axis_field=version&y_axis_field=bug_status&"
        f"format=table&action=wrap&"
        f"saved_report_id={REPORT_SAVED_ID}"
    )
    
    # Format the message with dynamic team name and link
    message = f"🐞 *BUGZILLA STATUS REPORT - {team_name.upper()} TEAM*\n"
    message += f"📅 {datetime_str}\n"
    message += "─────────────────────────\n\n"
    
    # Status counts
    message += f"• *UNCONFIRMED:* {team_data['UNCONFIRMED']}\n"
    message += f"• *CONFIRMED:* {team_data['CONFIRMED']}\n"
    message += f"• *IN_PROGRESS:* {team_data['IN_PROGRESS']}\n"
    message += f"• *IN_PROGRESS_DEV:* {team_data['IN_PROGRESS_DEV']}\n"
    message += f"• *NEEDS_INFO:* {team_data['NEEDS_INFO']}\n"
    message += f"• *UNDER_REVIEW:* {team_data['UNDER_REVIEW']}\n"
    message += f"• *RE-OPENED:* {team_data['RE-OPENED']}\n\n"
    
    # Total and link
    message += f"📊 *TOTAL ACTIVE ISSUES: {team_data['total']}*\n\n"
    message += f"🔗 <{report_url}|View Full Report>"
    
    # Post to Google Chat
    payload = {
        "text": message
    }
    
    response = requests.post(google_chat_webhook, json=payload)
    
    if response.status_code != 200:
        print(f"Error response: {response.text}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to post to Google Chat: {response.text}"
        )

@app.get("/")
async def root():
    """Root endpoint that returns API information"""
    return {
        "status": "active",
        "message": "Hello World! I am Bugzilla Report API"
    }

@app.get("/current-day-status")
async def get_bugzilla_report(notify_team: str = "os", google_chat_webhook: str = GOOGLE_CHAT_WEBHOOK):  # Default to "os" if no team specified
    try:
        # Create session and login
        session = get_session_with_login()
        
        # Parameters for the report
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
            "save_report_id": REPORT_SAVED_ID
        }
        
        # Get the report page
        response = session.get(REPORT_URL, params=params)
        
        # Debug information
        print(f"Response status code: {response.status_code}")
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, 
                              detail="Failed to fetch report")
        
        # Parse the HTML table
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the table that contains the bug status data
        # Look for table with specific structure - contains bug statuses
        tables = soup.find_all('table')
        target_table = None
        
        for table in tables:
            # Check if this table contains the expected bug statuses
            if table.find(text=lambda t: t and 'UNCONFIRMED' in t) and \
               table.find(text=lambda t: t and 'CONFIRMED' in t):
                target_table = table
                break
        
        if not target_table:
            # Print all tables for debugging
            print("Available tables:", len(tables))
            for i, t in enumerate(tables):
                print(f"Table {i} content:", t.get_text()[:100])
            return JSONResponse(
                status_code=404,
                content={"message": "Bug status table not found. You may need to log in again."}
            )
        
        # Convert the table to a pandas DataFrame
        df = pd.read_html(str(target_table))[0]
        
        # Print DataFrame info for debugging
        print("DataFrame columns:", df.columns)
        print("DataFrame head:", df.head())
        
        # Clean up the data
        # Replace '.' with 0 and clean column names
        df = df.replace('.', 0)
        df.columns = df.columns.str.strip()
        
        # The first column is usually unnamed or empty, rename it to 'Status'
        df = df.rename(columns={df.columns[0]: 'Status'})
        
        # Remove any empty columns (if any)
        df = df.dropna(axis=1, how='all')
        
        # Convert numeric columns to integers
        numeric_columns = [col for col in df.columns if col != 'Status']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
        # Transform data into team-based grouping
        teams_data = []
        
        # Get all columns except 'Status' and 'Total'
        version_columns = [col for col in df.columns if col not in ['Status', 'Total']]
        
        # Print data for debugging
        print("DataFrame content:")
        print(df)
        
        for team in version_columns:
            try:
                # Get the row for each status
                unconfirmed_val = df.loc[df['Status'].str.strip() == 'UNCONFIRMED', team].iloc[0]
                confirmed_val = df.loc[df['Status'].str.strip() == 'CONFIRMED', team].iloc[0]
                in_progress_val = df.loc[df['Status'].str.strip() == 'IN_PROGRESS', team].iloc[0]
                in_progress_dev_val = df.loc[df['Status'].str.strip() == 'IN_PROGRESS_DEV', team].iloc[0]
                needs_info_val = df.loc[df['Status'].str.strip() == 'NEEDS_INFO', team].iloc[0]
                under_review_val = df.loc[df['Status'].str.strip() == 'UNDER_REVIEW', team].iloc[0]
                reopened_val = df.loc[df['Status'].str.strip() == 'RE-OPENED', team].iloc[0]
                
                # Calculate total excluding the 'Total' row
                total = df.loc[df['Status'].str.strip() != 'Total', team].sum()
                
                team_data = {
                    "team": team.lower(),
                    "UNCONFIRMED": int(unconfirmed_val),
                    "CONFIRMED": int(confirmed_val),
                    "IN_PROGRESS": int(in_progress_val),
                    "IN_PROGRESS_DEV": int(in_progress_dev_val),
                    "NEEDS_INFO": int(needs_info_val),
                    "UNDER_REVIEW": int(under_review_val),
                    "RE-OPENED": int(reopened_val),
                    "total": int(total)
                }
                teams_data.append(team_data)
                
                # Debug print
                print(f"\nProcessed team {team}:")
                print(f"UNCONFIRMED: {unconfirmed_val}")
                print(f"CONFIRMED: {confirmed_val}")
                print(f"IN_PROGRESS: {in_progress_val}")
                print(f"IN_PROGRESS_DEV: {in_progress_dev_val}")
                print(f"NEEDS_INFO: {needs_info_val}")
                print(f"UNDER_REVIEW: {under_review_val}")
                print(f"RE-OPENED: {reopened_val}")
                print(f"Total: {total}")
                
            except Exception as e:
                print(f"Error processing team {team}: {str(e)}")
                continue
        
        print("notify_team", notify_team)
        # After processing the teams_data, post to Google Chat
        post_to_google_chat(teams_data, notify_team, google_chat_webhook)
        
        return {
            "status": "success",
            "message": "Report posted to Google Chat"
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing report: {str(e)}")

@app.get("/qa-status")
async def get_qa_status(
    google_chat_webhook: str = GOOGLE_CHAT_WEBHOOK,
    from_date: str = None,
    products: str = "BizomWeb,Mobile App"
):
    """Get QA status report and post to Google Chat"""
    try:
        session = get_session_with_login()
        
        params = {
            "x_axis_field": "bug_status",
            "y_axis_field": "qa_contact",
            "z_axis_field": "",
            "no_redirect": "1",
            "query_format": "report-table",
            "product": products.split(","),
            "bug_status": [
                "UNCONFIRMED", "CONFIRMED", "NEEDS_INFO",
                "IN_PROGRESS", "IN_PROGRESS_DEV", "RESOLVED",
                "VERIFIED", "UNDER_REVIEW", "RE-OPENED",
                "REVIEWED"
            ],
            "resolution": [
                "CLOSED_DATA_CORRECTION", "CLOSED_INFORMATION",
                "CLOSED_LOG", "RELEASED", "---", "FIXED",
                "INVALID", "WONTFIX", "DUPLICATE",
                "WORKSFORME", "MIGRATED", "CLOSED"
            ],
            "chfield": "qa_contact",
            "chfieldto": "Now",
            "format": "table",
            "action": "wrap"
        }
        
        if from_date:
            params["chfieldfrom"] = from_date
        else:
            params["chfieldfrom"] = "2025-02-19"
        
        response = session.get(f"{BUGZILLA_URL}/report.cgi", params=params)
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch QA report")
        
        qa_data = parse_qa_data(response.text)
        
        # Post to Google Chat
        post_qa_status_to_chat(qa_data, google_chat_webhook)
        
        return {
            "status": "success",
            "message": "QA status report posted to Google Chat",
            "data": qa_data
        }
        
    except Exception as e:
        print(f"Error details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing QA report: {str(e)}")

def parse_qa_data(html_content: str) -> list:
    """Parse QA data from HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the main container table
    container = soup.find('table', class_='tabular_report_container')
    if not container:
        raise HTTPException(status_code=404, detail="No report container found")
    
    # Get all rows from the table
    rows = container.find_all('tr')
    if not rows:
        raise HTTPException(status_code=404, detail="No data rows found")
        
    # Define status columns in order (excluding Total)
    status_columns = [
        "UNCONFIRMED",
        "CONFIRMED",
        "NEEDS_INFO",
        "IN_PROGRESS_DEV",
        "RESOLVED"
    ]
    
    # Process data rows
    qa_data = []
    
    # Process each row
    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 2:  # Need at least QA contact and one status
            continue
            
        qa_contact = cells[0].get_text(strip=True)
        if not qa_contact or '@mobisy.com' not in qa_contact:
            continue
            
        row_data = {
            "qa_contact": qa_contact,
            "statuses": {},
            "total": 0
        }
        
        # Process status cells in order (excluding Total)
        for idx, status in enumerate(status_columns, 1):  # Start from 1 to skip QA contact
            if idx < len(cells):
                value = cells[idx].get_text(strip=True)
                try:
                    count = int(value) if value and value != '.' else 0
                    if count > 0:  # Only include non-zero counts
                        row_data["statuses"][status] = count
                except ValueError:
                    continue
        
        # Get total from the last cell
        if len(cells) > len(status_columns) + 1:  # +1 for QA contact column
            total_value = cells[len(status_columns) + 1].get_text(strip=True)
            try:
                row_data["total"] = int(total_value) if total_value and total_value != '.' else 0
            except ValueError:
                row_data["total"] = sum(row_data["statuses"].values())
        
        if row_data["total"] > 0:  # Only include rows with data
            qa_data.append(row_data)
    
    # Add total row
    if qa_data:
        total_data = {
            "qa_contact": "Total",
            "statuses": {},
            "total": 0
        }
        
        # Calculate totals for each status
        for qa in qa_data:
            for status, count in qa["statuses"].items():
                total_data["statuses"][status] = total_data["statuses"].get(status, 0) + count
            total_data["total"] += qa["total"]  # Use the actual total from each QA
        
        qa_data.append(total_data)
    
    if not qa_data:
        raise HTTPException(status_code=404, detail="No QA data found in table")
    
    return qa_data 

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