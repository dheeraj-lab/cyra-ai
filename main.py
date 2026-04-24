"""
Cyra — Main entry point.
Features: VSeeFace auto-start, system tray, clean shutdown, wake word.
"""

import os
import sys
import warnings
import logging
warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import subprocess
import time
import threading
import signal
import psutil

from modules.llm import chat
from modules.tts import speak
from modules.stt import listen
from modules.wake_word import wait_for_wake_word
from modules.agent import handle_action
from modules.telegram_bot import start_telegram_bot
from modules.avatar import set_expression, reset_expression, start_idle
from modules.dashboard import start_dashboard, update_status, log_message

# ==================== Global State ====================

running = True

SLEEP_WORDS = [
    "goodbye", "bye bye", "go to sleep", "sleep mode", "sleep", "go sleep", "passive mode",
    "band ho jao", "chup ho jao", "good night", "stop listening", "quiet"
]

SHUTDOWN_WORDS = [
    "shut down yourself", "stop yourself", "close yourself", "shutdown", "turn off",
    "band ho ja", "apne aap band ho ja", "exit cyra", "quit cyra"
]

def is_sleep_command(text):
    text = text.lower().strip()
    return any(phrase in text for phrase in SLEEP_WORDS)

def is_shutdown_command(text):
    text = text.lower().strip()
    return any(phrase in text for phrase in SHUTDOWN_WORDS)

# ==================== VSeeFace ====================

def start_vseeface():
    """Start VSeeFace — it remembers last avatar config automatically."""
    vseeface_path = r"C:\Users\dheer\Downloads\VSeeFace-v1.13.38c4\VSeeFace\VSeeFace.exe"
    if not os.path.exists(vseeface_path):
        print("[VSeeFace] Not found, skipping.")
        return

    # Check if VSeeFace is already running
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == 'VSeeFace.exe':
            print("[VSeeFace] Already running, skipping launch.")
            # Still try to move it to monitor 2 if it's running
            _move_vseeface_to_other_monitor()
            return

    subprocess.Popen([vseeface_path])
    print("[VSeeFace] Starting... (auto-loads last avatar)")
    time.sleep(10)  # Give more time for VSeeFace to fully load

    _click_start_and_move()

