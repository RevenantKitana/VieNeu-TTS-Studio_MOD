@echo off
title VieNeu-TTS Portable Launcher
cd /d "%~dp0"

:: Set all paths to remain 100% inside this project folder
set "HF_HOME=%~dp0models_cache"
set "UV_PYTHON_INSTALL_DIR=%~dp0.uv_python"
set "UV_CACHE_DIR=%~dp0.uv_cache"

echo ================================================================
echo   [VieNeu-TTS] KHOI DONG CHE DO PORTABLE 100%%
echo   Thu muc du an: %~dp0
echo   Model Cache   : %HF_HOME%
echo ================================================================
echo.

:: Kiem tra tai nguyen truoc khi chay
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" -m apps.preflight
) else (
    uv run python -m apps.preflight
)

:: Khoi dong Web UI Server (Trinh duyet se tu dong mo sau khi Server san sang 100%)
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" apps\gradio_main.py
) else (
    uv run vieneu-web
)

pause
