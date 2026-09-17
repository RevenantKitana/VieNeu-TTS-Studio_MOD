"""Batch Studio for VieNeu-TTS:
Multi-block script parsing, project-based audio generation with resume & fault-tolerance,
metadata/timeline generation, and multi-format FFmpeg merging engine.
"""
from __future__ import annotations

import datetime
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterator, Optional

import numpy as np
import soundfile as sf

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
PROJECTS_DIR = OUTPUTS_DIR / "projects"

# CDN link for standalone ffmpeg binary
FFMPEG_CDN_URL = "https://cdn.mio.io.vn/ffmpeg.exe"

# Regex for block tags, ignoring emotion tags: [cười], [thở dài], [hắng giọng]
# Matches: [#Đoạn 1], [Block: Đoạn 1], [Đoạn 1], ![#Đoạn 2], [skip: #Đoạn 3], // [#Đoạn 4], etc.
BLOCK_LINE_PATTERN = re.compile(
    r'^(?:(?P<prefix>!|#|//|skip:)\s*)?\[(?!cười|thở dài|hắng giọng)(?:#|Block:\s*|skip:\s*)?(?P<tag>[^\]]+)\]',
    re.IGNORECASE
)


@dataclass
class BatchItem:
    index: int
    tag: str
    text: str
    is_skipped: bool = False
    file_name: str = ""
    start_sec: float = 0.0
    end_sec: float = 0.0
    duration_sec: float = 0.0
    start_timestamp: str = "00:00:00.000"
    end_timestamp: str = "00:00:00.000"
    status: str = "PENDING"  # PENDING, SUCCESS, FAILED, SKIPPED


def ensure_ffmpeg() -> Optional[str]:
    """Finds ffmpeg executable or downloads standalone ffmpeg.exe from CDN on Windows.
    Returns path to ffmpeg or 'ffmpeg' if available in PATH, or None on failure.
    """
    # 1. Check system PATH
    ffmpeg_in_path = shutil.which("ffmpeg")
    if ffmpeg_in_path:
        return ffmpeg_in_path

    # 2. Check local project root
    local_ffmpeg_exe = PROJECT_ROOT / "ffmpeg.exe"
    if local_ffmpeg_exe.exists() and local_ffmpeg_exe.is_file():
        return str(local_ffmpeg_exe)

    # 3. Check tools/ directory
    tools_ffmpeg_exe = PROJECT_ROOT / "tools" / "ffmpeg.exe"
    if tools_ffmpeg_exe.exists() and tools_ffmpeg_exe.is_file():
        return str(tools_ffmpeg_exe)

    # 4. On Windows, attempt auto-download from CDN
    if sys.platform == "win32":
        try:
            print(f"📥 FFmpeg không có sẵn trong PATH. Đang tự động tải từ CDN: {FFMPEG_CDN_URL}...")
            target_path = str(local_ffmpeg_exe)
            req = urllib.request.Request(
                FFMPEG_CDN_URL,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req) as resp, open(target_path, "wb") as out_f:
                shutil.copyfileobj(resp, out_f)
            if os.path.exists(target_path) and os.path.getsize(target_path) > 1000000:
                print(f"✅ Tải FFmpeg thành công: {target_path}")
                return target_path
        except Exception as e:
            print(f"⚠️ Không thể tự động tải FFmpeg: {e}")

    return None


def format_timestamp(seconds: float) -> str:
    """Formats float seconds into HH:MM:SS.mmm format."""
    if seconds < 0:
        seconds = 0.0
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        secs += 1
        millis = 0
    return f"{hrs:02d}:{mins:02d}:{secs:02d}.{millis:03d}"


