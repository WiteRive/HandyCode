"""
Вспомогательные функции для HandyCode
"""

import sys
import os


# Цвета для терминала
class Colors:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'


def supports_color():
    """Проверяет поддержку цветов"""
    if os.name == 'nt':  # Windows
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except:
            return False
    return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()


def colorize(text, color):
    """Добавляет цвет"""
    if supports_color():
        return f"{color}{text}{Colors.RESET}"
    return text


def print_colored(text, color):
    """Выводит цветной текст"""
    print(colorize(text, color))


def print_header(text):
    """Выводит заголовок"""
    print(colorize(text, Colors.CYAN + Colors.BOLD))


def print_success(text):
    """Выводит успех"""
    print(colorize(text, Colors.GREEN))


def print_error(text):
    """Выводит ошибку"""
    print(colorize(text, Colors.RED))
    return text


def print_warning(text):
    """Выводит предупреждение"""
    print(colorize(text, Colors.YELLOW))


def print_info(text):
    """Выводит информацию"""
    print(colorize(text, Colors.BLUE))


def print_logo():
    """Выводит логотип"""
    from .logo import get_logo
    print(get_logo())


def truncate(text, max_length=100):
    """Обрезает текст"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_size(size_bytes):
    """Форматирует размер"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"