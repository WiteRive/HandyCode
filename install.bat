@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

set LOG_FILE=%TEMP%\handycode_install_log.txt
echo HandyCode Install Log > "%LOG_FILE%"
echo Date: %DATE% %TIME% >> "%LOG_FILE%"

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║         HANDYCODE - УСТАНОВЩИК ДЛЯ WINDOWS          ║
echo ╚══════════════════════════════════════════════════════╝
echo.

:: Проверка Python
echo [1/5] Проверка Python...

where python >nul 2>nul
if %errorlevel% equ 0 set PYTHON_CMD=python & goto :python_found
where python3 >nul 2>nul
if %errorlevel% equ 0 set PYTHON_CMD=python3 & goto :python_found
where py >nul 2>nul
if %errorlevel% equ 0 set PYTHON_CMD=py & goto :python_found

echo [ERROR] Python не найден
pause
exit /b 1

:python_found
for /f "tokens=2" %%i in ('%PYTHON_CMD% --version 2^>^&1') do echo [OK] Python %%i

:: Установка pip и requests
echo [2/5] Установка зависимостей...

%PYTHON_CMD% -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Устанавливаю pip...
    %PYTHON_CMD% -m ensurepip --default-pip >> "%LOG_FILE%" 2>&1
)

echo [*] Устанавливаю requests...
%PYTHON_CMD% -m pip install requests --user >> "%LOG_FILE%" 2>&1
if %errorlevel% equ 0 (
    echo [OK] requests установлен
) else (
    echo [*] Пробую через ensurepip...
    %PYTHON_CMD% -m ensurepip --upgrade >> "%LOG_FILE%" 2>&1
    %PYTHON_CMD% -m pip install requests >> "%LOG_FILE%" 2>&1
)

:: Проверка requests
%PYTHON_CMD% -c "import requests; print('requests OK')" 2>nul
if %errorlevel% equ 0 (
    echo [OK] requests работает
) else (
    echo [ERROR] requests не установлен
    echo Установите вручную: %PYTHON_CMD% -m pip install requests
    pause
    exit /b 1
)

:: Скачивание файлов
echo [3/5] Скачивание HandyCode...

set HANDYCODE_DIR=%USERPROFILE%\.handycode
set HANDYCODE_SRC=%HANDYCODE_DIR%\HandyCode-main
set BIN_DIR=%USERPROFILE%\.local\bin

if not exist "%HANDYCODE_DIR%" mkdir "%HANDYCODE_DIR%"
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"

set BASE_URL=https://raw.githubusercontent.com/WiteRive/HandyCode/main

:: Создаём папку для модулей
set MODULE_DIR=%HANDYCODE_DIR%\modules\handycode
if not exist "%MODULE_DIR%" mkdir "%MODULE_DIR%"

set FILES=__init__.py __main__.py main.py cli.py assistant.py models.py file_manager.py security.py config.py utils.py logo.py project_templates.py

for %%f in (%FILES%) do (
    echo [*] handycode/%%f
    curl -s -L -o "%MODULE_DIR%\%%f" "%BASE_URL%/handycode/%%f" >> "%LOG_FILE%" 2>&1
)

:: Скачиваем setup.py
curl -s -L -o "%HANDYCODE_DIR%\modules\setup.py" "%BASE_URL%/setup.py" >> "%LOG_FILE%" 2>&1

echo [OK] Файлы скачаны

:: Копируем в site-packages
echo [4/5] Копирование файлов...

for /f "tokens=*" %%i in ('%PYTHON_CMD% -c "import site; print(site.getusersitepackages())" 2^>^&1') do set SITE_PACKAGES=%%i

if exist "%SITE_PACKAGES%" (
    if not exist "%SITE_PACKAGES%\handycode" mkdir "%SITE_PACKAGES%\handycode"
    copy /Y "%MODULE_DIR%\*.py" "%SITE_PACKAGES%\handycode\" >nul 2>&1
    echo [OK] Файлы скопированы в site-packages
) else (
    echo [!] site-packages не найден
)

:: Создаём скрипт запуска
echo [5/5] Создание скриптов...

(
echo @echo off
echo %PYTHON_CMD% -m handycode %%*
) > "%BIN_DIR%\hc.bat"

(
echo @echo off
echo %PYTHON_CMD% -m handycode %%*
) > "%BIN_DIR%\handycode.bat"

:: Проверка
echo [*] Проверка...

%PYTHON_CMD% -c "import handycode; print('HandyCode v' + handycode.__version__)" 2>nul
if %errorlevel% equ 0 (
    echo [OK] HandyCode работает!
) else (
    echo [ERROR] HandyCode не работает
    echo.
    echo Проверьте ошибки:
    %PYTHON_CMD% -c "import handycode" 2>&1
    echo.
    pause
    exit /b 1
)

:: API ключ
echo.
echo Нужен API ключ OpenRiver (бесплатно)
echo Получите: https://openrouter.ai/keys
echo.
set /p API_KEY="Введите API ключ (Enter - пропустить): "

(
echo # HandyCode Configuration
echo OPENROUTER_API_KEY=!API_KEY!
) > "%HANDYCODE_DIR%\.env"

:: Добавление в PATH
setx PATH "%PATH%;%BIN_DIR%" >nul 2>&1

echo.
echo ============================================================
echo УСТАНОВКА ЗАВЕРШЕНА!
echo ============================================================
echo.
echo Закройте окно, откройте новый терминал и введите: hc
echo.
echo Если не работает: %BIN_DIR%\hc.bat
echo.
pause