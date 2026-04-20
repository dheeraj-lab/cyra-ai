from pythonosc import udp_client
import time
import threading
import math
import random

VMC_IP = "127.0.0.1"
VMC_PORT = 39540

client = udp_client.SimpleUDPClient(VMC_IP, VMC_PORT)

EMOTION_EXPRESSIONS = {
    "neutral":   "Neutral",
    "happy":     "joy",
    "excited":   "Fun",
    "sad":       "Sorrow",
    "curious":   "smile",
    "concerned": "Sorrow",
    "angry":     "Angry",
    "surprised": "Surprised",
}

ALL_EXPRESSIONS = ["Joy", "Angry", "Sorrow", "Fun", "Surprised", "Neutral", "smile"]

idle_running = False
idle_thread = None
current_expression = "Neutral"
is_sleeping = False

excitement_timer = 0.0
current_anim = "idle"
anim_timer = 0.0

def play_animation(anim_name):
    global current_anim, anim_timer
    current_anim = anim_name
    anim_timer = 0.0

def set_sleeping(state):
    global is_sleeping
    is_sleeping = state

def set_expression(emotion="neutral"):
    global current_expression, excitement_timer
    try:
        expr = EMOTION_EXPRESSIONS.get(emotion, "Neutral")
        
        # Trigger excitement bounce if happy/excited!
        if emotion in ["happy", "excited"]:
            excitement_timer = 1.5 # 1.5 seconds of rapid bouncing
            
        if expr == current_expression:
            return True
            
        # Smooth transition: fade out old, fade in new (Max intensity 0.6)
        for i in range(10):
            progress = (i + 1) / 10.0
            for e in ALL_EXPRESSIONS:
                if e != expr:
                    client.send_message("/VMC/Ext/Blend/Val", [e, 0.6 * (1.0 - progress)])
            client.send_message("/VMC/Ext/Blend/Val", [expr, 0.6 * progress])
            client.send_message("/VMC/Ext/Blend/Apply", [])
            time.sleep(0.03)
            
        current_expression = expr
        return True
    except Exception as e:
        return False

def reset_expression():
    set_expression("neutral")

