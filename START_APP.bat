@echo off
title VieNeu-TTS Studio Launcher
cd /d "%~dp0"

:: Thiết lập thư mục cache lưu trữ 100% cục bộ trong thư mục dự án
set "HF_HOME=%~dp0models_cache"
set "UV_PYTHON_INSTALL_DIR=%~dp0.uv_python"
set "UV_CACHE_DIR=%~dp0.uv_cache"

echo ================================================================
echo   [VieNeu-TTS Studio] KHOI DONG HE THONG (PORTABLE 100%%)
echo   Thu muc du an: %~dp0
echo   Model Cache   : %HF_HOME%
echo ================================================================
echo.

:: 1. Chạy bước kiểm tra và tải trước tài nguyên (FFmpeg, Model weights)
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" -m apps.preflight
) else (
    uv run python -m apps.preflight
)

:: 2. Tự động mở trình duyệt sau 2 giây
start "" http://127.0.0.1:7860

:: 3. Khởi động Web UI Server
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" apps\gradio_main.py
) else (
    uv run vieneu-web
)

pause
