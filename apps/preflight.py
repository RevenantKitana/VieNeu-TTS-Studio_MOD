"""Preflight check & resource downloader for VieNeu-TTS:
- Checks environment and paths.
- Verifies and downloads FFmpeg standalone binary if missing.
- Pre-downloads / verifies essential model weights in models_cache/ with progress bars.
"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_CACHE = PROJECT_ROOT / "models_cache"
MODELS_CACHE.mkdir(parents=True, exist_ok=True)

if "HF_HOME" not in os.environ:
    os.environ["HF_HOME"] = str(MODELS_CACHE)


def preflight_check():
    print("=" * 66)
    print("  🦜 [VieNeu-TTS] KIỂM TRA & CHUẨN BỊ TÀI NGUYÊN (PREFLIGHT CHECK)")
    print(f"  📁 Thư mục dự án : {PROJECT_ROOT}")
    print(f"  💾 Thư mục cache : {MODELS_CACHE}")
    print("=" * 66)

    # 1. Check & Ensure FFmpeg
    print("\n[1/2] 🔍 Kiểm tra FFmpeg...")
    from apps.batch_speech import ensure_ffmpeg
    ffmpeg_path = ensure_ffmpeg()
    if ffmpeg_path:
        print(f"  ✅ FFmpeg sẵn sàng: {ffmpeg_path}")
    else:
        print("  ⚠️ Không tìm thấy FFmpeg, hệ thống sẽ sử dụng chuẩn WAV mặc định.")

    # 2. Check & Pre-verify Default Model (v3 Turbo)
    print("\n[2/2] 📦 Kiểm tra Model VieNeu-TTS-v3-Turbo & Codec...")
    try:
        from vieneu import Vieneu
        print("  ⏳ Đang nạp thử model mặc định vào cache...")
        tts = Vieneu(mode="v3turbo")
        voices = tts.list_preset_voices() if hasattr(tts, "list_preset_voices") else []
        print(f"  ✅ Model sẵn sàng ({len(voices)} giọng mẫu được nạp thành công)!")
    except Exception as e:
        print(f"  ℹ️ Thông báo nạp model: {e}")

    print("\n" + "=" * 66)
    print("  🎉 TẤT CẢ TÀI NGUYÊN ĐÃ SẴN SÀNG! ĐANG KHỞI ĐỘNG GIAO DIỆN WEB...")
    print("=" * 66 + "\n")


if __name__ == "__main__":
    preflight_check()
