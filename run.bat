@echo off
REM This script sets up a virtual environment and runs the PromptGen GUI.

echo Checking for Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not found in your PATH. Please install Python 3 and try again.
    pause
    exit /b
)

REM Set the name of the virtual environment directory
set VENV_DIR=venv

echo Checking for virtual environment...
if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    python -m venv %VENV_DIR%
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment.
        pause
        exit /b
    )
)

echo Activating virtual environment and installing dependencies...
call "%VENV_DIR%\Scripts\activate.bat"
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install requirements. Please check requirements.txt and your internet connection.
    pause
    exit /b
)

echo Launching PromptGen GUI...
python run.py

echo.
echo Application closed.
pause   