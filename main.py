import os
import time
import requests
from datetime import datetime
import tkinter as tk
from threading import Thread
import psutil
import pyautogui

CONFIDENCE_LEVEL = 0.85
BLOX_FRUITS_PLACE_ID = "2753915549"

class UniversalAutoRejoin:
    def __init__(self, root, tg_token, tg_chat_id, discord_webhook):
        self.root = root
        self.root.title("Universal Roblox Auto-Rejoin")
        self.root.geometry("450x350")
        self.root.configure(bg="#1e1e1e")
        
        self.tg_token = tg_token
        self.tg_chat_id = tg_chat_id
        self.discord_webhook = discord_webhook
        
        # Position window in the top-right corner of the screen
        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"450x350+{screen_width - 470}+50")
        self.root.attributes("-topmost", True)
        
        # Top panel (Title / Status)
        self.title_label = tk.Label(
            root, text="🛡️ ADVANCED AUTO-REJOIN", 
            bg="#1e1e1e", fg="#00ffcc", font=("Segoe UI", 11, "bold")
        )
        self.title_label.pack(pady=(10, 5))

        # Log window frame
        self.log_frame = tk.Frame(root, bg="#2d2d2d", bd=1, relief=tk.SOLID)
        self.log_frame.pack(expand=True, fill=tk.BOTH, padx=12, pady=5)

        # Log text widget
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

        self.join_url = f"roblox://placeID={BLOX_FRUITS_PLACE_ID}"
        self.check_interval = 5
        self.load_delay = 30

        self.setup_console()
        
        # Start monitoring and Telegram listener threads
        self.start_monitoring()
        if self.tg_token and self.tg_chat_id:
            self.start_telegram_listener()

    def log(self, message):
        now = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{now}] {message}\n"
        print(f"[{now}] {message}")
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, formatted_msg)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def setup_console(self):
        print("=== AUTO-REJOIN SETUP ===")
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
                    pass
        else:
            place_id = input("Enter Game Place ID (default 2753915549): ").strip()
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

        print("\nSetup completed! Running system...\n")

    def take_screenshot(self, filename="error_screen.png"):
        try:
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
            return filename
        except Exception:
            return None

    def send_notifications(self, message):
        self.log(message)
        screenshot_path = self.take_screenshot()

        # Send to Discord via Webhook
        if self.discord_webhook:
            try:
                data = {"content": f"🚨 **Roblox Alert:** {message}"}
                files = {}
                if screenshot_path and os.path.exists(screenshot_path):
                    files = {"file": open(screenshot_path, "rb")}
                requests.post(self.discord_webhook, data=data, files=files, timeout=10)
            except Exception as e:
                self.log(f"Discord webhook error: {e}")

        # Send to Telegram
        if self.tg_token and self.tg_chat_id:
            try:
                url = f"https://api.telegram.org/bot{self.tg_token}/sendPhoto"
                if screenshot_path and os.path.exists(screenshot_path):
                    with open(screenshot_path, "rb") as photo:
                        requests.post(url, data={"chat_id": self.tg_chat_id, "caption": f"🚨 {message}"}, files={"photo": photo}, timeout=10)
                else:
                    requests.post(f"https://api.telegram.org/bot{self.tg_token}/sendMessage", data={"chat_id": self.tg_chat_id, "text": f"🚨 {message}"}, timeout=10)
            except Exception as e:
                self.log(f"Telegram notification error: {e}")

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

    def full_restart(self):
        self.log("Manual restart triggered...")
        self.kill_roblox()
        time.sleep(2)
        self.launch_game()
        time.sleep(self.load_delay)
        self.log("Restart complete.")

    def monitoring_loop(self):
        self.log("Monitoring started...")
        while True:
            try:
                is_disconnected = False
                if not self.is_roblox_running():
                    is_disconnected = True
                    self.status_label.config(text="Status: Game closed / crashed", fg="#ff5555")
                elif self.check_disconnect_image():
                    is_disconnected = True
                    self.status_label.config(text="Status: Disconnect detected!", fg="#ffaa00")
                else:
                    self.status_label.config(text="Status: Running normally", fg="#00ff66")

                if is_disconnected:
                    self.send_notifications("Roblox crashed or disconnected! Reconnecting automatically...")
                    self.kill_roblox()
                    time.sleep(2)
                    self.launch_game()
                    time.sleep(self.load_delay)
                    self.send_notifications("Successfully reconnected to the game!")

            except Exception as e:
                self.log(f"Error in loop: {e}")

            time.sleep(self.check_interval)

    def telegram_listener(self):
        # Listens for commands from Telegram (/screenshot, /restart, /status)
        last_update_id = 0
        while True:
            try:
                url = f"https://api.telegram.org/bot{self.tg_token}/getUpdates?offset={last_update_id + 1}&timeout=30"
                response = requests.get(url, timeout=35).json()
                for update in response.get("result", []):
                    last_update_id = update["update_id"]
                    message = update.get("message", {})
                    chat_id = str(message.get("chat", {}).get("id"))
                    text = message.get("text", "").strip().lower()

                    if chat_id == str(self.tg_chat_id):
                        if text == "/screenshot":
                            path = self.take_screenshot("tg_screen.png")
                            if path:
                                with open(path, "rb") as photo:
                                    requests.post(f"https://api.telegram.org/bot{self.tg_token}/sendPhoto", data={"chat_id": chat_id, "caption": "📸 Current screen state:"}, files={"photo": photo})
                        elif text == "/restart":
                            requests.post(f"https://api.telegram.org/bot{self.tg_token}/sendMessage", data={"chat_id": chat_id, "text": "🔄 Full Roblox restart initiated..."})
                            self.full_restart()
                            requests.post(f"https://api.telegram.org/bot{self.tg_token}/sendMessage", data={"chat_id": chat_id, "text": "✅ Game restarted successfully!"})
                        elif text == "/status":
                            status = "Running" if self.is_roblox_running() else "Closed/Crashed"
                            requests.post(f"https://api.telegram.org/bot{self.tg_token}/sendMessage", data={"chat_id": chat_id, "text": f"📊 Current Status: {status}"})
            except Exception:
                time.sleep(5)

    def start_monitoring(self):
        Thread(target=self.monitoring_loop, daemon=True).start()

    def start_telegram_listener(self):
        Thread(target=self.telegram_listener, daemon=True).start()

if __name__ == "__main__":
    # NOTIFICATION SETTINGS
    TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"     # Your token telegram bot (get it from @BotFather)
    TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"         # Your numeric chat ID (get it from @userinfobot)
    DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL"   # Your Discord webhook URL

    root = tk.Tk()
    app = UniversalAutoRejoin(root, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DISCORD_WEBHOOK_URL)
    root.mainloop()
