"""
Управление файлами для HandyCode
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from handycode.utils import print_success, print_error, print_warning, print_info


class FileManager:
    """Управляет файловыми операциями HandyCode"""

    def __init__(self, project_root: Path):
        """Инициализация файлового менеджера"""
        self.project_root = Path(project_root).resolve()
        self.allowed_extensions = {
            '.html', '.css', '.scss', '.sass', '.less',
            '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
            '.vue', '.svelte', '.astro',
            '.py', '.pyi', '.pyx', '.pxd',
            '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',
            '.xml', '.env', '.gitignore', '.dockerignore',
            '.md', '.mdx', '.rst', '.txt', '.log',
            '.sql', '.sh', '.bash', '.zsh', '.bat', '.ps1',
            '.java', '.kt', '.scala',
            '.cpp', '.c', '.h', '.hpp', '.cs',
            '.rs', '.go', '.rb', '.php', '.swift',
            '.dart', '.r', '.jl', '.lua',
            '.dockerfile', '.makefile', '.cmake',
        }

        self.excluded_dirs = {
            'node_modules', '__pycache__', '.git', '.svn',
            'venv', '.venv', 'env', '.env',
            'dist', 'build', '.next', '.nuxt',
            'target', 'out', '.idea', '.vscode',
            '.DS_Store', 'Thumbs.db',
        }

    def scan_project(self) -> str:
        """Сканирует проект и возвращает структуру"""
        if not self.project_root.exists():
            return ""

        try:
            lines = [f"📁 Проект: {self.project_root.name}"]

            # Собираем все файлы
            all_files = []
            for ext in self.allowed_extensions:
                all_files.extend(self.project_root.rglob(f"*{ext}"))

            # Фильтруем исключённые
            files = [
                f for f in all_files
                if f.is_file() and not any(ex in f.parts for ex in self.excluded_dirs)
            ]

            lines.append(f"📄 Файлов: {len(files)}")

            # Строим дерево
            if files:
                lines.append("\n📂 Структура:")
                tree = self._build_tree(files)
                lines.extend(self._print_tree(tree))

            # Ключевые файлы
            key_files = [
                'package.json', 'requirements.txt', 'Dockerfile',
                'README.md', 'setup.py', 'pyproject.toml',
                'tsconfig.json', '.gitignore', 'docker-compose.yml',
                'main.py', 'app.py', 'index.js', 'server.js'
            ]

            for file in files:
                if file.name in key_files:
                    try:
                        content = file.read_text(encoding='utf-8')
                        if len(content) < 5000:
                            lines.append(f"\n{'=' * 40}")
                            lines.append(f"📄 {file.relative_to(self.project_root)}")
                            lines.append('=' * 40)
                            lines.append(content)
                    except:
                        pass

            return '\n'.join(lines)
        except Exception as e:
            return f"Ошибка сканирования: {e}"

    def _build_tree(self, files: List[Path]) -> dict:
        """Строит дерево директорий"""
        tree = {}
        for file in files:
            try:
                relative = file.relative_to(self.project_root)
                parts = relative.parts
                current = tree
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]

                if '__files__' not in current:
                    current['__files__'] = []
                current['__files__'].append(parts[-1])
            except:
                pass
        return tree

    def _print_tree(self, node: dict, indent: str = "") -> List[str]:
        """Выводит дерево директорий"""
        result = []
        # Сначала директории
        dirs = sorted([k for k in node if k != '__files__'])
        for d in dirs:
            result.append(f"{indent}📁 {d}/")
            result.extend(self._print_tree(node[d], indent + "  "))
        # Потом файлы
        if '__files__' in node:
            for f in sorted(node['__files__']):
                result.append(f"{indent}📄 {f}")
        return result

    def create_file(self, path: str, content: str) -> bool:
        """Создаёт файл"""
        try:
            full_path = self.project_root / path

            # Создаём директории
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Резервная копия если файл существует
            if full_path.exists():
                backup = full_path.with_suffix(full_path.suffix + '.bak')
                shutil.copy2(full_path, backup)
                print_warning(f"📦 Резервная копия: {backup.name}")

            # Записываем файл
            full_path.write_text(content, encoding='utf-8')

            lines = content.count('\n') + 1
            size = len(content)
            print_success(f"✅ Создан: {path} ({lines} строк, {size} байт)")

            return True
        except Exception as e:
            print_error(f"Ошибка создания {path}: {e}")
            return False

    def modify_file(self, path: str, content: str) -> bool:
        """Изменяет файл"""
        try:
            full_path = self.project_root / path

            if not full_path.exists():
                print_warning(f"Файл не существует, создаём: {path}")
                return self.create_file(path, content)

            # Резервная копия
            backup = full_path.with_suffix(full_path.suffix + '.bak')
            shutil.copy2(full_path, backup)
            print_warning(f"📦 Резервная копия: {backup.name}")

            # Записываем новое содержимое
            full_path.write_text(content, encoding='utf-8')

            lines = content.count('\n') + 1
            print_success(f"✅ Изменён: {path} ({lines} строк)")

            return True
        except Exception as e:
            print_error(f"Ошибка изменения {path}: {e}")
            return False

    def execute_command(self, command: str, timeout: int = 300) -> bool:
        """Выполняет команду"""
        try:
            print_warning(f"\n⚡ Выполнение: {command}")

            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.stdout:
                print(result.stdout)

            if result.returncode != 0:
                if result.stderr:
                    print_error(result.stderr)
                print_error(f"Команда завершилась с ошибкой (код {result.returncode})")
                return False

            print_success("✅ Команда выполнена успешно")
            return True

        except subprocess.TimeoutExpired:
            print_error(f"Таймаут выполнения ({timeout}с)")
            return False
        except Exception as e:
            print_error(f"Ошибка выполнения: {e}")
            return False

    def save_session(self, history: List[Dict], model: str, stats: Dict) -> str:
        """Сохраняет сессию в файл"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"handycode_сессия_{timestamp}.md"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# Сессия HandyCode\n\n")
                f.write(f"**Дата:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Модель:** {model}\n")
                f.write(f"**Сообщений:** {stats.get('messages_sent', 0)}\n\n")
                f.write("---\n\n")

                for msg in history[1:]:  # Пропускаем системный промпт
                    if msg['role'] == 'user':
                        f.write(f"## 👤 Пользователь\n\n{msg['content']}\n\n")
                    else:
                        clean = msg['content']
                        # Убираем маркеры действий для читаемости
                        clean = clean.replace('[[CREATE:', '').replace('[[MODIFY:', '').replace('[[EXEC:', '')
                        f.write(f"## 🤖 Ассистент\n\n{clean}\n\n---\n\n")

            return print_success(f"✅ Сессия сохранена: {filename}")
        except Exception as e:
            return print_error(f"Ошибка сохранения: {e}")