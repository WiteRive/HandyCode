# HandyCode Installer for Windows
# Usage: irm https://raw.githubusercontent.com/WiteRive/HandyCode/main/install.ps1 -OutFile $env:TEMP\install.ps1; & $env:TEMP\install.ps1

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

Clear-Host
Write-Host @"

    ====================================================
          HANDYCODE - AI CODE ASSISTANT
          Windows Installer v2.0.0
    ====================================================

"@ -ForegroundColor Cyan

# STEP 1: Check Python
Write-Host "[1/5] Checking Python..." -ForegroundColor Yellow

$pythonCmd = $null
$pythonPaths = @("python", "python3", "py")

foreach ($cmd in $pythonPaths) {
    try {
        $null = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = $cmd
            $version = & $cmd --version 2>&1
            Write-Host "  [OK] $version" -ForegroundColor Green
            break
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Host "  [ERROR] Python not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Please install Python 3.8+ from https://python.org"
    Write-Host "  During installation, check [V] Add Python to PATH"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# STEP 2: Check pip
Write-Host "[2/5] Checking pip..." -ForegroundColor Yellow

try {
    $null = & $pythonCmd -m pip --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] pip is ready" -ForegroundColor Green
    } else {
        throw "pip check failed"
    }
} catch {
    Write-Host "  [!] Installing pip..." -ForegroundColor Yellow
    try {
        & $pythonCmd -m ensurepip --upgrade 2>&1 | Out-Null
        Write-Host "  [OK] pip installed" -ForegroundColor Green
    } catch {
        Write-Host "  [ERROR] Failed to install pip" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# STEP 3: Prepare directories
Write-Host "[3/5] Preparing directories..." -ForegroundColor Yellow

$handycodeDir = "$env:USERPROFILE\.handycode"
$binDir = "$env:USERPROFILE\.local\bin"

try {
    if (-not (Test-Path $handycodeDir)) {
        New-Item -ItemType Directory -Path $handycodeDir -Force | Out-Null
    }
    if (-not (Test-Path $binDir)) {
        New-Item -ItemType Directory -Path $binDir -Force | Out-Null
    }
    Write-Host "  [OK] Directories created" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Failed to create directories" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# STEP 4: Install HandyCode
Write-Host "[4/5] Installing HandyCode..." -ForegroundColor Yellow

$installSuccess = $false

# Method 1: Install from PyPI
Write-Host "  [*] Trying PyPI..." -ForegroundColor Gray
try {
    $result = & $pythonCmd -m pip install --user handycode 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Installed from PyPI" -ForegroundColor Green
        $installSuccess = $true
    }
} catch {}

# Method 2: Install from local folder
if (-not $installSuccess) {
    if (Test-Path ".\setup.py") {
        Write-Host "  [*] Found local project, installing..." -ForegroundColor Gray
        try {
            & $pythonCmd -m pip install --user -e . 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  [OK] Installed locally" -ForegroundColor Green
                $installSuccess = $true
            }
        } catch {}
    }
}

# Method 3: Install from GitHub
if (-not $installSuccess) {
    $gitCmd = Get-Command git -ErrorAction SilentlyContinue

    if ($gitCmd) {
        Write-Host "  [*] Trying GitHub..." -ForegroundColor Gray

        $tempDir = "$env:TEMP\handycode_install"

        if (Test-Path $tempDir) {
            Remove-Item -Recurse -Force $tempDir -ErrorAction SilentlyContinue
        }

        try {
            git clone https://github.com/WiteRive/HandyCode.git $tempDir 2>&1 | Out-Null

            if (Test-Path "$tempDir\setup.py") {
                Push-Location $tempDir
                & $pythonCmd -m pip install --user -e . 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  [OK] Installed from GitHub" -ForegroundColor Green
                    $installSuccess = $true
                }
                Pop-Location
            }
        } catch {
            Write-Host "  [!] GitHub method failed" -ForegroundColor Yellow
        }
    }
}

