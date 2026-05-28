@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║         HANDYCODE - УСТАНОВЩИК ДЛЯ WINDOWS          ║
echo ╚══════════════════════════════════════════════════════╝
echo.

:: Проверка Python
echo [1/4] Проверка Python...
where python >nul 2>nul
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo [OK] Python %%i
    set PYTHON_CMD=python
    goto :check_pip
)

where python3 >nul 2>nul
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python3 --version 2^>^&1') do echo [OK] Python %%i
    set PYTHON_CMD=python3
    goto :check_pip
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    echo [OK] Python найден через py
    set PYTHON_CMD=py
    goto :check_pip
)

echo [ERROR] Python не найден!
echo.
echo Установите Python с https://python.org
echo При установке отметьте "Add Python to PATH"
pause
exit /b 1

:check_pip
echo [2/4] Проверка pip...
%PYTHON_CMD% -m pip --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] pip работает
) else (
    echo [!] Устанавливаю pip...
    %PYTHON_CMD% -m ensurepip --upgrade >nul 2>&1
)

:: Создание директорий
echo [3/4] Установка HandyCode...
set HANDYCODE_DIR=%USERPROFILE%\.handycode
set BIN_DIR=%USERPROFILE%\.local\bin

if not exist "%HANDYCODE_DIR%" mkdir "%HANDYCODE_DIR%"
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"

:: Установка пакета
echo [*] Устанавливаю пакет...

%PYTHON_CMD% -m pip install --user handycode 2>nul
if %errorlevel% equ 0 (
    echo [OK] Пакет установлен из PyPI
    goto :check_install
)

echo [!] PyPI не сработал, пробую GitHub...
where git >nul 2>nul
if %errorlevel% equ 0 (
    set TEMP_DIR=%TEMP%\handycode_install
    if exist "!TEMP_DIR!" rmdir /s /q "!TEMP_DIR!"
    git clone https://github.com/yourusername/handycode.git "!TEMP_DIR!" 2>nul
    if exist "!TEMP_DIR!\setup.py" (
        cd /d "!TEMP_DIR!"
        %PYTHON_CMD% -m pip install --user -e . 2>nul
        cd /d %USERPROFILE%
    )
)

:check_install
%PYTHON_CMD% -c "import handycode" 2>nul
if %errorlevel% equ 0 (
    echo [OK] HandyCode установлен
) else (
    echo [ERROR] Не удалось установить HandyCode
    echo Попробуйте: pip install handycode
    pause
    exit /b 1
)

:: API ключ
echo.
echo [4/4] Настройка...
echo.
echo Нужен API ключ OpenRouter (бесплатно)
echo Получите: https://openrouter.ai/keys
echo.
set /p API_KEY="Введите API ключ (Enter - пропустить): "

:: Сохранение конфигурации
(
echo # HandyCode Configuration
echo OPENROUTER_API_KEY=!API_KEY!
) > "%HANDYCODE_DIR%\.env"

echo [OK] Конфигурация сохранена

:: Создание скриптов
(
echo @echo off
echo %PYTHON_CMD% -m handycode %%*
) > "%BIN_DIR%\hc.bat"

(
echo @echo off
echo %PYTHON_CMD% -m handycode %%*
) > "%BIN_DIR%\handycode.bat"

echo [OK] Скрипты созданы

:: Добавление в PATH
setx PATH "%PATH%;%BIN_DIR%" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Добавлено в PATH
) else (
    echo [!] Добавьте в PATH вручную: %BIN_DIR%
)

:: Готово
echo.
echo ============================================================
echo УСТАНОВКА ЗАВЕРШЕНА!
echo ============================================================
echo.
echo Для использования:
echo   1. Закройте это окно
echo   2. Откройте новый терминал (Win+R -^> cmd)
echo   3. Введите: hc
echo.
echo Примеры:
echo   hc                    Запуск
echo   hc --help             Справка
echo.
pause