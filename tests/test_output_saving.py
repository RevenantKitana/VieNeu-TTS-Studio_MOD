import os
import shutil
import tempfile
import unittest
from pathlib import Path
import numpy as np
import soundfile as sf

from apps.gradio_main import save_output_audio, OUTPUTS_DIR
from apps.srt_speech import write_audio, OUTPUTS_DIR as SRT_OUTPUTS_DIR
from apps.batch_speech import (
    batch_to_speech,
    PROJECTS_DIR,
    ensure_ffmpeg,
    merge_project_audio,
)


class TestOutputSaving(unittest.TestCase):
    def setUp(self):
        self.test_dir = OUTPUTS_DIR / "_test_saving"
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_save_output_audio_creates_file_in_outputs(self):
        sr = 24000
        dummy_audio = np.zeros(sr, dtype=np.float32)
        out_path_str = save_output_audio(dummy_audio, sr, prefix="test_voice", target_dir=self.test_dir)
        
        out_path = Path(out_path_str)
        self.assertTrue(out_path.exists(), "File must exist on disk")
        self.assertTrue(str(out_path).startswith(str(self.test_dir.resolve())), "File must be inside target outputs folder")
        self.assertTrue(out_path.name.startswith("test_voice_"), "File name must include prefix")
        self.assertTrue(out_path.name.endswith(".wav"), "File must have .wav extension")
        
        info = sf.info(out_path_str)
        self.assertEqual(info.samplerate, sr)
        self.assertAlmostEqual(info.duration, 1.0, places=2)

    def test_srt_write_audio_saves_to_outputs(self):
        sr = 24000
        dummy_audio = np.zeros(sr // 2, dtype=np.float32)
        out_path_str, note = write_audio(dummy_audio, sr, fmt="wav")
        
        out_path = Path(out_path_str)
        try:
            self.assertTrue(out_path.exists())
            self.assertTrue(str(out_path).startswith(str(SRT_OUTPUTS_DIR.resolve())), "SRT audio must be in outputs/")
            self.assertTrue(out_path.name.startswith("srt_"))
        finally:
            if out_path.exists():
                out_path.unlink()

    def test_batch_speech_cleans_intermediate_temp_and_saves_to_project(self):
        sr = 24000
        script = "[#Đoạn 1] Nội dung câu 1.\n[#Đoạn 2] Nội dung câu 2."
        proj_name = "test_cleanup_proj"
        proj_dir = PROJECTS_DIR / proj_name
        
        created_single_files = []

        def mock_synthesize_single(text, voice, *args, **kwargs):
            # Simulate synthesize_speech saving to outputs
            audio = np.zeros(sr, dtype=np.float32)
            path = save_output_audio(audio, sr, prefix="single_mock", target_dir=OUTPUTS_DIR)
            created_single_files.append(path)
            yield None, "⏳ Đang tạo..."
            yield path, "✅ Hoàn tất!"

        dummy_tts = type("DummyTTS", (), {})()
        try:
            gen = batch_to_speech(
                tts=dummy_tts,
                script_text=script,
                project_name=proj_name,
                voice_id="Trúc Ly",
                resume_mode=False,
                auto_merge=False,
                merge_format="wav",
                silence_gap=0.5,
                stop_requested=lambda: False,
                synthesize_single_fn=mock_synthesize_single,
                max_chars_chunk=250,
                temperature=0.8,
                denoise=False,
                use_batch=False,
                batch_size=1,
                session_id="test_session"
            )
            
            for _ in gen:
                pass

            # Check that files exist in project directory
            block1 = proj_dir / "test_cleanup_proj_01.wav"
            block2 = proj_dir / "test_cleanup_proj_02.wav"
            self.assertTrue(block1.exists(), "Block 1 must exist in project folder")
            self.assertTrue(block2.exists(), "Block 2 must exist in project folder")

            # Check that intermediate files created by synthesize_single were moved/cleaned up
            for f in created_single_files:
                self.assertFalse(os.path.exists(f), f"Intermediate single file {f} must have been moved/cleaned up")

        finally:
            if proj_dir.exists():
                shutil.rmtree(proj_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
