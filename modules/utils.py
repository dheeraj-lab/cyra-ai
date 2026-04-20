import os
import subprocess

_app_path_cache = {}

def find_app_path(app_name):
    """Dynamic search for app path using Start Menu shortcuts and common locations."""
    app_name_lower = app_name.lower()
    
    if app_name_lower in _app_path_cache:
        path = _app_path_cache[app_name_lower]
        if os.path.exists(path):
            return path

    # Hardcoded Common Paths
    apps = {
        "brave": [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), r"BraveSoftware\Brave-Browser\Application\brave.exe"),
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        ],
        "chrome": [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe"),
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ],
        "firefox": [r"C:\Program Files\Mozilla Firefox\firefox.exe"],
        "vs code": [os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Programs\Microsoft VS Code\Code.exe")],
        "discord": [os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Discord\Update.exe")],
        "spotify": [os.path.join(os.environ.get("APPDATA", ""), r"Spotify\Spotify.exe")],
    }
    
    if app_name_lower in apps:
        for path in apps[app_name_lower]:
            if os.path.exists(path):
                _app_path_cache[app_name_lower] = path
                return path

    # Search Start Menu
    start_menu_paths = [
        os.path.join(os.environ.get("ProgramData", ""), r"Microsoft\Windows\Start Menu\Programs"),
        os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs")
    ]
    
    try:
        from win32com.client import Dispatch
        shell = Dispatch('WScript.Shell')
        for base_path in start_menu_paths:
            if not os.path.exists(base_path): continue
            for root, dirs, files in os.walk(base_path):
                for file in files:
                    if file.lower().endswith(".lnk") and app_name_lower in file.lower():
                        try:
                            shortcut = shell.CreateShortCut(os.path.join(root, file))
                            target = shortcut.Targetpath
                            if target and os.path.exists(target) and target.lower().endswith(".exe"):
                                _app_path_cache[app_name_lower] = target
                                return target
                        except: continue
    except: pass

    # CLI tools
    try:
        result = subprocess.run(["where", app_name], capture_output=True, text=True)
        if result.returncode == 0:
            path = result.stdout.splitlines()[0]
            _app_path_cache[app_name_lower] = path
            return path
    except: pass

    return None
