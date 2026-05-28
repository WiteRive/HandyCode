"""
Управление конфигурацией HandyCode
"""

import os
import json
from pathlib import Path
from typing import Optional
from datetime import datetime


class Config:
    """Управляет конфигурацией HandyCode"""

    def __init__(self):
        """Инициализация конфигурации"""
        self.config_dir = Path.home() / '.handycode'
        self.config_dir.mkdir(exist_ok=True)

        self.env_file = self.config_dir / '.env'
        self.config_file = self.config_dir / 'config.json'

        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Загружает конфигурацию из файла"""
        default_config = {
            "default_model": "deepseek",
            "auto_approve": False,
            "show_line_numbers": True,
            "backup_before_modify": True,
            "max_history": 100,
            "language": "ru",
            "installed_version": "2.0.0",
            "install_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "api_key_verified": False
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, encoding='utf-8') as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
            except:
                pass

        return default_config

    def save_config(self):
        """Сохраняет конфигурацию в файл"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def get_api_key(self) -> str:
        """Получает API ключ из различных источников"""
        api_key = None

        # 1. Переменная окружения
        api_key = os.getenv('OPENROUTER_API_KEY')
        if api_key:
            return api_key

        # 2. .env файл
        if self.env_file.exists():
            try:
                with open(self.env_file, encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('OPENROUTER_API_KEY='):
                            key = line.split('=', 1)[1].strip()
                            # Убираем кавычки если есть
                            key = key.strip('"').strip("'")
                            if key and not key.startswith('#'):
                                api_key = key
                                break
            except:
                pass

        if api_key:
            return api_key

        # 3. Файл конфигурации
        if 'api_key' in self.config and self.config['api_key']:
            return self.config['api_key']

        # 4. Запрашиваем у пользователя (один раз)
        api_key = self._request_api_key()
        if api_key:
            self._save_api_key(api_key)

        return api_key

    def _request_api_key(self) -> str:
        """Запрашивает API ключ у пользователя"""
        print("\n" + "=" * 60)
        print("🔑 API КЛЮЧ НЕ НАЙДЕН")
        print("=" * 60)
        print()
        print("Для работы HandyCode требуется API ключ OpenRouter.")
        print("Вы можете получить его бесплатно на сайте:")
        print("https://openrouter.ai/keys")
        print()
        print("Инструкция:")
        print("1. Зарегистрируйтесь на openrouter.ai")
        print("2. Перейдите в раздел Keys")
        print("3. Создайте новый ключ")
        print("4. Скопируйте ключ и вставьте его ниже")
        print()

        api_key = input("API ключ: ").strip()

        if api_key:
            print()
            print("✅ Ключ сохранён в ~/.handycode/.env")
            print("   Вы можете изменить его в любой момент")
            return api_key

        print()
        print("⚠️  Ключ не введён. Вы сможете добавить его позже.")
        print("   Создайте файл ~/.handycode/.env и добавьте строку:")
        print("   OPENROUTER_API_KEY=ваш_ключ")
        return ""

    def _save_api_key(self, api_key: str):
        """Сохраняет API ключ"""
        try:
            # Сохраняем в .env файл
            env_content = ""
            if self.env_file.exists():
                with open(self.env_file, encoding='utf-8') as f:
                    env_content = f.read()

            # Обновляем или добавляем ключ
            if 'OPENROUTER_API_KEY=' in env_content:
                lines = env_content.split('\n')
                new_lines = []
                for line in lines:
                    if line.startswith('OPENROUTER_API_KEY='):
                        new_lines.append(f'OPENROUTER_API_KEY={api_key}')
                    else:
                        new_lines.append(line)
                env_content = '\n'.join(new_lines)
            else:
                if env_content and not env_content.endswith('\n'):
                    env_content += '\n'
                env_content += f'OPENROUTER_API_KEY={api_key}\n'

            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)

            # Устанавливаем права только для владельца
            os.chmod(self.env_file, 0o600)

            # Сохраняем в конфиг
            self.config['api_key_verified'] = True
            self.save_config()

        except Exception as e:
            print(f"⚠️  Не удалось сохранить ключ: {e}")
            print("   Вы можете добавить его вручную в ~/.handycode/.env")

    def verify_api_key(self) -> bool:
        """Проверяет валидность API ключа"""
        import requests

        api_key = self.get_api_key()
        if not api_key:
            return False

        try:
            response = requests.get(
                "https://openrouter.ai/api/v1/auth/key",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=5
            )

            if response.status_code == 200:
                self.config['api_key_verified'] = True
                self.save_config()
                return True

            return False
        except:
            # Если нет интернета, считаем что ключ валидный
            return True

    def get(self, key: str, default=None):
        """Получает значение конфигурации"""
        return self.config.get(key, default)

    def set(self, key: str, value):
        """Устанавливает значение конфигурации"""
        self.config[key] = value
        self.save_config()