import requests
from fastapi import HTTPException
from typing import List, Dict
from datetime import datetime
import pytz
from base64 import b64encode

class BitbucketAPI:
    def __init__(self, username: str, app_password: str, workspace: str):
        self.auth = (username, app_password)
        self.workspace = workspace
        self.api_base = "https://api.bitbucket.org/2.0"
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
    def get_repositories(self) -> List[Dict]:
        """Get all repositories in the workspace"""
        url = f"{self.api_base}/workspaces/{self.workspace}/repositories"
        print(f"Requesting URL: {url}")
        print(f"Using auth: {self.auth[0]}:****")  # Print username but hide password
        
        response = requests.get(
            url,
            auth=self.auth,
            headers=self.headers,
            params={
                "pagelen": 100,
                "fields": "values.slug,values.name"
            }
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response body: {response.text[:200]}")
        
        if response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="Authentication failed. Please check your Bitbucket credentials."
            )
        elif response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch repositories: {response.text}"
            )
            
        return response.json().get('values', [])
        
    def get_user_uuid(self, username: str) -> str:
        """Get user's UUID from their username"""
        url = f"{self.api_base}/users/{username}"
        
        response = requests.get(
            url,
            auth=self.auth,
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json().get('uuid')
        elif response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"User {username} not found"
            )
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch user info: {response.text}"
            )

    def get_repository_prs(self, repo_slug: str = "bizomweb2") -> List[Dict]:
        """Get all open PRs for a repository"""
        url = f"{self.api_base}/repositories/{self.workspace}/{repo_slug}/pullrequests"
        print(f"Requesting URL: {url}")
        
        params = {
            "state": "OPEN",
            "pagelen": 50,  # Keep page size reasonable
            "fields": "values.id,values.title,values.author,values.destination.repository.name,values.created_on,values.links.html.href,values.source.branch.name,values.destination.branch.name,next"
        }
        
        try:
            all_prs = []
            while url:
                response = requests.get(
                    url,
                    auth=self.auth,
                    headers=self.headers,
                    params=params
                )
                
                print(f"Response status: {response.status_code}")
                
                if response.status_code == 401:
                    raise HTTPException(
                        status_code=401,
                        detail="Authentication failed. Please check your Bitbucket credentials."
                    )
                elif response.status_code != 200:
                    error_msg = response.text
                    try:
                        error_json = response.json()
                        if 'error' in error_json:
                            error_msg = error_json['error'].get('message', error_msg)
                    except:
                        pass
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Failed to fetch PRs: {error_msg}"
                    )
                
                data = response.json()
                all_prs.extend(data.get('values', []))
                
                # Get next page URL if it exists
                url = data.get('next')
                # Clear params as they're included in the next URL
                params = None if url else params
                
                print(f"Fetched {len(all_prs)} PRs so far...")
            
            print(f"Total PRs fetched: {len(all_prs)}")
            return all_prs
            
        except requests.RequestException as e:
            print(f"Request error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Request failed: {str(e)}"
            )

    def get_all_open_prs(self, authors: str = None) -> List[Dict]:
        """Get all open PRs for bizomweb2"""
        try:
            # Get all PRs first
            prs = self.get_repository_prs()
            
            # Process author names if provided
            author_list = []
            if authors:
                # Split by comma, clean each name (lowercase, no spaces)
                author_list = [
                    name.strip().lower().replace(" ", "")
                    for name in authors.split(",")
                    if name.strip()
                ]
            
            # Process each PR
            all_prs = []
            for pr in prs:
                # Convert UTC to IST
                created_on = datetime.fromisoformat(pr['created_on'].replace('Z', '+00:00'))
                ist_time = created_on.astimezone(pytz.timezone('Asia/Kolkata'))
                
                pr_data = {
                    "author": pr['author']['display_name'],
                    "title": pr['title'],
                    "repository": pr['destination']['repository']['name'],
                    "source_branch": pr['source']['branch']['name'],
                    "destination_branch": pr['destination']['branch']['name'],
                    "created_on": ist_time.strftime('%d %b %Y | %I:%M %p IST'),
                    "url": pr['links']['html']['href']
                }
                
                # Filter by authors if provided
                if not author_list or pr['author']['display_name'].lower().replace(" ", "") in author_list:
                    all_prs.append(pr_data)
        
            # Sort PRs by creation date (newest first)
            all_prs.sort(key=lambda x: x['created_on'], reverse=True)
            return all_prs
            
        except Exception as e:
            print(f"Error details: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching PRs: {str(e)}"
            )
    