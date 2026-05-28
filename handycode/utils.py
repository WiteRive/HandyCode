"""
Вспомогательные функции для HandyCode
"""

import sys
from typing import Any


class Colors:
    """Цвета для терминала"""
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def supports_color() -> bool:
    """Проверяет поддержку цветов терминалом"""
    return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()


def colorize(text: str, color: str) -> str:
    """Добавляет цвет к тексту"""
    if supports_color():
        return f"{color}{text}{Colors.RESET}"
    return text


def print_colored(text: str, color: str):
    """Выводит цветной текст"""
    print(colorize(text, color))


def print_header(text: str):
    """Выводит заголовок"""
    print(colorize(text, Colors.CYAN + Colors.BOLD))


def print_success(text: str):
    """Выводит сообщение об успехе"""
    print(colorize(text, Colors.GREEN))


def print_error(text: str) -> str:
    """Выводит сообщение об ошибке"""
    print(colorize(text, Colors.RED))
    return text


def print_warning(text: str):
    """Выводит предупреждение"""
    print(colorize(text, Colors.YELLOW))


def print_info(text: str):
    """Выводит информационное сообщение"""
    print(colorize(text, Colors.BLUE))


def print_logo():
    """Выводит логотип HandyCode"""
    from .logo import get_logo
    print(get_logo())


def print_small_logo():
    """Выводит маленький логотип"""
    from .logo import get_small_logo
    print(get_small_logo())


def print_install_logo():
    """Выводит логотип установки"""
    from .logo import get_install_logo
    print(get_install_logo())


def truncate(text: str, max_length: int = 100) -> str:
    """Обрезает текст до указанной длины"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_size(size_bytes: int) -> str:
    """Форматирует размер в байтах в читаемый вид"""
    for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} ТБ"


def confirm_action(message: str, default: bool = True) -> bool:
    """Запрашивает подтверждение действия"""
    suffix = "[Д/н]" if default else "[д/Н]"
    response = input(f"{message} {suffix}: ").strip().lower()

    if not response:
        return default

    return response in ['д', 'да', 'y', 'yes']