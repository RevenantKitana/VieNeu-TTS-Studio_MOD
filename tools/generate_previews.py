"""Utility script to generate uniform preview audio files for all built-in and custom voices."""
import io
import json
import os
import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import numpy as np
import soundfile as sf

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Ensure models_cache is used as portable default
if "HF_HOME" not in os.environ:
    os.environ["HF_HOME"] = str(PROJECT_ROOT / "models_cache")

from vieneu import Vieneu
from apps.user_voices import voices_home, load_user_voices, find_voice_preview

PREVIEW_TEXT = "[cười] Nếu như anh không thích em thì, anh cứ bảo là anh không thích em đi, [thở dài] sao cứ phải văn vở với nhau như thế nhở?"


def main():
    print("🚀 Đang khởi tạo mô hình VieNeu-TTS để sinh preview...")
    t0 = time.time()
    tts = Vieneu()
    print(f"✅ Mô hình đã sẵn sàng ({time.time() - t0:.2f}s)!\n")

    # Load custom voices into tts instance
    loaded_custom = load_user_voices(tts)
    print(f"📦 Giọng custom đã nạp: {loaded_custom}\n")

    assets_samples_dir = PROJECT_ROOT / "src" / "vieneu" / "assets" / "samples"
    assets_samples_dir.mkdir(parents=True, exist_ok=True)
    custom_voices_dir = voices_home()
    custom_voices_dir.mkdir(parents=True, exist_ok=True)

    # Get built-in voices from voices_v3_turbo.json
    turbo_json_path = PROJECT_ROOT / "src" / "vieneu" / "assets" / "voices_v3_turbo.json"
    builtin_voices = []
    if turbo_json_path.exists():
        with open(turbo_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            builtin_voices = list(data.get("presets", {}).keys())

    total_voices = len(builtin_voices) + len(loaded_custom)
    print(f"🎙️ Bắt đầu sinh preview cho {total_voices} giọng đọc:")
    print(f"💬 Nội dung: \"{PREVIEW_TEXT}\"\n")

    success_count = 0
    fail_count = 0

    # 1. Built-in voices -> assets/samples/preview_<name>.wav
    print(f"=== 1. Giọng mặc định hệ thống ({len(builtin_voices)} giọng) ===")
    for idx, name in enumerate(builtin_voices, start=1):
        target_file = assets_samples_dir / f"preview_{name}.wav"
        print(f"[{idx:02d}/{total_voices:02d}] Đang sinh preview cho: {name:<18} -> {target_file.name}...", end=" ", flush=True)
        try:
            t_start = time.time()
            wav = tts.infer(PREVIEW_TEXT, voice=name, temperature=0.8)
            if wav is not None and len(wav) > 0:
                sf.write(str(target_file), wav, tts.sample_rate)
                dur = len(wav) / tts.sample_rate
                elapsed = time.time() - t_start
                print(f"✅ OK ({dur:.1f}s audio, xử lý {elapsed:.2f}s)")
                success_count += 1
            else:
                print("❌ Lỗi (wav rỗng)")
                fail_count += 1
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            fail_count += 1

    # 2. Custom voices -> custom_voices/preview_<name>.wav
    if loaded_custom:
        print(f"\n=== 2. Giọng custom người dùng ({len(loaded_custom)} giọng) ===")
        for idx, name in enumerate(loaded_custom, start=len(builtin_voices) + 1):
            target_file = custom_voices_dir / f"preview_{name}.wav"
            print(f"[{idx:02d}/{total_voices:02d}] Đang sinh preview cho: {name:<18} -> {target_file.name}...", end=" ", flush=True)
            try:
                t_start = time.time()
                wav = tts.infer(PREVIEW_TEXT, voice=name, temperature=0.8)
                if wav is not None and len(wav) > 0:
                    sf.write(str(target_file), wav, tts.sample_rate)
                    dur = len(wav) / tts.sample_rate
                    elapsed = time.time() - t_start
                    print(f"✅ OK ({dur:.1f}s audio, xử lý {elapsed:.2f}s)")
                    success_count += 1
                else:
                    print("❌ Lỗi (wav rỗng)")
                    fail_count += 1
            except Exception as e:
                print(f"❌ Lỗi: {e}")
                fail_count += 1

    print("\n========================================================")
    print(f"🎉 Hoàn tất! Thành công: {success_count}/{total_voices} | Thất bại: {fail_count}")
    print("========================================================\n")


if __name__ == "__main__":
    main()
