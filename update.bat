@echo off
chcp 65001 >nul 2>&1
echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║           HANDYCODE - ОБНОВЛЕНИЕ                     ║
echo ╚══════════════════════════════════════════════════════╝
echo.

echo [*] Обновление HandyCode...
echo.

:: Способ 1: pip из GitHub
echo [1] Пробую обновить через pip...
pip install --upgrade --force-reinstall --no-cache-dir git+https://github.com/WiteRive/HandyCode.git

if %errorlevel% equ 0 (
    echo.
    echo [OK] HandyCode обновлён!
    goto :done
)

:: Способ 2: Клонирование и установка
echo [2] Пробую через git clone...
set TEMP_DIR=%TEMP%\handycode_update

if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"
git clone https://github.com/WiteRive/HandyCode.git "%TEMP_DIR%" 2>nul

if exist "%TEMP_DIR%\setup.py" (
    cd /d "%TEMP_DIR%"
    pip install --upgrade --force-reinstall --no-cache-dir -e .
    cd /d %USERPROFILE%
    if %errorlevel% equ 0 (
        echo.
        echo [OK] HandyCode обновлён!
        goto :done
    )
)

:: Способ 3: Скачивание файлов напрямую
echo [3] Пробую обновить файлы напрямую...

for /f "tokens=*" %%i in ('python -c "import handycode, os; print(os.path.dirname(handycode.__file__))" 2^>^&1') do set HC_DIR=%%i

if exist "%HC_DIR%" (
    echo [*] Папка HandyCode: %HC_DIR%

    set BASE_URL=https://raw.githubusercontent.com/WiteRive/HandyCode/main/handycode
    set FILES=__init__.py __main__.py main.py cli.py assistant.py models.py file_manager.py security.py config.py utils.py logo.py project_templates.py

    for %%f in (%FILES%) do (
        echo [*] Обновляю %%f...
        curl -s -L -o "%HC_DIR%\%%f" "!BASE_URL!/%%f" 2>nul
        if exist "%HC_DIR%\%%f" (
            echo   [OK] %%f
        ) else (
            echo   [--] %%f не обновлён
        )
    )

    echo.
    echo [OK] Файлы обновлены!
    goto :done
)

echo [ERROR] Не удалось обновить HandyCode
pause
exit /b 1

:done
echo.
echo Проверка версии...
python -c "import handycode; print('HandyCode v' + handycode.__version__)"
echo.
echo Готово! Запустите hc для проверки.
echo.
pause