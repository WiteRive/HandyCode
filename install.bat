@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: Показываем логотип
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║  ██╗  ██╗  █████╗  ███╗   ██╗  ██████╗  ██╗   ██╗           ║
echo ║  ██║  ██║  ██╔══██╗ ████╗  ██║  ██╔══██╗ ╚██╗ ██╔╝           ║
echo ║  ███████║  ███████║ ██╔██╗ ██║  ██║  ██║  ╚████╔╝            ║
echo ║  ██╔══██║  ██╔══██║ ██║╚██╗██║  ██║  ██║   ╚██╔╝             ║
echo ║  ██║  ██║  ██║  ██║ ██║ ╚████║  ██████╔╝    ██║              ║
echo ║  ╚═╝  ╚═╝  ╚═╝  ╚═╝ ╚═╝  ╚═══╝  ╚═════╝     ╚═╝              ║
echo ║                                                              ║
echo ║           ██████╗  ██████╗  ██████╗  ███████╗                ║
echo ║          ██╔════╝  ██╔══██╗ ██╔══██╗ ██╔════╝                ║
echo ║          ██║       ██║  ██║ ██║  ██║ █████╗                  ║
echo ║          ██║       ██║  ██║ ██║  ██║ ██╔══╝                  ║
echo ║          ╚██████╗  ██████╔╝ ██████╔╝ ███████╗                ║
echo ║           ╚═════╝  ╚═════╝  ╚═════╝  ╚══════╝                ║
echo ║                                                              ║
echo ║                    УСТАНОВКА HANDYCODE                         ║
echo ║              AI Ассистент для разработки                      ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Проверка прав администратора (для setx)
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  ВНИМАНИЕ: Для глобальной установки запустите от администратора
    echo.
)

:: Проверка Python
echo 🔍 Проверка Python...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo ❌ Python не найден!
    echo.
    echo Установите Python:
    echo 1. Скачайте с https://python.org
    echo 2. При установке ОБЯЗАТЕЛЬНО отметьте "Add Python to PATH"
    echo 3. После установки перезапустите этот скрипт
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% найден

:: Проверка pip
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip не найден
    echo Установите pip: python -m ensurepip --upgrade
    pause
    exit /b 1
)

:: Создание директорий
set INSTALL_DIR=%USERPROFILE%\.handycode
set BIN_DIR=%USERPROFILE%\.local\bin

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"

:: Установка пакета
echo.
echo 📦 Установка HandyCode...
pip install --user handycode 2>nul

if %errorlevel% neq 0 (
    echo ⚠️ Установка из PyPI не удалась, пробуем из GitHub...

    :: Проверяем git
    where git >nul 2>nul
    if %errorlevel% equ 0 (
        echo 📥 Загрузка через git...
        cd /d "%INSTALL_DIR%"
        if exist repo rmdir /s /q repo
        git clone https://github.com/yourusername/handycode.git repo 2>nul
        if exist repo (
            cd repo
            pip install --user -e .
        )
    ) else (
        echo ❌ Git не найден. Установите Git или скачайте проект вручную.
        echo https://github.com/yourusername/handycode
        pause
        exit /b 1
    )
)

:: Проверка установки
python -c "import handycode" 2>nul
if %errorlevel% neq 0 (
    echo ❌ Ошибка установки пакета handycode
    pause
    exit /b 1
)

echo ✅ Пакет handycode установлен

:: Запрос API ключа
echo.
echo ═══════════════════════════════════════════════════════════════
echo 🔑 НАСТРОЙКА API КЛЮЧА
echo ═══════════════════════════════════════════════════════════════
echo.
echo Для работы HandyCode требуется API ключ OpenRouter.
echo Вы можете получить его бесплатно на сайте:
echo https://openrouter.ai/keys
echo.
echo 1. Зарегистрируйтесь на openrouter.ai
echo 2. Перейдите в раздел Keys
echo 3. Создайте новый ключ
echo 4. Скопируйте ключ и вставьте его ниже
echo.

:ask_api_key
set /p API_KEY="Введите ваш API ключ (или нажмите Enter чтобы пропустить): "

if "%API_KEY%"=="" (
    echo.
    echo ⚠️  API ключ не введён.
    echo Вы сможете добавить его позже в файл:
    echo %INSTALL_DIR%\.env
    echo.
    set /p CONTINUE="Продолжить установку без ключа? [Д/н]: "
    if /i "%CONTINUE%"=="н" goto ask_api_key
    if /i "%CONTINUE%"=="n" goto ask_api_key
    goto save_config
)

