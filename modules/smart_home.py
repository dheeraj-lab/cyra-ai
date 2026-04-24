import tinytuya
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("TUYA_CLIENT_ID")
CLIENT_SECRET = os.getenv("TUYA_CLIENT_SECRET")
DEVICE_ID = os.getenv("TUYA_DEVICE_ID")

def get_cloud():
    cloud = tinytuya.Cloud(
        apiRegion="in",
        apiKey=CLIENT_ID,
        apiSecret=CLIENT_SECRET,
        apiDeviceID=DEVICE_ID
    )
    return cloud

def turn_on_bulb():
    try:
        cloud = get_cloud()
        result = cloud.sendcommand(DEVICE_ID, [{"code": "switch_led", "value": True}])
        return "Bulb turned on!"

    except Exception as e:
        return f"Could not turn on bulb: {str(e)}"


def turn_off_bulb():
    try:
        cloud = get_cloud()
        result = cloud.sendcommand(DEVICE_ID, [{"code": "switch_led", "value": False}])
        return "Bulb turned off!"

    except Exception as e:
        return f"Could not turn off bulb: {str(e)}"


def set_brightness(level):
    try:
        brightness = int((int(level) / 100) * 1000)
        cloud = get_cloud()
        result = cloud.sendcommand(DEVICE_ID, [
            {"code": "switch_led", "value": True},
            {"code": "bright_value_v2", "value": brightness}
        ])
        return f"Brightness set to {level}%!"

    except Exception as e:
        return f"Could not set brightness: {str(e)}"


def set_color(color):
    try:
        colors = {
            "red": (0, 255, 0),
            "green": (120, 255, 255),
            "blue": (240, 255, 255),
            "yellow": (60, 255, 255),
            "white": (0, 0, 255),
            "purple": (270, 255, 255),
            "orange": (30, 255, 255),
            "pink": (300, 255, 255),
        }
        
        color_lower = color.lower()
        if color_lower not in colors:
            return f"I don't know the color '{color}'! Try: red, green, blue, yellow, white, purple, orange, pink"

        
        h, s, v = colors[color_lower]
        cloud = get_cloud()
        result = cloud.sendcommand(DEVICE_ID, [
            {"code": "switch_led", "value": True},
            {"code": "work_mode", "value": "colour"},
            {"code": "colour_data_v2", "value": {"h": h, "s": s, "v": v}}
        ])
        return f"Bulb set to {color}!"

    except Exception as e:
        return f"Could not set color: {str(e)}"


def get_bulb_status():
    try:
        cloud = get_cloud()
        status = cloud.getstatus(DEVICE_ID)
        
        is_on = False
        brightness = 0
        
        for item in status.get("result", []):
            if item["code"] == "switch_led":
                is_on = item["value"]
            elif item["code"] == "bright_value_v2":
                brightness = round((item["value"] / 1000) * 100)
        
        return f"The bulb is {'on' if is_on else 'off'} with {brightness}% brightness!"

    except Exception as e:
        return f"Could not get status: {str(e)}"