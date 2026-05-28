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

echo -e "${YELLOW}🔍 Проверка Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 не установлен${NC}"
    echo "Установите Python 3.8+ с https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}✅ Python $PYTHON_VERSION найден${NC}"

INSTALL_DIR="$HOME/.handycode"
BIN_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR" "$BIN_DIR"

echo -e "${YELLOW}📦 Загрузка HandyCode...${NC}"
if command -v git &> /dev/null; then
    if [ -d "$INSTALL_DIR/repo" ]; then
        cd "$INSTALL_DIR/repo"
        git pull 2>/dev/null || {
            cd "$INSTALL_DIR"
            rm -rf repo
            git clone https://github.com/yourusername/handycode.git repo
        }
    else
        git clone https://github.com/yourusername/handycode.git "$INSTALL_DIR/repo" 2>/dev/null || {
            echo -e "${YELLOW}⚠️  Git clone не удался, скачиваем архив...${NC}"
            curl -L https://github.com/yourusername/handycode/archive/main.tar.gz | tar xz -C "$INSTALL_DIR"
            mv "$INSTALL_DIR/handycode-main" "$INSTALL_DIR/repo"
        }
    fi
else
    curl -L https://github.com/yourusername/handycode/archive/main.tar.gz | tar xz -C "$INSTALL_DIR"
    mv "$INSTALL_DIR/handycode-main" "$INSTALL_DIR/repo"
fi

cd "$INSTALL_DIR/repo"

echo -e "${YELLOW}📦 Установка HandyCode...${NC}"
pip3 install --user -e . 2>/dev/null || pip3 install --user .

mkdir -p "$HOME/.handycode"

if [ ! -f "$HOME/.handycode/.env" ]; then
    cat > "$HOME/.handycode/.env" << 'EOF'
OPENROUTER_API_KEY=
EOF
    chmod 600 "$HOME/.handycode/.env"
    echo -e "${YELLOW}⚠️  Добавьте ваш API ключ OpenRouter в:${NC}"
    echo -e "${BLUE}   $HOME/.handycode/.env${NC}"
fi

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

add_to_path "$HOME/.bashrc"
add_to_path "$HOME/.zshrc"
add_to_path "$HOME/.bash_profile"
add_to_path "$HOME/.profile"

echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║              ✅ HANDYCODE УСТАНОВЛЕН!                         ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${WHITE}📝 Быстрый старт:${NC}"
echo ""
echo -e "  1. Получите API ключ: ${YELLOW}https://openrouter.ai/keys${NC}"
echo -e "  2. Добавьте ключ в: ${YELLOW}$HOME/.handycode/.env${NC}"
echo -e "  3. Перезапустите терминал или выполните: ${YELLOW}source ~/.bashrc${NC}"
echo -e "  4. Начните программировать: ${GREEN}hc${NC}"
echo ""
echo -e "${WHITE}💡 Примеры:${NC}"
echo -e "  ${GREEN}hc${NC}                              # Интерактивный режим"
echo -e "  ${GREEN}hc -p мой-проект${NC}               # Открыть проект"
echo -e "  ${GREEN}hc -c \"Создай React приложение\"${NC} # Быстрая команда"
echo -e "  ${GREEN}hc --help${NC}                      # Справка"
echo ""