"""
Интерфейс командной строки для HandyCode
"""

import argparse
import sys
import os
from pathlib import Path

from handycode.assistant import HandyCode
from handycode.config import Config
from handycode.utils import print_error, print_warning, print_info, print_logo, print_success


def create_parser() -> argparse.ArgumentParser:
    """Создаёт парсер аргументов"""
    parser = argparse.ArgumentParser(
        prog='handycode',
        description='HandyCode - AI Assistant for coding',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  hc                              Interactive mode
  hc -p /path/to/project          Open project
  hc -c "Create React app"        Run command
  hc -m gpt4                      Use model
  hc -y -c "Create Python API"    Auto-approve
        """
    )

    parser.add_argument('-p', '--project', type=str, help='Project directory')
    parser.add_argument('-m', '--model', type=str, default='deepseek', help='AI model')
    parser.add_argument('-y', '--yes', action='store_true', help='Auto-approve')
    parser.add_argument('-c', '--command', type=str, help='Execute command and exit')
    parser.add_argument('--version', action='version', version='HandyCode v2.0.0')

    return parser


def main():
    """Главная функция CLI"""
    parser = create_parser()
    args = parser.parse_args()

    config = Config()

    project_dir = args.project if args.project else os.getcwd()
    project_path = Path(project_dir).resolve()

    if not validate_project_dir(project_path):
        sys.exit(1)

    try:
        assistant = HandyCode(
            project_path=project_path,
            model=args.model,
            auto_approve=args.yes,
            config=config
        )

        if args.command:
            assistant.execute_command(args.command)
        else:
            assistant.run()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print_error(f"\nError: {e}")
        sys.exit(1)


def validate_project_dir(project_path: Path) -> bool:
    """Проверяет директорию проекта"""
    if not project_path.exists():
        print_warning(f"Directory does not exist: {project_path}")
        create = input("Create it? [Y/n]: ").strip().lower()
        if create in ['', 'y', 'yes']:
            project_path.mkdir(parents=True, exist_ok=True)
            print_success(f"Created: {project_path}")
        else:
            return False

    if not project_path.is_dir():
        print_error(f"Not a directory: {project_path}")
        return False

    dangerous_paths = [
        '/', '/etc', '/bin', '/sbin', '/usr', '/System',
        '/Windows', '/boot', '/root', '/var', '/tmp'
    ]

    path_str = str(project_path)
    is_dangerous = any(path_str == d or path_str.startswith(d + '/') for d in dangerous_paths)

    if is_dangerous:
        print_error(f"WARNING: System directory!")
        print_error(f"Path: {project_path}")
        confirm = input("Continue? Type 'YES': ").strip()
        if confirm != 'YES':
            return False

    print(f"\nProject directory: {project_path}")

    home = Path.home()
    if project_path == home:
        print_warning("WARNING: This is your HOME directory!")
        confirm = input("Continue? [y/N]: ").strip().lower()
        if confirm not in ['y', 'yes']:
            return False

    contents = list(project_path.iterdir())
    if contents:
        visible = [c for c in contents if not c.name.startswith('.')]
        if visible:
            print(f"\nDirectory contains {len(visible)} items:")
            for item in visible[:10]:
                item_type = "[DIR]" if item.is_dir() else "[FILE]"
                print(f"  {item_type} {item.name}")
            if len(visible) > 10:
                print(f"  ... and {len(visible) - 10} more")
            print_warning("\nDirectory is not empty!")

    confirm = input("\nUse this directory? [Y/n]: ").strip().lower()
    if confirm not in ['', 'y', 'yes']:
        print_warning("Cancelled")
        return False

    print_success(f"Using: {project_path}\n")
    return True