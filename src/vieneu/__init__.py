import os
from pathlib import Path

# Đảm bảo mặc định HF_HOME trỏ về thư mục models_cache trong dự án (Portable 100%)
if "HF_HOME" not in os.environ:
    _project_root = Path(__file__).resolve().parent.parent.parent
    _default_hf_home = _project_root / "models_cache"
    os.environ["HF_HOME"] = str(_default_hf_home)

from .factory import Vieneu

__all__ = ["Vieneu"]

