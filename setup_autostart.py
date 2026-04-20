import os
import shutil
import subprocess

CYRA_DIR = os.path.dirname(os.path.abspath(__file__))
BAT_FILE = os.path.join(CYRA_DIR, "start_cyra.bat")
PNG_ICON = os.path.join(CYRA_DIR, "icon.png")
ICO_ICON = os.path.join(CYRA_DIR, "icon.ico")

def ensure_ico():
    """Convert icon.png to icon.ico if needed."""
    if os.path.exists(PNG_ICON) and not os.path.exists(ICO_ICON):
        try:
            from PIL import Image
            img = Image.open(PNG_ICON)
            # Save as ico
            img.save(ICO_ICON, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
            print(f"[OK] Converted {PNG_ICON} to {ICO_ICON}")
        except Exception as e:
            print(f"[Warn] Could not convert icon: {e}")

def create_shortcut_vbs(shortcut_path, target_path, icon_path=None):
    """Create a Windows shortcut (.lnk) using VBScript."""
    vbs_path = os.path.join(CYRA_DIR, "create_shortcut.vbs")
    
    icon_line = f'oShortcut.IconLocation = "{icon_path}"' if icon_path and os.path.exists(icon_path) else ""
    
    vbs_content = f'''
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{shortcut_path}"
Set oShortcut = oWS.CreateShortcut(sLinkFile)
oShortcut.TargetPath = "{target_path}"
oShortcut.WorkingDirectory = "{CYRA_DIR}"
oShortcut.Description = "Cyra AI Assistant"
{icon_line}
oShortcut.Save
'''
    with open(vbs_path, "w") as f:
        f.write(vbs_content)
    
    subprocess.run(["cscript", "/nologo", vbs_path], capture_output=True)
    os.remove(vbs_path)

def add_to_startup():
    """Add Cyra to Windows startup folder."""
    # First, remove any existing old entries to prevent double startup
    remove_from_startup()
    
    startup_dir = os.path.join(
        os.environ["APPDATA"],
        r"Microsoft\Windows\Start Menu\Programs\Startup"
    )

    shortcut_path = os.path.join(startup_dir, "Cyra AI.lnk")
    
    ensure_ico()
    icon_to_use = ICO_ICON if os.path.exists(ICO_ICON) else None
    
    create_shortcut_vbs(shortcut_path, BAT_FILE, icon_to_use)
    print(f"[OK] Added to startup: {shortcut_path}")

def create_desktop_shortcut():
    """Create a desktop shortcut for Cyra."""
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    shortcut_path = os.path.join(desktop, "Cyra AI.lnk")

    ensure_ico()
    icon_to_use = ICO_ICON if os.path.exists(ICO_ICON) else None

    create_shortcut_vbs(shortcut_path, BAT_FILE, icon_to_use)
    print(f"[OK] Desktop shortcut created: {shortcut_path}")

def remove_from_startup():
    """Remove Cyra from startup."""
    startup_dir = os.path.join(
        os.environ["APPDATA"],
        r"Microsoft\Windows\Start Menu\Programs\Startup"
    )
    shortcut_path = os.path.join(startup_dir, "Cyra AI.lnk")
    old_shortcut_path = os.path.join(startup_dir, "Cyra AI.bat")

    for p in [shortcut_path, old_shortcut_path]:
        if os.path.exists(p):
            os.remove(p)
            print(f"[OK] Removed: {p}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--remove":
        remove_from_startup()
    else:
        print("=" * 40)
        print("  Cyra Setup")
        print("=" * 40)
        add_to_startup()
        create_desktop_shortcut()
        print("\nDone! You can now:")
        print("  - Double-click 'Cyra AI' on Desktop")
        print("  - Cyra will auto-start with Windows")
        print("\nTo remove auto-start: python setup_autostart.py --remove")
