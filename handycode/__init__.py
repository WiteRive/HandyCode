"""
HandyCode - AI Ассистент для разработки
Аналог Claude Code для командной строки
"""

__version__ = "2.0.0"
__author__ = "HandyCode Team"
__license__ = "MIT"

from .main import main
from .assistant import HandyCode

__all__ = ["main", "HandyCode"]