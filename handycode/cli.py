"""
Интерфейс командной строки для HandyCode
"""

import argparse
import sys
import os
from pathlib import Path

from handycode.assistant import HandyCode
from handycode.config import Config
from handycode.utils import print_error, print_warning, print_info, print_logo, print_install_logo
from handycode.logo import get_logo


def create_parser() -> argparse.ArgumentParser:
    """Создаёт парсер аргументов командной строки"""
    parser = argparse.ArgumentParser(
        prog='handycode',
        description='HandyCode - AI Ассистент для разработки (аналог Claude Code)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  hc                              Интерактивный режим
  hc -p /путь/к/проекту           Открыть конкретный проект
  hc -c "Создай React приложение"  Выполнить одну команду
  hc -m gpt4                      Использовать модель GPT-4
  hc -y -c "Создай Python API"    Авто-подтверждение действий

Доступные модели:
  deepseek, deepseek-coder, deepseek-r1, gpt4, claude, 
  claude-sonnet, gemini, llama

Команды внутри программы:
  /help, /помощь          Справка
  /scan, /сканировать     Структура проекта
  /models, /модели        Список моделей
  /model, /модель         Сменить модель
  /clear, /очистить       Очистить историю
  /save, /сохранить       Сохранить сессию
  /stats, /статистика     Статистика
  /exit, /выход           Выйти
        """
    )

    parser.add_argument(
        '-p', '--project',
        type=str,
        help='Путь к директории проекта'
    )

    parser.add_argument(
        '-m', '--model',
        type=str,
        default='deepseek',
        help='Модель AI (по умолчанию: deepseek)'
    )

    parser.add_argument(
        '-y', '--yes',
        action='store_true',
        help='Автоматически подтверждать все действия'
    )

    parser.add_argument(
        '-c', '--command',
        type=str,
        help='Выполнить одну команду и выйти'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='HandyCode v2.0.0'
    )

    return parser


def main():
    """Главная функция CLI"""
    parser = create_parser()
    args = parser.parse_args()

    # Загружаем конфигурацию
    config = Config()

    # Определяем директорию проекта
    project_dir = args.project if args.project else os.getcwd()
    project_path = Path(project_dir).resolve()

    # Проверяем и подтверждаем директорию
    if not validate_project_dir(project_path):
        sys.exit(1)

    # Создаём и запускаем ассистента
    try:
        assistant = HandyCode(
            project_path=project_path,
            model=args.model,
            auto_approve=args.yes,
            config=config
        )

        if args.command:
            # Режим одной команды
            assistant.execute_command(args.command)
        else:
            # Интерактивный режим
            assistant.run()
    except KeyboardInterrupt:
        print("\n\n👋 До свидания!")
        sys.exit(0)
    except Exception as e:
        print_error(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)


def validate_project_dir(project_path: Path) -> bool:
    """Проверяет и подтверждает директорию проекта"""
    # Проверяем существование
    if not project_path.exists():
        print_warning(f"📁 Директория не существует: {project_path}")
        create = input("Создать? [Д/н]: ").strip().lower()
        if create in ['', 'д', 'да', 'y', 'yes']:
            try:
                project_path.mkdir(parents=True, exist_ok=True)
                print_success(f"✅ Создана: {project_path}")
            except Exception as e:
                print_error(f"❌ Не удалось создать директорию: {e}")
                return False
        else:
            return False

    # Проверяем, что это директория
    if not project_path.is_dir():
        print_error(f"❌ Не является директорией: {project_path}")
        return False

    # Проверка на системные директории
    dangerous_paths = [
        '/', '/etc', '/bin', '/sbin', '/usr', '/System',
        '/Windows', '/boot', '/root', '/var', '/tmp'
    ]

    path_str = str(project_path)
    is_dangerous = any(path_str == d or path_str.startswith(d + '/') for d in dangerous_paths)

    if is_dangerous:
        print_error("⚠️  ВНИМАНИЕ! Вы пытаетесь использовать системную директорию!")
        print_error(f"   Путь: {project_path}")
        print_error("   Это может быть опасно!")
        confirm = input("Вы уверены? Введите 'ДА' для продолжения: ").strip()
        if confirm != 'ДА':
            print_warning("❌ Отменено")
            return False

    # Показываем информацию о директории
    print(f"\n📁 Директория проекта: {project_path}")

    # Проверяем, не домашняя ли это директория
    home = Path.home()
    if project_path == home:
        print_warning("⚠️  ВНИМАНИЕ! Это ваша ДОМАШНЯЯ директория!")
        print_warning("    Все операции будут выполняться относительно домашней папки.")
        print_warning("    Рекомендуется использовать поддиректорию.")
        confirm = input("Всё равно продолжить? [д/Н]: ").strip().lower()
        if confirm not in ['д', 'да', 'y', 'yes']:
            print_warning("❌ Отменено")
            return False

    # Проверяем содержимое директории
    try:
        contents = list(project_path.iterdir())
        if contents:
            # Фильтруем скрытые файлы
            visible = [c for c in contents if not c.name.startswith('.')]
            if visible:
                print(f"\n📂 Директория содержит {len(visible)} элементов:")
                for item in visible[:10]:
                    item_type = "📁" if item.is_dir() else "📄"
                    print(f"  {item_type} {item.name}")
                if len(visible) > 10:
                    print(f"  ... и ещё {len(visible) - 10}")

                print_warning("\n⚠️  Директория не пуста!")
                print_warning("    AI может изменять существующие файлы.")
                print_info("    Перед изменениями создаются резервные копии (.bak)")
    except Exception:
        pass

    # Запрашиваем подтверждение
    confirm = input("\nИспользовать эту директорию? [Д/н]: ").strip().lower()
    if confirm not in ['', 'д', 'да', 'y', 'yes']:
        print_warning("❌ Отменено")
        return False

    print_success(f"✅ Используется: {project_path}\n")
    return True


# Импортируем здесь для избежания циклических зависимостей
from handycode.utils import print_success