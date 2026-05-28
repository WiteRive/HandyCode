# HandyCode Installer для Windows PowerShell
# Запуск: irm https://raw.githubusercontent.com/yourusername/handycode/main/install.ps1 | iex

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Функции для вывода
function Write-Color($Text, $Color = "White") {
    Write-Host $Text
}

function Write-Step($Text) {
    Write-Host ""
    Write-Host $Text
    Write-Host ("-" * 60)
}

function Write-Success($Text) {
    Write-Host "[OK] $Text" -ForegroundColor Green
}

function Write-Error($Text) {
    Write-Host "[ERROR] $Text" -ForegroundColor Red
}

function Write-Warning($Text) {
    Write-Host "[!] $Text" -ForegroundColor Yellow
}

function Write-Info($Text) {
    Write-Host "[*] $Text" -ForegroundColor Cyan
}

# Очистка экрана и логотип
Clear-Host
Write-Host @"

    ╔══════════════════════════════════════════════════════╗
    ║                                                      ║
    ║         HANDYCODE - AI Ассистент                     ║
    ║         Установщик для Windows                       ║
    ║         v2.0.0                                       ║
    ║                                                      ║
    ╚══════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

# Шаг 1: Проверка Python
Write-Step "ШАГ 1/5: Проверка Python"

$pythonCmd = $null
$pythonVersion = $null

# Ищем Python разными способами
$pythonPaths = @("python", "python3", "py")
foreach ($cmd in $pythonPaths) {
    try {
        $version = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = $cmd
            $pythonVersion = $version
            break
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Error "Python не найден!"
    Write-Host ""
    Write-Host "Пожалуйста, установите Python:"
    Write-Host "1. Откройте https://python.org"
    Write-Host "2. Скачайте Python 3.8 или новее"
    Write-Host "3. При установке ОБЯЗАТЕЛЬНО отметьте галочку:"
    Write-Host "   [V] Add Python to PATH"
    Write-Host "4. Перезапустите терминал"
    Write-Host "5. Запустите установщик снова"
    Write-Host ""
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Success "Найден: $pythonVersion"

# Шаг 2: Проверка pip
Write-Step "ШАГ 2/5: Проверка pip"

try {
    $pipVersion = & $pythonCmd -m pip --version 2>&1
    Write-Success "pip работает"
} catch {
    Write-Warning "pip не найден, устанавливаем..."
    try {
        & $pythonCmd -m ensurepip --upgrade 2>&1
        Write-Success "pip установлен"
    } catch {
        Write-Error "Не удалось установить pip"
        Read-Host "Нажмите Enter для выхода"
        exit 1
    }
}

# Шаг 3: Создание директорий
Write-Step "ШАГ 3/5: Подготовка"

$handycodeDir = "$env:USERPROFILE\.handycode"
$binDir = "$env:USERPROFILE\.local\bin"

try {
    if (-not (Test-Path $handycodeDir)) {
        New-Item -ItemType Directory -Path $handycodeDir -Force | Out-Null
    }
    if (-not (Test-Path $binDir)) {
        New-Item -ItemType Directory -Path $binDir -Force | Out-Null
    }
    Write-Success "Директории созданы"
} catch {
    Write-Error "Не удалось создать директории: $_"
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Шаг 4: Установка HandyCode
Write-Step "ШАГ 4/5: Установка HandyCode"

Write-Info "Устанавливаю пакет..."

$installSuccess = $false

# Способ 1: Установка из PyPI
Write-Info "Пробую установить из PyPI..."
try {
    $result = & $pythonCmd -m pip install --user handycode 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Пакет установлен из PyPI"
        $installSuccess = $true
    } else {
        Write-Warning "PyPI: $result"
    }
} catch {
    Write-Warning "Не удалось установить из PyPI"
}

# Способ 2: Установка из локальной папки если есть
if (-not $installSuccess) {
    # Ищем handycode в текущей директории
    if (Test-Path ".\setup.py") {
        Write-Info "Найден локальный проект, устанавливаю..."
        try {
            & $pythonCmd -m pip install --user -e . 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Пакет установлен локально"
                $installSuccess = $true
            }
        } catch {}
    }
}

# Способ 3: Установка из GitHub
if (-not $installSuccess) {
    Write-Info "Пробую установить из GitHub..."

    $gitAvailable = Get-Command git -ErrorAction SilentlyContinue

    if ($gitAvailable) {
        $tempDir = "$env:TEMP\handycode_install"

        if (Test-Path $tempDir) {
            Remove-Item -Recurse -Force $tempDir -ErrorAction SilentlyContinue
        }

        try {
            Write-Info "Клонирую репозиторий..."
            git clone https://github.com/yourusername/handycode.git $tempDir 2>&1

            if (Test-Path "$tempDir\setup.py") {
                Set-Location $tempDir
                & $pythonCmd -m pip install --user -e . 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Success "Пакет установлен из GitHub"
                    $installSuccess = $true
                }
                Set-Location $env:USERPROFILE
            }
        } catch {
            Write-Warning "Не удалось установить из GitHub: $_"
        }
    } else {
        Write-Warning "Git не найден, пропускаем установку из GitHub"
    }
}

