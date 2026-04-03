"""
NOVA Task Module - System Control
Handles OS-level operations: apps, volume, brightness, power, system info.
"""

import os
import subprocess
import socket
try:
    import psutil
except ImportError:
    psutil = None
from config import Config


class SystemControl:
    """System-level operations for NOVA."""

    def __init__(self, voice):
        self.voice = voice

    def open_app(self, query):
        """Open an application by name."""
        query_lower = query.lower()

        # Check configured app paths
        for app_name, path in Config.APP_PATHS.items():
            if app_name in query_lower:
                try:
                    if path.startswith("ms-"):
                        os.system(f"start {path}")
                    elif path.endswith(".exe") and "\\" not in path:
                        subprocess.Popen(path, shell=True)
                    else:
                        os.startfile(path)
                    self.voice.speak(f"Opening {app_name}.")
                    return f"Opened {app_name}."
                except Exception as e:
                    self.voice.speak(f"Failed to open {app_name}.")
                    return f"Failed to open {app_name}: {e}"

        # Check website shortcuts
        import webbrowser
        for site_name, url in Config.WEBSITE_SHORTCUTS.items():
            if site_name in query_lower:
                webbrowser.open(url)
                self.voice.speak(f"Opening {site_name}.")
                return f"Opened {site_name}."

        # Try generic open
        app = query_lower.replace("open ", "").replace("launch ", "").replace("start ", "").strip()
        if app:
            try:
                subprocess.Popen(f"start {app}", shell=True)
                self.voice.speak(f"Trying to open {app}.")
                return f"Attempting to open {app}."
            except Exception:
                import webbrowser
                url = f"https://www.{app}.com"
                webbrowser.open(url)
                self.voice.speak(f"Opening {app} in browser.")
                return f"Opened {app}.com in browser."

        return "Please specify what to open."

    def close_app(self, query):
        """Close an application by name."""
        for app_name in Config.APP_PATHS:
            if app_name in query.lower():
                try:
                    os.system(f"taskkill /f /im {app_name}.exe 2>nul")
                    self.voice.speak(f"Closed {app_name}.")
                    return f"Closed {app_name}."
                except Exception:
                    return f"Could not close {app_name}."

        app = query.lower().replace("close ", "").replace("kill ", "").strip()
        if app:
            os.system(f"taskkill /f /im {app}.exe 2>nul")
            self.voice.speak(f"Trying to close {app}.")
            return f"Attempted to close {app}."

        return "Please specify which app to close."

    def volume_control(self, action):
        """Control system volume using keyboard simulation."""
        import pyautogui
        if action == "up":
            for _ in range(5):
                pyautogui.press("volumeup")
            self.voice.speak("Volume increased.")
            return "Volume increased."
        elif action == "down":
            for _ in range(5):
                pyautogui.press("volumedown")
            self.voice.speak("Volume decreased.")
            return "Volume decreased."
        elif action == "mute":
            pyautogui.press("volumemute")
            self.voice.speak("Volume toggled.")
            return "Volume mute toggled."

    def brightness_control(self, action):
        """Control screen brightness (Windows)."""
        try:
            if action == "up":
                subprocess.run(
                    ["powershell", "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, (([Math]::Min(100, (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness + 20))))"],
                    capture_output=True, shell=True
                )
                self.voice.speak("Brightness increased.")
                return "Brightness increased."
            elif action == "down":
                subprocess.run(
                    ["powershell", "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, (([Math]::Max(0, (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness - 20))))"],
                    capture_output=True, shell=True
                )
                self.voice.speak("Brightness decreased.")
                return "Brightness decreased."
        except Exception:
            self.voice.speak("Brightness control is not available on this device.")
            return "Brightness control not available."

    def battery_status(self):
        """Get battery status."""
        try:
            if psutil is None:
                battery = None
            else:
                battery = psutil.sensors_battery()
        except Exception:
            battery = None

        if battery:
            percent = battery.percent
            plugged = "plugged in" if battery.power_plugged else "on battery"
            secs_left = battery.secsleft
            if secs_left == psutil.POWER_TIME_UNLIMITED:
                time_left = "charging"
            elif secs_left == psutil.POWER_TIME_UNKNOWN:
                time_left = "unknown time remaining"
            else:
                hours = secs_left // 3600
                minutes = (secs_left % 3600) // 60
                time_left = f"{hours} hours {minutes} minutes remaining"

            msg = f"Battery is at {percent}%, {plugged}. {time_left}."
            self.voice.speak(msg)
            return msg
        else:
            self.voice.speak("No battery detected. This might be a desktop PC or serverless host.")
            return "No battery detected."

    def lock_screen(self):
        """Lock the computer screen."""
        os.system("rundll32.exe user32.dll,LockWorkStation")
        self.voice.speak("Locking your screen.")
        return "Screen locked."

    def shutdown(self):
        """Shutdown the computer."""
        self.voice.speak("Shutting down the computer in 30 seconds. Say cancel to abort.")
        os.system("shutdown /s /t 30")
        return "Shutdown scheduled in 30 seconds."

    def restart(self):
        """Restart the computer."""
        self.voice.speak("Restarting the computer in 30 seconds.")
        os.system("shutdown /r /t 30")
        return "Restart scheduled in 30 seconds."

    def empty_recycle_bin(self):
        """Empty the recycle bin."""
        try:
            subprocess.run(
                ["powershell", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"],
                capture_output=True, shell=True
            )
            self.voice.speak("Recycle bin emptied.")
            return "Recycle bin emptied."
        except Exception:
            return "Could not empty recycle bin."

    def system_info(self):
        """Get system information."""
        import platform
        info = {
            "OS": f"{platform.system()} {platform.release()}",
            "Machine": platform.machine(),
            "Processor": platform.processor(),
            "CPU Cores": psutil.cpu_count(logical=False),
            "Logical CPUs": psutil.cpu_count(logical=True),
            "RAM": f"{psutil.virtual_memory().total / (1024**3):.1f} GB",
        }
        msg = ". ".join([f"{k}: {v}" for k, v in info.items()])
        self.voice.speak(f"System info: {msg}")
        return msg

    def cpu_usage(self):
        """Get current CPU usage."""
        usage = psutil.cpu_percent(interval=1)
        msg = f"CPU usage is at {usage}%."
        self.voice.speak(msg)
        return msg

    def memory_usage(self):
        """Get current memory usage."""
        mem = psutil.virtual_memory()
        msg = f"Memory usage: {mem.percent}% used. {mem.available / (1024**3):.1f} GB available out of {mem.total / (1024**3):.1f} GB."
        self.voice.speak(msg)
        return msg

    def disk_usage(self):
        """Get disk usage for all drives."""
        partitions = psutil.disk_partitions()
        results = []
        for p in partitions:
            try:
                usage = psutil.disk_usage(p.mountpoint)
                results.append(f"{p.device}: {usage.percent}% used ({usage.free / (1024**3):.1f} GB free)")
            except Exception:
                continue
        msg = "Disk usage: " + ", ".join(results) if results else "Could not read disk info."
        self.voice.speak(msg)
        return msg

    def get_ip_address(self):
        """Get local and public IP address."""
        try:
            # Local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()

            msg = f"Your local IP address is {local_ip}."
            self.voice.speak(msg)
            return msg
        except Exception:
            self.voice.speak("Could not determine IP address.")
            return "Could not determine IP address."

    def wifi_status(self):
        """Check Wi-Fi / internet connectivity."""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            self.voice.speak("You are connected to the internet.")
            return "Internet connection is active."
        except OSError:
            self.voice.speak("You are not connected to the internet.")
            return "No internet connection."