def parse_batch_script(raw_text: str) -> list[BatchItem]:
    """Parses a multi-block script into a list of BatchItem.
    - Matches block tags e.g. [#Đoạn 1], [Block: Đoạn 2], ![#Đoạn 3], [skip: #Đoạn 4].
    - Does NOT split on emotion tags e.g. [cười], [thở dài], [hắng giọng].
    - Handles untagged preambles by prepending to the first block.
    - Treats completely untagged scripts as [#Đoạn 1].
    - Preserves multi-line content within each block.
    """
    raw_text = raw_text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not raw_text:
        return []

    lines = raw_text.split("\n")
    
    current_tag = None
    current_is_skipped = False
    current_lines = []
    
    blocks: list[tuple[str, bool, list[str]]] = []
    preamble_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        m = BLOCK_LINE_PATTERN.match(stripped)
        
        # Also check inline skip tag like [skip: #Đoạn 2] or [skip: Đoạn 2]
        inline_skip = False
        if stripped.lower().startswith("[skip:") or stripped.lower().startswith("![") or stripped.lower().startswith("//[") or stripped.lower().startswith("#["):
            inline_skip = True

        if m:
            # Save previous block
            if current_tag is not None:
                blocks.append((current_tag, current_is_skipped, current_lines))
                current_lines = []
            elif current_lines:
                # Untagged preamble
                preamble_lines = current_lines[:]
                current_lines = []

            tag_name = m.group("tag").strip()
            # Clean tag name if it still has # or Block:
            tag_name = re.sub(r"^(?:#|Block:\s*|skip:\s*)", "", tag_name, flags=re.IGNORECASE).strip()
            if not tag_name:
                tag_name = f"Đoạn {len(blocks) + 1}"

            prefix = m.group("prefix")
            is_skipped = bool(prefix or inline_skip or "skip:" in m.group(0).lower())
            
            current_tag = tag_name
            current_is_skipped = is_skipped

            # Extract any text on the same line after the tag
            after_tag = stripped[m.end():].strip()
            if after_tag:
                current_lines.append(after_tag)
        else:
            current_lines.append(line)

    if current_tag is not None:
        blocks.append((current_tag, current_is_skipped, current_lines))
    elif current_lines:
        # Whole text has no tags -> single default block
        blocks.append(("Đoạn 1", False, current_lines))

    # Prepend preamble to first block if any
    if preamble_lines and blocks:
        first_tag, first_skip, first_lines = blocks[0]
        blocks[0] = (first_tag, first_skip, preamble_lines + first_lines)

    # Convert to BatchItem list
    items: list[BatchItem] = []
    idx = 1
    for tag, is_skip, blk_lines in blocks:
        text_content = "\n".join(blk_lines).strip()
        if not text_content and not is_skip:
            continue
        items.append(BatchItem(
            index=idx,
            tag=tag,
            text=text_content,
            is_skipped=is_skip,
            status="SKIPPED" if is_skip else "PENDING"
        ))
        idx += 1

    return items


def sanitize_project_name(name: Optional[str]) -> str:
    """Sanitizes project name or generates a timestamped fallback."""
    if not name or not name.strip():
        return f"batch_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    # Replace non-alphanumeric (except underscores and dashes)
    clean = re.sub(r"[^\w\-]", "_", name.strip())
    clean = re.sub(r"_+", "_", clean).strip("_")
    if not clean:
        return f"batch_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    return clean


