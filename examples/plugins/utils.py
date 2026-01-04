"""
Utility functions for ManagerX Example Plugin.
"""

from datetime import datetime

def current_time() -> str:
    """
    Returns the current time as a formatted string.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def is_even(number: int) -> bool:
    """
    Returns True if the number is even, False otherwise.
    """
    return number % 2 == 0