if (-not $installSuccess) {
    Write-Error "Не удалось установить HandyCode автоматически"
    Write-Host ""
    Write-Host "Попробуйте установить вручную:"
    Write-Host "1. pip install handycode"
    Write-Host "2. Или скачайте с https://github.com/yourusername/handycode"
    Write-Host ""
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Проверяем установку
try {
    $version = & $pythonCmd -c "import handycode; print(handycode.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "HandyCode v$version установлен успешно"
    }
} catch {
    Write-Warning "Пакет установлен, но проверка не удалась: $_"
}

# Шаг 5: Настройка
Write-Step "ШАГ 5/5: Настройка"

# Запрашиваем API ключ
Write-Host ""
Write-Host "Для работы нужен API ключ OpenRouter (бесплатно)"
Write-Host "Получите ключ: https://openrouter.ai/keys"
Write-Host ""

$apiKey = Read-Host "Введите API ключ (или Enter чтобы пропустить)"

if ($apiKey -and $apiKey.Length -gt 20) {
    Write-Success "API ключ получен"
} elseif ($apiKey) {
    Write-Warning "Ключ слишком короткий, пропускаем"
    $apiKey = ""
} else {
    Write-Warning "Ключ не введён. Добавите позже в файл ~/.handycode/.env"
}

# Сохраняем конфигурацию
$envContent = @"
# HandyCode Configuration
# Получить ключ: https://openrouter.ai/keys
OPENROUTER_API_KEY=$apiKey
"@

try {
    [System.IO.File]::WriteAllText("$handycodeDir\.env", $envContent, [System.Text.Encoding]::UTF8)
    Write-Success "Конфигурация сохранена"
} catch {
    Write-Warning "Не удалось сохранить .env: $_"
}

# Сохраняем config.json
$config = @{
    default_model = "deepseek"
    auto_approve = $false
    language = "ru"
    installed_version = "2.0.0"
    install_date = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
}

try {
    $configJson = $config | ConvertTo-Json
    [System.IO.File]::WriteAllText("$handycodeDir\config.json", $configJson, [System.Text.Encoding]::UTF8)
    Write-Success "Конфиг сохранён"
} catch {
    Write-Warning "Не удалось сохранить config.json: $_"
}

# Создаём скрипты запуска
try {
    # hc.bat
    @"
@echo off
python -m handycode %*
"@ | Out-File -FilePath "$binDir\hc.bat" -Encoding ASCII -Force

    # handycode.bat
    @"
@echo off
python -m handycode %*
"@ | Out-File -FilePath "$binDir\handycode.bat" -Encoding ASCII -Force

    Write-Success "Скрипты запуска созданы"
} catch {
    Write-Warning "Не удалось создать скрипты: $_"
}

# Добавляем в PATH
try {
    $userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($userPath -notlike "*$binDir*") {
        [Environment]::SetEnvironmentVariable("PATH", "$userPath;$binDir", "User")
        $env:Path = "$env:Path;$binDir"
        Write-Success "Добавлено в PATH"
    } else {
        Write-Success "Уже в PATH"
    }
} catch {
    Write-Warning "Не удалось добавить в PATH. Добавьте вручную: $binDir"
}

# Финальное сообщение
Write-Host ""
Write-Host ("=" * 60)
Write-Host "УСТАНОВКА ЗАВЕРШЕНА!" -ForegroundColor Green
Write-Host ("=" * 60)
Write-Host ""

if ($apiKey) {
    Write-Host "[V] API ключ настроен" -ForegroundColor Green
} else {
    Write-Host "[!] Добавьте API ключ в файл:" -ForegroundColor Yellow
    Write-Host "    $handycodeDir\.env" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Для использования:" -ForegroundColor White
Write-Host ""
Write-Host "  1. Закройте это окно"
Write-Host "  2. Откройте новый терминал (Win+R -> cmd или PowerShell)"
Write-Host "  3. Введите команду:" -ForegroundColor White
Write-Host ""
Write-Host "     hc" -ForegroundColor Green
Write-Host ""
Write-Host "Если команда не работает, перезагрузите компьютер"
Write-Host "или используйте полный путь:"
Write-Host "  $binDir\hc.bat" -ForegroundColor Cyan
Write-Host ""
Write-Host "Примеры:" -ForegroundColor White
Write-Host "  hc                              # Запуск" -ForegroundColor Green
Write-Host "  hc -c 'Создай Python проект'     # Быстрая команда" -ForegroundColor Green
Write-Host "  hc --help                       # Справка" -ForegroundColor Green
Write-Host ""

Read-Host "Нажмите Enter для завершения"