import os
import re
from datetime import datetime
import pytz
from typing import List, Dict, Any


class AssignmentParser:
    def __init__(self):
        pass

    def parse_date_string(self, date_str: str) -> datetime:
        """Parse various date formats that might come from classroom emails"""
        if not date_str or date_str == "Not found":
            return None
            
        # Remove timezone info like (EDT) for simpler parsing
        cleaned_date = re.sub(r'\s*\([^)]+\)', '', date_str)
        
        # Try different date formats
        date_formats = [
            "%I:%M %p, %b %d",  # "8:43 AM, Jun 13"
            "%b %d",            # "Jun 13"
            "%B %d",            # "June 13"
            "%m/%d/%Y",         # "06/13/2025"
            "%Y-%m-%d",         # "2025-06-13"
        ]
        
        for fmt in date_formats:
            try:
                # Parse the date
                parsed_date = datetime.strptime(cleaned_date, fmt)
                
                # If year is not specified, assume current year (2025)
                if parsed_date.year == 1900:  # Default year when not specified
                    parsed_date = parsed_date.replace(year=2025)
                
                return parsed_date
            except ValueError:
                continue
                
        # If no format works, try to extract just month and day
        month_day_match = re.search(r'(\w+)\s+(\d+)', cleaned_date)
        if month_day_match:
            try:
                month_name = month_day_match.group(1)
                day = int(month_day_match.group(2))
                
                # Convert month name to number
                month_map = {
                    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
                    'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
                    'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
                }
                
                if month_name in month_map:
                    return datetime(2025, month_map[month_name], day)
            except (ValueError, KeyError):
                pass
        
        print(f"Unable to parse date: {date_str}")
        return None

    def parse_assignments(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        pages = []

        # Parse the due date and posted date
        for assignment_data in data:
            due_date = None
            date_span = None
            reminder_date = None
            
            # Parse due date
            due_date_obj = self.parse_date_string(assignment_data.get("due_date"))
            if due_date_obj:
                # Convert to PST timezone
                pacific_tz = pytz.timezone("America/Los_Angeles")
                due_date_obj = pacific_tz.localize(due_date_obj)
                due_date = {"start": due_date_obj.isoformat(), "end": None}

            # Parse posted date for date span and reminder
            posted_date_obj = self.parse_date_string(assignment_data.get("posted_date"))
            if posted_date_obj:
                # Convert to PST timezone
                pacific_tz = pytz.timezone("America/Los_Angeles")
                posted_date_obj = pacific_tz.localize(posted_date_obj)
                
                # Create date span from posted date to due date
                if due_date and posted_date_obj:
                    # Ensure start date is before end date
                    due_date_obj_for_comparison = datetime.fromisoformat(due_date["start"].replace('Z', '+00:00'))
                    if posted_date_obj <= due_date_obj_for_comparison:
                        date_span = {
                            "start": posted_date_obj.isoformat(),
                            "end": due_date["start"]
                        }
                    else:
                        # If posted date is after due date, just use due date
                        date_span = {
                            "start": due_date["start"],
                            "end": None
                        }
                elif due_date:
                    # If no posted date but has due date, use due date
                    date_span = {
                        "start": due_date["start"],
                        "end": None
                    }
                elif posted_date_obj:
                    # If no due date, just use posted date as start
                    date_span = {
                        "start": posted_date_obj.isoformat(),
                        "end": None
                    }
                else:
                    date_span = None
                
                # Set reminder to posted date
                reminder_date = {"start": posted_date_obj.isoformat(), "end": None}
            else:
                reminder_date = None

            # Determine course name with fallback options
            course_name = assignment_data.get("class_name")
            if not course_name or course_name == "Not found":
                # Try to use teacher name as course identifier
                posted_by = assignment_data.get("posted_by", "")
                if posted_by and posted_by != "Not found":
                    course_name = f"{posted_by}'s Class"
                else:
                    course_name = "Classroom"

            # Create the Notion page structure matching the CSV format
            notion_page = {
                "parent": {"database_id": os.environ.get("NOTION_DATABASE_ID")},
                "properties": {
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": assignment_data["assignment_name"],
                                    "link": {
                                        "url": assignment_data.get("assignment_link", "")
                                    } if assignment_data.get("assignment_link") else None
                                }
                            }
                        ]
                    },
                    "Category": {
                        "select": {
                            "name": "Canvas"  # Match existing database structure
                        }
                    },
                    "Course": {
                        "select": {
                            "name": course_name
                        }
                    },
                    "Date Span": {"date": date_span},
                    "Due": {"date": due_date},
                    "Last edited": {
                        "date": {
                            "start": datetime.now().isoformat(),
                            "end": None
                        }
                    },
                    "Points": {
                        "number": None  # Can be filled in manually or parsed if available
                    },
                    "Reminder": {"date": reminder_date},
                    "Status": {
                        "status": {
                            "name": "To Do"
                        }
                    },
                    "URL": {
                        "url": assignment_data.get("assignment_link", "")
                    }
                },
            }

            pages.append(notion_page)

        return pages
