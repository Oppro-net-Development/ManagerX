"""
This file contains the main plugin functions.
These functions are independent and can be used in any bot Cog.
"""

def hello(user: str) -> str:
    """
    Example greeting function.
    """
    return f"Hello {user}! Welcome to ManagerX Example Plugin."

def add_numbers(a: int, b: int) -> int:
    """
    Example calculation function.
    """
    return a + b

def multiply_numbers(a: int, b: int) -> int:
    """
    Another example function for multiplication.
    """
    return a * b

def format_user_message(user: str, message: str) -> str:
    """
    Formats a message with the user's name.
    """
    return f"{user} says: {message}"