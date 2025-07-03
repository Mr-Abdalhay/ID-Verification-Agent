@echo off
echo ====================================================
echo   Passport Data Extractor - Installation (Windows)
echo ====================================================
echo.

REM Check Python installation
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8+ from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)
python --version
echo OK - Python is installed

REM Check Python version
echo.
echo [2/5] Checking Python version...
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"
if errorlevel 1 (
    echo ERROR: Python 3.8+ is required
    echo Please upgrade your Python installation
    pause
    exit /b 1
)
echo OK - Python version is compatible

REM Check Tesseract installation
echo.
echo [3/5] Checking Tesseract OCR...
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo OK - Tesseract found at default location
    "C:\Program Files\Tesseract-OCR\tesseract.exe" --version
) else (
    echo WARNING: Tesseract OCR not found at default location
    echo.
    echo Please install Tesseract OCR from:
    echo https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    echo Direct download link:
    echo https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.1.20230401.exe
    echo.
    echo Install to the default location: C:\Program Files\Tesseract-OCR\
    echo.
    set /p install_tesseract="Do you want to open the download page? (y/n): "
    if /i "%install_tesseract%"=="y" (
        start https://github.com/UB-Mannheim/tesseract/wiki
    )
    echo.
    set /p continue_anyway="Continue installation anyway? (y/n): "
    if /i not "%continue_anyway%"=="y" exit /b 1
)

REM Create virtual environment
echo.
echo [4/5] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo OK - Virtual environment created
)

REM Activate virtual environment and install dependencies
echo.
echo [5/5] Installing dependencies...
echo This may take a few minutes...

call venv\Scripts\activate
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip
python -m pip install --upgrade pip

REM Install requirements
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo.
    echo Common issues:
    echo - No internet connection
    echo - Antivirus blocking pip
    echo - Insufficient permissions
    pause
    exit /b 1
)

REM Create output directories
echo.
echo Creating output directories...
if not exist output mkdir output
if not exist output\enhanced mkdir output\enhanced
if not exist output\diagnostics mkdir output\diagnostics
if not exist output\results mkdir output\results

REM Create desktop shortcut
echo.
set /p create_shortcut="Create desktop shortcut? (y/n): "
if /i "%create_shortcut%"=="y" (
    powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\Passport Extractor.lnk'); $Shortcut.TargetPath = '%CD%\run_server.bat'; $Shortcut.WorkingDirectory = '%CD%'; $Shortcut.IconLocation = 'shell32.dll,47'; $Shortcut.Save()"
    echo Desktop shortcut created
)

REM Installation complete
echo.
echo ====================================================
echo   Installation Complete!
echo ====================================================
echo.
echo To start the server:
echo   1. Run: run_server.bat
echo   2. Open browser: http://localhost:5000
echo.
echo To test extraction:
echo   python tests\test_extraction.py
echo.
echo For help:
echo   See docs\USER_GUIDE.md
echo.
pause