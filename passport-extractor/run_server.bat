@echo off
echo ====================================================
echo   Passport Data Extractor - Server
echo ====================================================
echo.

REM Check if virtual environment exists
if not exist venv (
    echo ERROR: Virtual environment not found
    echo Please run install.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Dependencies not installed
    echo Please run install.bat first
    pause
    exit /b 1
)

REM Start the server
echo Starting server...
echo.
echo Server will be available at:
echo   http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

cd src
python app.py

REM If server exits, pause to show any error messages
pause