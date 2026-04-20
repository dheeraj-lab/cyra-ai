import os
import subprocess
import webbrowser
import psutil
import wikipedia
from ddgs import DDGS
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import comtypes
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import requests
import json
import threading
import time
import datetime
import re
from modules.vision import analyze_screen, analyze_webcam
from modules.pc_control import pc_control
from modules.email_handler import send_email
from modules.smart_home import turn_on_bulb, turn_off_bulb, set_brightness, set_color, get_bulb_status
from modules.utils import find_app_path


load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="user-modify-playback-state user-read-playback-state user-read-currently-playing"
))

def web_search(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        if results:
            response = f"I found this: {results[0]['title']}. {results[0]['body']}"
            return response
        return "I couldn't find anything for that."
    except Exception as e:
        return f"Search failed: {str(e)}"

def open_youtube(query=None):
    try:
        if query:
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        else:
            url = "https://www.youtube.com"
        
        brave_path = find_app_path("brave")
        if brave_path:
            subprocess.Popen([brave_path, url])
        else:
            webbrowser.open(url)
        return f"Opening YouTube{' and searching for ' + query if query else ''} in Brave~!" if brave_path else f"Opening YouTube{' and searching for ' + query if query else ''}~!"
    except Exception as e:
        return f"Could not open YouTube: {str(e)}"

    
def play_song(query):
    try:
        from modules.browser_agent import play_youtube_music
        return play_youtube_music(query)
    except Exception as e:
        return f"Could not play song: {str(e)}"

def play_pause_media(action="toggle"):
    try:
        from modules.browser_agent import pause_youtube_music
        force_pause = True if action == "pause" else False
        if action == "toggle":
            import pyautogui
            pyautogui.press('playpause')
            return "Media toggled via system keys!"
        return pause_youtube_music(force_pause)
    except Exception:
        import pyautogui
        if action == "pause": pyautogui.press('pause')
        elif action == "play": pyautogui.press('play')
        else: pyautogui.press('playpause')
        return f"Media {action}ed via system keys!"

def control_volume(action, level=None):
    # Initialize COM for this thread if not already done
    try:
        comtypes.CoInitialize()
    except:
        pass

    devices = None
    interface = None
    volume = None

    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        current = round(volume.GetMasterVolumeLevelScalar() * 100)
        
        result = ""
        if action == "set" and level is not None:
            volume.SetMasterVolumeLevelScalar(int(level) / 100, None)
            result = f"Volume set to {level} percent~!"
        elif action == "up":
            new_vol = min(100, current + 10)
            volume.SetMasterVolumeLevelScalar(new_vol / 100, None)
            result = f"Volume increased to {new_vol} percent~!"
        elif action == "down":
            new_vol = max(0, current - 10)
            volume.SetMasterVolumeLevelScalar(new_vol / 100, None)
            result = f"Volume decreased to {new_vol} percent~!"
        elif action == "mute":
            volume.SetMute(1, None)
            result = f"Muted! Volume was at {current} percent~!"
        elif action == "unmute":
            volume.SetMute(0, None)
            result = f"Unmuted! Volume is at {current} percent~!"
        elif action == "get":
            result = f"Current volume is {current} percent~!"
        
        # Explicitly release references
        volume = None
        interface = None
        devices = None
        
        return result
    except Exception as e:
        # Ensure references are cleared even on error
        volume = None
        interface = None
        devices = None
        return f"Volume control failed: {str(e)}"


def enable_hotspot():
    try:
        ps_script = """
        $connectionProfile = [Windows.Networking.Connectivity.NetworkInformation,Windows.Networking.Connectivity,ContentType=WindowsRuntime]::GetInternetConnectionProfile()
        $tetheringManager = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]::CreateFromConnectionProfile($connectionProfile)
        $tetheringManager.StartTetheringAsync()
        """
        subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
        return "Hotspot enabled~!"
    except Exception as e:
        return f"Could not enable hotspot: {str(e)}"

def disable_hotspot():
    try:
        ps_script = """
        $connectionProfile = [Windows.Networking.Connectivity.NetworkInformation,Windows.Networking.Connectivity,ContentType=WindowsRuntime]::GetInternetConnectionProfile()
        $tetheringManager = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]::CreateFromConnectionProfile($connectionProfile)
        $tetheringManager.StopTetheringAsync()
        """
        subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
        return "Hotspot disabled~!"
    except Exception as e:
        return f"Could not disable hotspot: {str(e)}"

# (Caching moved to utils.py)

def open_app(app_name):
    """Open an application using the best found path."""
    try:
        path = find_app_path(app_name)
        if path:
            os.startfile(path)
            return f"Opening {app_name}~!"
        
        # Last resort: Try running it directly (if in PATH)
        subprocess.Popen([app_name])
        return f"Opening {app_name} (via system path)~!"
    except Exception as e:
        return f"Could not open {app_name}: {str(e)}"



def wikipedia_search(query):
    try:
        summary = wikipedia.summary(query, sentences=2)
        return summary
    except Exception as e:
        return f"Could not find Wikipedia info: {str(e)}"

def shutdown_pc():
    os.system("shutdown /s /t 5")
    return "Okay shutting down your PC. Bye bye~!"

def restart_pc():
    os.system("shutdown /r /t 5")
    return "Restarting your PC~!"

def get_weather(city="Delhi"):
    try:
        api_key = os.getenv("WEATHER_API_KEY")
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url)
        data = response.json()
        if data["cod"] != 200:
            return f"Could not find weather for {city}!"
        temp = round(data["main"]["temp"])
        feels_like = round(data["main"]["feels_like"])
        humidity = data["main"]["humidity"]
        description = data["weather"][0]["description"]
        wind = round(data["wind"]["speed"])
        return f"In {city}, it's {temp}°C, feels like {feels_like}°C. {description.capitalize()}, humidity {humidity}%, wind {wind} km/h!"
    except Exception as e:
        return f"Weather fetch failed: {str(e)}"