:: Проверка длины ключа
set "KEY_LENGTH=0"
for /l %%i in (0,1,100) do (
    if not "!API_KEY:~%%i,1!"=="" set /a KEY_LENGTH+=1
)

if %KEY_LENGTH% LSS 20 (
    echo ❌ Ключ слишком короткий. Проверьте ключ и попробуйте снова.
    goto ask_api_key
)

echo ✅ API ключ принят

:save_config
:: Сохранение конфигурации
echo.
echo 💾 Сохранение конфигурации...

(
echo # HandyCode Configuration
echo # Получить API ключ: https://openrouter.ai/keys
echo OPENROUTER_API_KEY=%API_KEY%
echo.
echo # Настройки по умолчанию (опционально^)
echo # HANDYCODE_DEFAULT_MODEL=deepseek
echo # HANDYCODE_AUTO_APPROVE=false
) > "%INSTALL_DIR%\.env"

:: Создание конфигурационного JSON
set INSTALL_DATE=%DATE% %TIME%
(
echo {
echo     "default_model": "deepseek",
echo     "auto_approve": false,
echo     "show_line_numbers": true,
echo     "backup_before_modify": true,
echo     "max_history": 100,
echo     "language": "ru",
echo     "installed_version": "2.0.0",
echo     "install_date": "%INSTALL_DATE%"
echo }
) > "%INSTALL_DIR%\config.json"

echo ✅ Конфигурация сохранена

:: Создание скриптов запуска
echo.
echo 🔧 Создание команд...

(
echo @echo off
echo python -m handycode %%*
) > "%BIN_DIR%\hc.bat"

(
echo @echo off
echo python -m handycode %%*
) > "%BIN_DIR%\handycode.bat"

:: Создание PowerShell скрипта для удобства
(
echo # HandyCode Launcher
echo python -m handycode $args
) > "%BIN_DIR%\hc.ps1"

(
echo # HandyCode Launcher
echo python -m handycode $args
) > "%BIN_DIR%\handycode.ps1"

:: Добавление в PATH
echo 📝 Добавление в PATH...
setx PATH "%PATH%;%BIN_DIR%" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Путь добавлен в системный PATH
) else (
    echo ⚠️ Не удалось добавить в системный PATH (нужны права администратора^)
    echo.
    echo Добавьте папку в PATH вручную:
    echo 1. Откройте Параметры системы
    echo 2. Переменные среды
    echo 3. Добавьте в PATH: %BIN_DIR%
    echo.
    echo Или используйте команды из этой папки напрямую:
    echo %BIN_DIR%\hc.bat
)

:: Создание ярлыка на рабочем столе (опционально)
echo.
set /p CREATE_SHORTCUT="Создать ярлык на рабочем столе? [Д/н]: "
if /i "%CREATE_SHORTCUT%"=="" set CREATE_SHORTCUT=д
if /i "%CREATE_SHORTCUT%"=="д" goto create_shortcut
if /i "%CREATE_SHORTCUT%"=="y" goto create_shortcut
goto skip_shortcut

:create_shortcut
echo Создание ярлыка...
powershell -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\HandyCode.lnk'); $SC.TargetPath = '%BIN_DIR%\hc.bat'; $SC.WorkingDirectory = '%USERPROFILE%'; $SC.Description = 'HandyCode - AI Ассистент'; $SC.Save()" 2>nul
if %errorlevel% equ 0 (
    echo ✅ Ярлык создан на рабочем столе
) else (
    echo ⚠️ Не удалось создать ярлык
)

:skip_shortcut

:: Финальное сообщение
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║              ✅ HANDYCODE УСТАНОВЛЕН!                         ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

if not "%API_KEY%"=="" (
    echo ✅ API ключ настроен
) else (
    echo ⚠️  API ключ не настроен
    echo    Добавьте его в файл: %INSTALL_DIR%\.env
    echo    Или выполните: set OPENROUTER_API_KEY=ваш_ключ
)

echo.
echo 📝 Быстрый старт:
echo.
echo    1. Откройте командную строку или PowerShell
echo    2. Введите команду:
echo.
echo       hc
echo.
echo    Если команда не работает:
echo    • Перезапустите терминал
echo    • Или используйте полный путь: %BIN_DIR%\hc.bat
echo.
echo 💡 Примеры:
echo    hc                              Интерактивный режим
echo    hc -p мой-проект               Открыть проект
echo    hc -c "Создай React приложение"  Быстрая команда
echo    hc --help                       Справка
echo.
echo 📚 Полезные ссылки:
echo    • OpenRouter: https://openrouter.ai
echo    • GitHub: https://github.com/yourusername/handycode
echo.
echo Приятного программирования! 🚀
echo.
pause