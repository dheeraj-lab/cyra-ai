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
            return

    subprocess.Popen([vseeface_path])
    print("[VSeeFace] Starting... (auto-loads last avatar)")
    time.sleep(8)  # Wait for VSeeFace to fully load its UI

    try:
        import pyautogui
        import pygetwindow as gw
        import ctypes
        
        # Tell Windows we are DPI aware
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except:
            pass
            
        # Step 1: Find VSeeFace window (it cannot be maximized, so we must find its exact position)
        windows = gw.getWindowsWithTitle("VSeeFace")
        if windows:
            # Sort by size to ensure we get the real window, not a background process
            windows = sorted(windows, key=lambda w: w.width * w.height, reverse=True)
            win = windows[0]
            
            win.activate()
            time.sleep(1)
            
            # Step 2: Calculate Start button position
            # The start button is exactly in the horizontal middle, near the bottom edge.
            target_x = win.left + (win.width // 2)
            # Subtracting 155 pixels pushes the cursor slightly down from the previous edit
            target_y = win.bottom - 155
            
            # Move cursor visibly so user can see it
            pyautogui.moveTo(target_x, target_y, duration=1.0)
            time.sleep(0.5)
            pyautogui.click()
            pyautogui.click()
            pyautogui.press('enter')
            
            print(f"[VSeeFace] Clicked Start button at ({target_x}, {target_y})!")
            time.sleep(4) # Wait for tracking to initialize
            
            # Step 3: Move to second monitor
            pyautogui.hotkey('win', 'shift', 'right')
            time.sleep(1)
            pyautogui.hotkey('win', 'up') # Maximize on second screen (tracking screen IS resizable)
            print("[VSeeFace] Moved to Monitor 2 and maximized!")
        else:
            print("[VSeeFace] Could not find window to click.")
            
    except Exception as e:
        print(f"[VSeeFace] Could not auto-start: {e}")

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
    from modules.avatar import set_sleeping
    set_sleeping(False)
    update_status("Speaking")
    speak("Hmm? You called~?", "curious")

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

        # Get LLM response
        update_status("Thinking")
        response, history = chat(user_input, history)
        print(f"Cyra [{response['emotion']}]: {response['response']}\n")

        # Procedural Animations based on text
        from modules.avatar import play_animation
        resp_text = response['response'].lower()
        if "hello" in resp_text or "hi " in resp_text or "bye" in resp_text or "goodbye" in resp_text:
            play_animation("wave")
        elif "kiss" in resp_text or "love you" in resp_text or "muah" in resp_text:
            play_animation("kiss")

        # Show emotion on avatar and speak
        set_expression(response['emotion'])
        update_status("Speaking")
        speak(response['response'], response['emotion'])
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

# ==================== Main ====================

def main():
    global running

    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        global running
        print("\n[Cyra] Ctrl+C detected, shutting down...")
        running = False
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Start VSeeFace
    start_vseeface()

    print("=" * 50)
    print("  Cyra AI Assistant — Starting up...")
    print("=" * 50)

    # Start Telegram bot
    start_telegram_bot()

    # Start Dashboard
    from modules.dashboard import update_metrics
    import webbrowser
    start_dashboard()
    time.sleep(2) # Wait for server to stabilize
    update_metrics()
    webbrowser.open("http://localhost:5000")

    # Start idle animation
    start_idle()

    # Start system tray in background
    tray_thread = threading.Thread(target=start_tray, daemon=True)
    tray_thread.start()

    # Greeting
    speak("Ehehe~ Cyra is online! Say my name to wake me up~!", "excited")

    history = []
    from modules.avatar import set_sleeping

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

    # Cleanup
    print("[Cyra] Goodbye~!")
    try:
        from modules.browser_agent import close_browser
        close_browser()
    except:
        pass
        
    try:
        # Close VSeeFace process
        import os
        os.system("taskkill /f /im VSeeFace.exe >nul 2>&1")
        print("[VSeeFace] Closed.")
    except:
        pass

if __name__ == "__main__":
    main()