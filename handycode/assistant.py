"""
Основной класс ассистента HandyCode
"""

import os
import re
import json
import sys
import atexit
import signal
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

try:
    import readline
    HAS_READLINE = True
except ImportError:
    HAS_READLINE = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request
    import urllib.error
    import ssl

from handycode.config import Config
from handycode.models import MODELS, get_model_settings
from handycode.file_manager import FileManager
from handycode.security import SecurityChecker
from handycode.utils import (
    print_colored, print_header, print_success,
    print_error, print_warning, print_info, print_logo
)


class HandyCode:
    def __init__(self, project_path, model="deepseek", auto_approve=False, config=None):
        self.project_path = project_path
        self.auto_approve = auto_approve
        self.config = config or Config()

        self.api_key = self.config.get_api_key()
        if not self.api_key:
            raise ValueError("API key not found")

        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.current_model = MODELS.get(model, MODELS["deepseek"])
        self.model_settings = get_model_settings(self.current_model)

        self.file_manager = FileManager(self.project_path)
        self.security = SecurityChecker(self.project_path)

        # Сканируем проект и создаём системный промпт с контекстом
        project_context = self._build_project_context()

        self.conversation_history = [
            {"role": "system", "content": self._get_system_prompt() + project_context}
        ]

        self.stats = {
            "messages_sent": 0,
            "files_created": [],
            "files_modified": [],
            "commands_executed": [],
            "start_time": datetime.now()
        }

        self._setup_readline()
        signal.signal(signal.SIGINT, self._signal_handler)
        self._interrupt_count = 0

    def _build_project_context(self):
        """Собирает контекст проекта для системного промпта"""
        context = f"\n\n=== PROJECT CONTEXT ===\n"
        context += f"Working directory: {self.project_path}\n"

        try:
            # Получаем все файлы
            all_files = []
            for ext in self.file_manager.allowed_extensions:
                all_files.extend(self.project_path.rglob(f"*{ext}"))

            # Фильтруем
            files = [f for f in all_files if f.is_file()
                     and not any(ex in f.parts for ex in self.file_manager.excluded_dirs)]

            context += f"\nFiles in project ({len(files)} total):\n"

            # Список файлов
            for file in sorted(files):
                try:
                    rel_path = file.relative_to(self.project_path)
                    size = file.stat().st_size
                    context += f"  - {rel_path} ({size} bytes)\n"
                except:
                    pass

            # Содержимое файлов (до 50KB суммарно)
            context += f"\nFile contents:\n"
            total_size = 0
            max_total = 50000

            for file in sorted(files):
                if total_size >= max_total:
                    context += f"\n... (showing first {total_size} bytes, {len(files)} files total)\n"
                    break

                try:
                    content = file.read_text(encoding='utf-8', errors='ignore')
                    if len(content) > 5000:
                        content = content[:5000] + "\n... (truncated)"

                    rel_path = file.relative_to(self.project_path)
                    context += f"\n=== {rel_path} ===\n{content}\n"
                    total_size += len(content)
                except:
                    pass

        except Exception as e:
            context += f"\nError scanning project: {e}\n"

        return context

    def _get_system_prompt(self):
        return """You are HandyCode, a powerful AI code assistant.

CAPABILITIES:
1. Create files
2. Modify existing files  
3. Execute commands
4. Analyze code
5. Create projects from scratch

ACTION FORMAT:
[[CREATE:path/to/file.ext]]
file content here
(no need for ``` markers)

[[MODIFY:path/to/file.ext]]
new file content here

[[EXEC:command]]

IMPORTANT:
1. ALWAYS create/modify files BEFORE executing commands
2. Show COMPLETE file contents
3. Use the project context provided below

You can see all files in the project and their contents below.
Speak Russian. Write code in English."""

    def _setup_readline(self):
        if not HAS_READLINE:
            return
        try:
            histfile = os.path.join(os.path.expanduser("~"), ".handycode", "history")
            os.makedirs(os.path.dirname(histfile), exist_ok=True)
            readline.read_history_file(histfile)
            readline.set_history_length(1000)
            atexit.register(readline.write_history_file, histfile)
        except:
            pass

    def _signal_handler(self, sig, frame):
        self._interrupt_count += 1
        if self._interrupt_count == 1:
            print("\n\nPress Ctrl+C again to exit")
        else:
            os._exit(0)

    def reset_interrupt(self):
        self._interrupt_count = 0

    def _make_request(self, data):
        if HAS_REQUESTS:
            try:
                response = requests.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=data,
                    timeout=120
                )
                result = response.json()
                if 'choices' in result and result['choices']:
                    return result['choices'][0]['message']['content']
            except Exception as e:
                print_error(f"API Error: {e}")
        return ""

    def send_message(self, user_input):
        if user_input.startswith('/'):
            return self._handle_command(user_input)

        self.conversation_history.append({"role": "user", "content": user_input})

        payload = {
            "model": self.current_model,
            "messages": self.conversation_history,
            "temperature": self.model_settings.get("temperature", 0.3),
            "max_tokens": self.model_settings.get("max_tokens", 8000),
        }

        try:
            print_info(f"\nDEEPSEEK:")
            response = self._make_request(payload)

            if response:
                print(response)
                self.conversation_history.append({"role": "assistant", "content": response})

                actions = self._parse_actions(response)
                if actions:
                    self._execute_actions(actions)

                self.stats["messages_sent"] += 1
                return response
        except Exception as e:
            return print_error(f"Error: {e}")

    def _parse_actions(self, response):
        actions = []

        # CREATE
        create_pattern = r'\[\[CREATE:(.+?)\]\](.*?)(?=\[\[|$)'
        for match in re.finditer(create_pattern, response, re.DOTALL):
            path = match.group(1).strip()
            content = match.group(2).strip()
            content = re.sub(r'^```[\w]*\n', '', content)
            content = re.sub(r'\n```$', '', content)
            if content:
                actions.append({'type': 'create', 'path': path, 'content': content})

        # MODIFY
        modify_pattern = r'\[\[MODIFY:(.+?)\]\](.*?)(?=\[\[|$)'
        for match in re.finditer(modify_pattern, response, re.DOTALL):
            path = match.group(1).strip()
            content = match.group(2).strip()
            content = re.sub(r'^```[\w]*\n', '', content)
            content = re.sub(r'\n```$', '', content)
            if content:
                actions.append({'type': 'modify', 'path': path, 'content': content})

        # EXEC
        for match in re.finditer(r'\[\[EXEC:(.+?)\]\]', response):
            actions.append({'type': 'exec', 'command': match.group(1).strip()})

        # Сортировка: сначала файлы, потом команды
        return sorted(actions, key=lambda x: 0 if x['type'] in ['create', 'modify'] else 1)

    def _execute_actions(self, actions):
        if not actions:
            return

        print_header("\nFILE ACTIONS")
        for i, action in enumerate(actions, 1):
            if action['type'] == 'create':
                print(f"  {i}. Create: {action['path']}")
            elif action['type'] == 'modify':
                print(f"  {i}. Modify: {action['path']}")
            elif action['type'] == 'exec':
                print(f"  {i}. Execute: {action['command']}")

        if self.auto_approve:
            choice = 'A'
        else:
            print("\n[A] All  [S] Skip  [C] Cancel")
            choice = input("> ").strip().upper()

        if choice == 'A':
            for action in actions:
                self._execute_action(action)
        elif choice == 'S':
            return
        elif choice == 'C':
            return

    def _execute_action(self, action):
        if action['type'] == 'create':
            self.file_manager.create_file(action['path'], action['content'])
        elif action['type'] == 'modify':
            self.file_manager.modify_file(action['path'], action['content'])
        elif action['type'] == 'exec':
            self.file_manager.execute_command(action['command'])

    def _handle_command(self, user_input):
        cmd = user_input.lower().split()[0]
        if cmd in ['/help', '/h']:
            print("\nCommands: /help /scan /models /clear /stats /exit")
        elif cmd in ['/scan', '/s']:
            print(self.file_manager.scan_project())
        elif cmd in ['/models', '/m']:
            for name in MODELS:
                print(f"  {name}")
        elif cmd in ['/clear', '/c']:
            self.conversation_history = [self.conversation_history[0]]
            print_success("Cleared")
        elif cmd in ['/exit', '/q']:
            os._exit(0)
        return ""

    def execute_command(self, command):
        self.send_message(command)

    def run(self):
        print_logo()
        print()
        print_info(f"Project: {self.project_path}")
        print_info(f"Model: {self.current_model}")

        # Показываем найденные файлы
        try:
            files = list(self.project_path.rglob("*"))
            files = [f for f in files if f.is_file()
                     and not any(ex in f.parts for ex in self.file_manager.excluded_dirs)]
            visible = [f for f in files if not f.name.startswith('.')]
            if visible:
                print_info(f"\nFound {len(visible)} files in project")
        except:
            pass

        print_info("/help for commands\n")

        while True:
            try:
                self.reset_interrupt()
                user_input = input("> ").strip()
                if user_input:
                    self.send_message(user_input)
            except KeyboardInterrupt:
                continue
            except EOFError:
                break