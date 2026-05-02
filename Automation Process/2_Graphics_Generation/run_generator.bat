@echo off
echo ============================================
echo    BUHO VISION - Graphics Generator
echo ============================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Try different Python commands
echo Checking for Python installation...

where python >nul 2>&1
if %errorlevel% == 0 (
    echo Found python command
    python --version
    echo.
    echo Running graphics generator...
    python generate_graphics.py
    goto :end
)

where py >nul 2>&1
if %errorlevel% == 0 (
    echo Found py launcher
    py --version
    echo.
    echo Running graphics generator...
    py generate_graphics.py
    goto :end
)

where python3 >nul 2>&1
if %errorlevel% == 0 (
    echo Found python3 command
    python3 --version
    echo.
    echo Running graphics generator...
    python3 generate_graphics.py
    goto :end
)

echo ERROR: Python not found!
echo Please install Python 3.x from https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation
echo.

:end
echo.
pause