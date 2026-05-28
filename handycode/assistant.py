"""
Основной класс ассистента HandyCode
"""

import os
import re
import json
import sys
import atexit
import signal
import shutil
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

        project_context = self._build_project_context()

        self.conversation_history = [
            {"role": "system", "content": self._get_system_prompt() + project_context}
        ]

        self.stats = {
            "messages_sent": 0,
            "files_created": [],
            "files_modified": [],
            "files_deleted": [],
            "commands_executed": [],
            "start_time": datetime.now()
        }

        self._setup_readline()
        signal.signal(signal.SIGINT, self._signal_handler)
        self._interrupt_count = 0

    def _build_project_context(self):
        """Собирает контекст проекта"""
        context = f"\n\n=== PROJECT CONTEXT ===\n"
        context += f"Working directory: {self.project_path}\n"
        context += f"OS: {sys.platform}\n"

        try:
            all_files = []
            for ext in self.file_manager.allowed_extensions:
                all_files.extend(self.project_path.rglob(f"*{ext}"))

            all_files.extend(self.project_path.rglob("*"))
            all_files = list(set(all_files))

            files = [f for f in all_files if f.is_file()
                     and not any(ex in f.parts for ex in self.file_manager.excluded_dirs)]

            context += f"\nFiles in project ({len(files)} total):\n"

            for file in sorted(files):
                try:
                    rel_path = file.relative_to(self.project_path)
                    size = file.stat().st_size
                    context += f"  - {rel_path} ({self._format_size(size)})\n"
                except:
                    pass

            context += f"\nFile contents (for context):\n"
            total_size = 0
            max_total = 30000

            for file in sorted(files):
                if total_size >= max_total:
                    break

                try:
                    content = file.read_text(encoding='utf-8', errors='ignore')
                    if len(content) > 3000:
                        content = content[:3000] + "\n... (truncated)"

                    rel_path = file.relative_to(self.project_path)
                    context += f"\n=== {rel_path} ===\n{content}\n"
                    total_size += len(content)
                except:
                    pass

        except Exception as e:
            context += f"\nError: {e}\n"

        return context

    def _format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.0f}{unit}"
            size /= 1024
        return f"{size:.0f}GB"

    def _get_system_prompt(self):
        return """You are HandyCode, a powerful AI code assistant with FULL file system access.

YOU CAN:
- CREATE files: [[CREATE:path/to/file.ext]] content
- MODIFY files: [[MODIFY:path/to/file.ext]] new content
- DELETE files: [[DELETE:path/to/file.ext]]
- READ files: [[READ:path/to/file.ext]]
- LIST directory: [[LIST:path/to/dir]]
- EXECUTE commands: [[EXEC:command]]
- CREATE folders: [[MKDIR:path/to/dir]]
- COPY files: [[COPY:source]] -> [[CREATE:destination]] (use CREATE with content)
- MOVE files: [[MOVE:source]] [[CREATE:destination]]

FILES ARE AUTO-CREATED without asking. Only COMMANDS need confirmation.
You see ALL project files and their contents.

RULES:
1. CREATE/MODIFY/DELETE/MKDIR happen automatically
2. EXEC commands need user confirmation
3. Show COMPLETE file contents
4. Create ALL needed files
5. Use the project context

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

    def _make_request_stream(self, data):
        """Отправляет запрос и получает ответ в реальном времени"""
        if not HAS_REQUESTS:
            return self._make_request(data)

        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={**data, "stream": True},
                timeout=120,
                stream=True
            )

            full_response = ""

            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data_str)
                            if 'choices' in chunk and chunk['choices']:
                                delta = chunk['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    print(content, end="", flush=True)
                                    full_response += content
                        except:
                            continue

            print()
            return full_response

        except Exception as e:
            print_error(f"API Error: {e}")
            return ""

    def _make_request(self, data):
        """Обычный запрос без стриминга"""
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
            response = self._make_request_stream(payload)

            if response:
                self.conversation_history.append({"role": "assistant", "content": response})

                actions = self._parse_actions(response)
                if actions:
                    self._execute_actions_smart(actions)

                self.stats["messages_sent"] += 1
                return response
        except Exception as e:
            return print_error(f"Error: {e}")

    def _parse_actions(self, response):
        """Парсит все типы действий"""
        actions = []

        # CREATE
        for match in re.finditer(r'\[\[CREATE:(.+?)\]\](.*?)(?=\[\[|$)', response, re.DOTALL):
            path = match.group(1).strip()
            content = match.group(2).strip()
            content = re.sub(r'^```[\w]*\n?', '', content)
            content = re.sub(r'\n?```$', '', content)
            actions.append({'type': 'create', 'path': path, 'content': content})

        # MODIFY
        for match in re.finditer(r'\[\[MODIFY:(.+?)\]\](.*?)(?=\[\[|$)', response, re.DOTALL):
            path = match.group(1).strip()
            content = match.group(2).strip()
            content = re.sub(r'^```[\w]*\n?', '', content)
            content = re.sub(r'\n?```$', '', content)
            actions.append({'type': 'modify', 'path': path, 'content': content})

        # DELETE
        for match in re.finditer(r'\[\[DELETE:(.+?)\]\]', response):
            actions.append({'type': 'delete', 'path': match.group(1).strip()})

        # READ
        for match in re.finditer(r'\[\[READ:(.+?)\]\]', response):
            actions.append({'type': 'read', 'path': match.group(1).strip()})

        # LIST
        for match in re.finditer(r'\[\[LIST:(.+?)\]\]', response):
            actions.append({'type': 'list', 'path': match.group(1).strip()})

        # MKDIR
        for match in re.finditer(r'\[\[MKDIR:(.+?)\]\]', response):
            actions.append({'type': 'mkdir', 'path': match.group(1).strip()})

        # COPY
        for match in re.finditer(r'\[\[COPY:(.+?)\]\]', response):
            actions.append({'type': 'copy', 'path': match.group(1).strip()})

        # MOVE
        for match in re.finditer(r'\[\[MOVE:(.+?)\]\]', response):
            actions.append({'type': 'move', 'path': match.group(1).strip()})

        # EXEC
        for match in re.finditer(r'\[\[EXEC:(.+?)\]\]', response):
            actions.append({'type': 'exec', 'command': match.group(1).strip()})

        return actions

    def _execute_actions_smart(self, actions):
        """Умное выполнение: файлы авто, команды с подтверждением"""
        if not actions:
            return

        file_actions = [a for a in actions if a['type'] in ['create', 'modify', 'delete', 'mkdir', 'read', 'list', 'copy', 'move']]
        exec_actions = [a for a in actions if a['type'] == 'exec']

        # Файловые операции выполняем автоматически
        if file_actions:
            print_header("\nAUTO FILE OPERATIONS:")
            for action in file_actions:
                self._execute_action(action)

        # Команды требуют подтверждения
        if exec_actions:
            print_header("\nCOMMANDS TO EXECUTE:")
            for i, action in enumerate(exec_actions, 1):
                print(f"  {i}. {action['command']}")

            print("\n[A] Execute all  [S] Skip all  [1-N] Select  [C] Cancel")
            choice = input("> ").strip().upper()

            if choice == 'A':
                for action in exec_actions:
                    self._execute_action(action)
            elif choice == 'S':
                print_warning("Skipped")
            elif choice == 'C':
                print_warning("Cancelled")
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(exec_actions):
                    self._execute_action(exec_actions[idx])

    def _execute_action(self, action):
        """Выполняет одно действие"""
        try:
            if action['type'] == 'create':
                self.file_manager.create_file(action['path'], action['content'])
                self.stats["files_created"].append(action['path'])

            elif action['type'] == 'modify':
                self.file_manager.modify_file(action['path'], action['content'])
                self.stats["files_modified"].append(action['path'])

            elif action['type'] == 'delete':
                self._delete_file(action['path'])
                self.stats["files_deleted"].append(action['path'])

            elif action['type'] == 'read':
                self._read_file(action['path'])

            elif action['type'] == 'list':
                self._list_directory(action['path'])

            elif action['type'] == 'mkdir':
                self._make_directory(action['path'])

            elif action['type'] == 'exec':
                self.file_manager.execute_command(action['command'])
                self.stats["commands_executed"].append(action['command'])

            elif action['type'] == 'copy':
                self._copy_file(action['path'])

            elif action['type'] == 'move':
                self._move_file(action['path'])

        except Exception as e:
            print_error(f"Failed: {e}")

    def _delete_file(self, path):
        """Удаляет файл"""
        full_path = self.project_path / path
        if not self.security.is_safe_path(str(path)):
            print_error(f"Unsafe: {path}")
            return

        if full_path.exists():
            # Бэкап перед удалением
            backup = full_path.with_suffix(full_path.suffix + '.bak')
            shutil.copy2(full_path, backup)
            full_path.unlink()
            print_success(f"Deleted: {path} (backup: {backup.name})")
        else:
            print_warning(f"Not found: {path}")

    def _read_file(self, path):
        """Читает и показывает файл"""
        full_path = self.project_path / path
        if full_path.exists():
            content = full_path.read_text(encoding='utf-8', errors='ignore')
            print_header(f"\n=== {path} ===")
            print(content)
            print_header("=" * (len(path) + 8))
        else:
            print_warning(f"Not found: {path}")

    def _list_directory(self, path):
        """Показывает содержимое директории"""
        full_path = self.project_path / path
        if full_path.exists() and full_path.is_dir():
            items = sorted(full_path.iterdir())
            print_header(f"\n=== {path}/ ({len(items)} items) ===")
            for item in items:
                if item.is_dir():
                    print(f"  [DIR]  {item.name}/")
                else:
                    size = item.stat().st_size
                    print(f"  [FILE] {item.name} ({self._format_size(size)})")
        else:
            print_warning(f"Not found: {path}")

    def _make_directory(self, path):
        """Создаёт директорию"""
        full_path = self.project_path / path
        full_path.mkdir(parents=True, exist_ok=True)
        print_success(f"Created dir: {path}")

    def _copy_file(self, source):
        """Копирует файл (ожидает, что следом будет CREATE)"""
        print_info(f"Copy source noted: {source}")

    def _move_file(self, source):
        """Перемещает файл (ожидает, что следом будет CREATE)"""
        full_path = self.project_path / source
        if full_path.exists():
            print_info(f"Move source noted: {source}")
        else:
            print_warning(f"Source not found: {source}")

    def _handle_command(self, user_input):
        cmd = user_input.lower().split()[0]
        if cmd in ['/help', '/h']:
            print("""
