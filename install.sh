#!/bin/bash
set -e

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
NC='\033[0m'

# Функция для отображения логотипа
show_logo() {
echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║  ██╗  ██╗  █████╗  ███╗   ██╗  ██████╗  ██╗   ██╗           ║"
echo "║  ██║  ██║  ██╔══██╗ ████╗  ██║  ██╔══██╗ ╚██╗ ██╔╝           ║"
echo "║  ███████║  ███████║ ██╔██╗ ██║  ██║  ██║  ╚████╔╝            ║"
echo "║  ██╔══██║  ██╔══██║ ██║╚██╗██║  ██║  ██║   ╚██╔╝             ║"
echo "║  ██║  ██║  ██║  ██║ ██║ ╚████║  ██████╔╝    ██║              ║"
echo "║  ╚═╝  ╚═╝  ╚═╝  ╚═╝ ╚═╝  ╚═══╝  ╚═════╝     ╚═╝              ║"
echo "║                                                              ║"
echo "║           ██████╗  ██████╗  ██████╗  ███████╗                ║"
echo "║          ██╔════╝  ██╔══██╗ ██╔══██╗ ██╔════╝                ║"
echo "║          ██║       ██║  ██║ ██║  ██║ █████╗                  ║"
echo "║          ██║       ██║  ██║ ██║  ██║ ██╔══╝                  ║"
echo "║          ╚██████╗  ██████╔╝ ██████╔╝ ███████╗                ║"
echo "║           ╚═════╝  ╚═════╝  ╚═════╝  ╚══════╝                ║"
echo "║                                                              ║"
echo "║                    УСТАНОВКА HANDYCODE                         ║"
echo "║              AI Ассистент для разработки                      ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
}

