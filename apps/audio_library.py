"""Audio Library & Merging Engine for VieNeu-TTS:
Scans outputs/projects/, presents project timeline and metadata,
exports ZIP bundles, and opens project folders in OS file explorer.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

import soundfile as sf

from apps.batch_speech import (
    PROJECTS_DIR,
    format_timestamp,
    merge_project_audio,
)


def list_projects() -> list[tuple[str, str]]:
    """Scans outputs/projects/ and returns a list of (display_label, project_name)
    tuples sorted from newest to oldest.
    """
    if not PROJECTS_DIR.exists():
        PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        return []

    project_list = []

    for item in PROJECTS_DIR.iterdir():
        if item.is_dir():
            proj_name = item.name
            info_file = item / "info.json"
            meta = {}
            if info_file.exists():
                try:
                    with open(info_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                except Exception:
                    pass

            # Extract info
            created_at = meta.get("created_at")
            if not created_at:
                mtime = item.stat().st_mtime
                import datetime
                created_at = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

            total_items = meta.get("total_items")
            if total_items is None:
                # Count wav files
                wav_count = len([f for f in item.glob("*.wav") if "_full_merged" not in f.name.lower()])
                total_items = wav_count

            voice = meta.get("voice", "")
            voice_str = f" - {voice}" if voice else ""

            # Format display label
            # e.g.: sach_noi_chuong_1 (5 câu - Trúc Ly - 2026-09-17 21:50)
            created_short = created_at[:16] if len(created_at) >= 16 else created_at
            label = f"{proj_name} ({total_items} câu{voice_str} - {created_short})"
            
            project_list.append((item.stat().st_mtime, label, proj_name))

    # Sort descending by modification timestamp
    project_list.sort(key=lambda x: x[0], reverse=True)
    return [(label, name) for _, label, name in project_list]


def get_project_table_data(project_name: Optional[str]) -> tuple[list[list[str]], str, Optional[str], Optional[str]]:
    """Loads metadata for a given project name.
    Returns (table_rows, summary_markdown, first_audio_or_merged_path, merged_download_path).
    """
    if not project_name:
        return [], "ℹ️ Chưa chọn dự án nào.", None, None

    proj_dir = PROJECTS_DIR / project_name
    if not proj_dir.exists() or not proj_dir.is_dir():
        return [], f"⚠️ Thư mục dự án **{project_name}** không tồn tại.", None, None

    info_file = proj_dir / "info.json"
    meta = {}
    if info_file.exists():
        try:
            with open(info_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception:
            pass

    # Find merged file if any
    merged_file = None
    for ext in ["mp3", "wav", "flac", "m4a", "ogg"]:
        candidate = proj_dir / f"{project_name}_FULL_MERGED.{ext}"
        if candidate.exists() and candidate.stat().st_size > 0:
            merged_file = str(candidate)
            break

    items_data = meta.get("items", [])
    
    # If info.json is missing or has no items, scan folder directly
    if not items_data:
        wav_files = []
        for f in proj_dir.iterdir():
            if f.is_file() and f.suffix.lower() == ".wav" and "_full_merged" not in f.name.lower():
                m = re.search(r"_(\d+)\.wav$", f.name, re.IGNORECASE)
                idx = int(m.group(1)) if m else 999
                wav_files.append((idx, f))
        wav_files.sort(key=lambda x: x[0])
        
        curr_time = 0.0
        for idx, f in wav_files:
            try:
                info = sf.info(str(f))
                dur = info.duration
            except Exception:
                dur = 0.0
            start_t = curr_time
            end_t = curr_time + dur
            curr_time = end_t
            items_data.append({
                "index": idx,
                "tag": f"Đoạn {idx}",
                "file_name": f.name,
                "text": "",
                "start_sec": start_t,
                "end_sec": end_t,
                "duration_sec": dur,
                "start_timestamp": format_timestamp(start_t),
                "end_timestamp": format_timestamp(end_t),
                "status": "SUCCESS"
            })

    table_rows = []
    first_audio = merged_file

    for it in items_data:
        idx_str = f"{it.get('index', 0):02d}"
        tag_str = f"{it.get('tag', '')} ({it.get('file_name', '')})"
        dur_val = it.get("duration_sec", 0.0)
        dur_str = f"{dur_val:.1f}s"
        start_ts = it.get("start_timestamp", "00:00:00.000")
        end_ts = it.get("end_timestamp", "00:00:00.000")
        time_str = f"{start_ts} ➔ {end_ts}"
        
        txt = it.get("text", "")
        preview_text = (txt[:50] + "...") if len(txt) > 50 else txt
        status = it.get("status", "SUCCESS")
        if status == "FAILED":
            preview_text = f"❌ [LỖI] {preview_text}"
        elif status == "SKIPPED":
            preview_text = f"⏭️ [BỎ QUA] {preview_text}"

        file_name = it.get("file_name", "")
        file_path = str(proj_dir / file_name) if file_name else ""

        if not first_audio and file_path and os.path.exists(file_path):
            first_audio = file_path

        table_rows.append([idx_str, tag_str, dur_str, time_str, preview_text, file_path])

    # Summary
    total_dur = meta.get("total_duration_formatted", format_timestamp(sum(it.get("duration_sec", 0.0) for it in items_data)))
    created_at = meta.get("created_at", "N/A")
    voice = meta.get("voice", "N/A")
    backbone = meta.get("model_backbone", "VieNeu-TTS")

    summary_md = f"""### 📁 Dự án: `{project_name}`
- ⏱️ **Tổng thời lượng:** `{total_dur}` | 📊 **Số đoạn:** `{len(items_data)}` | 🎤 **Giọng:** `{voice}`
- 🤖 **Model:** `{backbone}` | 📅 **Ngày tạo:** `{created_at}`
- 📂 **Thư mục:** `{proj_dir.resolve()}`
"""
    return table_rows, summary_md, first_audio, merged_file


def export_project_zip(project_name: Optional[str]) -> tuple[Optional[str], str]:
    """Compresses project folder into a ZIP file.
    Returns (zip_path | None, status_message).
    """
    if not project_name:
        return None, "⚠️ Vui lòng chọn một dự án trước khi tải ZIP."

    proj_dir = PROJECTS_DIR / project_name
    if not proj_dir.exists():
        return None, "❌ Thư mục dự án không tồn tại."

    try:
        temp_dir = Path(tempfile.gettempdir())
        zip_path = temp_dir / f"{project_name}.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(str(proj_dir)):
                for file in files:
                    full_p = Path(root) / file
                    rel_p = full_p.relative_to(proj_dir)
                    zf.write(full_p, arcname=str(rel_p))

        return str(zip_path), f"✅ Đã đóng gói dự án **{project_name}** thành công ({os.path.getsize(zip_path) / 1024 / 1024:.2f} MB)."
    except Exception as e:
        return None, f"❌ Lỗi đóng gói ZIP: {e}"


def open_project_folder(project_name: Optional[str]) -> str:
    """Opens project folder on the host OS File Explorer."""
    if not project_name:
        target_dir = PROJECTS_DIR
    else:
        target_dir = PROJECTS_DIR / project_name

    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)

    path_str = str(target_dir.resolve())
    try:
        if sys.platform == "win32":
            os.startfile(path_str)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path_str])
        else:
            subprocess.Popen(["xdg-open", path_str])
        return f"📂 Đã mở thư mục: `{path_str}`"
    except Exception as e:
        return f"⚠️ Không thể mở thư mục tự động: {e}. Đường dẫn: `{path_str}`"
