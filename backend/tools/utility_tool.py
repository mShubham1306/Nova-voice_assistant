"""
NOVA Tool — Utility
Screenshot, timers, alarms, calculator, clipboard, type text, unit conversion.
"""

from __future__ import annotations

import datetime
import re
import threading
import time
from typing import Any

from tools.base_tool import BaseTool, ToolResult, param

try:
    import pyautogui
    _PYAUTOGUI = True
except ImportError:
    _PYAUTOGUI = False

try:
    import pyperclip
    _PYPERCLIP = True
except ImportError:
    _PYPERCLIP = False


class UtilityTool(BaseTool):
    name = "utility_tool"
    description = (
        "General utilities: take screenshots, set countdown timers and alarms, "
        "calculate math expressions, read/write clipboard, type text, and convert units."
    )
    actions = [
        "screenshot",
        "set_timer",
        "set_alarm",
        "calculate",
        "read_clipboard",
        "write_clipboard",
        "type_text",
        "convert_units",
    ]
    parameters = {
        "screenshot": {
            "filename": param("string", "Optional filename for the screenshot (without extension)"),
        },
        "set_timer": {
            "duration": param("string", "Timer duration e.g. '5 minutes', '30 seconds', '1 hour 30 minutes'", required=True),
            "label": param("string", "Optional label for this timer, e.g. 'pizza timer'"),
        },
        "set_alarm": {
            "time": param("string", "Alarm time in HH:MM format or relative like '30 minutes from now'", required=True),
            "label": param("string", "Optional label for this alarm"),
        },
        "calculate": {
            "expression": param("string", "Math expression to evaluate e.g. '25 * 4', 'sqrt(144)', '15% of 200'", required=True),
        },
        "write_clipboard": {
            "text": param("string", "Text to write to clipboard", required=True),
        },
        "type_text": {
            "text": param("string", "Text to type at the current cursor position", required=True),
            "delay": param("number", "Delay in seconds before typing starts (default 1.0)"),
        },
        "convert_units": {
            "value": param("number", "The numeric value to convert", required=True),
            "from_unit": param("string", "Unit to convert from, e.g. 'km', 'kg', 'celsius'", required=True),
            "to_unit": param("string", "Unit to convert to, e.g. 'miles', 'pounds', 'fahrenheit'", required=True),
        },
    }

    def __init__(self) -> None:
        from config import settings
        self._settings = settings
        self._active_timers: list[dict] = []

    def execute(self, action: str, params: dict[str, Any]) -> ToolResult:
        dispatch = {
            "screenshot":       self._screenshot,
            "set_timer":        self._set_timer,
            "set_alarm":        self._set_alarm,
            "calculate":        self._calculate,
            "read_clipboard":   self._read_clipboard,
            "write_clipboard":  self._write_clipboard,
            "type_text":        self._type_text,
            "convert_units":    self._convert_units,
        }
        fn = dispatch.get(action)
        if fn is None:
            return self._not_implemented(action)
        return fn(params)

    def _screenshot(self, p: dict) -> ToolResult:
        if not _PYAUTOGUI:
            return ToolResult.fail("Screenshots unavailable — pyautogui not installed.")
        ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        fname = p.get("filename", f"screenshot_{ts}") + ".png"
        path = self._settings.SCREENSHOTS_DIR / fname
        try:
            img = pyautogui.screenshot()
            img.save(str(path))
            return ToolResult.ok(f"Screenshot saved as {fname}.", data={"path": str(path)})
        except Exception as e:
            return ToolResult.fail(f"Screenshot failed: {e}")

    def _parse_duration_seconds(self, text: str) -> int | None:
        """Parse human-readable duration to seconds."""
        text = text.lower().strip()
        total = 0
        patterns = [
            (r"(\d+)\s*hour", 3600),
            (r"(\d+)\s*hr",   3600),
            (r"(\d+)\s*h\b",  3600),
            (r"(\d+)\s*minute", 60),
            (r"(\d+)\s*min",    60),
            (r"(\d+)\s*m\b",    60),
            (r"(\d+)\s*second", 1),
            (r"(\d+)\s*sec",    1),
            (r"(\d+)\s*s\b",    1),
        ]
        for pattern, multiplier in patterns:
            for m in re.finditer(pattern, text):
                total += int(m.group(1)) * multiplier
        return total if total > 0 else None

    def _set_timer(self, p: dict) -> ToolResult:
        duration_str = p.get("duration", "").strip()
        label = p.get("label", "Timer")
        seconds = self._parse_duration_seconds(duration_str)
        if not seconds:
            return ToolResult.fail("I couldn't understand that duration. Try '5 minutes' or '30 seconds'.")

        human = duration_str
        timer_info = {"label": label, "seconds": seconds, "started_at": datetime.datetime.now().isoformat()}
        self._active_timers.append(timer_info)

        def _fire():
            time.sleep(seconds)
            # TTS will be handled by assistant via socketio event
            print(f"[Timer] {label} - {human} elapsed!")

        threading.Thread(target=_fire, daemon=True).start()
        return ToolResult.ok(f"{label} set for {human}. I'll notify you when it's done.", data=timer_info)

    def _set_alarm(self, p: dict) -> ToolResult:
        time_str = p.get("time", "").strip()
        label = p.get("label", "Alarm")

        # Try relative duration first
        seconds = self._parse_duration_seconds(time_str)
        if seconds:
            def _fire():
                time.sleep(seconds)
                print(f"[Alarm] {label} - ringing!")
            threading.Thread(target=_fire, daemon=True).start()
            return ToolResult.ok(f"{label} set for {time_str} from now.")

        # Try absolute time HH:MM
        try:
            now = datetime.datetime.now()
            alarm_time = datetime.datetime.strptime(time_str, "%H:%M").replace(
                year=now.year, month=now.month, day=now.day
            )
            if alarm_time < now:
                alarm_time += datetime.timedelta(days=1)
            wait_secs = (alarm_time - now).total_seconds()

            def _fire_abs():
                time.sleep(wait_secs)
                print(f"[Alarm] {label} - ringing!")
            threading.Thread(target=_fire_abs, daemon=True).start()
            return ToolResult.ok(f"{label} set for {time_str}.")
        except ValueError:
            return ToolResult.fail(f"Couldn't parse alarm time '{time_str}'. Try '07:30' or '30 minutes'.")

    def _calculate(self, p: dict) -> ToolResult:
        expr = p.get("expression", "").strip()
        if not expr:
            return ToolResult.fail("Please provide a math expression.")

        # Handle percentage queries like "15% of 200"
        pct_match = re.match(r"(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)", expr, re.IGNORECASE)
        if pct_match:
            pct, total = float(pct_match.group(1)), float(pct_match.group(2))
            result = (pct / 100) * total
            return ToolResult.ok(f"{pct}% of {total} is {result:.4g}.", data={"result": result})

        # Normalize words to operators
        expr_clean = expr.lower()
        replacements = [
            ("plus", "+"), ("minus", "-"), ("times", "*"), ("multiplied by", "*"),
            ("divided by", "/"), ("over", "/"), ("to the power of", "**"),
            ("power", "**"), ("mod ", "% "), ("modulo", "%"), (" x ", " * "),
        ]
        for word, op in replacements:
            expr_clean = expr_clean.replace(word, op)

        # Add math functions
        import math
        safe_globals = {
            "__builtins__": {},
            "sqrt": math.sqrt, "abs": abs, "round": round,
            "floor": math.floor, "ceil": math.ceil,
            "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "log": math.log, "log10": math.log10,
            "pi": math.pi, "e": math.e,
        }

        # Only allow safe characters
        allowed = set("0123456789+-*/().% \t")
        filtered = "".join(c for c in expr_clean if c in allowed or c.isalpha())

        try:
            result = eval(filtered, safe_globals, {})
            return ToolResult.ok(f"The answer is {result:g}.", data={"expression": expr, "result": result})
        except Exception:
            return ToolResult.fail(f"I couldn't calculate '{expr}'. Please check the expression.")

    def _read_clipboard(self, p: dict) -> ToolResult:
        if _PYPERCLIP:
            try:
                content = pyperclip.paste()
                if content:
                    return ToolResult.ok(f"Clipboard contains: {content[:200]}", data={"content": content})
                return ToolResult.ok("Clipboard is empty.")
            except Exception as e:
                return ToolResult.fail(f"Could not read clipboard: {e}")
        # Fallback: PowerShell
        import subprocess
        r = subprocess.run(["powershell", "Get-Clipboard"], capture_output=True, text=True, shell=True)
        content = r.stdout.strip()
        if content:
            return ToolResult.ok(f"Clipboard: {content[:200]}", data={"content": content})
        return ToolResult.ok("Clipboard is empty.")

    def _write_clipboard(self, p: dict) -> ToolResult:
        text = p.get("text", "")
        if _PYPERCLIP:
            try:
                pyperclip.copy(text)
                return ToolResult.ok(f"Copied to clipboard: {text[:50]}")
            except Exception as e:
                return ToolResult.fail(f"Could not write clipboard: {e}")
        return ToolResult.fail("Clipboard write unavailable — pyperclip not installed.")

    def _type_text(self, p: dict) -> ToolResult:
        if not _PYAUTOGUI:
            return ToolResult.fail("Typing simulation unavailable — pyautogui not installed.")
        text = p.get("text", "").strip()
        delay = float(p.get("delay", 1.0))
        if not text:
            return ToolResult.fail("Please specify the text to type.")

        def _do_type():
            time.sleep(delay)
            pyautogui.typewrite(text, interval=0.04)

        threading.Thread(target=_do_type, daemon=True).start()
        return ToolResult.ok(f"Typing '{text[:30]}{'...' if len(text) > 30 else ''}' in {delay:.0f} second(s).")

    def _convert_units(self, p: dict) -> ToolResult:
        value = float(p.get("value", 0))
        from_u = p.get("from_unit", "").lower().strip()
        to_u = p.get("to_unit", "").lower().strip()

        # Conversion table (from → to → factor or function)
        conversions: dict[tuple[str, str], float | Any] = {
            # Length
            ("km", "miles"): 0.621371, ("miles", "km"): 1.60934,
            ("m", "ft"): 3.28084, ("ft", "m"): 0.3048,
            ("cm", "inches"): 0.393701, ("inches", "cm"): 2.54,
            ("m", "yards"): 1.09361, ("yards", "m"): 0.9144,
            # Weight
            ("kg", "pounds"): 2.20462, ("pounds", "kg"): 0.453592,
            ("kg", "lbs"): 2.20462, ("lbs", "kg"): 0.453592,
            ("grams", "oz"): 0.035274, ("oz", "grams"): 28.3495,
            # Temperature (special)
            ("celsius", "fahrenheit"): lambda c: c * 9 / 5 + 32,
            ("fahrenheit", "celsius"): lambda f: (f - 32) * 5 / 9,
            ("celsius", "kelvin"): lambda c: c + 273.15,
            ("kelvin", "celsius"): lambda k: k - 273.15,
            # Speed
            ("kmh", "mph"): 0.621371, ("mph", "kmh"): 1.60934,
            # Data
            ("gb", "mb"): 1024, ("mb", "gb"): 1 / 1024,
            ("tb", "gb"): 1024, ("gb", "tb"): 1 / 1024,
        }

        key = (from_u, to_u)
        if key not in conversions:
            return ToolResult.fail(f"I don't know how to convert {from_u} to {to_u}. Supported: km/miles, kg/pounds, celsius/fahrenheit, and more.")

        factor = conversions[key]
        result = factor(value) if callable(factor) else value * factor
        return ToolResult.ok(f"{value} {from_u} = {result:.4g} {to_u}.", data={"result": result, "from": from_u, "to": to_u})
