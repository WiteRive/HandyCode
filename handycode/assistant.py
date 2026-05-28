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

# readline только для Linux/Mac
try:
    import readline
    HAS_READLINE = True
except ImportError:
    HAS_READLINE = False

# requests или urllib
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
    """Основной класс ассистента HandyCode"""

    def __init__(
        self,
        project_path: Path,
        model: str = "deepseek",
        auto_approve: bool = False,
        config: Optional[Config] = None
    ):
        self.project_path = project_path
        self.auto_approve = auto_approve
        self.config = config or Config()

        self.api_key = self.config.get_api_key()
        if not self.api_key:
            raise ValueError("API ключ не найден. Установите OPENROUTER_API_KEY")

        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

        self.current_model = MODELS.get(model, MODELS["deepseek"])
        self.model_settings = get_model_settings(self.current_model)

        self.conversation_history = [
            {
                "role": "system",
                "content": self._get_system_prompt()
            }
        ]

        self.file_manager = FileManager(self.project_path)
        self.security = SecurityChecker(self.project_path)

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

    def _get_system_prompt(self) -> str:
        return """You are HandyCode, a powerful AI code assistant for the command line.

CAPABILITIES:
1. Create complete projects from scratch
2. Modify existing files
3. Execute shell commands
4. Analyze code and find bugs
5. Suggest architectural improvements

ACTION FORMAT:
To create a file:
[[CREATE:path/to/file.ext]]
full file content here

To modify a file:
[[MODIFY:path/to/file.ext]]
complete new content of the file

To run commands:
[[EXEC:command to execute]]

IMPORTANT:
1. ALWAYS show COMPLETE file contents
2. Create ALL necessary files
3. Verify the project is ready to run

Speak Russian. Write code in English."""

    def _setup_readline(self):
        """Настройка истории команд (только Linux/Mac)"""
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
            print("\n\nPress Ctrl+C again to exit, or /exit")
            signal.signal(signal.SIGINT, self._signal_handler)
        else:
            print("\n\nGoodbye!")
            os._exit(0)

    def reset_interrupt(self):
        self._interrupt_count = 0

    def _make_request(self, data: dict) -> str:
        """Отправляет запрос к API"""
        if HAS_REQUESTS:
            return self._make_request_requests(data)
        else:
            return self._make_request_urllib(data)

    def _make_request_requests(self, data: dict) -> str:
        """Запрос через requests"""
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "HandyCode"
                },
                json=data,
                timeout=120
            )

            response.raise_for_status()
            result = response.json()

            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']

            return ""
        except Exception as e:
            print_error(f"API Error: {e}")
            return ""

    def _make_request_urllib(self, data: dict) -> str:
        """Запрос через urllib"""
        try:
            json_data = json.dumps(data).encode('utf-8')

            req = urllib.request.Request(
                self.api_url,
                data=json_data,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "HandyCode"
                },
                method='POST'
            )

            ctx = ssl.create_default_context()

            with urllib.request.urlopen(req, context=ctx, timeout=120) as response:
                result = json.loads(response.read().decode('utf-8'))

                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']

                return ""
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print_error(f"HTTP Error {e.code}: {error_body}")
            return ""
        except Exception as e:
            print_error(f"Request error: {e}")
            return ""

    def send_message(self, user_input: str) -> str:
        if user_input.startswith('/'):
            return self._handle_command(user_input)

        context_keywords = [
            'create', 'make', 'build', 'project', 'code', 'file',
            'app', 'api', 'component', 'module', 'class',
        ]

        if any(kw in user_input.lower() for kw in context_keywords):
            context = self.file_manager.scan_project()
            if context:
                user_input += f"\n\n[Project Context]\n{context}"

        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        payload = {
            "model": self.current_model,
            "messages": self.conversation_history,
            "temperature": self.model_settings.get("temperature", 0.3),
            "max_tokens": self.model_settings.get("max_tokens", 8000),
        }

        try:
            model_name = self._get_model_display_name()
            print_info(f"\n{model_name}: ", end="")

            response = self._make_request(payload)

            if response:
                print(response)

                self.conversation_history.append({
                    "role": "assistant",
                    "content": response
                })

                actions = self._parse_actions(response)
                if actions:
                    self._execute_actions(actions)

                self.stats["messages_sent"] += 1
                return response

            return print_error("Empty response from API")

        except Exception as e:
            return print_error(f"Error: {e}")

    def _get_model_display_name(self) -> str:
        for name, model_id in MODELS.items():
            if model_id == self.current_model:
                return name.upper()
        return self.current_model

    def _parse_actions(self, response: str) -> List[Dict]:
        actions = []

        create_pattern = r'\[\[CREATE:(.+?)\]\][\s\S]*?```(?:[\w]*\n)?([\s\S]*?)```'
        for match in re.finditer(create_pattern, response):
            actions.append({
                'type': 'create',
                'path': match.group(1).strip(),
                'content': match.group(2).strip()
            })

        modify_pattern = r'\[\[MODIFY:(.+?)\]\][\s\S]*?```(?:[\w]*\n)?([\s\S]*?)```'
        for match in re.finditer(modify_pattern, response):
            actions.append({
                'type': 'modify',
                'path': match.group(1).strip(),
                'content': match.group(2).strip()
            })

        exec_pattern = r'\[\[EXEC:(.+?)\]\]'
        for match in re.finditer(exec_pattern, response):
            actions.append({
                'type': 'exec',
                'command': match.group(1).strip()
            })

        return actions

    def _execute_actions(self, actions: List[Dict]):
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
            print("\n[A] All  [S] Skip all  [C] Cancel")
            choice = input("> ").strip().upper()

        if choice == 'C':
            print_warning("Cancelled")
            return
        elif choice == 'S':
            print_warning("Skipped")
            return
        elif choice == 'A':
            for action in actions:
                self._execute_action(action)

    def _execute_action(self, action: Dict):
        try:
            if action['type'] == 'create':
                self._create_file(action['path'], action['content'])
            elif action['type'] == 'modify':
                self._modify_file(action['path'], action['content'])
            elif action['type'] == 'exec':
                self._execute_command(action['command'])
        except Exception as e:
            print_error(f"Action failed: {e}")

    def _create_file(self, path: str, content: str):
        if not self.security.is_safe_path(path):
            print_error(f"Unsafe path: {path}")
            return

        if self.file_manager.create_file(path, content):
            self.stats["files_created"].append(path)

    def _modify_file(self, path: str, content: str):
        if not self.security.is_safe_path(path):
            print_error(f"Unsafe path: {path}")
            return

        if self.file_manager.modify_file(path, content):
            self.stats["files_modified"].append(path)

    def _execute_command(self, command: str):
        if not self.security.is_safe_command(command):
            print_error(f"Unsafe command: {command}")
            return

        if self.file_manager.execute_command(command):
            self.stats["commands_executed"].append(command)

    def _handle_command(self, user_input: str) -> str:
        parts = user_input.split()
        cmd = parts[0].lower()

        if cmd in ['/help', '/h', '/помощь']:
            print("""
COMMANDS:
  /help          Show help
  /scan          Scan project
  /models        List models
  /model NAME    Switch model
  /clear         Clear history
  /save          Save session
  /stats         Statistics
  /exit          Exit
            """)
        elif cmd in ['/scan', '/s', '/сканировать']:
            print(self.file_manager.scan_project())
        elif cmd in ['/models', '/m', '/модели']:
            for name, model_id in MODELS.items():
                marker = " (current)" if model_id == self.current_model else ""
                print(f"  {name}{marker}")
        elif cmd in ['/clear', '/c', '/очистить']:
            self.conversation_history = [self.conversation_history[0]]
            print_success("Cleared")
        elif cmd in ['/save', '/сохранить']:
            self.file_manager.save_session(
                self.conversation_history,
                self.current_model,
                self.stats
            )
        elif cmd in ['/stats', '/статистика']:
            duration = datetime.now() - self.stats["start_time"]
            print(f"Messages: {self.stats['messages_sent']}")
            print(f"Created: {len(self.stats['files_created'])} files")
            print(f"Modified: {len(self.stats['files_modified'])} files")
            print(f"Commands: {len(self.stats['commands_executed'])}")
            print(f"Duration: {duration}")
        elif cmd in ['/exit', '/q', '/выход']:
            print_success("Goodbye!")
            os._exit(0)
        elif cmd in ['/model', '/модель'] and len(parts) > 1:
            model_name = parts[1]
            if model_name in MODELS:
                self.current_model = MODELS[model_name]
                self.model_settings = get_model_settings(self.current_model)
                print_success(f"Switched to: {model_name}")
            else:
                print_error(f"Unknown model: {model_name}")
        else:
            print_error(f"Unknown command: {cmd}")

        return ""

    def execute_command(self, command: str):
        print_header(f"\nExecuting: {command}")
        self.send_message(command)
        print_success("\nDone!")

    def run(self):
        print_logo()
        print()
        print_info(f"Project: {self.project_path}")
        print_info(f"Model: {self.current_model}")
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
                print("\nGoodbye!")
                break