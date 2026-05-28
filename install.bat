@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ╔══════════════════════════════════════════════════════════════╗
echo ║              УСТАНОВКА HANDYCODE ДЛЯ WINDOWS                  ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo 🔍 Проверка Python...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python не найден. Установите с https://python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% найден

set INSTALL_DIR=%USERPROFILE%\.handycode
set BIN_DIR=%USERPROFILE%\.local\bin
mkdir "%INSTALL_DIR%" 2>nul
mkdir "%BIN_DIR%" 2>nul

echo 📦 Установка HandyCode...
pip install --user handycode 2>nul

if %errorlevel% neq 0 (
    echo ⚠️ pip install не удался, пробуем из исходников...
    cd /d "%INSTALL_DIR%"
    if exist repo rmdir /s /q repo
    git clone https://github.com/yourusername/handycode.git repo 2>nul
    if exist repo (
        cd repo
        pip install --user -e .
    )
)

echo @echo off > "%BIN_DIR%\hc.bat"
echo python -m handycode %%* >> "%BIN_DIR%\hc.bat"

echo @echo off > "%BIN_DIR%\handycode.bat"
echo python -m handycode %%* >> "%BIN_DIR%\handycode.bat"

setx PATH "%PATH%;%BIN_DIR%" >nul

echo.
echo ✅ HandyCode установлен!
echo.
echo 📝 Использование:
echo   hc                    Интерактивный режим
echo   hc -p проект          Открыть проект
echo   hc -c "команда"       Выполнить команду
echo.
echo 🔑 Добавьте API ключ:
echo   set OPENROUTER_API_KEY=ваш_ключ
echo.
echo ⚠️ Перезапустите терминал для использования команды 'hc'
echo.
pause