COMMANDS:
  /help      Show help
  /scan      Scan project
  /models    List models
  /model N   Switch model
  /clear     Clear history
  /save      Save session
  /stats     Statistics
  /exit      Exit
            """)
        elif cmd in ['/scan', '/s']:
            print(self.file_manager.scan_project())
        elif cmd in ['/models', '/m']:
            for name in MODELS:
                print(f"  {name}")
        elif cmd in ['/clear', '/c']:
            self.conversation_history = [self.conversation_history[0]]
            print_success("Cleared")
        elif cmd in ['/save']:
            self.file_manager.save_session(self.conversation_history, self.current_model, self.stats)
        elif cmd in ['/stats']:
            duration = datetime.now() - self.stats["start_time"]
            print(f"Messages: {self.stats['messages_sent']}")
            print(f"Created: {len(self.stats['files_created'])} files")
            print(f"Modified: {len(self.stats['files_modified'])} files")
            print(f"Deleted: {len(self.stats['files_deleted'])} files")
            print(f"Commands: {len(self.stats['commands_executed'])}")
            print(f"Duration: {duration}")
        elif cmd in ['/exit', '/q']:
            print_success("Goodbye!")
            os._exit(0)
        elif cmd in ['/model'] and len(user_input.split()) > 1:
            model_name = user_input.split()[1]
            if model_name in MODELS:
                self.current_model = MODELS[model_name]
                self.model_settings = get_model_settings(self.current_model)
                print_success(f"Switched to: {model_name}")
            else:
                print_error(f"Unknown model: {model_name}")
        return ""

    def execute_command(self, command):
        self.send_message(command)

    def run(self):
        print_logo()
        print()
        print_info(f"Project: {self.project_path}")
        print_info(f"Model: {self.current_model}")

        try:
            files = list(self.project_path.rglob("*"))
            files = [f for f in files if f.is_file()
                     and not any(ex in f.parts for ex in self.file_manager.excluded_dirs)]
            visible = [f for f in files if not f.name.startswith('.')]
            if visible:
                print_info(f"\nFound {len(visible)} files (AI sees all)")
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