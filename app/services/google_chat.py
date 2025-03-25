from datetime import datetime
import pytz
import requests
from fastapi import HTTPException
from typing import Dict, List
import os
    
class GoogleChatService:
    def __init__(self, webhook_url: str, base_url: str = None):
        self.webhook_url = webhook_url
        self.base_url = base_url or os.getenv('BUGZILLA_URL', 'https://bugzilla.bizom.in')

    def send_current_day_bug_notification(self, teams_data: dict, team_name: str) -> bool:
        """Send notification to Google Chat for a specific team with modern card layout"""
        try:
            team_data = teams_data.get(team_name.upper())
            if not team_data:
                raise ValueError(f"Team '{team_name}' not found in the report")
            
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
            
            # Calculate total bugs
            total = sum(team_data.values())
            
            # Create a card-based message for Google Chat
            card = {
                "cards": [
                    {
                        "header": {
                            "title": f"🐞 Bugzilla Status Report - {team_name.upper()} TEAM",
                            "subtitle": f"{total} active bugs | {datetime_str}"
                        },
                        "sections": [
                            {
                                "widgets": [
                                    {
                                        "textParagraph": {
                                            "text": f"<b>Current Day bug status breakdown for {team_name.upper()} team:</b>"
                                        }
                                    }
                                ]
                            },
                            {
                                "widgets": [
                                    {
                                        "keyValue": {
                                            "content": (
                                                f"<font color=''>• UNCONFIRMED: {team_data['UNCONFIRMED']}</font>\n"
                                                f"<font color=''>• CONFIRMED: {team_data['CONFIRMED']}</font>\n"
                                                f"<font color=''>• IN_PROGRESS: {team_data['IN_PROGRESS']}</font>\n"
                                                f"<font color=''>• IN_PROGRESS_DEV: {team_data['IN_PROGRESS_DEV']}</font>\n"
                                                f"<font color=''>• NEEDS_INFO: {team_data['NEEDS_INFO']}</font>\n"
                                                f"<font color=''>• UNDER_REVIEW: {team_data['UNDER_REVIEW']}</font>\n"
                                                f"<font color=''>• RE-OPENED: {team_data['RE-OPENED']}</font>"
                                            ),
                                            "contentMultiline": True
                                        }
                                    }
                                ]
                            },
                            {
                                "widgets": [
                                    {
                                        "keyValue": {
                                            "topLabel": "Summary",
                                            "content": f"<b>Total Active Issues: {total}</b>",
                                            "icon": "DESCRIPTION"
                                        }
                                    },
                                    {
                                        "buttons": [
                                            {
                                                "textButton": {
                                                    "text": "VIEW FULL REPORT",
                                                    "onClick": {
                                                        "openLink": {
                                                            "url": report_url
                                                        }
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
            
            # Send the card to Google Chat
            response = requests.post(self.webhook_url, json=card)
            
            if response.status_code != 200:
                print(f"Failed to send notification to Google Chat: {response.text}")
                return False
            
            return True
            
        except Exception as e:
            print(f"Error sending notification: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send notification: {str(e)}"
            )

    def send_priority_bug_notification(self, result, team_name):
        """
        Send SLA miss notification to Google Chat.
        
        Args:
            result: Dictionary containing SLA miss data
            team_name: Name of the team to notify
        """
        bugs = result.get("bugs", [])
        if not bugs:
            return
            
        # Get current date in IST
        import pytz
        from datetime import datetime
        ist_timezone = pytz.timezone('Asia/Kolkata')
        ist_time = datetime.now(ist_timezone)
        datetime_str = ist_time.strftime('%d %b %Y | %I:%M %p IST')
        
        # Create a card-based message for Google Chat with modern design
        card = {
            "cards": [
                {
                    "header": {
                        "title": f"🚨 P0/P1 SLA Miss Report - {team_name.upper()} TEAM",
                        "subtitle": f"{len(bugs)} bugs found | {datetime_str}"
                    },
                    "sections": [
                        {
                            "widgets": [
                                {
                                    "textParagraph": {
                                        "text": f"<font color=\"#D93025\"><b>The following {len(bugs)} high-priority bugs have missed their SLA and require immediate attention:</b></font>"
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Group bugs by component
        bugs_by_component = {}
        for bug in bugs:
            component = bug.get("component", "Other")
            if component not in bugs_by_component:
                bugs_by_component[component] = []
            bugs_by_component[component].append(bug)
        
        # Add a section for each component
        for component, component_bugs in bugs_by_component.items():
            component_section = {
                "widgets": [
                    {
                        "textParagraph": {
                            "text": f"<b><font color=\"#4285F4\">{component}</font></b> - {len(component_bugs)} bugs"
                        }
                    }
                ]
            }
            
            # Add each bug in this component
            for bug in component_bugs:
                bug_id = bug.get("bug_id", "N/A")
                product = bug.get("product", "N/A")
                assigned_to = bug.get("assigned_to", "Unassigned")
                status = bug.get("bug_status", "N/A")
                description = bug.get("short_desc", "No description")
                changed_date = bug.get("changeddate", "N/A")
                
                # Add bug details with modern styling
                component_section["widgets"].append({
                    "keyValue": {
                        "topLabel": f"Bug #{bug_id}",
                        "content": f"<b>{description}</b>",
                        "contentMultiline": True,
                        "bottomLabel": f"Status: {status}"
                    }
                })
                
                component_section["widgets"].append({
                    "keyValue": {
                        "content": f"<font color=\"#5F6368\">Product: {product} | Assigned to: {assigned_to} | Last changed: {changed_date}</font>",
                        "contentMultiline": True
                    }
                })
                
                # Add a button to view the bug
                component_section["widgets"].append({
                    "buttons": [
                        {
                            "textButton": {
                                "text": "VIEW BUG",
                                "onClick": {
                                    "openLink": {
                                        "url": f"{self.base_url}/show_bug.cgi?id={bug_id}"
                                    }
                                }
                            }
                        }
                    ]
                })
            
            card["cards"][0]["sections"].append(component_section)
        
        # Add a footer section with action items
        card["cards"][0]["sections"].append({
            "widgets": [
                {
                    "textParagraph": {
                        "text": "<b>⚠️ Action Required:</b> Please review and update these high-priority bugs as soon as possible to meet SLA requirements."
                    }
                },
                {
                    "buttons": [
                        {
                            "textButton": {
                                "text": "VIEW ALL BUGS",
                                "onClick": {
                                    "openLink": {
                                        "url": f"{self.base_url}/buglist.cgi?bug_status=UNCONFIRMED&bug_status=CONFIRMED&bug_status=NEEDS_INFO&bug_status=IN_PROGRESS&bug_status=IN_PROGRESS_DEV&bug_status=UNDER_REVIEW&bug_status=RE-OPENED&version={team_name}"
                                    }
                                }
                            }
                        }
                    ]
                }
            ]
        })
        
        # Send the card to Google Chat
        response = requests.post(self.webhook_url, json=card)
        
        if response.status_code != 200:
            print(f"Failed to send notification to Google Chat: {response.text}")
            return False
        
        return True

    def send_sla_missed_bugs_notification(self, result, team_name):
        """
        Send SLA missed bugs notification to Google Chat.
        
        Args:
            result: Dictionary containing SLA missed bugs data
            team_name: Name of the team to notify
        """
        bugs = result.get("bugs", [])
        if not bugs:
            return False
            
        # Get current date in IST
        import pytz
        from datetime import datetime
        ist_timezone = pytz.timezone('Asia/Kolkata')
        ist_time = datetime.now(ist_timezone)
        datetime_str = ist_time.strftime('%d %b %Y | %I:%M %p IST')
        
        # Create a card-based message for Google Chat
        card = {
            "cards": [
                {
                    "header": {
                        "title": f"⏰ SLA Missed Bugs - {team_name.upper()} TEAM",
                        "subtitle": f"{len(bugs)} bugs found | {datetime_str}"
                    },
                    "sections": [
                        {
                            "widgets": [
                                {
                                    "textParagraph": {
                                        "text": f"<b>The following {len(bugs)} bugs have missed their SLA and require immediate attention:</b>"
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Group bugs by component
        bugs_by_component = {}
        for bug in bugs:
            component = bug.get("component", "Other")
            if component not in bugs_by_component:
                bugs_by_component[component] = []
            bugs_by_component[component].append(bug)
        
        # Add a section for each component
        for component, component_bugs in bugs_by_component.items():
            component_section = {
                "header": f"Component: {component} ({len(component_bugs)} bugs)",
                "widgets": []
            }
            
            # Add each bug in this component
            for bug in component_bugs:
                bug_id = bug.get("bug_id", "N/A")
                product = bug.get("product", "N/A")
                assigned_to = bug.get("assigned_to", "Unassigned")
                status = bug.get("bug_status", "N/A")
                description = bug.get("short_desc", "No description")
                changed_date = bug.get("changeddate", "N/A")
                
                # Add bug title
                component_section["widgets"].append({
                    "keyValue": {
                        "topLabel": f"Bug #{bug_id}",
                        "content": description,
                        "contentMultiline": True,
                        "bottomLabel": f"Status: {status}"
                    }
                })
                
                # Add bug details
                component_section["widgets"].append({
                    "keyValue": {
                        "topLabel": "Details",
                        "content": f"Product: {product}\nAssigned to: {assigned_to}\nLast changed: {changed_date}",
                        "contentMultiline": True
                    }
                })
                
                # Add a button to view the bug
                component_section["widgets"].append({
                    "buttons": [
                        {
                            "textButton": {
                                "text": "VIEW BUG",
                                "onClick": {
                                    "openLink": {
                                        "url": f"{self.base_url}/show_bug.cgi?id={bug_id}"
                                    }
                                }
                            }
                        }
                    ]
                })
            
            # Add a divider between bugs
            if bug != component_bugs[-1]:
                component_section["widgets"].append({"divider": {}})
        
            card["cards"][0]["sections"].append(component_section)
        
            # Add a footer section with action items
            card["cards"][0]["sections"].append({
            "widgets": [
                {
                    "textParagraph": {
                        "text": "<b>⚠️ Action Required:</b> Please review and update these bugs as soon as possible to meet SLA requirements."
                    }
                },
                {
                    "buttons": [
                        {
                            "textButton": {
                                "text": "VIEW ALL BUGS",
                                "onClick": {
                                    "openLink": {
                                        "url": f"{self.base_url}/buglist.cgi?bug_status=UNCONFIRMED&bug_status=CONFIRMED&bug_status=NEEDS_INFO&bug_status=IN_PROGRESS&bug_status=IN_PROGRESS_DEV&bug_status=UNDER_REVIEW&bug_status=RE-OPENED&version={team_name}"
                                    }
                                }
                            }
                        }
                    ]
                }
            ]
        })
            
            # Send the card to Google Chat
            response = requests.post(self.webhook_url, json=card)
            
            if response.status_code != 200:
                print(f"Failed to send notification to Google Chat: {response.text}")
                return False
            
            return True

    def send_open_bitbucket_prs_notification(self, prs: List[Dict]) -> bool:
        """
        Send Bitbucket PRs notification to Google Chat with modern card design
        
        Args:
            prs: List of pull request dictionaries
            
        Returns:
            bool: True if notification was sent successfully
        """
        if not prs:
            return self.send_message("No open pull requests found.")
        
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
        
        # Calculate total PRs
        total_prs = sum(len(prs) for prs in prs_by_author.values())
        
        # Create a very simple text-based message
        text_message = f"🔄 *OPEN PULL REQUESTS*\n📅 {datetime_str}\n\n*SUMMARY*\n"
        
        # Add summary info to text portion
        for author, author_prs in sorted_authors:
            text_message += f"• {author}: {len(author_prs)} PRs\n"
        
        text_message += f"\n*TOTAL: {total_prs} PULL REQUESTS*\n\n"
        
        # Add details for each PR
        for author, author_prs in sorted_authors:
            text_message += f"\n👤 *{author}*\n"
            
            for pr in author_prs:
                text_message += f"\n*{pr['title']}*\n"
                text_message += f"Source: `{pr['source_branch']}` → Target: `{pr['destination_branch']}`\n"
                text_message += f"Created: {pr['created_on']}\n"
                text_message += f"Link: {pr['url']}\n"
                text_message += "───────────────────\n"
        
        # Send as a simple text message
        simple_message = {
            "text": text_message
        }
        
        response = requests.post(self.webhook_url, json=simple_message)
        
        if response.status_code != 200:
            print(f"Failed to send notification to Google Chat: {response.text}")
            return False
        
        return True