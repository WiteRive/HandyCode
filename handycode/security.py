"""
Проверка безопасности для HandyCode
"""

from pathlib import Path
from typing import List


class SecurityChecker:
    """Проверяет пути и команды на безопасность"""

    def __init__(self, project_root: Path):
        """Инициализация проверки безопасности"""
        self.project_root = Path(project_root).resolve()

        # Опасные системные директории
        self.dangerous_dirs = {
            '/', '/etc', '/bin', '/sbin', '/usr/bin', '/usr/sbin',
            '/boot', '/root', '/var', '/tmp', '/dev', '/proc', '/sys',
            '/System', '/Library', '/Windows', '/Program Files',
            '/Program Files (x86)', '/system32',
        }

        # Опасные команды
        self.dangerous_commands = [
            'rm -rf /',
            'rm -rf ~',
            'rm -rf .',
            'mkfs.',
            'dd if=',
            ':(){ :|:& };:',
            'chmod 777 /',
            'chown -R',
            '> /dev/sda',
            'format c:',
            'del /f /s /q',
            'shutdown',
            'reboot',
            'halt',
            'poweroff',
        ]

        # Подозрительные паттерны
        self.suspicious_patterns = [
            'sudo ',
            'su ',
            'passwd',
            'curl.*|.*sh',
            'wget.*|.*sh',
            'eval ',
            'exec ',
            'base64.*decode',
        ]

    def is_safe_path(self, path: str) -> bool:
        """Проверяет безопасность пути к файлу"""
        try:
            full_path = (self.project_root / path).resolve()

            # Должен быть внутри проекта
            full_path.relative_to(self.project_root)

            # Проверяем опасные символы
            path_str = str(path)
            dangerous_chars = ['..', '~', '$', '`', '|', '&', ';', '\n', '\r']
            for char in dangerous_chars:
                if char in path_str:
                    return False

            # Проверяем опасные директории
            path_str = str(full_path)
            for dangerous in self.dangerous_dirs:
                if path_str == dangerous or path_str.startswith(dangerous + '/'):
                    return False

            return True
        except (ValueError, OSError):
            return False

    def is_safe_command(self, command: str) -> bool:
        """Проверяет безопасность команды"""
        command_lower = command.lower().strip()

        # Проверяем опасные команды
        for dangerous in self.dangerous_commands:
            if dangerous.lower() in command_lower:
                return False

        # Проверяем подозрительные паттерны
        for pattern in self.suspicious_patterns:
            if pattern.lower() in command_lower:
                # Разрешаем безопасные комбинации
                if 'npm' not in command_lower and 'pip' not in command_lower:
                    return False

        # Блокируем доступ к системным директориям
        for dangerous in ['/etc', '/bin/', '/sbin/', '/usr/', '/boot', '/root', '/var/']:
            if dangerous in command:
                # Разрешаем для пакетных менеджеров
                if not any(safe in command_lower for safe in ['npm', 'pip', 'apt', 'brew', 'yarn']):
                    return False

        return True