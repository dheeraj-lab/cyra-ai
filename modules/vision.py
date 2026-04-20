import ollama
import base64
import tempfile
import os
from datetime import datetime

def capture_screen():
    """Capture screen using PIL instead of pyautogui — more reliable."""
    from PIL import ImageGrab
    screenshot = ImageGrab.grab()
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp_path = tmp.name
    tmp.close()
    screenshot.save(tmp_path)
    return tmp_path

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def analyze_screen(question="What do you see on the screen?"):
    try:
        # Force garbage collection to clear any hanging COM pointers (pycaw, etc.)
        # This helps prevent the "access violation" crash on Windows.
        import gc
        gc.collect()
        
        screen_path = capture_screen()
        
        with open(screen_path, "rb") as f:
            image_data = f.read()
        
        response = ollama.chat(
            model="moondream",
            messages=[
                {
                    "role": "user",
                    "content": question,
                    "images": [image_data]
                }
            ]
        )
        
        os.unlink(screen_path)
        
        # Track usage
        try:
            from modules.stats import update_usage
            update_usage("vision_requests", 1)
        except:
            pass

        return response.message.content
        
    except Exception as e:
        return f"Screen dekh nahi paya: {str(e)}"

def analyze_webcam(question="What do you see?"):
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return "Webcam nahi mila!"
        
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp_path = tmp.name
        tmp.close()
        cv2.imwrite(tmp_path, frame)
        
        with open(tmp_path, "rb") as f:
            image_data = f.read()
        
        response = ollama.chat(
            model="moondream",
            messages=[
                {
                    "role": "user",
                    "content": question,
                    "images": [image_data]
                }
            ]
        )
        
        os.unlink(tmp_path)
        return response.message.content
        
    except Exception as e:
        return f"Webcam dekh nahi paya: {str(e)}"
    
def analyze_and_click(instruction):
    """Handle click/interaction instructions using OS-level shortcuts."""
    try:
        import pyautogui
        import time

        instruction_lower = instruction.lower()

        # Minimize all windows
        if "minimize all" in instruction_lower or "all windows" in instruction_lower:
            pyautogui.hotkey("win", "d")
            time.sleep(0.5)
            return "All windows minimized!"

        # Close window
        elif "close" in instruction_lower:
            pyautogui.hotkey("alt", "f4")
            return "Window closed!"

        # Minimize single window
        elif "minimize" in instruction_lower:
            pyautogui.hotkey("win", "down")
            return "Window minimized!"

        # Maximize window
        elif "maximize" in instruction_lower:
            pyautogui.hotkey("win", "up")
            return "Window maximized!"

        # Show desktop
        elif "show desktop" in instruction_lower or "desktop show" in instruction_lower:
            pyautogui.hotkey("win", "d")
            return "Desktop shown!"

        # Open apps via Windows search — reliable approach
        else:
            import re
            words = re.findall(r'\b\w+\b', instruction_lower)
            skip = ["click", "open", "the", "on", "icon", "taskbar", "please", "karo", "kholo", "kar", "do"]
            search_term = " ".join([w for w in words if w not in skip])
            
            if search_term.strip():
                pyautogui.hotkey("win", "s")
                time.sleep(1)
                pyautogui.hotkey("ctrl", "a")
                pyautogui.press("delete")
                pyautogui.write(search_term, interval=0.05)
                time.sleep(2)
                pyautogui.press("enter")
                return f"Searched and opened: {search_term}"
            else:
                return "Could not understand what to click!"

    except Exception as e:
        return f"Could not perform action: {str(e)}"