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
        "show_desktop": "Showing desktop!",
        "minimize_all": "Minimizing all windows!",
        "peek_desktop": "Peeking at desktop!",
        "maximize": "Window maximized!",
        "minimize": "Window minimized!",
        "snap_left": "Snapped window to left!",
        "snap_right": "Snapped window to right!",
        "move_monitor_left": "Moved window to left monitor!",
        "move_monitor_right": "Moved window to right monitor!",
        "task_manager": "Opening Task Manager!",
        "task_view": "Opening Task View!",
        "file_explorer": "Opening File Explorer!",
        "settings": "Opening Settings!",
        "search": "Opening Search!",
        "run": "Opening Run dialog!",
        "quick_settings": "Opening Quick Settings!",
        "clipboard_history": "Opening clipboard history!",
        "undo": "Undone!",
        "redo": "Redone!",
        "copy": "Copied to clipboard!",
        "paste": "Pasted!",
        "cut": "Cut to clipboard!",
        "lock_screen": "Locking screen!",
        "project_screen": "Opening project settings!",
        "new_folder": "New folder created!",
        "rename": "Rename mode enabled!",
        "refresh": "Refreshed!",
        "properties": "Opening properties!",
        "switch_apps": "Switching apps!",
        "new_virtual_desktop": "New virtual desktop created!",
        "next_desktop": "Switched to next desktop!",
        "prev_desktop": "Switched to previous desktop!",
        "close_virtual_desktop": "Virtual desktop closed!",
        "parent_folder": "Navigating to parent folder!",
        "taskbar_1": "Opening taskbar app 1!",
        "taskbar_2": "Opening taskbar app 2!",
        "taskbar_3": "Opening taskbar app 3!",
        "taskbar_4": "Opening taskbar app 4!",
        "taskbar_5": "Opening taskbar app 5!",
        "scroll_up": "Scrolled up! ⬆️",
        "scroll_down": "Scrolled down! ⬇️",
        "close": "Window closed! ❌",
    }


    try:
        if action in actions:
            actions[action]()
            time.sleep(0.3)
            return action_messages.get(action, f"Action '{action}' completed!")

        else:
            return f"I don't know the action '{action}'!"

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
                return f"Maximized '{title}' window! ✨"

            else:
                return f"Could not find a window named '{title}'!"

        else:
            pyautogui.hotkey("win", "up")
            return "Maximized active window! ✨"

    except Exception as e:
        return f"Error maximizing: {str(e)}"


def close_window(title=None):
    """Close a specific window by title or the active one."""
    try:
        if title:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                win = windows[0]
                win.close()
                return f"Closed '{title}' window! ❌"

            else:
                return f"Could not find a window named '{title}'!"

        else:
            pyautogui.hotkey("alt", "f4")
            return "Closed active window! ❌"

    except Exception as e:
        return f"Error closing: {str(e)}"


def set_wallpaper(image_path):
    """Set Windows desktop wallpaper."""
    if not os.path.exists(image_path):
        return f"File not found: {image_path}"

    
    try:
        # SPI_SETDESKWALLPAPER = 0x0014
        # SPIF_UPDATEINIFILE = 0x01
        # SPIF_SENDWININICHANGE = 0x02
        ctypes.windll.user32.SystemParametersInfoW(0x0014, 0, image_path, 0x01 | 0x02)
        return "Wallpaper updated! How does it look? ✨"

    except Exception as e:
        return f"Could not change wallpaper: {str(e)}"