def save_project_metadata(
    project_dir: Path,
    project_name: str,
    model_backbone: str,
    voice: str,
    items: list[BatchItem],
    created_at: Optional[str] = None
) -> dict:
    """Generates and writes info.json and <project_name>_mapping.txt."""
    project_dir.mkdir(parents=True, exist_ok=True)
    
    if not created_at:
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Recalculate timeline
    current_sec = 0.0
    total_valid = 0
    item_dicts = []
    mapping_lines = []

    for item in items:
        if item.status == "SUCCESS" and item.duration_sec > 0:
            item.start_sec = round(current_sec, 3)
            item.end_sec = round(current_sec + item.duration_sec, 3)
            current_sec = item.end_sec
            total_valid += 1
        else:
            item.start_sec = round(current_sec, 3)
            item.end_sec = round(current_sec, 3)
        
        item.start_timestamp = format_timestamp(item.start_sec)
        item.end_timestamp = format_timestamp(item.end_sec)
        
        item_dicts.append({
            "index": item.index,
            "tag": item.tag,
            "file_name": item.file_name,
            "text": item.text,
            "start_sec": item.start_sec,
            "end_sec": item.end_sec,
            "duration_sec": round(item.duration_sec, 3),
            "start_timestamp": item.start_timestamp,
            "end_timestamp": item.end_timestamp,
            "status": item.status
        })

        if item.status == "SUCCESS" and item.file_name:
            mapping_lines.append(
                f"[{item.file_name}] [{item.start_timestamp} -> {item.end_timestamp}] [{item.tag}]"
            )

    meta = {
        "project_name": project_name,
        "created_at": created_at,
        "model_backbone": model_backbone,
        "voice": voice,
        "total_items": len(items),
        "total_duration_sec": round(current_sec, 3),
        "total_duration_formatted": format_timestamp(current_sec),
        "items": item_dicts
    }

    # Write info.json
    info_path = project_dir / "info.json"
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # Write mapping.txt
    mapping_path = project_dir / f"{project_name}_mapping.txt"
    with open(mapping_path, "w", encoding="utf-8") as f:
        f.write("\n".join(mapping_lines) + ("\n" if mapping_lines else ""))

    return meta


# Format map for FFmpeg conversion
AUDIO_FORMAT_OPTIONS = {
    "WAV (Lossless PCM)": {"ext": "wav", "args": ["-c:a", "pcm_s16le"]},
    "MP3 (320 kbps)": {"ext": "mp3", "args": ["-c:a", "libmp3lame", "-b:a", "320k"]},
    "MP3 (192 kbps)": {"ext": "mp3", "args": ["-c:a", "libmp3lame", "-b:a", "192k"]},
    "MP3 (128 kbps)": {"ext": "mp3", "args": ["-c:a", "libmp3lame", "-b:a", "128k"]},
    "FLAC (Lossless Compressed)": {"ext": "flac", "args": ["-c:a", "flac"]},
    "M4A / AAC (256 kbps)": {"ext": "m4a", "args": ["-c:a", "aac", "-b:a", "256k"]},
    "OGG / Vorbis (192 kbps)": {"ext": "ogg", "args": ["-c:a", "libvorbis", "-b:a", "192k"]},
}


