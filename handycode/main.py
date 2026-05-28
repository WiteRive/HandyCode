#!/usr/bin/env python3
"""Главная точка входа HandyCode"""

import sys
import os

if __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handycode.cli import main as cli_main


def main():
    """Главная точка входа"""
    try:
        cli_main()
    except KeyboardInterrupt:
        print("\n\n👋 До свидания!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()