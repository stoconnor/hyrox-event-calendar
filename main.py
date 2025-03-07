import requests
import os
import re
from googleapiclient.discovery import build
from google.oauth2 import service_account
from datetime import datetime

# 🔹 Load RapidAPI key from GitHub Secrets
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
PROFILE = "hybridathleteevents.ie"  # Change to your actual Instagram username
USER_ID = "263765230"  # Change this to the user ID if necessary

# 🔹 Google Calendar Setup
SERVICE_ACCOUNT_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/calendar"]
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
calendar_service = build("calendar", "v3", credentials=creds)

# 🔹 Function to Extract Event Details from Captions
def extract_event_details(text):
    match = re.search(r"(Hyrox \w+) - (\w+ \d{1,2}, \d{4}) - (.+)", text)
    if match:
        return match.group(1), match.group(2), match.group(3)
    return None, None, None

# 🔹 Function to Add Events to Google Calendar
def add_event_to_calendar(event_name, event_date, event_location):
    try:
        event_datetime = datetime.strptime(event_date, "%B %d, %Y").isoformat()
        event = {
            'summary': event_name,
            'location': event_location,
            'start': {'dateTime': event_datetime, 'timeZone': 'UTC'},
            'end': {'dateTime': event_datetime, 'timeZone': 'UTC'},
        }
        calendar_service.events().insert(calendarId="primary", body=event).execute()
        print(f"✅ Added event: {event_name} on {event_date} at {event_location}")
    except Exception as e:
        print(f"❌ Error adding event: {e}")

# 🔹 Fetch Instagram Posts from RapidAPI
def fetch_instagram_posts(profile):
    url = f"https://instagram230.p.rapidapi.com/user/posts"
    params = {"username": profile}
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "instagram230.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Failed to fetch Instagram posts: {response.status_code} - {response.text}")
        return None

# 🔹 Fetch Instagram Stories from RapidAPI
def fetch_instagram_stories(user_id):
    url = f"https://instagram230.p.rapidapi.com/user/stories"
    params = {"user_id": user_id}
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "instagram230.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Failed to fetch Instagram stories: {response.status_code} - {response.text}")
        return None

# 🔹 Process Instagram Posts
data = fetch_instagram_posts(PROFILE)

if data:
    for post in data.get("posts", []):
        caption = post.get("caption", "")
        event_name, event_date, event_location = extract_event_details(caption)

        if event_name and event_date and event_location:
            add_event_to_calendar(event_name, event_date, event_location)

# 🔹 Process Instagram Stories
story_data = fetch_instagram_stories(USER_ID)

if story_data:
    for story in story_data.get("stories", []):
        text = story.get("caption", "")
        event_name, event_date, event_location = extract_event_details(text)

        if event_name and event_date and event_location:
            add_event_to_calendar(event_name, event_date, event_location)

print("🎉 All events added from Instagram posts and stories!")
