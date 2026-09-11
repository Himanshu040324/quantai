"""
Public contract for the news module.
Other modules and main.py should import ONLY from here — never reach
into modules.news.internal.* directly.
"""
from modules.news.internal.router import router

__all__ = ["router"]