def idle_animation():
    global idle_running, is_sleeping, excitement_timer
    t = 0
    blink_timer = 0
    
    # Trackers
    target_eye_x, target_eye_y = 0.0, 0.0
    current_eye_x, current_eye_y = 0.0, 0.0
    eye_dart_timer = 0
    sleep_weight = 0.0 # Smooth transition variable
    
    while idle_running:
        try:
            # Smoothly transition between awake (0.0) and asleep (1.0)
            target_sleep = 1.0 if is_sleeping else 0.0
            sleep_weight += (target_sleep - sleep_weight) * 0.05
            
            # 1. Head & Neck Smooth Blending
            wake_head_y = math.sin(t * 0.6) * 0.04
            wake_head_x = math.sin(t * 0.3) * 0.02
            
            sleep_head_y = math.sin(t * 0.4) * 0.02
            sleep_head_x = 0.15 + math.sin(t * 0.2) * 0.015 # Tilted forward with slight natural sway
            
            head_y = wake_head_y * (1.0 - sleep_weight) + sleep_head_y * sleep_weight
            head_x = wake_head_x * (1.0 - sleep_weight) + sleep_head_x * sleep_weight
            
            cy, sy = math.cos(head_y), math.sin(head_y)
            cp, sp = math.cos(head_x), math.sin(head_x)
            client.send_message("/VMC/Ext/Bone/Pos",
                ["Head", 0.0, 0.0, 0.0, cy*sp, sy*cp, -sy*sp, cy*cp])

            # 2. Natural Body Animation + Isolated Boob Wiggle
            
            # Slow, natural breathing on Spine and Chest
            breath = math.sin(t * 1.5) * 0.008
            sleep_breath = math.sin(t * 1.0) * 0.012
            final_breath = breath * (1.0 - sleep_weight) + sleep_breath * sleep_weight
            
            # Gentle chest tilt for breathing
            chest_pitch = math.sin(t * 1.5) * 0.02 * (1.0 - sleep_weight)
            sp_chest = math.sin(chest_pitch / 2.0)
            cp_chest = math.cos(chest_pitch / 2.0)
            
            client.send_message("/VMC/Ext/Bone/Pos",
                ["Spine", 0.0, final_breath, 0.0, 0.0, 0.0, 0.0, 1.0])
            client.send_message("/VMC/Ext/Bone/Pos",
                ["Chest", 0.0, final_breath * 0.5, 0.0, sp_chest, 0.0, 0.0, cp_chest])
                
            # Isolated Boob Wiggle (Targets VRM SpringBones directly without moving torso)
            wiggle = math.sin(t * 16.0) * 0.05 + math.sin(t * 10.0) * 0.03
            wiggle_pitch = wiggle * (1.0 - sleep_weight)
            sp_bust = math.sin(wiggle_pitch / 2.0)
            cp_bust = math.cos(wiggle_pitch / 2.0)
            
            # Send to common VRoid/VRM breast bone names
            for bust_bone in ["J_Sec_L_Bust1", "J_Sec_R_Bust1", "J_Sec_L_Bust2", "J_Sec_R_Bust2"]:
                client.send_message("/VMC/Ext/Bone/Pos",
                    [bust_bone, 0.0, 0.0, 0.0, sp_bust, 0.0, 0.0, cp_bust])

            # 3. Eyes & Blinking
            if sleep_weight > 0.95:
                # Fully asleep
                client.send_message("/VMC/Ext/Blend/Val", ["Blink", 1.0])
                client.send_message("/VMC/Ext/Blend/Apply", [])
                current_eye_x += (0.0 - current_eye_x) * 0.1
                current_eye_y += (0.0 - current_eye_y) * 0.1
            else:
                # Awake: Eye darting
                eye_dart_timer += 0.05
                if eye_dart_timer > random.uniform(1.5, 4.0):
                    target_eye_x = random.uniform(-0.4, 0.4)
                    target_eye_y = random.uniform(-0.2, 0.3)
                    if random.random() > 0.5:
                        target_eye_x, target_eye_y = 0.0, 0.0
                    eye_dart_timer = 0
                    
                current_eye_x += (target_eye_x - current_eye_x) * 0.2
                current_eye_y += (target_eye_y - current_eye_y) * 0.2
                
                # Smart blinking
                blink_timer += 0.05
                if blink_timer > random.uniform(2.5, 5.0) and sleep_weight < 0.1:
                    client.send_message("/VMC/Ext/Blend/Val", ["Blink", 1.0])
                    client.send_message("/VMC/Ext/Blend/Apply", [])
                    time.sleep(0.08)
                    client.send_message("/VMC/Ext/Blend/Val", ["Blink", 0.0])
                    client.send_message("/VMC/Ext/Blend/Apply", [])
                    blink_timer = 0
                elif sleep_weight > 0.0:
                    client.send_message("/VMC/Ext/Blend/Val", ["Blink", sleep_weight])
                    client.send_message("/VMC/Ext/Blend/Apply", [])

            client.send_message("/VMC/Ext/Blend/Val", ["LookLeft", max(0, current_eye_x)])
            client.send_message("/VMC/Ext/Blend/Val", ["LookRight", max(0, -current_eye_x)])
            client.send_message("/VMC/Ext/Blend/Val", ["LookUp", max(0, current_eye_y)])
            client.send_message("/VMC/Ext/Blend/Val", ["LookDown", max(0, -current_eye_y)])
            client.send_message("/VMC/Ext/Blend/Apply", [])

            # 4. Arms & Procedural Animations
            global current_anim, anim_timer
            anim_timer += 0.033
            
            # Default Sexy/Relaxed Pose
            left_up = [0.05, 0.0, 0.6, 0.8]
            right_up = [0.05, 0.0, -0.6, 0.8]
            left_low = [0.0, -0.3, 0.0, 0.95]
            right_low = [0.0, 0.3, 0.0, 0.95]
            
            if current_anim == "wave":
                if anim_timer > 2.5:
                    current_anim = "idle"
                else:
                    # Right arm up and waving
                    right_up = [0.0, 0.0, 0.6, 0.8] # Arm extended
                    right_low = [0.0, 0.0, 0.6, 0.8] # Elbow bent up
                    wave_tilt = math.sin(anim_timer * 15.0) * 0.4
                    client.send_message("/VMC/Ext/Bone/Pos", ["RightHand", 0.0, 0.0, 0.0, 0.0, 0.0, wave_tilt, 0.9])
                    
            elif current_anim == "kiss":
                if anim_timer > 2.5:
                    current_anim = "idle"
                else:
                    if anim_timer < 1.0:
                        # Hand near mouth
                        right_up = [0.3, 0.0, 0.2, 0.9]
                        right_low = [0.6, 0.0, 0.0, 0.8]
                    else:
                        # Throw kiss (arm extends outward)
                        right_up = [0.2, 0.0, -0.4, 0.9]
                        right_low = [0.0, 0.0, 0.0, 1.0]

            client.send_message("/VMC/Ext/Bone/Pos", ["LeftUpperArm", 0.0, 0.0, 0.0] + left_up)
            client.send_message("/VMC/Ext/Bone/Pos", ["RightUpperArm", 0.0, 0.0, 0.0] + right_up)
            client.send_message("/VMC/Ext/Bone/Pos", ["LeftLowerArm", 0.0, 0.0, 0.0] + left_low)
            client.send_message("/VMC/Ext/Bone/Pos", ["RightLowerArm", 0.0, 0.0, 0.0] + right_low)

            t += 0.05
            time.sleep(0.033)
        except Exception as e:
            time.sleep(0.1)

def start_idle():
    global idle_running, idle_thread
    if idle_running: return
    idle_running = True
    idle_thread = threading.Thread(target=idle_animation, daemon=True)
    idle_thread.start()

def stop_idle():
    global idle_running
    idle_running = False