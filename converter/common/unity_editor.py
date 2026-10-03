"""Locate the Unity Editor without executing similarly named CLI programs."""

import json
import os
from pathlib import Path


def _is_editor(path: Path) -> bool:
    path = path.resolve()
    return path.is_file() and (
        (path.parent / 'Data/Managed/UnityEditor.dll').is_file()
        or (path.parent.name == 'MacOS'
            and (path.parent.parent / 'Managed/UnityEditor.dll').is_file())
    )


def _hub_editors():
    appdata = os.environ.get('APPDATA')
    if not appdata:
        return
    try:
        manifest = json.loads((Path(appdata) / 'UnityHub/editors-v2.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return
    entries = manifest.get('data', []) if isinstance(manifest, dict) else []
    if not isinstance(entries, list):
        return
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        locations = entry.get('location', [])
        if isinstance(locations, list):
            for location in locations:
                if isinstance(location, str) and location:
                    yield Path(location)


def default_unity_editor() -> Path | None:
    configured = os.environ.get('UNITY_EDITOR')
    if configured:
        return Path(configured)
    # Inspect every PATH entry: a CLI named unity.exe may precede the Editor.
    for directory in os.get_exec_path():
        for name in ('Unity.exe', 'Unity'):
            candidate = Path(directory) / name
            if _is_editor(candidate):
                return candidate
    for candidate in _hub_editors():
        if _is_editor(candidate):
            return candidate
    return None


def resolve_unity_editor(explicit: Path | None = None) -> Path:
    candidate = explicit if explicit is not None else default_unity_editor()
    if candidate is None:
        raise SystemExit('Unity Editor not found. Set UNITY_EDITOR or pass --unity to the Editor executable.')
    candidate = candidate.expanduser().resolve()
    if not candidate.is_file():
        raise SystemExit(f'Unity Editor not found: {candidate}. Set UNITY_EDITOR or pass --unity.')
    if not _is_editor(candidate):
        raise SystemExit(f'Not a Unity Editor installation: {candidate}. '
                         'Set UNITY_EDITOR or pass --unity to the Editor executable.')
    print(f'[unity] Editor: {candidate}', flush=True)
    return candidate
