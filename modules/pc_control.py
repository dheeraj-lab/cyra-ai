import pyautogui
import subprocess
import time
import ctypes
import os
import pygetwindow as gw

def pc_control(action):
    actions = {
        # Desktop
        "show_desktop": lambda: pyautogui.hotkey("win", "d"),
        "minimize_all": lambda: pyautogui.hotkey("win", "m"),
        "peek_desktop": lambda: pyautogui.hotkey("win", ","),

        # Window management
        "maximize": lambda: pyautogui.hotkey("win", "up"),
        "minimize": lambda: pyautogui.hotkey("win", "down"),
        "snap_left": lambda: pyautogui.hotkey("win", "left"),
        "snap_right": lambda: pyautogui.hotkey("win", "right"),
        "move_monitor_left": lambda: pyautogui.hotkey("win", "shift", "left"),
        "move_monitor_right": lambda: pyautogui.hotkey("win", "shift", "right"),

        # Apps
        "task_manager": lambda: pyautogui.hotkey("ctrl", "shift", "esc"),
        "task_view": lambda: pyautogui.hotkey("win", "tab"),
        "file_explorer": lambda: pyautogui.hotkey("win", "e"),
        "settings": lambda: pyautogui.hotkey("win", "i"),
        "search": lambda: pyautogui.hotkey("win", "s"),
        "run": lambda: pyautogui.hotkey("win", "r"),
        "quick_settings": lambda: pyautogui.hotkey("win", "a"),

        # Clipboard
        "clipboard_history": lambda: pyautogui.hotkey("win", "v"),
        "undo": lambda: pyautogui.hotkey("ctrl", "z"),
        "redo": lambda: pyautogui.hotkey("ctrl", "y"),
        "copy": lambda: pyautogui.hotkey("ctrl", "c"),
        "paste": lambda: pyautogui.hotkey("ctrl", "v"),
        "cut": lambda: pyautogui.hotkey("ctrl", "x"),

        # System
        "lock_screen": lambda: pyautogui.hotkey("win", "l"),
        "project_screen": lambda: pyautogui.hotkey("win", "p"),
        "new_folder": lambda: pyautogui.hotkey("ctrl", "shift", "n"),
        "rename": lambda: pyautogui.press("f2"),
        "refresh": lambda: pyautogui.press("f5"),
        "properties": lambda: pyautogui.hotkey("alt", "enter"),
        "switch_apps": lambda: pyautogui.hotkey("alt", "tab"),

        # Virtual desktops
        "new_virtual_desktop": lambda: pyautogui.hotkey("win", "ctrl", "d"),
        "next_desktop": lambda: pyautogui.hotkey("win", "ctrl", "right"),
        "prev_desktop": lambda: pyautogui.hotkey("win", "ctrl", "left"),
        "close_virtual_desktop": lambda: pyautogui.hotkey("win", "ctrl", "f4"),

        # File explorer
        "parent_folder": lambda: pyautogui.hotkey("alt", "up"),

        # Taskbar apps
        "taskbar_1": lambda: pyautogui.hotkey("win", "1"),
        "taskbar_2": lambda: pyautogui.hotkey("win", "2"),
        "taskbar_3": lambda: pyautogui.hotkey("win", "3"),
        "taskbar_4": lambda: pyautogui.hotkey("win", "4"),
        "taskbar_5": lambda: pyautogui.hotkey("win", "5"),
        
        # Scrolling
        "scroll_up": lambda: pyautogui.scroll(500),
        "scroll_down": lambda: pyautogui.scroll(-500),
        "close": lambda: pyautogui.hotkey("alt", "f4"),
    }

    action_messages = {
        "show_desktop": "Desktop show kar diya!",
        "minimize_all": "Sab windows minimize kar diye!",
        "peek_desktop": "Desktop peek kar rahi hoon!",
        "maximize": "Window maximize kar diya!",
        "minimize": "Window minimize kar diya!",
        "snap_left": "Window left snap kar diya!",
        "snap_right": "Window right snap kar diya!",
        "move_monitor_left": "Window left monitor pe move kar diya!",
        "move_monitor_right": "Window right monitor pe move kar diya!",
        "task_manager": "Task Manager khol diya!",
        "task_view": "Task View khol diya!",
        "file_explorer": "File Explorer khol diya!",
        "settings": "Settings khol di!",
        "search": "Search khol diya!",
        "run": "Run dialog khol diya!",
        "quick_settings": "Quick Settings khol di!",
        "clipboard_history": "Clipboard history khol di!",
        "undo": "Undo kar diya!",
        "redo": "Redo kar diya!",
        "copy": "Copy kar diya!",
        "paste": "Paste kar diya!",
        "cut": "Cut kar diya!",
        "lock_screen": "Screen lock kar diya!",
        "project_screen": "Project screen khol diya!",
        "new_folder": "Naya folder banaya!",
        "rename": "Rename mode on!",
        "refresh": "Refresh kar diya!",
        "properties": "Properties khol di!",
        "switch_apps": "Apps switch kar rahi hoon!",
        "new_virtual_desktop": "Naya virtual desktop banaya!",
        "next_desktop": "Next desktop pe gayi!",
        "prev_desktop": "Previous desktop pe gayi!",
        "close_virtual_desktop": "Virtual desktop band kar diya!",
        "parent_folder": "Parent folder pe gayi!",
        "taskbar_1": "Taskbar app 1 open kar diya!",
        "taskbar_2": "Taskbar app 2 open kar diya!",
        "taskbar_3": "Taskbar app 3 open kar diya!",
        "taskbar_4": "Taskbar app 4 open kar diya!",
        "taskbar_5": "Taskbar app 5 open kar diya!",
        "scroll_up": "Upar scroll kar diya! ⬆️",
        "scroll_down": "Neeche scroll kar diya! ⬇️",
        "close": "Window band kar di! ❌",
    }

    try:
        if action in actions:
            actions[action]()
            time.sleep(0.3)
            return action_messages.get(action, f"{action} kar diya!")
        else:
            return f"Action '{action}' nahi pata!"
    except Exception as e:
        return f"Error: {str(e)}"

def maximize_window(title=None):
    """Maximize a specific window by title or the active one."""
    try:
        if title:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                win = windows[0]
                if win.isMinimized:
                    win.restore()
                win.maximize()
                win.activate()
                return f"'{title}' window maximize kar di! ✨"
            else:
                return f"'{title}' naam ki koi window nahi mili!"
        else:
            pyautogui.hotkey("win", "up")
            return "Active window maximize kar di! ✨"
    except Exception as e:
        return f"Maximize karne mein error: {str(e)}"

def close_window(title=None):
    """Close a specific window by title or the active one."""
    try:
        if title:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                win = windows[0]
                win.close()
                return f"'{title}' window band kar di! ❌"
            else:
                return f"'{title}' naam ki koi window nahi mili!"
        else:
            pyautogui.hotkey("alt", "f4")
            return "Active window band kar di! ❌"
    except Exception as e:
        return f"Close karne mein error: {str(e)}"

def set_wallpaper(image_path):
    """Set Windows desktop wallpaper."""
    if not os.path.exists(image_path):
        return f"File nahi mili: {image_path}"
    
    try:
        # SPI_SETDESKWALLPAPER = 0x0014
        # SPIF_UPDATEINIFILE = 0x01
        # SPIF_SENDWININICHANGE = 0x02
        ctypes.windll.user32.SystemParametersInfoW(0x0014, 0, image_path, 0x01 | 0x02)
        return "Wallpaper change kar diya! Kaisa lag raha hai? ✨"
    except Exception as e:
        return f"Wallpaper change nahi hua: {str(e)}"