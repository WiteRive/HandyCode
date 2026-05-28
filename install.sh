#!/bin/bash
set -e

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# Лог-файл
LOG_FILE="/tmp/handycode_install_log.txt"
echo "HandyCode Install Log" > "$LOG_FILE"
echo "Date: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Функция логирования
log() {
    echo "$1" | tee -a "$LOG_FILE"
}

# Функция для отображения логотипа
show_logo() {
echo -e "${CYAN}"
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
echo ""
log "HandyCode Installer v2.0.0"
log "========================================="
}

# Функция проверки команды
check_command() {
    if command -v "$1" &> /dev/null; then
        log "  [OK] $1: $(command -v "$1")"
        return 0
    else
        log "  [--] $1: not found"
        return 1
    fi
}

# Функция для проверки Python
check_python() {
    log ""
    log "[Step 1/5] Checking Python..."

    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        log "  [ERROR] Python not found!"
        echo -e "${RED}[ERROR] Python не найден!${NC}"
        echo "Установите Python 3.8+ с https://python.org"
        exit 1
    fi

    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
    log "  [OK] Python found: $PYTHON_VERSION"
    echo -e "${GREEN}[OK] $PYTHON_VERSION${NC}"

    # Проверяем версию
    PYTHON_MAJOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.major)" 2>&1)
    PYTHON_MINOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.minor)" 2>&1)

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        log "  [ERROR] Python version too old: $PYTHON_MAJOR.$PYTHON_MINOR"
        echo -e "${RED}[ERROR] Нужен Python 3.8+, у вас $PYTHON_MAJOR.$PYTHON_MINOR${NC}"
        exit 1
    fi

    log "  [OK] Python version OK: $PYTHON_MAJOR.$PYTHON_MINOR"
}

# Функция проверки pip
check_pip() {
    log ""
    log "[Step 2/5] Checking pip..."

    if $PYTHON_CMD -m pip --version &> /dev/null; then
        PIP_VERSION=$($PYTHON_CMD -m pip --version 2>&1)
        log "  [OK] pip found: $PIP_VERSION"
        echo -e "${GREEN}[OK] pip работает${NC}"
        return 0
    fi

    log "  [--] pip not found, installing..."
    echo -e "${YELLOW}[*] Устанавливаю pip...${NC}"

    $PYTHON_CMD -m ensurepip --upgrade >> "$LOG_FILE" 2>&1
    if [ $? -eq 0 ]; then
        log "  [OK] pip installed"
        echo -e "${GREEN}[OK] pip установлен${NC}"
        return 0
    fi

    # Пробуем через get-pip.py
    log "  [*] Trying get-pip.py..."
    curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py >> "$LOG_FILE" 2>&1
    $PYTHON_CMD /tmp/get-pip.py --user >> "$LOG_FILE" 2>&1

    if $PYTHON_CMD -m pip --version &> /dev/null; then
        log "  [OK] pip installed via get-pip.py"
        echo -e "${GREEN}[OK] pip установлен${NC}"
        return 0
    fi

    log "  [ERROR] Failed to install pip"
    echo -e "${RED}[ERROR] Не удалось установить pip${NC}"
    return 1
}

