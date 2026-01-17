"""
ManagerX - Utility Functions
=============================

Hilfsfunktionen für den Bot
"""

from colorama import Fore, Style
from .config import BotConfig

def print_logo():
    """Gibt das ManagerX ASCII-Logo in der Konsole aus"""
    logo_lines = [
        r" _____ ______   ________  ________   ________  ________  _______   ________      ___   ___ ",
        r"|\   _ \  _   \|\   __  \|\   ___  \|\   __  \|\   ____\|\  ___ \ |\   __  \    |\  \ /  /|",
        r"\ \  \\\__\ \  \ \  \|\  \ \  \\ \  \ \  \|\  \ \  \___|\ \  __/|\ \  \|\  \   \ \  \/  / /",
        r" \ \  \\|__| \  \ \   __  \ \  \\ \  \ \   __  \ \  \  __\ \  _|/_\ \   _  _\   \ \    / / ",
        r"  \ \  \     \ \  \ \  \ \  \ \  \\ \  \ \  \ \  \ \  \|\  \ \  \_|\ \ \  \\  \|   /     \/  ",
        r"   \ \__\     \ \__\ \__\ \__\ \__\\ \__\ \__\ \__\ \_______\ \_______\ \__\\ _\  /  /\   \  ",
        r"    \|__|      \|__|\|__|\|__|\|__| \|__|\|__|\|__|\|_______|\|_______|\|__|\|__|/__/ /\ __\ ",
        r"                                                                               |__|/ \|__| "
    ]
    
    print(Fore.CYAN)
    for line in logo_lines:
        print(line)
    print(f"{'=' * 91}")
    print(f" ManagerX Discord Bot v{BotConfig.VERSION}")
    print(f"{'=' * 91}{Style.RESET_ALL}\n")


def format_uptime(seconds: int) -> str:
    """
    Formatiert Sekunden in lesbare Uptime.
    
    Args:
        seconds: Anzahl Sekunden
        
    Returns:
        str: Formatierte Uptime (z.B. "2d 5h 30m")
    """
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{int(days)}d")
    if hours > 0:
        parts.append(f"{int(hours)}h")
    if minutes > 0:
        parts.append(f"{int(minutes)}m")
    if seconds > 0 or not parts:
        parts.append(f"{int(seconds)}s")
    
    return " ".join(parts)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Kürzt Text auf maximale Länge.
    
    Args:
        text: Zu kürzender Text
        max_length: Maximale Länge
        suffix: Suffix bei gekürztem Text
        
    Returns:
        str: Gekürzter Text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix