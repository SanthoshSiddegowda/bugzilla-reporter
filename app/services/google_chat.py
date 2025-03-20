from datetime import datetime
import pytz
import requests
from fastapi import HTTPException
from typing import Dict, List
import os

class GoogleChatService:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def format_bugzilla_message(self, team_data: dict, team_name: str) -> str:
        """Format bug status data into a Google Chat message"""
        # Get current date in IST
        ist_timezone = pytz.timezone('Asia/Kolkata')
        ist_time = datetime.now(ist_timezone)
        datetime_str = ist_time.strftime('%d %b %Y | %I:%M %p IST')
        
        bugzilla_url = os.getenv('BUGZILLA_URL')
                               
        # Construct Bugzilla report URL
        report_url = (
            f"{bugzilla_url}/report.cgi?"
            f"bug_severity=blocker&bug_severity=critical&bug_severity=major&"
            f"bug_severity=normal&bug_severity=minor&bug_severity=trivial&"
            f"bug_status=UNCONFIRMED&bug_status=CONFIRMED&bug_status=NEEDS_INFO&"
            f"bug_status=IN_PROGRESS&bug_status=IN_PROGRESS_DEV&bug_status=UNDER_REVIEW&"
            f"bug_status=RE-OPENED&"
            f"product=BizomWeb&product=Mobile%20App&"
            f"x_axis_field=version&y_axis_field=bug_status&"
            f"format=table&action=wrap"
        )
        
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
        
        # Calculate total
        total = sum(team_data.values())
        message += f"📊 *TOTAL ACTIVE ISSUES: {total}*\n\n"
        message += f"🔗 <{report_url}|View Full Report>"
        
        return message

    def format_prs_for_chat(self, prs: List[Dict]) -> str:
        """Format PRs data for Google Chat message"""
        if not prs:
            return "No open pull requests found."
        
        # Get current date in IST
        ist_timezone = pytz.timezone('Asia/Kolkata')
        ist_time = datetime.now(ist_timezone)
        datetime_str = ist_time.strftime('%d %b %Y | %I:%M %p IST')
        
        # Group PRs by author
        prs_by_author = {}
        for pr in prs:
            author = pr['author']
            if author not in prs_by_author:
                prs_by_author[author] = []
            prs_by_author[author].append(pr)
        
        # Sort authors by PR count (descending)
        sorted_authors = sorted(
            prs_by_author.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        # Start with summary section
        message = f"🔄 *OPEN PULL REQUESTS*\n"
        message += f"📅 {datetime_str}\n"
        message += "─────────────────────────\n\n"
        
        # Add summary section
        message += "📊 *SUMMARY*\n"
        for author, author_prs in sorted_authors:
            message += f"• {author}: {len(author_prs)} PRs\n"
        
        # Add total count
        total_prs = sum(len(prs) for prs in prs_by_author.values())
        message += f"• *Total: {total_prs} PRs*\n"
        message += "\n─────────────────────────\n\n"
        
        # Add detailed PR section
        message += "📝 *DETAILS*\n\n"
        for author, author_prs in sorted_authors:
            message += f"👤 *{author}* ({len(author_prs)} PRs)\n\n"
            
            for pr in author_prs:
                message += f"• *<{pr['url']}|{pr['title']}>*\n"
                message += f"  ├ Source: `{pr['source_branch']}`\n"
                message += f"  ├ Target: `{pr['destination_branch']}`\n"
                message += f"  └ Created: {pr['created_on']}\n\n"
        
        return message

    def send_message(self, message: str) -> bool:
        """Send a message to Google Chat"""
        try:
            payload = {"text": message}
            response = requests.post(self.webhook_url, json=payload)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to post to Google Chat: {response.text}"
                )
            
            return True
            
        except Exception as e:
            print(f"Error sending message: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send message: {str(e)}"
            )

    def send_team_notification(self, teams_data: dict, team_name: str) -> bool:
        """Send notification to Google Chat for a specific team"""
        try:
            team_data = teams_data.get(team_name.upper())
            if not team_data:
                raise ValueError(f"Team '{team_name}' not found in the report")
            
            message = self.format_bugzilla_message(team_data, team_name)
            return self.send_message(message)
            
        except Exception as e:
            print(f"Error sending notification: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send notification: {str(e)}"
            ) 