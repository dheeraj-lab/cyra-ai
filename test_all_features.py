import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.agent import handle_action

def test_media():
    print("\n--- Testing Media ---")
    print(handle_action("play_song", "Lofi Hip Hop"))
    input("Press Enter once YouTube starts...")
    print(handle_action("media_play_pause", "pause"))
    input("Check if paused, then press Enter...")
    print(handle_action("media_play_pause", "play"))

def test_volume():
    print("\n--- Testing Volume ---")
    print(handle_action("volume_set", "20"))
    input("Check if volume is 20%, then press Enter...")
    print(handle_action("volume_up"))
    print(handle_action("volume_get"))

def test_apps():
    print("\n--- Testing Apps ---")
    print(handle_action("open_app", "notepad"))
    print(handle_action("open_app", "chrome"))
    print("Testing dynamic search for 'code'...")
    print(handle_action("open_app", "code"))

def test_vision():
    print("\n--- Testing Vision ---")
    print("Analyzing screen...")
    print(handle_action("see_screen", "What is visible on my screen right now?"))

def test_communication():
    print("\n--- Testing WhatsApp ---")
    print("Note: This requires WhatsApp Web to be logged in.")
    # print(handle_action("whatsapp", "Self|This is a test from Cyra!"))

if __name__ == "__main__":
    print("=" * 40)
    print("  Cyra Feature Testing Suite")
    print("=" * 40)
    print("1. Media & YouTube")
    print("2. Volume Control")
    print("3. App Opening (Dynamic)")
    print("4. Vision (Screen)")
    print("5. All of the above")
    
    choice = input("\nChoose a test (1-5): ")
    
    if choice == "1": test_media()
    elif choice == "2": test_volume()
    elif choice == "3": test_apps()
    elif choice == "4": test_vision()
    elif choice == "5":
        test_volume()
        test_apps()
        test_vision()
    
    print("\nTests completed!")