# Функция для запроса API ключа
request_api_key() {
    echo ""
    echo -e "${YELLOW}🔑 НАСТРОЙКА API КЛЮЧА${NC}"
    echo ""
    echo -e "${WHITE}Для работы HandyCode требуется API ключ OpenRouter.${NC}"
    echo -e "${WHITE}Вы можете получить его бесплатно на сайте:${NC}"
    echo -e "${BLUE}https://openrouter.ai/keys${NC}"
    echo ""
    echo -e "${WHITE}1. Зарегистрируйтесь на openrouter.ai${NC}"
    echo -e "${WHITE}2. Перейдите в раздел Keys${NC}"
    echo -e "${WHITE}3. Создайте новый ключ${NC}"
    echo -e "${WHITE}4. Скопируйте ключ и вставьте его ниже${NC}"
    echo ""

    while true; do
        read -p "Введите ваш API ключ (или нажмите Enter чтобы пропустить): " api_key

        if [ -z "$api_key" ]; then
            echo ""
            echo -e "${YELLOW}⚠️  API ключ не введён. Вы сможете добавить его позже в файл:${NC}"
            echo -e "${BLUE}   ~/.handycode/.env${NC}"
            echo ""
            read -p "Продолжить установку без ключа? [Д/н]: " continue_without
            if [[ "$continue_without" =~ ^[НнNn]$ ]]; then
                echo -e "${YELLOW}Введите ключ или нажмите Enter чтобы пропустить${NC}"
                continue
            fi
            api_key=""
            break
        fi

        # Проверяем формат ключа (обычно начинается с sk-or-)
        if [[ ${#api_key} -lt 20 ]]; then
            echo -e "${RED}❌ Ключ слишком короткий. Проверьте ключ и попробуйте снова.${NC}"
            continue
        fi

        echo ""
        echo -e "${GREEN}✅ API ключ принят${NC}"
        break
    done

    return_api_key="$api_key"
}

# Функция для добавления в PATH
add_to_path() {
    local config_file="$1"
    local path_line='export PATH="$HOME/.local/bin:$PATH"'

    if [ -f "$config_file" ]; then
        if ! grep -q "$HOME/.local/bin" "$config_file"; then
            echo "" >> "$config_file"
            echo "# HandyCode" >> "$config_file"
            echo "$path_line" >> "$config_file"
        fi
    fi
}

# Показываем логотип
show_logo

# Проверяем Python
echo -e "${YELLOW}🔍 Проверка Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 не установлен${NC}"
    echo "Установите Python 3.8+ с https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}✅ Python $PYTHON_VERSION найден${NC}"

# Проверяем pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3 не установлен${NC}"
    echo "Установите pip: python3 -m ensurepip --upgrade"
    exit 1
fi

# Создаём директории
INSTALL_DIR="$HOME/.handycode"
BIN_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR" "$BIN_DIR"

# Проверяем наличие git
echo -e "${YELLOW}📦 Загрузка HandyCode...${NC}"
if command -v git &> /dev/null; then
    if [ -d "$INSTALL_DIR/repo" ]; then
        echo -e "${BLUE}Обновление существующей установки...${NC}"
        cd "$INSTALL_DIR/repo"
        git pull 2>/dev/null || {
            echo -e "${YELLOW}⚠️  Не удалось обновить через git, переустанавливаем...${NC}"
            cd "$INSTALL_DIR"
            rm -rf repo
            git clone https://github.com/WiteRive/HandyCode.git repo 2>/dev/null
        }
    else
        git clone https://github.com/WiteRive/HandyCode.git "$INSTALL_DIR/repo" 2>/dev/null || {
            echo -e "${YELLOW}⚠️  Git clone не удался, пробуем curl...${NC}"
            if command -v curl &> /dev/null; then
                curl -L https://github.com/WiteRive/HandyCode/archive/main.tar.gz | tar xz -C "$INSTALL_DIR"
                mv "$INSTALL_DIR/handycode-main" "$INSTALL_DIR/repo"
            else
                echo -e "${RED}❌ Ни git, ни curl не найдены${NC}"
                exit 1
            fi
        }
    fi
else
    if command -v curl &> /dev/null; then
        curl -L https://github.com/WiteRive/HandyCode/archive/main.tar.gz | tar xz -C "$INSTALL_DIR"
        mv "$INSTALL_DIR/handycode-main" "$INSTALL_DIR/repo"
    elif command -v wget &> /dev/null; then
        wget -qO- https://github.com/WiteRive/HandyCode/archive/main.tar.gz | tar xz -C "$INSTALL_DIR"
        mv "$INSTALL_DIR/handycode-main" "$INSTALL_DIR/repo"
    else
        echo -e "${RED}❌ Ни git, ни curl, ни wget не найдены${NC}"
        echo "Установите один из них или скачайте проект вручную"
        exit 1
    fi
fi

cd "$INSTALL_DIR/repo"

# Устанавливаем пакет
echo -e "${YELLOW}📦 Установка HandyCode...${NC}"
pip3 install --user -e . 2>/dev/null || pip3 install --user .

# Проверяем установку
if python3 -c "import handycode" 2>/dev/null; then
    echo -e "${GREEN}✅ Пакет handycode установлен успешно${NC}"
else
    echo -e "${RED}❌ Ошибка установки пакета${NC}"
    exit 1
fi

# Создаём конфигурацию
mkdir -p "$HOME/.handycode"

# Запрашиваем API ключ
request_api_key
api_key="$return_api_key"

# Сохраняем конфигурацию
cat > "$HOME/.handycode/.env" << EOF
# HandyCode Configuration
# Получить API ключ: https://openrouter.ai/keys
OPENROUTER_API_KEY=$api_key

# Настройки по умолчанию (опционально)
# HANDYCODE_DEFAULT_MODEL=deepseek
# HANDYCODE_AUTO_APPROVE=false
EOF

chmod 600 "$HOME/.handycode/.env"

# Создаём конфигурационный файл
cat > "$HOME/.handycode/config.json" << 'EOF'
{
    "default_model": "deepseek",
    "auto_approve": false,
    "show_line_numbers": true,
    "backup_before_modify": true,
    "max_history": 100,
    "language": "ru",
    "installed_version": "2.0.0",
    "install_date": "INSTALL_DATE_PLACEHOLDER"
}
EOF

# Подставляем дату установки
INSTALL_DATE=$(date "+%Y-%m-%d %H:%M:%S")
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/INSTALL_DATE_PLACEHOLDER/$INSTALL_DATE/" "$HOME/.handycode/config.json"
else
    sed -i "s/INSTALL_DATE_PLACEHOLDER/$INSTALL_DATE/" "$HOME/.handycode/config.json"
fi

# Создаём скрипты запуска
cat > "$BIN_DIR/hc" << 'EOF'
#!/bin/bash
python3 -m handycode "$@"
EOF
chmod +x "$BIN_DIR/hc"

cat > "$BIN_DIR/handycode" << 'EOF'
#!/bin/bash
python3 -m handycode "$@"
EOF
chmod +x "$BIN_DIR/handycode"

# Добавляем в PATH
add_to_path "$HOME/.bashrc"
add_to_path "$HOME/.zshrc"
add_to_path "$HOME/.bash_profile"
add_to_path "$HOME/.profile"

# Пытаемся добавить в текущую сессию
export PATH="$HOME/.local/bin:$PATH" 2>/dev/null || true

# Проверяем, работает ли команда
if command -v hc &> /dev/null || command -v handycode &> /dev/null; then
    COMMAND_WORKS=true
else
    COMMAND_WORKS=false
fi

# Финальное сообщение
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║              ✅ HANDYCODE УСТАНОВЛЕН!                         ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ -n "$api_key" ]; then
    echo -e "${GREEN}✅ API ключ настроен${NC}"
else
    echo -e "${YELLOW}⚠️  API ключ не настроен${NC}"
    echo -e "${YELLOW}   Добавьте его в файл: $HOME/.handycode/.env${NC}"
    echo -e "${YELLOW}   Или установите переменную: export OPENROUTER_API_KEY=ваш_ключ${NC}"
fi

echo ""
echo -e "${WHITE}📝 Быстрый старт:${NC}"
echo ""

if [ "$COMMAND_WORKS" = false ]; then
    echo -e "${YELLOW}⚠️  Чтобы использовать команды 'hc' и 'handycode', выполните:${NC}"
    echo -e "${BLUE}   source ~/.bashrc${NC}"
    echo -e "${BLUE}   # или${NC}"
    echo -e "${BLUE}   source ~/.zshrc${NC}"
    echo ""
fi

echo -e "${WHITE}💡 Примеры использования:${NC}"
echo -e "  ${GREEN}hc${NC}                              # Интерактивный режим"
echo -e "  ${GREEN}hc -p мой-проект${NC}               # Открыть проект"
echo -e "  ${GREEN}hc -c \"Создай React приложение\"${NC} # Быстрая команда"
echo -e "  ${GREEN}hc -m deepseek-coder${NC}           # Выбрать модель"
echo -e "  ${GREEN}hc --help${NC}                      # Справка"
echo ""

echo -e "${WHITE}📚 Полезные ссылки:${NC}"
echo -e "  ${BLUE}• OpenRouter:${NC} https://openrouter.ai"
echo -e "  ${BLUE}• Документация:${NC} https://github.com/yourusername/handycode"
echo -e "  ${BLUE}• Баг-репорты:${NC} https://github.com/yourusername/handycode/issues"
echo ""

echo -e "${GREEN}Приятного программирования! 🚀${NC}"