if (-not $installSuccess) {
    Write-Host "  [ERROR] Installation failed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Try manual installation:"
    Write-Host "  1. pip install handycode"
    Write-Host "  2. Or download from: https://github.com/WiteRive/HandyCode"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Verify installation
try {
    $version = & $pythonCmd -c "import handycode; print(handycode.__version__)" 2>&1
    Write-Host "  [OK] HandyCode v$version installed" -ForegroundColor Green
} catch {
    Write-Host "  [!] Installed but verification failed" -ForegroundColor Yellow
}

# STEP 5: Configuration
Write-Host "[5/5] Configuration..." -ForegroundColor Yellow

# Ask for API key
Write-Host ""
Write-Host "  An OpenRouter API key is required (free)" -ForegroundColor White
Write-Host "  Get your key at: https://openrouter.ai/keys" -ForegroundColor Cyan
Write-Host ""

$apiKey = Read-Host "  Enter API key (or press Enter to skip)"

if ($apiKey -and $apiKey.Length -gt 20) {
    Write-Host "  [OK] API key accepted" -ForegroundColor Green
} elseif ($apiKey -and $apiKey.Length -le 20) {
    Write-Host "  [!] Key too short, skipped" -ForegroundColor Yellow
    $apiKey = ""
} else {
    Write-Host "  [!] No key provided. Add it later in:" -ForegroundColor Yellow
    Write-Host "     $handycodeDir\.env" -ForegroundColor Cyan
}

# Save .env file
$envContent = "# HandyCode Configuration`n# Get key: https://openrouter.ai/keys`nOPENROUTER_API_KEY=$apiKey`n"

try {
    [System.IO.File]::WriteAllText("$handycodeDir\.env", $envContent, [System.Text.Encoding]::ASCII)
    Write-Host "  [OK] Config saved" -ForegroundColor Green
} catch {
    Write-Host "  [!] Failed to save .env file" -ForegroundColor Yellow
}

# Save config.json
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
    Write-Host "  [OK] Settings saved" -ForegroundColor Green
} catch {
    Write-Host "  [!] Failed to save config" -ForegroundColor Yellow
}

# Create launcher scripts
try {
    $hcBat = "@echo off`npython -m handycode %*`n"
    [System.IO.File]::WriteAllText("$binDir\hc.bat", $hcBat, [System.Text.Encoding]::ASCII)

    $handycodeBat = "@echo off`npython -m handycode %*`n"
    [System.IO.File]::WriteAllText("$binDir\handycode.bat", $handycodeBat, [System.Text.Encoding]::ASCII)

    Write-Host "  [OK] Launcher scripts created" -ForegroundColor Green
} catch {
    Write-Host "  [!] Failed to create scripts" -ForegroundColor Yellow
}

# Add to PATH
try {
    $userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($userPath -notlike "*$binDir*") {
        [Environment]::SetEnvironmentVariable("PATH", "$userPath;$binDir", "User")
        $env:Path = "$env:Path;$binDir"
        Write-Host "  [OK] Added to PATH" -ForegroundColor Green
    } else {
        Write-Host "  [OK] Already in PATH" -ForegroundColor Green
    }
} catch {
    Write-Host "  [!] Add to PATH manually: $binDir" -ForegroundColor Yellow
}

# Final message
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "         INSTALLATION COMPLETE!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

if ($apiKey) {
    Write-Host "  [V] API key configured" -ForegroundColor Green
} else {
    Write-Host "  [!] Add API key to: $handycodeDir\.env" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "To start using HandyCode:" -ForegroundColor White
Write-Host ""
Write-Host "  1. Close this window" -ForegroundColor White
Write-Host "  2. Open new terminal (Win+R -> cmd or PowerShell)" -ForegroundColor White
Write-Host "  3. Type:" -ForegroundColor White
Write-Host ""
Write-Host "     hc" -ForegroundColor Green
Write-Host ""
Write-Host "If command not found, restart your computer" -ForegroundColor Yellow
Write-Host "or use full path:" -ForegroundColor Yellow
Write-Host "  $binDir\hc.bat" -ForegroundColor Cyan
Write-Host ""
Write-Host "Examples:" -ForegroundColor White
Write-Host "  hc                         Start interactive mode" -ForegroundColor Green
Write-Host "  hc -c 'Create Python app'   Quick command" -ForegroundColor Green
Write-Host "  hc --help                   Show help" -ForegroundColor Green
Write-Host ""

Read-Host "Press Enter to finish"