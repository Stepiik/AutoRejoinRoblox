import os
import time
from datetime import datetime
import tkinter as tk
from threading import Thread
import psutil
import pyautogui

CONFIDENCE_LEVEL = 0.85

class UniversalAutoRejoin:
    def __init__(self, root):
        self.root = root
        self.root.title("Universal Roblox Auto-Rejoin")
        self.root.geometry("450x350")
        self.root.configure(bg="#1e1e1e")
        
        # Position in the top-right corner of the screen
        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"450x350+{screen_width - 470}+50")
        self.root.attributes("-topmost", True)
        
        # Top panel (Title / Status)
        self.title_label = tk.Label(
            root, text="🛡️ AUTO-REJOIN SYSTEM", 
            bg="#1e1e1e", fg="#00ffcc", font=("Segoe UI", 11, "bold")
        )
        self.title_label.pack(pady=(10, 5))

        # Log window (console in GUI)
        self.log_frame = tk.Frame(root, bg="#2d2d2d", bd=1, relief=tk.SOLID)
        self.log_frame.pack(expand=True, fill=tk.BOTH, padx=12, pady=5)

        self.log_text = tk.Text(
            self.log_frame, wrap=tk.WORD, bg="#111111", fg="#00ff66", 
            font=("Consolas", 9), insertbackground="white", bd=0, highlightthickness=0
        )
        self.log_text.pack(expand=True, fill=tk.BOTH, padx=8, pady=8)
        self.log_text.config(state=tk.DISABLED)

        # Bottom status bar
        self.status_label = tk.Label(
            root, text="Status: Waiting for disconnect...", 
            bg="#1e1e1e", fg="#aaaaaa", font=("Segoe UI", 8)
        )
        self.status_label.pack(pady=(5, 10))

        # Default settings
        self.join_url = "roblox://placeID=2753915549"
        self.check_interval = 5
        self.load_delay = 30

        # Start console setup and monitoring thread
        self.setup_console()
        self.start_monitoring()

    def log(self, message):
        now = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{now}] {message}\n"
        print(f"[{now}] {message}")
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, formatted_msg)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def setup_console(self):
        print("=== UNIVERSAL AUTO-REJOIN SETUP ===")
        print("1 - Normal Mode (Enter Game Place ID)")
        print("2 - Private / VIP Server (via link)")
        choice = input("Select mode (1 or 2): ").strip()

        if choice == "2":
            vip_link = input("Paste VIP server link: ").strip()
            if "placeID=" in vip_link and "privateServerLinkCode=" in vip_link:
                try:
                    place_id = vip_link.split("placeID=")[1].split("&")[0]
                    code = vip_link.split("privateServerLinkCode=")[1].split("&")[0]
                    self.join_url = f"roblox://placeID={place_id}&linkCode={code}"
                except Exception:
                    print("Error parsing link, using default.")
            else:
                print("Invalid link, using default.")
        else:
            place_id = input("Enter Game Place ID (e.g., 2753915549 for Blox Fruits): ").strip()
            if place_id.isdigit():
                self.join_url = f"roblox://placeID={place_id}"

        try:
            self.check_interval = int(input("Check interval in seconds (default 5): ").strip() or "5")
        except ValueError:
            self.check_interval = 5

        try:
            self.load_delay = int(input("Load delay in seconds (default 30): ").strip() or "30")
        except ValueError:
            self.load_delay = 30

        print("\nSetup completed! GUI launched.\n")

    def is_roblox_running(self):
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() in ['robloxplayerbeta.exe', 'roblox.exe']:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def kill_roblox(self):
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() in ['robloxplayerbeta.exe', 'roblox.exe']:
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    def check_disconnect_image(self):
        if not os.path.exists("disconnect.png"):
            self.status_label.config(text="Error: 'disconnect.png' not found!", fg="#ff5555")
            return False

        try:
            location = pyautogui.locateOnScreen("disconnect.png", confidence=CONFIDENCE_LEVEL)
            if location is not None:
                return True
        except Exception:
            pass
        return False

    def launch_game(self):
        os.system(f"start {self.join_url}")

    def monitoring_loop(self):
        self.log("Monitoring started. Waiting for connection loss...")

        while True:
            try:
                is_disconnected = False

                if not self.is_roblox_running():
                    self.log("Game process not found.")
                    is_disconnected = True
                    self.status_label.config(text="Status: Game closed / crashed", fg="#ff5555")
                elif self.check_disconnect_image():
                    self.log("Disconnect window detected!")
                    is_disconnected = True
                    self.status_label.config(text="Status: Disconnect detected!", fg="#ffaa00")
                else:
                    self.status_label.config(text="Status: Game running normally", fg="#00ff66")

                if is_disconnected:
                    self.log("Cleaning up stuck processes...")
                    self.kill_roblox()
                    time.sleep(2)
                    
                    self.log("Reconnecting to game...")
                    self.launch_game()
                    
                    self.log(f"Waiting for game to load ({self.load_delay} sec)...")
                    time.sleep(self.load_delay)
                    self.log("Wait complete, resuming monitoring.")

            except Exception as e:
                self.log(f"Error in loop: {e}")

            time.sleep(self.check_interval)

    def start_monitoring(self):
        thread = Thread(target=self.monitoring_loop, daemon=True)
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = UniversalAutoRejoin(root)
    root.mainloop()