def set_timer(seconds, message="Timer complete!"):
    def timer_thread():
        time.sleep(seconds)
        from modules.tts import speak
        speak(f"Hey Dheeraj! {message}", "excited")
        print(f"\n[Timer: {message}]")
    thread = threading.Thread(target=timer_thread, daemon=True)
    thread.start()
    return f"Timer set for {seconds} seconds!"

alarms = []

def set_alarm(time_str):
    try:
        now = datetime.datetime.now()
        time_formats = ["%I:%M %p", "%H:%M", "%I %p", "%I:%M%p", "%I%p"]
        alarm_time = None
        for fmt in time_formats:
            try:
                parsed = datetime.datetime.strptime(time_str.strip().upper(), fmt)
                alarm_time = now.replace(hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0)
                break
            except:
                continue
        if not alarm_time:
            return "Could not parse time — use '7:30 AM' or '19:30' format!"
        if alarm_time < now:
            alarm_time += datetime.timedelta(days=1)
        alarms.append(alarm_time)
        def alarm_thread():
            while True:
                if datetime.datetime.now() >= alarm_time:
                    from modules.tts import speak
                    speak(f"Dheeraj! Alarm! Time is up — {time_str}!", "excited")
                    print(f"\n[ALARM] {time_str} — RING RING!")
                    if alarm_time in alarms:
                        alarms.remove(alarm_time)
                    break
                time.sleep(10)
        thread = threading.Thread(target=alarm_thread, daemon=True)
        thread.start()
        time_left = alarm_time - now
        hours = int(time_left.seconds // 3600)
        minutes = int((time_left.seconds % 3600) // 60)
        return f"Alarm set for {time_str}! {hours}h {minutes}m from now!"
    except Exception as e:
        return f"Alarm failed: {str(e)}"

def list_alarms():
    if not alarms:
        return "No alarms set!"
    result = f"{len(alarms)} alarm(s) set:\n"
    for alarm in alarms:
        result += f"- {alarm.strftime('%I:%M %p')}\n"
    return result

def cancel_alarms():
    alarms.clear()
    return "All alarms cancelled!"

def parse_timer(params):
    if not params:
        return 60, "Timer done!"
    params = params.lower()
    seconds = 0
    hours = re.search(r'(\d+)\s*hour', params)
    minutes = re.search(r'(\d+)\s*min', params)
    secs = re.search(r'(\d+)\s*sec', params)
    if hours: seconds += int(hours.group(1)) * 3600
    if minutes: seconds += int(minutes.group(1)) * 60
    if secs: seconds += int(secs.group(1))
    if seconds == 0:
        numbers = re.findall(r'\d+', params)
        if numbers:
            seconds = int(numbers[0]) * 60
    return seconds, "Timer done! Hey Dheeraj, time is up!"

NOTES_FILE = "notes.json"

def save_note(note):
    try:
        notes = load_notes()
        notes.append({"text": note, "timestamp": datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")})
        with open(NOTES_FILE, "w") as f:
            json.dump(notes, f, indent=2)
        return f"Note saved: {note}!"
    except Exception as e:
        return f"Could not save note: {str(e)}"

def load_notes():
    try:
        if os.path.exists(NOTES_FILE):
            with open(NOTES_FILE, "r") as f:
                return json.load(f)
        return []
    except:
        return []

def read_notes():
    notes = load_notes()
    if not notes:
        return "No notes saved yet!"
    result = f"You have {len(notes)} notes:\n"
    for i, note in enumerate(notes[-5:], 1):
        result += f"{i}. {note['text']} ({note['timestamp']})\n"
    return result

def delete_notes():
    try:
        with open(NOTES_FILE, "w") as f:
            json.dump([], f)
        return "All notes deleted!"
    except Exception as e:
        return f"Could not delete notes: {str(e)}"
    
def take_screenshot():
    try:
        import gc
        gc.collect()
        from PIL import ImageGrab
        screenshots_dir = os.path.expanduser("~") + r"\Pictures\Cyra Screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(screenshots_dir, filename)
        screenshot = ImageGrab.grab()
        screenshot.save(filepath)
        return "Screenshot taken! Saved in your Pictures folder!"
    except Exception as e:
        return f"Screenshot failed: {str(e)}"
    
def daily_briefing():
    try:
        now = datetime.datetime.now()
        day = now.strftime("%A, %d %B %Y")
        hour = now.hour
        if hour < 12: greeting = "Good morning"
        elif hour < 17: greeting = "Good afternoon"
        else: greeting = "Good evening"
        briefing = f"{greeting} Dheeraj! Today is {day}. "
        weather = get_weather("Delhi")
        briefing += f"Weather — {weather} "
        notes = load_notes()
        if notes:
            briefing += f"You have {len(notes)} saved notes. Latest — {notes[-1]['text']}. "
        else:
            briefing += "No pending notes. "
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text("India top news today", max_results=2))
            if results:
                briefing += f"Top news — {results[0]['title']}. "
        except:
            pass
        briefing += "Have a great day!"
        return briefing
    except Exception as e:
        return f"Briefing failed: {str(e)}"

def load_contacts():
    try:
        with open("contacts.json", "r") as f:
            return json.load(f)
    except:
        return {}

def send_whatsapp(params):
    """Send WhatsApp message using Playwright browser automation."""
    try:
        from modules.browser_agent import send_whatsapp_message
        contacts = load_contacts()
        parts = params.split("|")
        if len(parts) < 2:
            return "Format: name|message"
        contact = parts[0].strip()
        message = parts[1].strip()
        # Check contacts list for name mapping
        if contact.lower() in contacts:
            contact = contacts[contact.lower()]
        return send_whatsapp_message(contact, message)
    except Exception as e:
        return f"WhatsApp message failed: {str(e)}"

def send_whatsapp_file_action(params):
    """Send file via WhatsApp using Playwright."""
    try:
        from modules.browser_agent import send_whatsapp_file
        parts = params.split("|")
        if len(parts) < 2:
            return "Format: contact|file_path"
        contact = parts[0].strip()
        file_path = parts[1].strip()
        contacts = load_contacts()
        if contact.lower() in contacts:
            contact = contacts[contact.lower()]
        return send_whatsapp_file(contact, file_path)
    except Exception as e:
        return f"WhatsApp file send failed: {str(e)}"

def organize_desktop():
    """Organize desktop files into folders — no pyautogui, pure filesystem."""
    try:
        import shutil
        desktop = os.path.expanduser("~") + r"\Desktop"
        folders = {
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
            "Videos": [".mp4", ".mkv", ".avi", ".mov", ".wmv"],
            "Documents": [".pdf", ".docx", ".doc", ".txt", ".pptx", ".xlsx", ".csv"],
            "Audio": [".mp3", ".wav", ".flac", ".aac"],
            "Archives": [".zip", ".rar", ".7z", ".tar"],
            "Code": [".py", ".js", ".html", ".css", ".cpp", ".java", ".json"],
            "Executables": [".exe", ".msi", ".bat"],
            "Shortcuts": [".lnk", ".url"],
        }
        moved = 0
        for file in os.listdir(desktop):
            file_path = os.path.join(desktop, file)
            if os.path.isfile(file_path):
                ext = os.path.splitext(file)[1].lower()
                for folder, extensions in folders.items():
                    if ext in extensions:
                        folder_path = os.path.join(desktop, folder)
                        os.makedirs(folder_path, exist_ok=True)
                        dest = os.path.join(folder_path, file)
                        if not os.path.exists(dest):
                            shutil.move(file_path, dest)
                            moved += 1
                        break
        # Refresh desktop via PowerShell (no pyautogui needed)
        subprocess.run([
            "powershell", "-Command",
            "$shell = New-Object -ComObject Shell.Application; $desktop = $shell.NameSpace(0); $desktop.Self.InvokeVerb('Refresh')"
        ], capture_output=True)
        return f"Desktop organized! {moved} files moved!"
    except Exception as e:
        return f"Desktop organize failed: {str(e)}"
    
def create_folder(folder_name="New Folder"):
    """Create folder on desktop — pure filesystem, no pyautogui."""
    try:
        desktop = os.path.expanduser("~") + r"\Desktop"
        folder_path = os.path.join(desktop, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        return f"Folder '{folder_name}' created on Desktop!"
    except Exception as e:
        return f"Error creating folder: {str(e)}"

def delete_temp():
    try:
        import shutil
        temp_folders = [os.environ.get("TEMP", ""), os.environ.get("TMP", ""), r"C:\Windows\Temp"]
        deleted = 0
        for folder in temp_folders:
            if folder and os.path.exists(folder):
                for item in os.listdir(folder):
                    item_path = os.path.join(folder, item)
                    try:
                        if os.path.isfile(item_path):
                            os.unlink(item_path)
                            deleted += 1
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                            deleted += 1
                    except:
                        pass
        return f"Temp files cleaned! {deleted} items deleted!"
    except Exception as e:
        return f"Temp delete failed: {str(e)}"

def empty_recycle_bin():
    try:
        subprocess.run(
            ["powershell", "-Command", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"],
            capture_output=True
        )
        return "Recycle bin emptied!"
    except Exception as e:
        return f"Recycle bin failed: {str(e)}"

def find_file(filename):
    try:
        search_paths = [
            os.path.expanduser("~") + r"\Desktop",
            os.path.expanduser("~") + r"\Documents",
            os.path.expanduser("~") + r"\Downloads",
            os.path.expanduser("~") + r"\Pictures",
            os.path.expanduser("~") + r"\Videos",
            os.path.expanduser("~") + r"\Music",
        ]
        found = []
        for path in search_paths:
            for root, dirs, files in os.walk(path):
                for file in files:
                    if filename.lower() in file.lower():
                        found.append(os.path.join(root, file))
        if found:
            result = f"{len(found)} file(s) found: "
            for f in found[:3]:
                result += f"\n- {f}"
            return result
        else:
            return f"{filename} not found!"
    except Exception as e:
        return f"File search failed: {str(e)}"

def upload_assignment_action(params):
    """Upload assignment to Google Classroom via Playwright."""
    try:
        from modules.browser_agent import upload_assignment
        parts = params.split("|")
        class_name = parts[0].strip() if len(parts) > 0 else ""
        assignment_title = parts[1].strip() if len(parts) > 1 else ""
        file_path = parts[2].strip() if len(parts) > 2 else None
        text_body = parts[3].strip() if len(parts) > 3 else None
        if not class_name or not assignment_title:
            return "Format: class_name|assignment_title|file_path(optional)|text(optional)"
        return upload_assignment(class_name, assignment_title, file_path, text_body)
    except Exception as e:
        return f"Assignment upload failed: {str(e)}"

def open_url_action(url):
    """Open URL using Playwright browser."""
    try:
        from modules.browser_agent import open_url
        return open_url(url)
    except Exception as e:
        return f"Could not open URL: {str(e)}"

def handle_action(action, params=None):
    """
    Unified Action Dispatcher.
    Maps LLM intents to Python functions.
    """
    
    # Mapping table: {action_name: (function, param_parser_if_any)}
    ACTION_MAP = {
        # --- Media & Entertainment ---
        "play_song": play_song,
        "open_youtube": open_youtube,
        "media_play_pause": lambda p: play_pause_media(p if p in ["pause", "play"] else "toggle"),
        "wikipedia": wikipedia_search,
        "play_music": play_song, # Alias for consistency
        
        # --- System Volume ---
        "volume_up": lambda _: control_volume("up"),
        "volume_down": lambda _: control_volume("down"),
        "mute": lambda _: control_volume("mute"),
        "unmute": lambda _: control_volume("unmute"),
        "volume_get": lambda _: control_volume("get"),
        "volume_set": lambda p: control_volume("set", int(''.join(filter(str.isdigit, str(p)))) if p and any(c.isdigit() for c in str(p)) else 50),
        
        # --- PC Control & Apps ---
        "open_app": open_app,
        "shutdown": shutdown_pc,
        "restart": restart_pc,
        "screenshot": take_screenshot,
        "pc_control": pc_control,
        "enable_hotspot": enable_hotspot,
        "disable_hotspot": disable_hotspot,
        "organize_desktop": organize_desktop,
        "create_folder": lambda p: create_folder(p if p else "New Folder"),
        "delete_temp": delete_temp,
        "empty_recycle_bin": empty_recycle_bin,
        "find_file": find_file,
        
        # --- Communication ---
        "whatsapp": send_whatsapp,
        "whatsapp_file": send_whatsapp_file_action,
        "send_email": lambda p: (
            send_email(*(p.split("|") + [None]*4)[:4]) if p and "|" in p 
            else "Format: to|subject|body|optional_file"
        ),
        
        # --- Information & Tools ---
        "weather": lambda p: get_weather(p if p else "Delhi"),
        "set_timer": lambda p: set_timer(*parse_timer(p)),
        "set_alarm": set_alarm,
        "list_alarms": lambda _: list_alarms(),
        "cancel_alarms": lambda _: cancel_alarms(),
        "save_note": save_note,
        "read_notes": lambda _: read_notes(),
        "delete_notes": lambda _: delete_notes(),
        "daily_briefing": lambda _: daily_briefing(),
        
        # --- Vision & AI ---
        "see_screen": lambda p: analyze_screen(p if p else "What do you see on the screen?"),
        "see_webcam": lambda p: analyze_webcam(p if p else "What do you see?"),
        "click_screen": lambda p: analyze_and_click(p) if "analyze_and_click" in globals() else "Click feature not loaded",
        "type_text": lambda p: (pyperclip.copy(p), pyautogui.hotkey("ctrl", "v")) and f"Typed: {p}" if p else "Nothing to type",
        
        # --- Browser & Automation ---
        "open_url": open_url_action,
        "upload_assignment": upload_assignment_action,
        
        # --- Smart Home ---
        "bulb_on": turn_on_bulb,
        "bulb_off": turn_off_bulb,
        "bulb_brightness": set_brightness,
        "bulb_color": set_color,
        "bulb_status": get_bulb_status,
        
        # --- Config & Settings ---
        "update_config": lambda p: (
            (set_value(*(p.split("=", 1) + [""]*2)[:2]) if "=" in p else "Format: key=value")
            if "set_value" in globals() else "Config module not loaded"
        ),
        "get_config": lambda p: f"{p} = {get(p)}" if "get" in globals() else "Config module not loaded",
        "get_usage_stats": lambda _: __import__("modules.stats", fromlist=["get_stats_summary"]).get_stats_summary(),
        "set_background": lambda p: set_wallpaper(os.path.abspath(p if p and os.path.exists(p) else "background.png")),
    }

    try:
        if action in ACTION_MAP:
            func = ACTION_MAP[action]
            # Execute with params if function expects them, or just call it
            return func(params)
        else:
            return None
    except Exception as e:
        return f"Action '{action}' failed: {str(e)}"