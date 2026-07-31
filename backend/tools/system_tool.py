"""
NOVA Tool — System Control
OS-level operations: apps, volume, brightness, power, hardware stats.
"""

from __future__ import annotations

import os
import platform
import socket
import subprocess
from typing import Any

from tools.base_tool import BaseTool, ToolResult, param

try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False

try:
    import pyautogui
    _PYAUTOGUI = True
except ImportError:
    _PYAUTOGUI = False


class SystemTool(BaseTool):
    name = "system_tool"
    description = (
        "Controls the operating system: open/close apps, adjust volume and brightness, "
        "lock/shutdown/restart the PC, and read hardware stats like CPU, RAM, disk, battery."
    )
    actions = [
        "open_app",
        "close_app",
        "volume_up",
        "volume_down",
        "volume_mute",
        "brightness_up",
        "brightness_down",
        "lock_screen",
        "shutdown",
        "restart",
        "cancel_shutdown",
        "battery_status",
        "cpu_usage",
        "memory_usage",
        "disk_usage",
        "system_info",
        "get_ip",
        "wifi_status",
        "empty_recycle_bin",
        "list_running_apps",
        "kill_process",
    ]
    parameters = {
        "open_app": {
            "app_name": param("string", "Name of the application or website to open, e.g. 'chrome', 'vscode', 'spotify'"),
        },
        "close_app": {
            "app_name": param("string", "Name of the process/app to close, e.g. 'notepad', 'chrome'"),
        },
        "volume_up": {
            "steps": param("integer", "How many steps to increase volume (default 5)"),
        },
        "volume_down": {
            "steps": param("integer", "How many steps to decrease volume (default 5)"),
        },
        "brightness_up": {
            "amount": param("integer", "Percentage amount to increase brightness (default 20)"),
        },
        "brightness_down": {
            "amount": param("integer", "Percentage amount to decrease brightness (default 20)"),
        },
        "kill_process": {
            "process_name": param("string", "Exact process name to kill, e.g. 'chrome.exe'"),
        },
    }
    dangerous_actions = ["shutdown", "restart", "kill_process", "empty_recycle_bin"]

    def __init__(self) -> None:
        from config import settings
        self._settings = settings

    def execute(self, action: str, params: dict[str, Any]) -> ToolResult:
        dispatch = {
            "open_app":         self._open_app,
            "close_app":        self._close_app,
            "volume_up":        self._volume_up,
            "volume_down":      self._volume_down,
            "volume_mute":      self._volume_mute,
            "brightness_up":    self._brightness_up,
            "brightness_down":  self._brightness_down,
            "lock_screen":      self._lock_screen,
            "shutdown":         self._shutdown,
            "restart":          self._restart,
            "cancel_shutdown":  self._cancel_shutdown,
            "battery_status":   self._battery_status,
            "cpu_usage":        self._cpu_usage,
            "memory_usage":     self._memory_usage,
            "disk_usage":       self._disk_usage,
            "system_info":      self._system_info,
            "get_ip":           self._get_ip,
            "wifi_status":      self._wifi_status,
            "empty_recycle_bin": self._empty_recycle_bin,
            "list_running_apps": self._list_running_apps,
            "kill_process":     self._kill_process,
        }
        fn = dispatch.get(action)
        if fn is None:
            return self._not_implemented(action)
        return fn(params)

    # ── App Control ───────────────────────────────────────────────────────────

    def _open_app(self, p: dict) -> ToolResult:
        app_name = p.get("app_name", "").lower().strip()
        if not app_name:
            return ToolResult.fail("Please specify which app to open.")

        # 1. Check configured app paths
        for key, path in self._settings.APP_PATHS.items():
            if key in app_name or app_name in key:
                try:
                    if path.startswith("ms-"):
                        os.system(f"start {path}")
                    elif path == "code":
                        subprocess.Popen("code", shell=True)
                    elif "\\" in path or "/" in path:
                        os.startfile(path)
                    else:
                        subprocess.Popen(path, shell=True)
                    return ToolResult.ok(f"Opening {key}.", action=f"open:{key}")
                except Exception as e:
                    return ToolResult.fail(f"Failed to open {key}: {e}")

        # 2. Check website shortcuts
        import webbrowser
        for site, url in self._settings.WEBSITE_SHORTCUTS.items():
            if site in app_name or app_name in site:
                webbrowser.open(url)
                return ToolResult.ok(f"Opening {site} in your browser.", action=f"open_web:{site}")

        # 3. Generic shell open
        try:
            subprocess.Popen(f"start {app_name}", shell=True)
            return ToolResult.ok(f"Trying to open {app_name}.", action=f"open_generic:{app_name}")
        except Exception:
            import webbrowser
            webbrowser.open(f"https://www.{app_name}.com")
            return ToolResult.ok(f"Opened {app_name}.com in your browser.")

    def _close_app(self, p: dict) -> ToolResult:
        app_name = p.get("app_name", "").lower().strip()
        if not app_name:
            return ToolResult.fail("Please specify which app to close.")
        # Try with and without .exe
        name_exe = app_name if app_name.endswith(".exe") else f"{app_name}.exe"
        result = subprocess.run(
            f"taskkill /f /im {name_exe}", shell=True, capture_output=True, text=True
        )
        if result.returncode == 0:
            return ToolResult.ok(f"Closed {app_name}.")
        return ToolResult.fail(f"Could not close {app_name}. It may not be running.")

    # ── Volume ────────────────────────────────────────────────────────────────

    def _volume_up(self, p: dict) -> ToolResult:
        if not _PYAUTOGUI:
            return ToolResult.fail("Volume control unavailable — pyautogui not installed.")
        steps = int(p.get("steps", 5))
        for _ in range(steps):
            pyautogui.press("volumeup")
        return ToolResult.ok(f"Volume increased by {steps} steps.")

    def _volume_down(self, p: dict) -> ToolResult:
        if not _PYAUTOGUI:
            return ToolResult.fail("Volume control unavailable — pyautogui not installed.")
        steps = int(p.get("steps", 5))
        for _ in range(steps):
            pyautogui.press("volumedown")
        return ToolResult.ok(f"Volume decreased by {steps} steps.")

    def _volume_mute(self, p: dict) -> ToolResult:
        if not _PYAUTOGUI:
            return ToolResult.fail("Volume control unavailable — pyautogui not installed.")
        pyautogui.press("volumemute")
        return ToolResult.ok("Volume muted/unmuted.")

    # ── Brightness ────────────────────────────────────────────────────────────

    def _brightness_up(self, p: dict) -> ToolResult:
        amount = int(p.get("amount", 20))
        try:
            script = (
                f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods)"
                f".WmiSetBrightness(1, ([Math]::Min(100, "
                f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness + {amount})))"
            )
            subprocess.run(["powershell", script], capture_output=True, shell=True)
            return ToolResult.ok(f"Brightness increased by {amount}%.")
        except Exception:
            return ToolResult.fail("Brightness control not available on this device.")

    def _brightness_down(self, p: dict) -> ToolResult:
        amount = int(p.get("amount", 20))
        try:
            script = (
                f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods)"
                f".WmiSetBrightness(1, ([Math]::Max(0, "
                f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness - {amount})))"
            )
            subprocess.run(["powershell", script], capture_output=True, shell=True)
            return ToolResult.ok(f"Brightness decreased by {amount}%.")
        except Exception:
            return ToolResult.fail("Brightness control not available on this device.")

    # ── Power ─────────────────────────────────────────────────────────────────

    def _lock_screen(self, p: dict) -> ToolResult:
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return ToolResult.ok("Screen locked.")

    def _shutdown(self, p: dict) -> ToolResult:
        os.system("shutdown /s /t 30")
        return ToolResult.ok("Shutting down in 30 seconds. Say 'cancel shutdown' to abort.")

    def _restart(self, p: dict) -> ToolResult:
        os.system("shutdown /r /t 30")
        return ToolResult.ok("Restarting in 30 seconds. Say 'cancel shutdown' to abort.")

    def _cancel_shutdown(self, p: dict) -> ToolResult:
        os.system("shutdown /a")
        return ToolResult.ok("Shutdown cancelled.")

    # ── Hardware Stats ────────────────────────────────────────────────────────

    def _battery_status(self, p: dict) -> ToolResult:
        if not _PSUTIL:
            return ToolResult.fail("Battery info unavailable — psutil not installed.")
        battery = psutil.sensors_battery()
        if not battery:
            return ToolResult.ok("No battery detected — this looks like a desktop PC.", speak=True)
        pct = battery.percent
        plugged = "plugged in" if battery.power_plugged else "on battery"
        secs = battery.secsleft
        if secs == psutil.POWER_TIME_UNLIMITED:
            time_str = "charging"
        elif secs == psutil.POWER_TIME_UNKNOWN or secs < 0:
            time_str = "unknown time remaining"
        else:
            h, m = divmod(secs, 3600)
            m //= 60
            time_str = f"{h}h {m}m remaining"
        msg = f"Battery is at {pct:.0f}%, {plugged}. {time_str}."
        return ToolResult.ok(msg, data={"percent": pct, "plugged": battery.power_plugged})

    def _cpu_usage(self, p: dict) -> ToolResult:
        if not _PSUTIL:
            return ToolResult.fail("CPU info unavailable.")
        usage = psutil.cpu_percent(interval=1)
        return ToolResult.ok(f"CPU usage is {usage:.1f}%.", data={"cpu_percent": usage})

    def _memory_usage(self, p: dict) -> ToolResult:
        if not _PSUTIL:
            return ToolResult.fail("Memory info unavailable.")
        mem = psutil.virtual_memory()
        available_gb = mem.available / (1024 ** 3)
        total_gb = mem.total / (1024 ** 3)
        msg = f"RAM usage is {mem.percent:.1f}%. {available_gb:.1f} GB free of {total_gb:.1f} GB."
        return ToolResult.ok(msg, data={"percent": mem.percent, "available_gb": round(available_gb, 2)})

    def _disk_usage(self, p: dict) -> ToolResult:
        if not _PSUTIL:
            return ToolResult.fail("Disk info unavailable.")
        parts = []
        data_parts = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                free_gb = usage.free / (1024 ** 3)
                parts.append(f"{part.device}: {usage.percent:.0f}% used, {free_gb:.1f} GB free")
                data_parts.append({"device": part.device, "percent": usage.percent, "free_gb": round(free_gb, 2)})
            except Exception:
                continue
        msg = "Disk usage: " + "; ".join(parts) if parts else "Could not read disk info."
        return ToolResult.ok(msg, data={"disks": data_parts})

    def _system_info(self, p: dict) -> ToolResult:
        info = {
            "OS": f"{platform.system()} {platform.release()} {platform.version()}",
            "Machine": platform.machine(),
            "Processor": platform.processor() or "Unknown",
        }
        if _PSUTIL:
            info["CPU Cores"] = psutil.cpu_count(logical=False)
            info["Logical CPUs"] = psutil.cpu_count(logical=True)
            info["RAM"] = f"{psutil.virtual_memory().total / (1024 ** 3):.1f} GB"
        msg = ". ".join(f"{k}: {v}" for k, v in info.items())
        return ToolResult.ok(f"System info — {msg}", data=info)

    def _get_ip(self, p: dict) -> ToolResult:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ToolResult.ok(f"Your local IP is {ip}.", data={"ip": ip})
        except Exception:
            return ToolResult.fail("Could not determine your IP address.")

    def _wifi_status(self, p: dict) -> ToolResult:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return ToolResult.ok("You're connected to the internet.")
        except OSError:
            return ToolResult.fail("No internet connection detected.")

    def _empty_recycle_bin(self, p: dict) -> ToolResult:
        try:
            subprocess.run(
                ["powershell", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"],
                capture_output=True, shell=True
            )
            return ToolResult.ok("Recycle bin emptied.")
        except Exception as e:
            return ToolResult.fail(f"Could not empty recycle bin: {e}")

    def _list_running_apps(self, p: dict) -> ToolResult:
        if not _PSUTIL:
            return ToolResult.fail("Process list unavailable.")
        procs = []
        for proc in psutil.process_iter(["name", "pid", "memory_percent"]):
            try:
                procs.append(proc.info)
            except Exception:
                continue
        # Top 10 by memory
        top = sorted(procs, key=lambda x: x.get("memory_percent", 0) or 0, reverse=True)[:10]
        names = ", ".join(p["name"] for p in top if p.get("name"))
        return ToolResult.ok(f"Top running processes: {names}", data={"processes": top}, speak=False)

    def _kill_process(self, p: dict) -> ToolResult:
        name = p.get("process_name", "").strip()
        if not name:
            return ToolResult.fail("Please specify the process name to kill.")
        name_exe = name if name.endswith(".exe") else f"{name}.exe"
        result = subprocess.run(f"taskkill /f /im {name_exe}", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return ToolResult.ok(f"Process {name} terminated.")
        return ToolResult.fail(f"Could not kill {name}. It may not be running.")
