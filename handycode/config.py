"""
Управление конфигурацией HandyCode
"""

import os
import json
from pathlib import Path
from typing import Optional


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
        # 1. Переменная окружения
        api_key = os.getenv('OPENROUTER_API_KEY')
        if api_key:
            return api_key

        # 2. .env файл
        if self.env_file.exists():
            try:
                with open(self.env_file, encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('OPENROUTER_API_KEY='):
                            key = line.split('=', 1)[1].strip()
                            if key:
                                return key
            except:
                pass

        # 3. Файл конфигурации
        if 'api_key' in self.config and self.config['api_key']:
            return self.config['api_key']

        # 4. Запрашиваем у пользователя
        print("\n⚠️  API ключ OpenRouter не найден!")
        print("   Получите ключ на: https://openrouter.ai/keys")
        api_key = input("   Введите ваш API ключ: ").strip()

        if api_key:
            # Сохраняем для будущего использования
            try:
                with open(self.env_file, 'w', encoding='utf-8') as f:
                    f.write(f'OPENROUTER_API_KEY={api_key}\n')
                os.chmod(self.env_file, 0o600)
            except:
                pass

        return api_key

    def get(self, key: str, default=None):
        """Получает значение конфигурации"""
        return self.config.get(key, default)

    def set(self, key: str, value):
        """Устанавливает значение конфигурации"""
        self.config[key] = value
        self.save_config()