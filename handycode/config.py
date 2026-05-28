"""
Управление конфигурацией HandyCode (без внешних зависимостей)
"""

import os
import json
from pathlib import Path


class Config:
    """Управляет конфигурацией HandyCode"""

    def __init__(self):
        self.config_dir = Path.home() / '.handycode'
        self.config_dir.mkdir(exist_ok=True)

        self.env_file = self.config_dir / '.env'
        self.config_file = self.config_dir / 'config.json'

        self.config = self._load_config()

    def _load_config(self) -> dict:
        default_config = {
            "default_model": "deepseek",
            "auto_approve": False,
            "language": "ru",
            "installed_version": "2.0.0",
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
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def get_api_key(self) -> str:
        api_key = os.getenv('OPENROUTER_API_KEY')
        if api_key:
            return api_key

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

        if 'api_key' in self.config and self.config['api_key']:
            return self.config['api_key']

        print("\nAPI ключ не найден!")
        print("Получите ключ на: https://openrouter.ai/keys")
        api_key = input("Введите API ключ: ").strip()

        if api_key:
            try:
                with open(self.env_file, 'w', encoding='utf-8') as f:
                    f.write(f'OPENROUTER_API_KEY={api_key}\n')
                os.chmod(self.env_file, 0o600)
            except:
                pass

        return api_key

    def get(self, key: str, default=None):
        return self.config.get(key, default)