from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import requests
from bs4 import BeautifulSoup
import pandas as pd
from pydantic import BaseModel
import numpy as np
import json
from dotenv import load_dotenv
import os
from datetime import datetime
import pytz  # Add this import at the top

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
    'GOOGLE_CHAT_KEY', 'GOOGLE_CHAT_TOKEN', 'REPORT_SAVED_ID'
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
        
        # First get the login page to get the token
        login_page = session.get(
            f"{BUGZILLA_URL}/index.cgi?GoAheadAndLogIn=1",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            }
        )
        
        # Parse the login page
        soup = BeautifulSoup(login_page.text, 'html.parser')
        login_form = soup.find('form', {'id': 'login'})
        
        # Get all hidden fields from the form
        login_data = {
            "Bugzilla_login": BUGZILLA_EMAIL,
            "Bugzilla_password": BUGZILLA_PASSWORD,
            "GoAheadAndLogIn": "Log in",
            "Bugzilla_remember": "on"
        }
        
        if login_form:
            for hidden in login_form.find_all('input', type='hidden'):
                login_data[hidden['name']] = hidden['value']
        
        # Get the token from cookie
        login_token = session.cookies.get('Bugzilla_login_request_cookie')
        if login_token:
            login_data['token'] = login_token
        
        print("Login data prepared:", {k: v for k, v in login_data.items() if k != 'Bugzilla_password'})
        
        # Perform login
        login_response = session.post(
            f"{BUGZILLA_URL}/index.cgi",
            data=login_data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Origin": BUGZILLA_URL,
                "Referer": f"{BUGZILLA_URL}/index.cgi?GoAheadAndLogIn=1"
            },
            allow_redirects=True
        )
        
        print(f"Login response status: {login_response.status_code}")
        print(f"Login cookies: {session.cookies.get_dict()}")
        
        # Verify login success
        if 'Bugzilla_login' not in session.cookies:
            print("Login failed - no login cookie found")
            print("Response content preview:", login_response.text[:500])
            raise HTTPException(
                status_code=401,
                detail="Login failed - authentication error"
            )
        
        # Make a test request to verify login
        test_response = session.get(f"{BUGZILLA_URL}/report.cgi?saved_report_id={REPORT_SAVED_ID}")
        
        if test_response.status_code != 200:
            print(f"Test request failed with status: {test_response.status_code}")
            raise HTTPException(
                status_code=401,
                detail="Failed to access report after login"
            )
        
        if "Log in to Bugzilla" in test_response.text:
            print("Still getting login page after authentication")
            raise HTTPException(
                status_code=401,
                detail="Login session not established"
            )
        
        print("Login successful!")
        return session
        
    except requests.RequestException as e:
        print(f"Network error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Network error: {str(e)}"
        )
    except Exception as e:
        print(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Login failed: {str(e)}"
        )

def post_to_google_chat(teams_data):
    # Find OS team data
    os_team = next((team for team in teams_data if team['team'].lower() == 'os'), None)
    
    if not os_team:
        print("OS team data not found")
        return
    
    # Get current date in IST with human-readable format
    ist_timezone = pytz.timezone('Asia/Kolkata')
    ist_time = datetime.now(ist_timezone)
    datetime_str = ist_time.strftime('%d %b %Y | %I:%M %p IST')
    
    # Format the message
    message = "🐞 *BUGZILLA STATUS REPORT - OS TEAM*\n"
    message += f"📅 {datetime_str}\n"
    message += "─────────────────────────\n\n"
    
    # Status counts
    message += f"• *UNCONFIRMED:* {os_team['UNCONFIRMED']}\n"
    message += f"• *CONFIRMED:* {os_team['CONFIRMED']}\n"
    message += f"• *IN_PROGRESS:* {os_team['IN_PROGRESS']}\n"
    message += f"• *IN_PROGRESS_DEV:* {os_team['IN_PROGRESS_DEV']}\n"
    message += f"• *NEEDS_INFO:* {os_team['NEEDS_INFO']}\n"
    message += f"• *UNDER_REVIEW:* {os_team['UNDER_REVIEW']}\n"
    message += f"• *RE-OPENED:* {os_team['RE-OPENED']}\n\n"
    
    # Total
    message += "📊 *TOTAL ACTIVE ISSUES: " + str(os_team['total']) + "*"
    
    # Post to Google Chat
    payload = {
        "text": message
    }
    
    response = requests.post(GOOGLE_CHAT_WEBHOOK, json=payload)
    
    if response.status_code != 200:
        print(f"Error response: {response.text}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to post to Google Chat: {response.text}"
        )

@app.get("/bugzilla/report")
async def get_bugzilla_report():
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
            "saved_report_id": REPORT_SAVED_ID
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
        
        # After processing the teams_data, post to Google Chat
        post_to_google_chat(teams_data)
        
        return {
            "status": "success",
            "report": teams_data
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing report: {str(e)}") 