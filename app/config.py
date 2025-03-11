import os
from dotenv import load_dotenv

load_dotenv()

# Bugzilla Config
BUGZILLA_URL = os.getenv('BUGZILLA_URL')
BUGZILLA_EMAIL = os.getenv('BUGZILLA_EMAIL')
BUGZILLA_PASSWORD = os.getenv('BUGZILLA_PASSWORD')

# Google Chat Config
GOOGLE_CHAT_WEBHOOK_URL = os.getenv('GOOGLE_CHAT_WEBHOOK_URL')
GOOGLE_CHAT_SPACE_ID = os.getenv('GOOGLE_CHAT_SPACE_ID')
GOOGLE_CHAT_KEY = os.getenv('GOOGLE_CHAT_KEY')
GOOGLE_CHAT_TOKEN = os.getenv('GOOGLE_CHAT_TOKEN')

GOOGLE_CHAT_WEBHOOK = f"{GOOGLE_CHAT_WEBHOOK_URL}/{GOOGLE_CHAT_SPACE_ID}/messages?key={GOOGLE_CHAT_KEY}&token={GOOGLE_CHAT_TOKEN}"

# Add these to your existing config.py
BITBUCKET_USERNAME = os.getenv('BITBUCKET_USERNAME')
BITBUCKET_PASSWORD = os.getenv('BITBUCKET_PASSWORD')
BITBUCKET_URL = os.getenv('BITBUCKET_URL', 'https://api.bitbucket.org/2.0') 