def _click_start_and_move():
    """Click Start button in VSeeFace and move to Monitor 2. Retries if needed."""
    try:
        import pyautogui
        import pygetwindow as gw
        import ctypes
        
        # Tell Windows we are DPI aware
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except:
            pass
        
        # Retry finding the window up to 3 times
        win = None
        for attempt in range(3):
            windows = gw.getWindowsWithTitle("VSeeFace")
            if windows:
                # Sort by size to ensure we get the real window
                windows = sorted(windows, key=lambda w: w.width * w.height, reverse=True)
                win = windows[0]
                break
            print(f"[VSeeFace] Window not found, retry {attempt+1}/3...")
            time.sleep(3)
        
        if not win:
            print("[VSeeFace] Could not find window after retries.")
            return
        
        try:
            win.activate()
        except Exception:
            # Sometimes activate fails if window is minimized
            try:
                win.restore()
                time.sleep(0.5)
                win.activate()
            except:
                pass
        time.sleep(1)
        
        # Calculate Start button position
        target_x = win.left + (win.width // 2)
        target_y = win.bottom - 155
        
        # Move cursor and click
        pyautogui.moveTo(target_x, target_y, duration=0.5)
        time.sleep(0.3)
        pyautogui.click()
        time.sleep(0.2)
        pyautogui.click()
        pyautogui.press('enter')
        
        print(f"[VSeeFace] Clicked Start button at ({target_x}, {target_y})!")
        time.sleep(4)  # Wait for tracking to initialize
        
        # Move to second monitor
        _move_vseeface_to_other_monitor()
            
    except Exception as e:
        print(f"[VSeeFace] Auto-start error: {e}")

def _move_vseeface_to_other_monitor():
    """Move VSeeFace to the OTHER monitor (opposite of where it currently is)."""
    try:
        import pyautogui
        import pygetwindow as gw
        import ctypes
        
        windows = gw.getWindowsWithTitle("VSeeFace")
        if not windows:
            print("[VSeeFace] Cannot find window to move.")
            return
        
        win = sorted(windows, key=lambda w: w.width * w.height, reverse=True)[0]
        
        try:
            win.activate()
        except:
            try:
                win.restore()
                time.sleep(0.3)
                win.activate()
            except:
                pass
        time.sleep(0.5)
        
        # Detect which monitor VSeeFace is on
        primary_width = ctypes.windll.user32.GetSystemMetrics(0)  # Primary monitor width
        
        # If window center is on primary monitor, move RIGHT to secondary
        # If window center is on secondary, move LEFT to primary
        win_center_x = win.left + (win.width // 2)
        if win_center_x < primary_width:
            direction = 'right'  # On primary → move to secondary
        else:
            direction = 'left'   # On secondary → move to primary
        
        pyautogui.hotkey('win', 'shift', direction)
        time.sleep(1)
        pyautogui.hotkey('win', 'up')  # Maximize
        print(f"[VSeeFace] Moved to other monitor (direction: {direction})!")
    except Exception as e:
        print(f"[VSeeFace] Could not move: {e}")

# ==================== System Tray ====================

def start_tray():
    """System tray icon — right-click to stop Cyra."""
    try:
        import pystray
        from PIL import Image

        # Path to the icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
        
        if os.path.exists(icon_path):
            img = Image.open(icon_path)
        else:
            # Fallback: Create a small Cyra icon (pink circle) if file is missing
            img = Image.new('RGB', (64, 64), color=(255, 105, 180))

        def on_quit(icon, item):
            global running
            print("\n[Cyra] Shutting down from tray...")
            running = False
            icon.stop()

        icon = pystray.Icon(
            "Cyra",
            img,
            "Cyra AI Assistant",
            menu=pystray.Menu(
                pystray.MenuItem("Cyra is running~!", None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Stop Cyra", on_quit)
            )
        )
        icon.run()
    except Exception as e:
        print(f"[Tray] Could not start: {e}")

# ==================== Active Conversation ====================

def active_mode(history):
    """Active conversation mode — Cyra is listening and responding."""
    global running
    from modules.avatar import set_sleeping, play_animation
    from modules.memory import build_memory_context, save_memory
    from modules.vision import analyze_screen
    from modules.sound_analyzer import start_sound_monitoring
    from modules.stt import calibrate_user
    from modules.dashboard import update_emotion
    
    set_sleeping(False)
    update_status("Speaking")
    
    # Dynamic greeting instead of boring "You called?"
    from modules.greeting import get_dynamic_greeting
    greeting = get_dynamic_greeting()
    speak(greeting, "excited")

    # Start Sound Awareness
    start_sound_monitoring(speak)

    def proactive_vision_loop():
        """Background thread to watch the screen and provide commentary."""
        while running:
            time.sleep(120)  # Every 2 minutes
            if not running: break
            
            # Don't interrupt if currently speaking or listening
            from modules.tts import is_speaking
            if is_speaking():
                continue
            
            print("[Vision] Proactive check...")
            try:
                from modules.config import get
                owner = get("owner", "User")
                context = analyze_screen("What is the user doing? Give a very short, cute commentary.")
                if context and len(context) > 10:
                    speak(f"Aww, {owner}! {context}", "happy")
                    save_memory(f"User was seen doing: {context}")

            except Exception as e:
                print(f"[Vision] Error: {e}")

    def notification_monitor_loop():
        """Check for WhatsApp notifications every 5 minutes."""
        from modules.browser_agent import check_whatsapp_notifications
        while running:
            time.sleep(300)  # Every 5 minutes
            if not running: break
            
            try:
                notifs = check_whatsapp_notifications()
                if notifs:
                    from modules.config import get
                    owner = get("owner", "User")
                    speak(f"{owner}, you have unread messages from {' and '.join(notifs[:2])}!", "excited")

            except:
                pass

    def reminder_loop():
        """Check for upcoming calendar events every minute."""
        from modules.calendar import check_upcoming_reminders
        while running:
            time.sleep(60)  # Every minute
            if not running: break
            
            try:
                reminders = check_upcoming_reminders()
                if reminders:
                    from modules.config import get
                    owner = get("owner", "User")
                    speak(f"{owner}, don't forget! You have: {', '.join(reminders)} coming up soon!", "excited")

            except:
                pass

    vision_thread = threading.Thread(target=proactive_vision_loop, daemon=True)
    vision_thread.start()
    
    notif_thread = threading.Thread(target=notification_monitor_loop, daemon=True)
    notif_thread.start()
    
    reminder_thread = threading.Thread(target=reminder_loop, daemon=True)
    reminder_thread.start()

    while running:
        update_status("Listening")
        user_input = listen()

        if not user_input:
            continue

        print(f"You: {user_input}")

        # Check for shutdown command
        if is_shutdown_command(user_input):
            speak("Okay~ shutting down! See you later~!", "sad")
            running = False
            return history

        # Check for sleep command
        if is_sleep_command(user_input):
            speak("Okay okay~ I will be quiet! Call me when you need me~!", "sad")
            set_sleeping(True)
            return history

        # Check for calibration
        if "calibrate my voice" in user_input.lower():
            speak("Okay! Please speak clearly after I say go!", "excited")
            time.sleep(1)
            speak("GO!", "happy")
            result = calibrate_user()
            speak(result, "happy")
            continue

        # Get LLM response
        update_status("Thinking")
        response, history = chat(user_input, history)

        # Procedural Animations based on text
        resp_text = response['response'].lower()
        if "hello" in resp_text or "hi " in resp_text or "bye" in resp_text or "goodbye" in resp_text:
            play_animation("wave")
        elif "kiss" in resp_text or "love you" in resp_text or "muah" in resp_text:
            play_animation("kiss")

        # Show emotion on avatar and speak
        update_emotion(response['emotion'])
        set_expression(response['emotion'])
        update_status("Speaking")
        
        def on_speak_start():
            print(f"Cyra [{response['emotion']}]: {response['response']}\n")
            from modules.dashboard import log_message
            log_message("cyra", response['response'])
            
        speak(response['response'], response['emotion'], on_playback_start=on_speak_start)
        
        # Save to long-term memory
        save_memory(f"User said: {user_input}")
        save_memory(f"Cyra said: {response['response']}")
        
        reset_expression()

        # Execute action if any
        if response.get('action'):
            print(f"[Action: {response['action']} | Params: {response.get('params')}]")
            result = handle_action(response['action'], response.get('params'))
            if result:
                print(f"[Result: {result}]")
                if response['action'] not in ["see_screen", "see_webcam"]:
                    speak(result, "neutral")

    return history

def cleanup():
    """Cleanup — always runs on exit."""
    print("[Cyra] Cleaning up...")
    try:
        from modules.browser_agent import close_browser
        close_browser()
    except:
        pass
    try:
        os.system("taskkill /f /im VSeeFace.exe >nul 2>&1")
        print("[VSeeFace] Closed.")
    except:
        pass

import atexit
atexit.register(cleanup)

def main():
    global running

    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        global running
        print("\n[Cyra] Ctrl+C detected, shutting down...")
        running = False
        cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    
    # Ensure VSeeFace closes when the console is closed (Windows specific)
    try:
        import win32api
        def console_ctrl_handler(ctrl_type):
            cleanup()
            return True
        win32api.SetConsoleCtrlHandler(console_ctrl_handler, True)
    except ImportError:
        pass

    # Start VSeeFace in BACKGROUND (don't block startup)
    vseeface_thread = threading.Thread(target=start_vseeface, daemon=True)
    vseeface_thread.start()

    print("=" * 50)
    print("  Cyra AI Assistant — Starting up...")
    print("=" * 50)

    # Start Telegram bot
    start_telegram_bot()

    # Start Dashboard
    from modules.dashboard import update_metrics
    import webbrowser
    start_dashboard()
    time.sleep(1)  # Reduced wait
    update_metrics()
    webbrowser.open("http://localhost:5000")

    # Start idle animation
    start_idle()

    # Start system tray in background
    tray_thread = threading.Thread(target=start_tray, daemon=True)
    tray_thread.start()

    # Greeting
    speak("Cyra is online! Say my name to wake me up~!", "excited")

    history = []
    from modules.avatar import set_sleeping
    from modules.greeting import get_dynamic_greeting

    # Main loop
    while running:
        print("\nSleeping... waiting for wake word...")
        try:
            set_sleeping(True)
            wait_for_wake_word()
            if running:
                history = active_mode(history)
        except Exception as e:
            print(f"[Error] {e}")
            time.sleep(1)

    cleanup()

if __name__ == "__main__":
    main()