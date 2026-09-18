import os
import shutil
import unittest
from pathlib import Path
import numpy as np

from apps import user_voices as uv
from apps.user_voices import (
    voices_home,
    save_user_voice,
    delete_user_voice,
    find_voice_preview,
    PROJECT_ROOT,
)


class _FakeTurbo:
    default_style = "tu_nhien"

    def __init__(self):
        self._preset_voices = {
            "Minh Quân": {"description": "nam", "speaker_emb": np.ones(192, np.float32), "codes": np.zeros(10, np.int64)}
        }
        self._default_voice = "Minh Quân"

    def add_voice(self, name, ref_audio, *, denoise=True, description="", **kw):
        self._preset_voices[name] = {
            "description": description,
            "gender": "",
            "style": self.default_style,
            "speaker_emb": np.full(192, 0.5, np.float32),
            "codes": np.arange(6, dtype=np.int64),
        }
        return name

    def remove_voice(self, name, save=False):
        self._preset_voices.pop(name, None)

    def list_preset_voices(self):
        return [(n, n) for n in self._preset_voices]


class TestVoicePreviewAndStorage(unittest.TestCase):
    def setUp(self):
        self.test_custom_dir = PROJECT_ROOT / "custom_voices_test_tmp"
        self.test_custom_dir.mkdir(parents=True, exist_ok=True)
        os.environ["VIENEU_HOME"] = str(self.test_custom_dir)

    def tearDown(self):
        if "VIENEU_HOME" in os.environ:
            del os.environ["VIENEU_HOME"]
        if self.test_custom_dir.exists():
            shutil.rmtree(self.test_custom_dir, ignore_errors=True)

    def test_default_voices_home_in_project(self):
        del os.environ["VIENEU_HOME"]
        home = voices_home()
        self.assertEqual(home, PROJECT_ROOT / "custom_voices")
        self.assertTrue(home.exists())

    def test_save_and_find_voice_preview(self):
        tts = _FakeTurbo()
        dummy_wav = self.test_custom_dir / "sample_input.wav"
        dummy_wav.write_bytes(b"RIFF dummy audio content")

        # Save user voice
        save_user_voice(tts, "Bảo Nam", str(dummy_wav), description="Giọng mẫu test")
        
        # Verify preview file created in custom voices folder
        expected_preview = self.test_custom_dir / "preview_Bảo Nam.wav"
        self.assertTrue(expected_preview.exists(), "preview_Bảo Nam.wav should be saved in custom voices folder")

        # Verify find_voice_preview finds it
        found = find_voice_preview("Bảo Nam", tts=tts)
        self.assertIsNotNone(found)
        self.assertEqual(Path(found).resolve(), expected_preview.resolve())

        # Test finding built-in samples in assets/samples
        found_builtin = find_voice_preview("Bình", tts=tts)
        if (PROJECT_ROOT / "src" / "vieneu" / "assets" / "samples" / "Bình (nam miền Bắc).wav").exists():
            self.assertIsNotNone(found_builtin)
            self.assertTrue("Bình" in Path(found_builtin).name)

        # Test deleting user voice cleans up preview
        delete_user_voice(tts, "Bảo Nam")
        self.assertFalse(expected_preview.exists(), "Preview file should be deleted on voice deletion")
        self.assertIsNone(find_voice_preview("Bảo Nam", tts=tts))

    def test_nonexistent_preview_returns_none(self):
        found = find_voice_preview("NonExistentVoice_123456789")
        self.assertIsNone(found)


if __name__ == "__main__":
    unittest.main()
