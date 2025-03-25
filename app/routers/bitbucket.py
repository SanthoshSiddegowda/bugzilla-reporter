from fastapi import APIRouter, HTTPException, Query
import os
from app.services.bitbucket import BitbucketAPI
from app.services.google_chat import GoogleChatService

router = APIRouter(prefix="/bitbucket", tags=["bitbucket"])

# Get environment variables
BITBUCKET_USERNAME = os.getenv('BITBUCKET_USERNAME')
BITBUCKET_PASSWORD = os.getenv('BITBUCKET_PASSWORD')
BITBUCKET_URL = os.getenv('BITBUCKET_URL')
GOOGLE_CHAT_WEBHOOK = os.getenv('GOOGLE_CHAT_WEBHOOK')

@router.get("/open-prs")
async def get_all_open_prs(
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
            chat_url = webhook_url or GOOGLE_CHAT_WEBHOOK       
            chat_service = GoogleChatService(chat_url)   
            responseChat = chat_service.send_open_bitbucket_prs_notification(prs)
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