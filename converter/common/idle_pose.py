"""Extract one static Humanoid pose from a motion already solved by Unity."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def sample_baked_pose(baked_file: Path, clip_name: str, frame_index: int) -> dict[str, Any]:
    data = json.loads(baked_file.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != 8:
        raise ValueError(f"Unsupported baked motion schema: {baked_file}")
    clips = [clip for clip in data.get("clips", []) if clip.get("name") == clip_name]
    if len(clips) != 1:
        raise ValueError(f"{baked_file}: expected one clip named {clip_name}, got {len(clips)}")
    clip = clips[0]
    frames = int(clip["frames"])
    index = frame_index if frame_index >= 0 else frames + frame_index
    if frames <= 0 or not 0 <= index < frames:
        raise ValueError(f"{baked_file}: invalid pose frame {frame_index} for {clip_name}")
    tracks = []
    for track in clip["tracks"]:
        rotation = track.get("rotation", [])
        if len(rotation) != frames * 4:
            raise ValueError(f"{baked_file}: invalid rotation track for {track.get('bone')}")
        pose_track = {
            "bone": track["bone"],
            "rotation": rotation[index * 4:index * 4 + 4],
        }
        if track["bone"] == "Hips" and track.get("translation"):
            translation = track["translation"]
            if len(translation) != frames * 3:
                raise ValueError(f"{baked_file}: invalid Hips translation track")
            pose_track["translation"] = translation[index * 3:index * 3 + 3]
        tracks.append(pose_track)
    return {"tracks": tracks}
