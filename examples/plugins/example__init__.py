"""
ManagerX Example Plugin

This package exposes functions for ManagerX bots.
No automatic bot registration is done here.
"""

from .functions import hello, add_numbers, multiply_numbers, format_user_message
from .utils import current_time, is_even

__all__ = [
    "hello",
    "add_numbers",
    "multiply_numbers",
    "format_user_message",
    "current_time",
    "is_even"
]