def merge_project_audio(
    project_dir: str | Path,
    output_format: str = "MP3 (320 kbps)",
    silence_gap: float = 0.5
) -> tuple[Optional[str], str]:
    """Merges all valid segment files in project_dir (*_01.wav, *_02.wav, etc.)
    into <project_name>_FULL_MERGED.<ext> with user-defined silence gap.
    Returns (merged_file_path | None, status_message).
    """
    project_dir = Path(project_dir)
    if not project_dir.exists():
        return None, "❌ Thư mục dự án không tồn tại."

    project_name = project_dir.name
    
    # 1. Scan valid segment wav files, strictly excluding _FULL_MERGED and _merged
    wav_files = []
    for f in project_dir.iterdir():
        if f.is_file() and f.suffix.lower() == ".wav":
            if "_full_merged" in f.name.lower() or "_merged" in f.name.lower():
                continue
            # Match pattern <prefix>_<digits>.wav
            m = re.search(r"_(\d+)\.wav$", f.name, re.IGNORECASE)
            if m:
                wav_files.append((int(m.group(1)), f))

    if not wav_files:
        return None, "❌ Không tìm thấy file âm thanh phân đoạn nào để nối."

    wav_files.sort(key=lambda x: x[0])
    file_list = [f for _, f in wav_files]

    # If only 1 file and wav requested, handle smoothly
    fmt_info = AUDIO_FORMAT_OPTIONS.get(output_format, AUDIO_FORMAT_OPTIONS["MP3 (320 kbps)"])
    ext = fmt_info["ext"]
    out_merged_path = project_dir / f"{project_name}_FULL_MERGED.{ext}"

    # 2. Read audio clips and concatenate with silence
    try:
        clips = []
        sr = 48000
        for f in file_list:
            data, cur_sr = sf.read(str(f), dtype="float32")
            if data.ndim > 1:
                data = data.mean(axis=-1)
            sr = cur_sr
            clips.append(data)

        silence_samples = int(max(0.0, silence_gap) * sr)
        silence = np.zeros(silence_samples, dtype=np.float32)

        parts = []
        for i, clip in enumerate(clips):
            if i > 0 and silence_samples > 0:
                parts.append(silence)
            parts.append(clip)

        full_track = np.concatenate(parts) if parts else np.zeros(sr, dtype=np.float32)

        # Peak normalization
        peak = float(np.abs(full_track).max()) if full_track.size else 0.0
        if peak > 0.98:
            full_track = full_track * (0.98 / peak)

    except Exception as e:
        return None, f"❌ Lỗi đọc và nối dữ liệu âm thanh: {e}"

    # 3. Write audio: direct soundfile write for WAV, or convert via FFmpeg for MP3/M4A/etc.
    temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_wav.close()
    try:
        if ext == "wav":
            sf.write(str(out_merged_path), full_track, sr)
        else:
            sf.write(temp_wav.name, full_track, sr)
            ffmpeg_cmd = ensure_ffmpeg()
            if ffmpeg_cmd:
                cmd = [
                    ffmpeg_cmd, "-y",
                    "-i", temp_wav.name,
                    *fmt_info["args"],
                    str(out_merged_path)
                ]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if res.returncode != 0:
                    print(f"⚠️ FFmpeg returncode != 0: {res.stderr[:200]}")
                    sf.write(str(out_merged_path), full_track, sr)
            else:
                # Fallback if no ffmpeg: write wav or let soundfile try MP3
                if ext == "mp3" and "MP3" in sf.available_formats():
                    sf.write(str(out_merged_path), full_track, sr, format="MP3")
                else:
                    out_merged_path = project_dir / f"{project_name}_FULL_MERGED.wav"
                    sf.write(str(out_merged_path), full_track, sr)

        dur = len(full_track) / sr
        return str(out_merged_path), f"✅ Đã nối {len(file_list)} đoạn thành công! (Tổng: {format_timestamp(dur)}) -> {out_merged_path.name}"
    except Exception as e:
        return None, f"❌ Lỗi xuất file nối âm thanh: {e}"
    finally:
        if os.path.exists(temp_wav.name):
            try:
                os.unlink(temp_wav.name)
            except Exception:
                pass


def extract_speaker_and_text(line: str) -> tuple[Optional[str], Optional[str]]:
    """Tách tên nhân vật và lời thoại CHỈ qua dấu ngoặc tròn ():
    - (Tên) Lời thoại hoặc (Tên): Lời thoại hoặc (Tên:) Lời thoại
    - **(Tên)** Lời thoại hoặc **(Tên):** Lời thoại hoặc (**Tên**) Lời thoại
    Dấu ngoặc vuông [] được giữ nguyên hoàn toàn cho tag cảm xúc [cười], [thở dài] và tag đoạn [#Đoạn 1].
    """
    s = line.strip()
    if not s:
        return None, None

    # Bỏ qua dòng tiêu đề phân đoạn
    if s.startswith("[#") or s.startswith("[Block") or s.startswith("![#") or s.startswith("[skip:"):
        return None, None

    # Blacklist từ khóa không phải tên nhân vật
    EXCLUDED_NAMES = {
        "cười", "thở dài", "hắng giọng",
        "lưu ý", "ghi chú", "chú ý", "ví dụ", "thời gian", "kết quả",
        "tóm lại", "kết luận", "chương", "hồi", "tập", "cảnh", "skip", "block", "đoạn"
    }

    # Match (Tên) hoặc (Tên): hoặc **(Tên)** hoặc (**Tên**)
    m = re.match(
        r"^(?:\*\*\s*)?\(\s*(?:\*\*\s*)?([A-Za-zÀ-ỹ0-9_ \.\-]+?)(?::)?(?:\s*\*\*)?\s*\)(?:\s*\*\*)?\s*:?\s*(.+)$",
        s
    )
    if m:
        spk = m.group(1).strip()
        dlg = m.group(2).strip()
        if spk.lower() not in EXCLUDED_NAMES and not spk.isdigit() and len(spk) <= 35 and not spk.startswith("#"):
            return spk, dlg

    return None, None


