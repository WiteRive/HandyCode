"""
Конфигурация AI моделей
"""

MODELS = {
    # DeepSeek модели
    "deepseek": "deepseek/deepseek-chat",
    "deepseek-coder": "deepseek/deepseek-coder",
    "deepseek-r1": "deepseek/deepseek-r1",
    "deepseek-r1-distill": "deepseek/deepseek-r1-distill-qwen-32b",

    # OpenAI модели
    "gpt4": "openai/gpt-4-turbo-preview",
    "gpt4o": "openai/gpt-4o",
    "gpt3": "openai/gpt-3.5-turbo",

    # Anthropic модели
    "claude": "anthropic/claude-3-opus",
    "claude-sonnet": "anthropic/claude-3-sonnet",
    "claude-haiku": "anthropic/claude-3-haiku",

    # Google модели
    "gemini": "google/gemini-pro",
    "gemini-flash": "google/gemini-flash-1.5",

    # Meta модели
    "llama": "meta-llama/llama-3-70b-instruct",
    "llama-8b": "meta-llama/llama-3-8b-instruct",

    # Другие модели
    "mixtral": "mistralai/mixtral-8x7b-instruct",
    "codellama": "codellama/codellama-70b-instruct",
}

MODEL_SETTINGS = {
    "deepseek/deepseek-chat": {
        "temperature": 1,
        "max_tokens": 80000,
        "description": "DeepSeek V3 - Лучший баланс скорости и качества"
    },
    "deepseek/deepseek-coder": {
        "temperature": 1,
        "max_tokens": 80000,
        "description": "DeepSeek Coder - Специализирована для написания кода"
    },
    "deepseek/deepseek-r1": {
        "temperature": 1,
        "max_tokens": 40000,
        "description": "DeepSeek R1 - Глубокое мышление и анализ"
    },
    "openai/gpt-4-turbo-preview": {
        "temperature": 0.3,
        "max_tokens": 4000,
        "description": "GPT-4 Turbo - Мощная универсальная модель"
    },
    "anthropic/claude-3-opus": {
        "temperature": 0.3,
        "max_tokens": 4000,
        "description": "Claude 3 Opus - Продвинутый анализ"
    },
    "anthropic/claude-3-sonnet": {
        "temperature": 0.3,
        "max_tokens": 4000,
        "description": "Claude 3 Sonnet - Быстрая и способная"
    },
}

DEFAULT_SETTINGS = {
    "temperature": 0.3,
    "max_tokens": 4000,
    "description": "Универсальная модель"
}


def get_model_settings(model_id: str) -> dict:
    """Получает настройки для конкретной модели"""
    return MODEL_SETTINGS.get(model_id, DEFAULT_SETTINGS)