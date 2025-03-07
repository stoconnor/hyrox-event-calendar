import instaloader
import pytesseract
from PIL import Image
import os
import re
from googleapiclient.discovery import build
from google.oauth2 import service_account
from datetime import datetime

# Google Calendar Setup
SERVICE_ACCOUNT_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/calendar"]
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
calendar_service = build("calendar", "v3", credentials=creds)

# Instaloader Setup
L = instaloader.Instaloader()
PROFILE = "hybridathleteevents.ie"

# Login (Required for stories)
L.load_session_from_file(PROFILE)  # Ensure you have a valid session

# Function to extract event details (from caption or OCR text)
def extract_event_details(text):
    match = re.search(r"(Hyrox \w+) - (\w+ \d{1,2}, \d{4}) - (.+)", text)
    if match:
        return match.group(1), match.group(2), match.group(3)
    return None, None, None

# Function to add events to Google Calendar
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

# 1. Scrape Instagram Posts (Captions & OCR)
for post in instaloader.Profile.from_username(L.context, PROFILE).get_posts():
    # Extract event details from the caption
    event_name, event_date, event_location = extract_event_details(post.caption)
    
    if event_name and event_date and event_location:
        add_event_to_calendar(event_name, event_date, event_location)
    
    # Download & Process OCR from Post Image
    image_path = f"{post.shortcode}.jpg"
    L.download_post(post, PROFILE)
    
    if os.path.exists(image_path):  # Ensure the file exists before OCR
        text = pytesseract.image_to_string(Image.open(image_path))
        event_name, event_date, event_location = extract_event_details(text)
        
        if event_name and event_date and event_location:
            add_event_to_calendar(event_name, event_date, event_location)

# 2. Scrape Instagram Stories (OCR Only)
print("📥 Downloading latest Instagram stories...")

for story in L.get_stories():
    for item in story.get_items():
        filename = L.download_storyitem(item, PROFILE)
        
        if filename.endswith((".jpg", ".png")):
            text = pytesseract.image_to_string(Image.open(filename))
            event_name, event_date, event_location = extract_event_details(text)
            
            if event_name and event_date and event_location:
                add_event_to_calendar(event_name, event_date, event_location)

print("🎉 All events added from posts and stories!")
