from pythonosc import udp_client
import time

client = udp_client.SimpleUDPClient("127.0.0.1", 39539)

# Common VRM blendshape names try karo
expressions = [
    "Joy", "Angry", "Sorrow", "Fun", "Surprised",
    "happy", "angry", "sad", "surprised", "neutral",
    "A", "I", "U", "E", "O",
    "Blink", "Blink_L", "Blink_R"
]

for expr in expressions:
    print(f"Trying: {expr}")
    client.send_message("/VMC/Ext/Blend/Val", [expr, 1.0])
    client.send_message("/VMC/Ext/Blend/Apply", [])
    time.sleep(1)
    client.send_message("/VMC/Ext/Blend/Val", [expr, 0.0])
    client.send_message("/VMC/Ext/Blend/Apply", [])
    time.sleep(0.5)