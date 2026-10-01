"""Choose an Editor executable without a machine-specific installation path."""

import os
import shutil
from pathlib import Path


def default_unity_editor() -> Path:
    return Path(os.environ.get('UNITY_EDITOR') or shutil.which('Unity')
                or shutil.which('Unity.exe') or 'Unity.exe')
