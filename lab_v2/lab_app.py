import customtkinter as ctk
from PIL import Image, ImageTk
import os
import time
import sys
import threading
from engine import LabEngine

# We no longer import direct modules here to keep lab_app clean

# System Settings
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class CyraLabApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Cyra Lab V2 | Virtual Avatar Studio")
        self.geometry("1100x750")

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar (Settings) ---
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar, text="LAB V2", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Lighting Section
        self.light_label = ctk.CTkLabel(self.sidebar, text="LIGHTING SETTINGS", font=ctk.CTkFont(size=12, weight="bold"))
        self.light_label.grid(row=1, column=0, padx=20, pady=(20, 5), sticky="w")

        self.light_intensity = ctk.CTkSlider(self.sidebar, from_=0, to=100)
        self.light_intensity.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.light_intensity.set(80)

        self.light_color = ctk.CTkOptionMenu(self.sidebar, values=["White", "Cyan", "Pink", "Golden"])
        self.light_color.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # Expressions Section
        self.exp_label = ctk.CTkLabel(self.sidebar, text="EXPRESSIONS", font=ctk.CTkFont(size=12, weight="bold"))
        self.exp_label.grid(row=4, column=0, padx=20, pady=(20, 5), sticky="w")

        self.btn_happy = ctk.CTkButton(self.sidebar, text="HAPPY", fg_color="#ff007f", command=lambda: self.change_expression("happy"))
        self.btn_happy.grid(row=5, column=0, padx=20, pady=5, sticky="ew")

        self.btn_sad = ctk.CTkButton(self.sidebar, text="SAD", fg_color="#7000ff", command=lambda: self.change_expression("sad"))
        self.btn_sad.grid(row=6, column=0, padx=20, pady=5, sticky="ew")

        self.btn_angry = ctk.CTkButton(self.sidebar, text="ANGRY", fg_color="#ff4444", command=lambda: self.change_expression("angry"))
        self.btn_angry.grid(row=7, column=0, padx=20, pady=5, sticky="ew")

        # Connectivity Monitor
        self.conn_label = ctk.CTkLabel(self.sidebar, text="CONNECTIVITY LOGS", font=ctk.CTkFont(size=12, weight="bold"))
        self.conn_label.grid(row=8, column=0, padx=20, pady=(40, 5), sticky="w")

        self.log_box = ctk.CTkTextbox(self.sidebar, height=150, font=ctk.CTkFont(size=10))
        self.log_box.grid(row=9, column=0, padx=20, pady=10, sticky="ew")
        self.log_box.insert("0.0", "Cyra Lab v2.0\nReady to Initialize...\n")

        # Start Cyra Engine Button
        self.btn_start = ctk.CTkButton(self.sidebar, text="INITIALIZE CYRA", fg_color="green", command=self.start_cyra_thread)
        self.btn_start.grid(row=10, column=0, padx=20, pady=20, sticky="ew")

        # --- Main Viewport (3D Area) ---
        self.viewport = ctk.CTkFrame(self, fg_color="#0d0221")
        self.viewport.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.viewport.grid_rowconfigure(0, weight=1)
        self.viewport.grid_columnconfigure(0, weight=1)

        # Character Image (Simulating 3D Viewport)
        try:
            # Find the generated image path (most recent)
            img_path = r"C:\Users\dheer\.gemini\antigravity\brain\dfa15693-730a-4f5e-a9a2-8491645289c3\lab_default_avatar_1776736465154.png"
            img_data = Image.open(img_path)
            self.avatar_img = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(600, 600))
            self.avatar_label = ctk.CTkLabel(self.viewport, image=self.avatar_img, text="")
            self.avatar_label.grid(row=0, column=0, sticky="nsew")
        except Exception as e:
            print(f"Error loading image: {e}")
            self.avatar_label = ctk.CTkLabel(self.viewport, text="3D VIEWPORT ERROR\nImage not found", font=ctk.CTkFont(size=20))
            self.avatar_label.grid(row=0, column=0)

        # Status Bar
        self.status_bar = ctk.CTkLabel(self, text="Ready | FPS: 60 | Mode: Experimental", anchor="w", padx=20)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

        # --- Engine Initialization ---
        self.engine = LabEngine(self.log)

    def change_expression(self, exp):
        timestamp = time.strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{timestamp}] Expression -> {exp.upper()}\n")
        self.log_box.see("end")
        # For now, expression is just logged in the lab
        # But we could import set_expression inside the engine if needed

    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{timestamp}] {message}\n")
        self.log_box.see("end")

    def start_cyra_thread(self):
        self.btn_start.configure(state="disabled", text="RUNNING...")
        self.log("Initializing Lab Engine...")
        threading.Thread(target=self.run_cyra_loop, daemon=True).start()

    def run_cyra_loop(self):
        while True:
            response, user_input = self.engine.process_input()
            
            if not response:
                continue

            # Update UI & Speak
            self.change_expression(response['emotion'])
            
            if response['action']:
                self.log(f"Action: {response['action']}")
            
            self.engine.speak_response(response['response'], response['emotion'])

if __name__ == "__main__":
    app = CyraLabApp()
    app.mainloop()