def parse_block_dialogue(block_text: str) -> list[dict[str, Optional[str]]]:
    """Splits a block's content into dialogue turns:
    Returns a list of turns: [{'speaker': 'Phương', 'text': '...'}, ...]
    If no speaker format is found, returns [{'speaker': None, 'text': block_text}]
    """
    if not block_text:
        return []

    lines = block_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    turns: list[dict[str, Optional[str]]] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        spk, dlg = extract_speaker_and_text(stripped)
        if spk and dlg:
            turns.append({"speaker": spk, "text": dlg})
        else:
            if turns:
                # Continuation of current speaker's turn
                turns[-1]["text"] = (turns[-1]["text"] or "") + " " + stripped
            else:
                # Untagged preamble line
                turns.append({"speaker": None, "text": stripped})

    if not turns:
        return [{"speaker": None, "text": block_text.strip()}]
    
    return turns


def batch_to_speech(
    tts,
    script_text: str,
    project_name: str,
    voice_id: str,
    resume_mode: bool,
    auto_merge: bool,
    merge_format: str,
    silence_gap: float,
    stop_requested: Callable[[], bool],
    synthesize_single_fn: Callable,
    max_chars_chunk: int = 256,
    temperature: float = 0.8,
    denoise: bool = True,
    use_batch: bool = True,
    batch_size: int = 4,
    session_id: str = "default",
    speaker_mapping: Optional[dict[str, str]] = None,
    dialogue_silence_gap: float = 0.3,
) -> Iterator[tuple[Optional[str], str, str]]:
    """Gradio generator executing Batch Studio workflow.
    Yields (audio_path | None, status_text, estimate_text).
    - Checks resume / overwrite logic
    - Supports Multi-Speaker dialogue turns inside each block
    - Fault-tolerance per block
    - Saves info.json and mapping.txt
    - Auto merges if requested
    """
    if tts is None:
        yield None, "⚠️ Vui lòng tải model trước!", ""
        return

    if not script_text or not script_text.strip():
        yield None, "⚠️ Kịch bản đang trống. Hãy nhập hoặc dán nội dung kịch bản!", ""
        return

    items = parse_batch_script(script_text)
    if not items:
        yield None, "⚠️ Không tìm thấy đoạn văn bản hợp lệ nào trong kịch bản.", ""
        return

    proj_name = sanitize_project_name(project_name)
    proj_dir = PROJECTS_DIR / proj_name
    proj_dir.mkdir(parents=True, exist_ok=True)

    # Determine backbone model name
    backbone_name = getattr(tts, "model_name", "VieNeu-TTS")
    if hasattr(tts, "config") and isinstance(tts.config, dict):
        backbone_name = tts.config.get("repo", backbone_name)

    total_items = len(items)
    pad_len = 2 if total_items < 100 else 3

    # Check existing info.json for creation timestamp
    info_file = proj_dir / "info.json"
    created_at = None
    if info_file.exists():
        try:
            with open(info_file, "r", encoding="utf-8") as f:
                old_info = json.load(f)
                created_at = old_info.get("created_at")
        except Exception:
            pass

    t0 = time.time()
    processed_count = 0
    durations_history: list[float] = []

    yield None, f"📦 Bắt đầu dự án: **{proj_name}** ({total_items} đoạn). Chế độ: {'Resume (Bỏ qua đã có)' if resume_mode else 'Ghi đè toàn bộ'}...", ""

    last_wav_path: Optional[str] = None

    def _resolve_turn_voice(spk_name: Optional[str]) -> str:
        if not spk_name or not speaker_mapping:
            return voice_id
        v = speaker_mapping.get(spk_name.lower())
        if not v:
            # Fuzzy match
            for k, mapped_v in speaker_mapping.items():
                if k in spk_name.lower() or spk_name.lower() in k:
                    return mapped_v
            return voice_id
        return v

    for i, item in enumerate(items, start=1):
        if stop_requested():
            yield None, "⏹️ Đã dừng tiến trình tạo Batch theo yêu cầu.", ""
            break

        file_name = f"{proj_name}_{i:0{pad_len}d}.wav"
        item.file_name = file_name
        file_path = proj_dir / file_name

        # 1. Check if skipped manually
        if item.is_skipped:
            item.status = "SKIPPED"
            item.duration_sec = 0.0
            continue

        # 2. Check if already exists in Resume mode
        if resume_mode and file_path.exists() and file_path.stat().st_size > 44:
            try:
                info = sf.info(str(file_path))
                if info.duration > 0:
                    item.duration_sec = info.duration
                    item.status = "SUCCESS"
                    last_wav_path = str(file_path)
                    processed_count += 1
                    save_project_metadata(proj_dir, proj_name, backbone_name, voice_id, items, created_at)
                    yield str(file_path), f"⚡ Đoạn {i}/{total_items} ({item.tag}): Đã có sẵn -> Bỏ qua (Độ dài: {info.duration:.1f}s)", ""
                    continue
            except Exception as e:
                print(f"File {file_path} bị lỗi, sẽ render lại: {e}")

        # 3. Render audio for this item with Multi-Speaker & Fault-Tolerance
        t_block_start = time.time()
        turns = parse_block_dialogue(item.text)
        is_multi_turn = len(turns) > 1 or (len(turns) == 1 and turns[0]["speaker"] is not None)

        yield None, f"⏳ Đang xử lý: Đoạn {i}/{total_items} ({item.tag}) [{len(turns)} lượt thoại]...", ""

        try:
            if not is_multi_turn:
                # Single turn block: direct synthesis
                gen = synthesize_single_fn(
                    item.text,
                    voice_id,
                    None,  # custom_audio
                    "",    # custom_text
                    "preset_mode",  # mode
                    "Standard (Một lần)",
                    use_batch,
                    batch_size,
                    temperature,
                    max_chars_chunk,
                    denoise,
                    session_id
                )
                
                block_audio_path = None
                for out_path, status_text in gen:
                    if stop_requested():
                        break
                    if out_path:
                        block_audio_path = out_path

                if stop_requested():
                    yield None, "⏹️ Đã dừng tiến trình tạo Batch.", ""
                    break

                if block_audio_path and os.path.exists(block_audio_path):
                    shutil.copyfile(block_audio_path, str(file_path))
                else:
                    item.status = "FAILED"
                    save_project_metadata(proj_dir, proj_name, backbone_name, voice_id, items, created_at)
                    yield None, f"⚠️ Đoạn {i}/{total_items} ({item.tag}): Không sinh được âm thanh.", ""
                    continue
            else:
                # Multi-speaker block: synthesize turns & join
                sub_clips = []
                cur_sr = 48000
                
                for t_idx, turn in enumerate(turns, start=1):
                    if stop_requested():
                        break
                    t_spk = turn["speaker"]
                    t_txt = turn["text"] or ""
                    t_voice = _resolve_turn_voice(t_spk)
                    
                    spk_disp = f"[{t_spk}] " if t_spk else ""
                    yield None, f"⏳ Đoạn {i}/{total_items} ({item.tag}) -> Thoại {t_idx}/{len(turns)}: {spk_disp}{t_txt[:30]}...", ""
                    
                    gen = synthesize_single_fn(
                        t_txt,
                        t_voice,
                        None, "", "preset_mode", "Standard (Một lần)",
                        use_batch, batch_size, temperature, max_chars_chunk,
                        denoise, session_id
                    )
                    sub_out = None
                    for out_p, _ in gen:
                        if stop_requested():
                            break
                        if out_p:
                            sub_out = out_p

                    if sub_out and os.path.exists(sub_out):
                        data, audio_sr = sf.read(sub_out, dtype="float32")
                        if data.ndim > 1:
                            data = data.mean(axis=-1)
                        cur_sr = audio_sr
                        sub_clips.append(data)

                if stop_requested():
                    yield None, "⏹️ Đã dừng tiến trình tạo Batch.", ""
                    break

                if sub_clips:
                    # Concatenate sub-clips with dialogue silence
                    silence_samples = int(max(0.0, dialogue_silence_gap) * cur_sr)
                    silence_arr = np.zeros(silence_samples, dtype=np.float32)
                    joined = []
                    for c_idx, clip in enumerate(sub_clips):
                        if c_idx > 0 and silence_samples > 0:
                            joined.append(silence_arr)
                        joined.append(clip)
                    
                    block_full_audio = np.concatenate(joined)
                    sf.write(str(file_path), block_full_audio, cur_sr)
                else:
                    item.status = "FAILED"
                    save_project_metadata(proj_dir, proj_name, backbone_name, voice_id, items, created_at)
                    yield None, f"⚠️ Đoạn {i}/{total_items} ({item.tag}): Không sinh được âm thanh cho các lượt thoại.", ""
                    continue

            # Record success
            if file_path.exists():
                audio_info = sf.info(str(file_path))
                item.duration_sec = audio_info.duration
                item.status = "SUCCESS"
                last_wav_path = str(file_path)
                processed_count += 1
                
                block_dur = time.time() - t_block_start
                durations_history.append(block_dur)

                # Estimate remaining
                avg_time = sum(durations_history) / len(durations_history)
                remaining_blocks = total_items - i
                est_remain = avg_time * remaining_blocks
                estimate_msg = f"Đoạn {i}/{total_items} | Ước tính còn lại: ~{est_remain:.0f}s"

                save_project_metadata(proj_dir, proj_name, backbone_name, voice_id, items, created_at)
                yield str(file_path), f"🔊 Hoàn thành đoạn {i}/{total_items} ({item.tag}) [{audio_info.duration:.1f}s]", estimate_msg

        except Exception as e:
            item.status = "FAILED"
            save_project_metadata(proj_dir, proj_name, backbone_name, voice_id, items, created_at)
            yield None, f"❌ Lỗi ở đoạn {i}/{total_items} ({item.tag}): {e} (Tiếp tục đoạn sau...)", ""

    # Final metadata save
    final_meta = save_project_metadata(proj_dir, proj_name, backbone_name, voice_id, items, created_at)
    total_time = time.time() - t0
    
    success_count = sum(1 for item in items if item.status == "SUCCESS")
    total_dur_str = final_meta.get("total_duration_formatted", "00:00:00.000")

    final_audio_result = last_wav_path

    # Auto merge if requested
    if auto_merge and success_count > 0:
        yield None, f"🔗 Đang tự động nối {success_count} đoạn thành file tổng ({merge_format})...", ""
        merged_path, merge_note = merge_project_audio(proj_dir, output_format=merge_format, silence_gap=silence_gap)
        if merged_path and os.path.exists(merged_path):
            final_audio_result = merged_path
            yield final_audio_result, f"✅ Hoàn tất toàn bộ dự án **{proj_name}**! {merge_note} (Thời gian thực hiện: {total_time:.1f}s)", ""
            return
        else:
            yield final_audio_result, f"⚠️ Hoàn tất tạo {success_count}/{total_items} đoạn, nhưng nối file thất bại: {merge_note}", ""
            return

    yield final_audio_result, f"✅ Hoàn tất dự án **{proj_name}** ({success_count}/{total_items} đoạn thành công, tổng thời lượng: {total_dur_str})!", ""