# Функция установки пакета
install_package() {
    log ""
    log "[Step 3/5] Installing HandyCode..."

    INSTALL_DIR="$HOME/.handycode"
    BIN_DIR="$HOME/.local/bin"

    mkdir -p "$INSTALL_DIR" "$BIN_DIR"
    log "  [OK] Directories created: $INSTALL_DIR, $BIN_DIR"

    # Способ 1: pip install
    log "  [*] Method 1: pip install handycode"
    echo -e "${YELLOW}[*] Пробую установить через pip...${NC}"

    $PYTHON_CMD -m pip install --user handycode >> "$LOG_FILE" 2>&1
    if [ $? -eq 0 ]; then
        log "  [OK] Installed via pip"
        echo -e "${GREEN}[OK] Установлено через pip${NC}"
        return 0
    fi
    log "  [--] pip install failed"

    # Способ 2: pip install из GitHub
    log "  [*] Method 2: pip install from GitHub"
    echo -e "${YELLOW}[*] Пробую установить из GitHub...${NC}"

    $PYTHON_CMD -m pip install --user git+https://github.com/WiteRive/HandyCode.git >> "$LOG_FILE" 2>&1
    if [ $? -eq 0 ]; then
        log "  [OK] Installed from GitHub via pip"
        echo -e "${GREEN}[OK] Установлено из GitHub${NC}"
        return 0
    fi
    log "  [--] pip+git failed"

    # Способ 3: Клонирование git
    log "  [*] Method 3: git clone"
    echo -e "${YELLOW}[*] Пробую клонировать репозиторий...${NC}"

    if command -v git &> /dev/null; then
        TEMP_DIR="/tmp/handycode_install"
        rm -rf "$TEMP_DIR"

        git clone https://github.com/WiteRive/HandyCode.git "$TEMP_DIR" >> "$LOG_FILE" 2>&1

        if [ -f "$TEMP_DIR/setup.py" ]; then
            log "  [OK] Repository cloned"
            cd "$TEMP_DIR"
            $PYTHON_CMD -m pip install --user -e . >> "$LOG_FILE" 2>&1
            cd - > /dev/null

            if [ $? -eq 0 ]; then
                log "  [OK] Installed from git clone"
                echo -e "${GREEN}[OK] Установлено из git${NC}"
                return 0
            fi
        fi
        log "  [--] git clone install failed"
    else
        log "  [--] git not available"
    fi

    # Способ 4: Скачивание ZIP
    log "  [*] Method 4: Download ZIP"
    echo -e "${YELLOW}[*] Скачиваю архив...${NC}"

    ZIP_FILE="/tmp/handycode.zip"
    ZIP_DIR="/tmp/handycode_main"
    rm -f "$ZIP_FILE"
    rm -rf "$ZIP_DIR"

    if command -v curl &> /dev/null; then
        curl -L -o "$ZIP_FILE" https://github.com/WiteRive/HandyCode/archive/main.zip >> "$LOG_FILE" 2>&1
    elif command -v wget &> /dev/null; then
        wget -O "$ZIP_FILE" https://github.com/WiteRive/HandyCode/archive/main.zip >> "$LOG_FILE" 2>&1
    else
        log "  [ERROR] No curl or wget"
        echo -e "${RED}[ERROR] Нет curl или wget${NC}"
        return 1
    fi

    if [ -f "$ZIP_FILE" ]; then
        log "  [OK] ZIP downloaded"
        mkdir -p "$ZIP_DIR"

        if command -v unzip &> /dev/null; then
            unzip -q "$ZIP_FILE" -d "$ZIP_DIR" >> "$LOG_FILE" 2>&1
        else
            $PYTHON_CMD -c "import zipfile; zipfile.ZipFile('$ZIP_FILE').extractall('$ZIP_DIR')" >> "$LOG_FILE" 2>&1
        fi

        if [ -f "$ZIP_DIR/HandyCode-main/setup.py" ]; then
            log "  [OK] ZIP extracted"
            cd "$ZIP_DIR/HandyCode-main"
            $PYTHON_CMD -m pip install --user -e . >> "$LOG_FILE" 2>&1
            cd - > /dev/null

            if [ $? -eq 0 ]; then
                log "  [OK] Installed from ZIP"
                echo -e "${GREEN}[OK] Установлено из архива${NC}"
                return 0
            fi
        fi
        log "  [--] ZIP install failed"
    fi

    # Способ 5: Ручная установка
    log "  [*] Method 5: Manual install"
    echo -e "${YELLOW}[*] Ручная установка...${NC}"

    MODULE_DIR="$INSTALL_DIR/modules/handycode"
    mkdir -p "$MODULE_DIR"

    BASE_URL="https://raw.githubusercontent.com/WiteRive/HandyCode/main/handycode"

    FILES="__init__.py __main__.py main.py cli.py assistant.py models.py file_manager.py security.py config.py utils.py logo.py project_templates.py"

    for file in $FILES; do
        if command -v curl &> /dev/null; then
            curl -sS -L -o "$MODULE_DIR/$file" "$BASE_URL/$file" >> "$LOG_FILE" 2>&1
        elif command -v wget &> /dev/null; then
            wget -q -O "$MODULE_DIR/$file" "$BASE_URL/$file" >> "$LOG_FILE" 2>&1
        fi

        if [ -f "$MODULE_DIR/$file" ]; then
            log "    [OK] $file"
        else
            log "    [--] $file failed"
        fi
    done

    # Копируем в site-packages
    SITE_PACKAGES=$($PYTHON_CMD -c "import site; print(site.getusersitepackages())" 2>&1)
    if [ -d "$SITE_PACKAGES" ]; then
        mkdir -p "$SITE_PACKAGES/handycode"
        cp "$MODULE_DIR"/*.py "$SITE_PACKAGES/handycode/" 2>> "$LOG_FILE"
        log "  [OK] Copied to site-packages: $SITE_PACKAGES/handycode"
        echo -e "${GREEN}[OK] Файлы скопированы${NC}"
        return 0
    fi

    log "  [ERROR] All methods failed"
    echo -e "${RED}[ERROR] Все способы установки не сработали${NC}"
    echo "Смотрите лог: $LOG_FILE"
    return 1
}

# Функция проверки установки
check_install() {
    log ""
    log "[Step 4/5] Checking installation..."

    if $PYTHON_CMD -c "import handycode; print(handycode.__version__)" >> "$LOG_FILE" 2>&1; then
        VERSION=$($PYTHON_CMD -c "import handycode; print(handycode.__version__)" 2>&1)
        log "  [OK] HandyCode v$VERSION works!"
        echo -e "${GREEN}[OK] HandyCode v$VERSION работает!${NC}"
        return 0
    fi

    log "  [ERROR] Import failed"
    echo -e "${RED}[ERROR] HandyCode не работает${NC}"
    echo ""
    echo "Отладочная информация:"
    $PYTHON_CMD -c "import handycode" 2>&1 | tee -a "$LOG_FILE"
    return 1
}

# Функция настройки
configure() {
    log ""
    log "[Step 5/5] Configuration..."

    CONFIG_DIR="$HOME/.handycode"
    BIN_DIR="$HOME/.local/bin"

    # API ключ
    echo ""
    echo -e "${YELLOW}Нужен API ключ OpenRouter (бесплатно)${NC}"
    echo -e "${BLUE}Получите: https://openrouter.ai/keys${NC}"
    echo ""
    read -p "Введите API ключ (Enter - пропустить): " API_KEY

    cat > "$CONFIG_DIR/.env" << EOF
# HandyCode Configuration
OPENROUTER_API_KEY=$API_KEY
EOF

    chmod 600 "$CONFIG_DIR/.env"
    log "  [OK] Config saved to $CONFIG_DIR/.env"
    echo -e "${GREEN}[OK] Конфигурация сохранена${NC}"

    # Скрипты запуска
    cat > "$BIN_DIR/hc" << EOF
#!/bin/bash
$PYTHON_CMD -m handycode "\$@"
EOF
    chmod +x "$BIN_DIR/hc"

    cat > "$BIN_DIR/handycode" << EOF
#!/bin/bash
$PYTHON_CMD -m handycode "\$@"
EOF
    chmod +x "$BIN_DIR/handycode"

    log "  [OK] Scripts created: $BIN_DIR/hc, $BIN_DIR/handycode"
    echo -e "${GREEN}[OK] Скрипты созданы${NC}"

    # Добавление в PATH
    for rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile" "$HOME/.bash_profile"; do
        if [ -f "$rc" ]; then
            if ! grep -q "$BIN_DIR" "$rc"; then
                echo "" >> "$rc"
                echo "# HandyCode" >> "$rc"
                echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$rc"
                log "  [OK] Added to $rc"
            fi
        fi
    done

    # Текущая сессия
    export PATH="$BIN_DIR:$PATH"
    log "  [OK] PATH updated"
    echo -e "${GREEN}[OK] PATH обновлён${NC}"
}

# Функция финального сообщения
show_final() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║              ✅ HANDYCODE УСТАНОВЛЕН!                         ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    if [ -n "$API_KEY" ]; then
        echo -e "${GREEN}[V] API ключ настроен${NC}"
    else
        echo -e "${YELLOW}[!] Добавьте API ключ в: $HOME/.handycode/.env${NC}"
    fi

    echo ""
    echo -e "${WHITE}Для запуска:${NC}"
    echo "  1. Перезапустите терминал (или выполните: source ~/.bashrc)"
    echo "  2. Введите: hc"
    echo ""
    echo -e "${WHITE}Примеры:${NC}"
    echo "  hc                    Интерактивный режим"
    echo "  hc --help             Справка"
    echo ""
    echo -e "${WHITE}Лог установки:${NC} $LOG_FILE"
}

# Главная функция
main() {
    show_logo

    check_python
    check_pip

    if ! install_package; then
        echo ""
        echo -e "${RED}Установка не удалась. Смотрите лог: $LOG_FILE${NC}"
        echo ""
        echo "Попробуйте установить вручную:"
        echo "  pip install handycode"
        echo "  или"
        echo "  pip install git+https://github.com/WiteRive/HandyCode.git"
        exit 1
    fi

    if ! check_install; then
        echo ""
        echo -e "${RED}Проверка не пройдена. Смотрите лог: $LOG_FILE${NC}"
        exit 1
    fi

    configure
    show_final
}

# Запуск
main "$@"