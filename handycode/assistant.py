"""
Основной класс ассистента HandyCode (без внешних зависимостей)
"""

import os
import re
import json
import ssl
import urllib.request
import urllib.error
import readline
import atexit
import signal
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

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
            raise ValueError("API ключ не найден")

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
3. Execute shell commands (npm install, pip install, git, etc.)
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
        histfile = self.config.config_dir / 'history'
        try:
            readline.read_history_file(str(histfile))
            readline.set_history_length(1000)
        except:
            pass
        atexit.register(readline.write_history_file, str(histfile))

    def _signal_handler(self, sig, frame):
        self._interrupt_count += 1
        if self._interrupt_count == 1:
            print("\n\nPress Ctrl+C again to exit")
        else:
            os._exit(0)

    def reset_interrupt(self):
        self._interrupt_count = 0

    def _make_request(self, data: dict) -> str:
        """Отправляет запрос через urllib (без requests)"""
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

        # Игнорируем SSL ошибки (только для отладки)
        ctx = ssl.create_default_context()

        try:
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
            print_info(f"\n🤖 {self.current_model}:")
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

            return print_error("Empty response")

        except Exception as e:
            return print_error(f"Error: {e}")

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
            print("\n[A] All  [S] Skip  [C] Cancel")
            choice = input("> ").strip().upper()

        if choice == 'C':
            return
        elif choice == 'S':
            return
        elif choice == 'A':
            for action in actions:
                self._execute_action(action)

    def _execute_action(self, action: Dict):
        try:
            if action['type'] == 'create':
                self.file_manager.create_file(action['path'], action['content'])
            elif action['type'] == 'modify':
                self.file_manager.modify_file(action['path'], action['content'])
            elif action['type'] == 'exec':
                self.file_manager.execute_command(action['command'])
        except Exception as e:
            print_error(f"Error: {e}")

    def _handle_command(self, user_input: str) -> str:
        cmd = user_input.lower().split()[0]

        if cmd in ['/help', '/h']:
            print("\nCommands: /help /scan /models /clear /save /stats /exit")
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

    def execute_command(self, command: str):
        self.send_message(command)

    def run(self):
        print_logo()
        print_info(f"\nProject: {self.project_path}")
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
                break