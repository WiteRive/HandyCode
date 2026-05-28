"""
Основной класс ассистента HandyCode
"""

import os
import re
import json
import time
import readline
import atexit
import signal
import requests
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from handycode.config import Config
from handycode.models import MODELS, get_model_settings
from handycode.file_manager import FileManager
from handycode.security import SecurityChecker
from handycode.utils import (
    print_colored, print_header, print_success,
    print_error, print_warning, print_info, print_logo, print_small_logo
)


class HandyCode:
    """Основной класс ассистента HandyCode"""

    def __init__(
            self,
            project_path: Path,
            model: str = "deepseek",
            auto_approve: bool = False,
            config: Optional[Config] = None
    ):
        """Инициализация HandyCode"""
        self.project_path = project_path
        self.auto_approve = auto_approve
        self.config = config or Config()

        # Настройка API
        self.api_key = self.config.get_api_key()
        if not self.api_key:
            raise ValueError("API ключ не найден. Установите OPENROUTER_API_KEY")

        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "HandyCode"
        }

        # Настройка модели
        self.current_model = MODELS.get(model, MODELS["deepseek"])
        self.model_settings = get_model_settings(self.current_model)

        # История разговора
        self.conversation_history = [
            {
                "role": "system",
                "content": self._get_system_prompt()
            }
        ]

        # Менеджер файлов
        self.file_manager = FileManager(self.project_path)

        # Проверка безопасности
        self.security = SecurityChecker(self.project_path)

        # Статистика сессии
        self.stats = {
            "messages_sent": 0,
            "files_created": [],
            "files_modified": [],
            "commands_executed": [],
            "start_time": datetime.now()
        }

        # Настройка истории команд
        self._setup_readline()

        # Обработчики сигналов
        signal.signal(signal.SIGINT, self._signal_handler)
        self._interrupt_count = 0

    def _get_system_prompt(self) -> str:
        """Получает системный промпт для AI"""
        return """Ты HandyCode - мощный AI ассистент для разработки в командной строке.

ТВОИ ВОЗМОЖНОСТИ:
1. Создавать полные проекты с нуля
2. Изменять существующие файлы
3. Выполнять команды (npm install, pip install, git и т.д.)
4. Анализировать код и находить ошибки
5. Предлагать архитектурные улучшения
6. Генерировать документацию
7. Настраивать окружение разработки

ФОРМАТ ДЕЙСТВИЙ:
Для создания файла:
[[CREATE:путь/к/файлу.ext]]
полное содержимое файла
Для изменения файла:
[[MODIFY:путь/к/файлу.ext]]
полное новое содержимое файла

Для выполнения команд:
[[EXEC:команда для выполнения]]

ВАЖНЫЕ ПРАВИЛА:
1. ВСЕГДА показывай ПОЛНОЕ содержимое файлов
2. ВСЕГДА используй современные лучшие практики
3. ВСЕГДА проверяй безопасность команд
4. Создавай ВСЕ необходимые файлы для работы проекта
5. Добавляй .gitignore, README.md, requirements.txt и т.д.
6. Проверяй, что проект готов к запуску после создания

Общайся на русском языке. Пиши понятный код с комментариями."""

    def _setup_readline(self):
        """Настраивает историю команд"""
        histfile = self.config.config_dir / 'history'
        try:
            readline.read_history_file(str(histfile))
            readline.set_history_length(1000)
        except FileNotFoundError:
            pass

        atexit.register(readline.write_history_file, str(histfile))

    def _signal_handler(self, sig, frame):
        """Обрабатывает Ctrl+C"""
        self._interrupt_count += 1

        if self._interrupt_count == 1:
            print("\n\n⚠️  Нажмите Ctrl+C ещё раз для принудительного выхода или /exit")
            signal.signal(signal.SIGINT, self._signal_handler)
        else:
            print("\n\n👋 Принудительный выход")
            os._exit(0)

    def reset_interrupt(self):
        """Сбрасывает счётчик прерываний"""
        self._interrupt_count = 0

    def send_message(self, user_input: str) -> str:
        """Отправляет сообщение в AI API"""
        # Обработка команд
        if user_input.startswith('/'):
            return self._handle_command(user_input)

        # Добавляем контекст проекта для запросов связанных с кодом
        context_keywords = [
            'создай', 'сделай', 'проект', 'код', 'файл',
            'приложение', 'компонент', 'модуль', 'класс',
            'api', 'функцию', 'структуру', 'тесты', 'документацию',
            'create', 'make', 'build', 'project', 'code', 'file',
            'app', 'component', 'module', 'class', 'api'
        ]

        if any(kw in user_input.lower() for kw in context_keywords):
            context = self.file_manager.scan_project()
            if context:
                user_input += f"\n\n[Контекст проекта]\n{context}"

        # Добавляем в историю
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        # Настройки модели
        payload = {
            "model": self.current_model,
            "messages": self.conversation_history,
            "temperature": self.model_settings.get("temperature", 0.3),
            "max_tokens": self.model_settings.get("max_tokens", 8000),
            "stream": True
        }

        try:
            model_name = self._get_model_display_name()
            print_info(f"\n🤖 {model_name}: ", end="")

            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=120,
                stream=True
            )

            response.raise_for_status()

            full_response = ""

            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str.strip() == '[DONE]':
                            break

                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and data['choices']:
                                delta = data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    print(content, end="", flush=True)
                                    full_response += content
                        except:
                            continue

            print()

            if full_response:
                # Сохраняем ответ без контекста проекта
                clean_response = re.sub(r'\[Контекст проекта\].*', '', full_response, flags=re.DOTALL)
                self.conversation_history.append({
                    "role": "assistant",
                    "content": clean_response
                })

                # Парсим и выполняем действия
                actions = self._parse_actions(full_response)
                if actions:
                    self._execute_actions(actions)

                self.stats["messages_sent"] += 1
                return full_response

            return print_error("Получен пустой ответ от API")

        except requests.exceptions.RequestException as e:
            return print_error(f"Ошибка API: {e}")
        except Exception as e:
            return print_error(f"Ошибка: {e}")

    def _get_model_display_name(self) -> str:
        """Получает отображаемое имя модели"""
        for name, model_id in MODELS.items():
            if model_id == self.current_model:
                return name.upper()
        return self.current_model

    def _parse_actions(self, response: str) -> List[Dict]:
        """Парсит действия из ответа AI"""
        actions = []

        # Шаблон CREATE
        create_pattern = r'\[\[CREATE:(.+?)\]\][\s\S]*?```(?:[\w]*\n)?([\s\S]*?)```'
        for match in re.finditer(create_pattern, response):
            actions.append({
                'type': 'create',
                'path': match.group(1).strip(),
                'content': match.group(2).strip()
            })

        # Шаблон MODIFY
        modify_pattern = r'\[\[MODIFY:(.+?)\]\][\s\S]*?```(?:[\w]*\n)?([\s\S]*?)```'
        for match in re.finditer(modify_pattern, response):
            actions.append({
                'type': 'modify',
                'path': match.group(1).strip(),
                'content': match.group(2).strip()
            })

        # Шаблон EXEC
        exec_pattern = r'\[\[EXEC:(.+?)\]\]'
        for match in re.finditer(exec_pattern, response):
            actions.append({
                'type': 'exec',
                'command': match.group(1).strip()
            })

        return actions

    def _execute_actions(self, actions: List[Dict]):
        """Выполняет действия с файлами"""
        if not actions:
            return

        print_header("\n📝 ДЕЙСТВИЯ С ФАЙЛАМИ")
        for i, action in enumerate(actions, 1):
            if action['type'] == 'create':
                print(f"  {i}. 📄 Создать: {action['path']}")
            elif action['type'] == 'modify':
                print(f"  {i}. ✏️  Изменить: {action['path']}")
            elif action['type'] == 'exec':
                print(f"  {i}. ⚡ Выполнить: {action['command']}")

        if self.auto_approve:
            choice = 'A'
        else:
            print("\n[A] Все  [S] Пропустить  [1-N] Выбрать  [C] Отмена")
            choice = input("> ").strip().upper()

        if choice == 'C':
            print_warning("Отменено")
            return
        elif choice == 'S':
            print_warning("Пропущено")
            return
        elif choice == 'A':
            for action in actions:
                self._execute_action(action)
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(actions):
                self._execute_action(actions[idx])

    def _execute_action(self, action: Dict):
        """Выполняет одно действие"""
        try:
            if action['type'] == 'create':
                self._create_file(action['path'], action['content'])
            elif action['type'] == 'modify':
                self._modify_file(action['path'], action['content'])
            elif action['type'] == 'exec':
                self._execute_command(action['command'])
        except Exception as e:
            print_error(f"Ошибка выполнения: {e}")

    def _create_file(self, path: str, content: str):
        """Создаёт файл"""
        if not self.security.is_safe_path(path):
            print_error(f"Небезопасный путь: {path}")
            return

        if self.file_manager.create_file(path, content):
            self.stats["files_created"].append(path)

    def _modify_file(self, path: str, content: str):
        """Изменяет файл"""
        if not self.security.is_safe_path(path):
            print_error(f"Небезопасный путь: {path}")
            return

        if self.file_manager.modify_file(path, content):
            self.stats["files_modified"].append(path)

    def _execute_command(self, command: str):
        """Выполняет команду"""
        if not self.security.is_safe_command(command):
            print_error(f"Небезопасная команда: {command}")
            return

        if self.file_manager.execute_command(command):
            self.stats["commands_executed"].append(command)

    def _handle_command(self, user_input: str) -> str:
        """Обрабатывает внутренние команды"""
        parts = user_input.split()
        cmd = parts[0].lower()

        commands = {
            '/help': self._cmd_help,
            '/помощь': self._cmd_help,
            '/models': self._cmd_models,
            '/модели': self._cmd_models,
            '/model': lambda: self._cmd_switch_model(parts[1] if len(parts) > 1 else None),
            '/модель': lambda: self._cmd_switch_model(parts[1] if len(parts) > 1 else None),
            '/scan': self._cmd_scan,
            '/сканировать': self._cmd_scan,
            '/clear': self._cmd_clear,
            '/очистить': self._cmd_clear,
            '/save': self._cmd_save,
            '/сохранить': self._cmd_save,
            '/stats': self._cmd_stats,
            '/статистика': self._cmd_stats,
            '/exit': self._cmd_exit,
            '/выход': self._cmd_exit,
        }

        if cmd in commands:
            return commands[cmd]()

        return print_error(f"Неизвестная команда: {cmd}")

    def _cmd_help(self) -> str:
        """Показывает справку"""
        help_text = f"""
╔══════════════════════════════════════════════════════════════╗
║                    КОМАНДЫ HANDYCODE                         ║
╚══════════════════════════════════════════════════════════════╝

Проект: {self.project_path}
Модель: {self.current_model}

КОМАНДЫ:
  /help, /помощь          Показать эту справку
  /models, /модели        Список доступных моделей
  /model N, /модель N     Переключить модель
  /scan, /сканировать     Показать структуру проекта
  /clear, /очистить       Очистить историю разговора
  /save, /сохранить       Сохранить сессию в файл
  /stats, /статистика     Статистика сессии
  /exit, /выход           Выйти из программы

ПРИМЕРЫ ЗАПРОСОВ:
  Создай React приложение с TypeScript
  Добавь аутентификацию в мой FastAPI проект
  Напиши Telegram бота на Python
  Оптимизируй запросы к базе данных
  Напиши тесты для src/main.py
  Создай Docker образ для деплоя
"""
        print(help_text)
        return ""

    def _cmd_models(self) -> str:
        """Показывает доступные модели"""
        print_header("\n📋 ДОСТУПНЫЕ МОДЕЛИ")
        for name, model_id in MODELS.items():
            marker = " ← текущая" if model_id == self.current_model else ""
            desc = get_model_settings(model_id).get("description", "")
            print(f"  {name:20} {marker}")
            if desc:
                print(f"  {'':20} {desc}")
        return ""

    def _cmd_switch_model(self, model_name: Optional[str] = None) -> str:
        """Переключает модель AI"""
        if not model_name:
            self._cmd_models()
            model_name = input("\nНазвание модели: ").strip()

        if model_name in MODELS:
            self.current_model = MODELS[model_name]
            self.model_settings = get_model_settings(self.current_model)
            desc = self.model_settings.get("description", "")
            print_success(f"Переключено на: {model_name}")
            if desc:
                print_info(f"  {desc}")
            return ""

        return print_error(f"Неизвестная модель: {model_name}")

    def _cmd_scan(self) -> str:
        """Сканирует проект"""
        result = self.file_manager.scan_project()
        print(result)
        return ""

    def _cmd_clear(self) -> str:
        """Очищает историю"""
        self.conversation_history = [self.conversation_history[0]]
        return print_success("История очищена")

    def _cmd_save(self) -> str:
        """Сохраняет сессию"""
        return self.file_manager.save_session(
            self.conversation_history,
            self.current_model,
            self.stats
        )

    def _cmd_stats(self) -> str:
        """Показывает статистику"""
        duration = datetime.now() - self.stats["start_time"]

        stats_text = f"""
╔══════════════════════════════════════════════════════════════╗
║                   СТАТИСТИКА СЕССИИ                          ║
╚══════════════════════════════════════════════════════════════╝

Проект:     {self.project_path}
Модель:     {self.current_model}
Длительность: {duration}
Сообщений:  {self.stats["messages_sent"]}
Создано:    {len(self.stats["files_created"])} файлов
Изменено:   {len(self.stats["files_modified"])} файлов
Команд:     {len(self.stats["commands_executed"])}
"""
        print(stats_text)

        if self.stats["files_created"]:
            print("📄 Созданные файлы:")
            for f in self.stats["files_created"]:
                print(f"  ✅ {f}")

        if self.stats["files_modified"]:
            print("\n📝 Изменённые файлы:")
            for f in self.stats["files_modified"]:
                print(f"  ✏️  {f}")

        return ""

    def _cmd_exit(self) -> str:
        """Выходит из программы"""
        print_success("\n👋 До свидания!")
        os._exit(0)
        return ""

    def execute_command(self, command: str):
        """Выполняет одиночную команду"""
        print_header(f"\n🎯 Выполнение: {command}")
        self.send_message(command)
        print_success("\n✅ Готово!")

    def run(self):
        """Запускает интерактивный режим"""
        print_logo()
        print()
        print_info(f"📁 Проект: {self.project_path}")
        print_info(f"🤖 Модель: {self.current_model}")
        print_info(f"\n💡 Опишите, что нужно создать или изменить")
        print_info("   /help для списка команд\n")

        while True:
            try:
                self.reset_interrupt()
                user_input = input("❯ ").strip()
                if user_input:
                    self.send_message(user_input)
            except KeyboardInterrupt:
                continue
            except EOFError:
                print("\n👋 До свидания!")
                break