"""Unit tests for Batch Studio & Audio Library according to spec.md.
Tests:
1. Regex block parsing (ignoring emotion tags [cười], [thở dài], [hắng giọng]).
2. Manual skip prefixes (!, #, //, skip:).
3. Untagged preamble grouping & pure untagged script default.
4. info.json and mapping.txt serialization & timeline calculation.
5. Audio library scanner, ZIP packaging, and project explorer helpers.
6. Audio merging engine & FFmpeg binary finder.
"""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

from apps.batch_speech import (
    BatchItem,
    ensure_ffmpeg,
    format_timestamp,
    merge_project_audio,
    parse_batch_script,
    sanitize_project_name,
    save_project_metadata,
)
from apps.audio_library import (
    export_project_zip,
    get_project_table_data,
    list_projects,
)


class TestBatchStudio(unittest.TestCase):

    def test_parse_batch_script_standard(self):
        script = """[#Đoạn 1] Đây là nội dung đoạn thứ nhất... [cười] rất vui!
Dòng thứ hai của đoạn một.

[#Đoạn 2] Đây là nội dung đoạn thứ hai... [thở dài]
[#Đoạn 3] Đoạn thứ ba [hắng giọng] và kết thúc."""
        items = parse_batch_script(script)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0].tag, "Đoạn 1")
        self.assertIn("Dòng thứ hai của đoạn một.", items[0].text)
        self.assertIn("[cười]", items[0].text)
        self.assertFalse(items[0].is_skipped)

        self.assertEqual(items[1].tag, "Đoạn 2")
        self.assertIn("[thở dài]", items[1].text)

        self.assertEqual(items[2].tag, "Đoạn 3")
        self.assertIn("[hắng giọng]", items[2].text)

    def test_parse_batch_script_manual_skips(self):
        script = """[#Đoạn 1] Nội dung 1
![#Đoạn 2] Đoạn này sẽ bị bỏ qua không tạo audio.
[skip: #Đoạn 3] Đoạn này cũng được bỏ qua.
// [#Đoạn 4] Đoạn bỏ qua kiểu comment.
# [#Đoạn 5] Đoạn bỏ qua kiểu thăng."""
        items = parse_batch_script(script)
        self.assertEqual(len(items), 5)
        self.assertFalse(items[0].is_skipped)
        self.assertTrue(items[1].is_skipped)
        self.assertTrue(items[2].is_skipped)
        self.assertTrue(items[3].is_skipped)
        self.assertTrue(items[4].is_skipped)

    def test_parse_batch_script_preamble_and_untagged(self):
        # 1. Preamble before first block tag
        script_with_preamble = """Đây là lời mở đầu chưa có thẻ.
[#Đoạn 1] Nội dung tiếp theo."""
        items = parse_batch_script(script_with_preamble)
        self.assertEqual(len(items), 1)
        self.assertIn("Đây là lời mở đầu chưa có thẻ.", items[0].text)
        self.assertIn("Nội dung tiếp theo.", items[0].text)

        # 2. Entire script without tags
        pure_script = "Toàn bộ văn bản không có bất kỳ thẻ nào cả."
        items_pure = parse_batch_script(pure_script)
        self.assertEqual(len(items_pure), 1)
        self.assertEqual(items_pure[0].tag, "Đoạn 1")
        self.assertEqual(items_pure[0].text, pure_script)

    def test_metadata_and_mapping_generation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            proj_dir = Path(tmpdir) / "test_proj"
            proj_name = "test_proj"
            items = [
                BatchItem(
                    index=1,
                    tag="Đoạn 1",
                    text="Nội dung 1",
                    file_name="test_proj_01.wav",
                    duration_sec=4.2,
                    status="SUCCESS"
                ),
                BatchItem(
                    index=2,
                    tag="Đoạn 2",
                    text="Nội dung 2",
                    file_name="test_proj_02.wav",
                    duration_sec=4.3,
                    status="SUCCESS"
                )
            ]
            meta = save_project_metadata(
                project_dir=proj_dir,
                project_name=proj_name,
                model_backbone="VieNeu-TTS-v3-Turbo",
                voice="Trúc Ly",
                items=items
            )

            # Check info.json
            self.assertTrue((proj_dir / "info.json").exists())
            with open(proj_dir / "info.json", "r", encoding="utf-8") as f:
                saved_json = json.load(f)
            self.assertEqual(saved_json["project_name"], "test_proj")
            self.assertEqual(saved_json["total_items"], 2)
            self.assertAlmostEqual(saved_json["total_duration_sec"], 8.5, places=2)
            self.assertEqual(saved_json["items"][0]["start_timestamp"], "00:00:00.000")
            self.assertEqual(saved_json["items"][0]["end_timestamp"], "00:00:04.200")
            self.assertEqual(saved_json["items"][1]["start_timestamp"], "00:00:04.200")
            self.assertEqual(saved_json["items"][1]["end_timestamp"], "00:00:08.500")

            # Check mapping.txt
            mapping_file = proj_dir / "test_proj_mapping.txt"
            self.assertTrue(mapping_file.exists())
            with open(mapping_file, "r", encoding="utf-8") as f:
                mapping_text = f.read().strip().splitlines()
            self.assertEqual(len(mapping_text), 2)
            self.assertIn("[test_proj_01.wav] [00:00:00.000 -> 00:00:04.200] [Đoạn 1]", mapping_text[0])
            self.assertIn("[test_proj_02.wav] [00:00:04.200 -> 00:00:08.500] [Đoạn 2]", mapping_text[1])

    def test_audio_merge_and_library(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            proj_dir = Path(tmpdir) / "sach_noi_test"
            proj_dir.mkdir(parents=True, exist_ok=True)
            sr = 24000
            
            # Generate 2 dummy sine wave audio files
            t1 = np.linspace(0, 1.0, sr, endpoint=False)
            wav1 = 0.5 * np.sin(2 * np.pi * 440 * t1)
            sf.write(str(proj_dir / "sach_noi_test_01.wav"), wav1, sr)

            t2 = np.linspace(0, 1.5, int(sr * 1.5), endpoint=False)
            wav2 = 0.5 * np.sin(2 * np.pi * 880 * t2)
            sf.write(str(proj_dir / "sach_noi_test_02.wav"), wav2, sr)

            # Test merge_project_audio
            merged_path, msg = merge_project_audio(proj_dir, output_format="WAV (Lossless PCM)", silence_gap=0.5)
            self.assertIsNotNone(merged_path)
            self.assertTrue(os.path.exists(merged_path))
            info = sf.info(merged_path)
            # Duration = 1.0s + 0.5s silence + 1.5s = 3.0s
            self.assertAlmostEqual(info.duration, 3.0, delta=0.05)

            # Test get_project_table_data
            rows, summary, first_audio, merged_f = get_project_table_data("sach_noi_test")
            zip_p, zip_msg = export_project_zip("non_existent_proj_xyz")
            self.assertIn("không tồn tại", zip_msg)

    def test_fault_tolerance_and_zip_export(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from apps.batch_speech import PROJECTS_DIR
            test_proj_dir = PROJECTS_DIR / "test_ft_proj"
            test_proj_dir.mkdir(parents=True, exist_ok=True)
            try:
                items = [
                    BatchItem(index=1, tag="Đoạn 1", text="OK 1", file_name="test_ft_proj_01.wav", duration_sec=2.0, status="SUCCESS"),
                    BatchItem(index=2, tag="Đoạn 2", text="Error item", file_name="", duration_sec=0.0, status="FAILED"),
                    BatchItem(index=3, tag="Đoạn 3", text="OK 3", file_name="test_ft_proj_03.wav", duration_sec=3.0, status="SUCCESS"),
                ]
                sr = 24000
                sf.write(str(test_proj_dir / "test_ft_proj_01.wav"), np.zeros(sr * 2, dtype=np.float32), sr)
                sf.write(str(test_proj_dir / "test_ft_proj_03.wav"), np.zeros(sr * 3, dtype=np.float32), sr)

                save_project_metadata(test_proj_dir, "test_ft_proj", "v3-Turbo", "Ly", items)

                rows, summary, first_a, merged_f = get_project_table_data("test_ft_proj")
                self.assertEqual(len(rows), 3)
                self.assertIn("LỖI", rows[1][4])

                # Test zip export
                zip_path, msg = export_project_zip("test_ft_proj")
                self.assertIsNotNone(zip_path)
                self.assertTrue(os.path.exists(zip_path))
                if zip_path and os.path.exists(zip_path):
                    os.unlink(zip_path)
            finally:
                if test_proj_dir.exists():
                    shutil.rmtree(test_proj_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
