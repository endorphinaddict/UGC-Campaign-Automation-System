@echo off
rem Double-click to run. Uses "python" if available, otherwise the "py" launcher.
cd /d "%~dp0"
where python >nul 2>nul
if %errorlevel%==0 (python -m ugc_poster setup) else (py -m ugc_poster setup)
echo.
pause
