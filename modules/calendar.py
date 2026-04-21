import json
import os
import datetime
from datetime import timedelta

CALENDAR_FILE = "memories/calendar.json"

def load_calendar():
    if os.path.exists(CALENDAR_FILE):
        with open(CALENDAR_FILE, "r") as f:
            return json.load(f)
    return []

def save_calendar(events):
    os.makedirs("memories", exist_ok=True)
    with open(CALENDAR_FILE, "w") as f:
        json.dump(events, f, indent=2)

def add_event(title, time_str, date_str=None):
    """Add event. time_str: '14:30', date_str: '2026-04-21'"""
    events = load_calendar()
    if not date_str:
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    events.append({
        "title": title,
        "time": time_str,
        "date": date_str
    })
    save_calendar(events)
    return f"Event '{title}' added for {date_str} at {time_str}!"

def get_today_events():
    events = load_calendar()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    today_events = [e for e in events if e["date"] == today]
    
    if not today_events:
        return "You have no events scheduled for today."
    
    res = "Today's schedule:\n"
    for e in sorted(today_events, key=lambda x: x['time']):
        res += f"- {e['time']}: {e['title']}\n"
    return res

def check_upcoming_reminders():
    """Check for events starting in the next 15 minutes."""
    events = load_calendar()
    now = datetime.datetime.now()
    today = now.strftime("%Y-%m-%d")
    
    reminders = []
    for e in events:
        if e["date"] == today:
            event_time = datetime.datetime.strptime(f"{today} {e['time']}", "%Y-%m-%d %H:%M")
            # If event is in next 15 mins and hasn't passed
            if now < event_time < now + timedelta(minutes=15):
                reminders.append(e["title"])
    return reminders
