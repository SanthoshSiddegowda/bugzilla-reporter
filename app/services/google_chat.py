from datetime import datetime
import pytz
import requests
from fastapi import HTTPException

def post_qa_status_to_chat(qa_data: list, webhook_url: str) -> None:
    """Post QA status report to Google Chat"""
    try:
        if not qa_data:
            raise ValueError("No QA data to post")

        # Get current date in IST
        ist_time = datetime.now(pytz.timezone('Asia/Kolkata'))
        datetime_str = ist_time.strftime('%d %b %Y | %I:%M %p IST')
        
        # Format message
        message = f"🔍 *QA STATUS REPORT*\n"
        message += f"📅 {datetime_str}\n"
        message += "─────────────────────────\n\n"
        
        # Status order for consistent display
        status_order = [
            "UNCONFIRMED",
            "CONFIRMED",
            "NEEDS_INFO",
            "IN_PROGRESS_DEV",
            "RESOLVED"
        ]
        
        # Add QA-wise status (excluding Total)
        for qa in qa_data:
            if qa['qa_contact'] == 'Total':
                continue
                
            message += f"*{qa['qa_contact']}*\n"
            # Display statuses in order
            for status in status_order:
                if status in qa['statuses'] and qa['statuses'][status] > 0:
                    message += f"• {status}: {qa['statuses'][status]}\n"
            message += f"📊 Total: {qa['total']}\n\n"
        
        # Add total section
        total = next((qa for qa in qa_data if qa['qa_contact'] == 'Total'), None)
        if total:
            message += "*OVERALL TOTALS*\n"
            # Display total statuses in order
            for status in status_order:
                if status in total['statuses'] and total['statuses'][status] > 0:
                    message += f"• {status}: {total['statuses'][status]}\n"
            message += f"📊 *TOTAL BUGS: {total['total']}*\n\n"
        
        # Post to Google Chat
        response = requests.post(webhook_url, json={"text": message})
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to post to Google Chat: {response.text}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error posting to Google Chat: {str(e)}"
        ) 