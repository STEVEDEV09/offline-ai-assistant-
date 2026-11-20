import os
import sys
import platform
import subprocess
import webbrowser
from datetime import datetime
import re

def get_current_time_info() -> str:
    """Return formatted current date, day, and time."""
    now = datetime.now()
    return now.strftime("Current Time: %I:%M:%S %p | Date: %A, %B %d, %Y")

def get_system_stats() -> dict:
    """Return system information including OS, Python, architecture."""
    stats = {
        "os": f"{platform.system()} {platform.release()}",
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "time": datetime.now().strftime("%I:%M:%S %p"),
        "date": datetime.now().strftime("%Y-%m-%d")
    }

    # Battery info on Windows via powershell (if on laptop)
    if platform.system() == "Windows":
        try:
            cmd = "powershell -Command \"(Get-WmiObject -Class Win32_Battery).EstimatedChargeRemaining\""
            res = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=2)
            val = res.stdout.strip()
            if val and val.isdigit():
                stats["battery"] = f"{val}%"
        except Exception:
            pass

    return stats

def open_url(url: str) -> str:
    """Open a URL in the default web browser."""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url} in your browser."

def search_web(query: str) -> str:
    """Search Google in default browser."""
    url = f"https://www.google.com/search?q={urllib_quote(query)}"
    webbrowser.open(url)
    return f"Searching Google for: '{query}'"

def urllib_quote(text: str) -> str:
    import urllib.parse
    return urllib.parse.quote_plus(text)

def launch_application(app_name: str) -> str:
    """Launch common desktop applications on Windows."""
    app_lower = app_name.lower().strip()
    if platform.system() != "Windows":
        return "Application launcher is currently optimized for Windows."

    app_mapping = {
        "notepad": "notepad.exe",
        "calc": "calc.exe",
        "calculator": "calc.exe",
        "explorer": "explorer.exe",
        "file manager": "explorer.exe",
        "cmd": "cmd.exe",
        "terminal": "wt.exe",
        "powershell": "powershell.exe",
        "edge": "msedge.exe",
        "chrome": "chrome.exe"
    }

    target = app_mapping.get(app_lower, app_lower)
    try:
        subprocess.Popen(target, shell=True)
        return f"Launched {app_name} successfully."
    except Exception as e:
        return f"Could not launch {app_name}: {str(e)}"

def safe_calculate(expression: str) -> str:
    """Safely calculate mathematical expressions."""
    # Allow only numbers, operators, parens, spaces
    cleaned = expression.strip()
    if not re.match(r"^[\d\s\+\-\*\/\%\(\)\.\^]+$", cleaned):
        return "Invalid math expression. Only standard arithmetic is allowed."
    cleaned = cleaned.replace("^", "**")
    try:
        # Use restricted eval for math
        result = eval(cleaned, {"__builtins__": {}}, {})
        return f"Result: {expression} = {result}"
    except Exception as e:
        return f"Calculation error: {str(e)}"

def execute_tool_intent(user_prompt: str) -> str | None:
    """
    Detect if user prompt matches a system tool command.
    Returns the tool output string if handled, else None.
    """
    p = user_prompt.lower().strip()

    # Time & Date queries
    if any(q in p for q in ["what time is it", "current time", "kya time hua", "aaj ki date", "what is the date", "today's date"]):
        return get_current_time_info()

    # System specs
    if any(q in p for q in ["system info", "system stats", "battery level", "pc specs", "computer info"]):
        stats = get_system_stats()
        lines = ["💻 **System Information**:"]
        for k, v in stats.items():
            lines.append(f"- **{k.capitalize()}**: {v}")
        return "\n".join(lines)

    # Launching apps
    match_open = re.search(r"^(?:open|launch|start|khol do)\s+(notepad|calculator|calc|explorer|terminal|cmd|powershell|edge|chrome)", p)
    if match_open:
        app = match_open.group(1)
        return launch_application(app)

    # Search web
    match_search = re.search(r"^(?:search|google|find)\s+(?:for\s+)?(.+)", p)
    if match_search:
        query = match_search.group(1)
        return search_web(query)

    # Open specific websites
    if "open youtube" in p or "youtube kholo" in p:
        return open_url("https://www.youtube.com")
    if "open google" in p:
        return open_url("https://www.google.com")
    if "open github" in p:
        return open_url("https://www.github.com")

    # Math calculations
    match_calc = re.search(r"^(?:calculate|compute|solve|hisaab)\s+(.+)", p)
    if match_calc:
        return safe_calculate(match_calc.group(1))

    return None
