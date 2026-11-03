"""Persistent content-addressed GPU texture preprocessing."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

TEXTURE_ROOT = Path(__file__).resolve().parents[2] / "compressed_texture"
QUALITY = 3
IDENTIFIER = b"\xabKTX 20\xbb\r\n\x1a\n"


def encoding_options(color_space: str, mip_count: int) -> list[str]:
    options = ["--t2", "--encode", "uastc", "--uastc_quality", str(QUALITY), "--zcmp", "6",
               "--target_type", "RGBA", "--assign_oetf", color_space,
               "--assign_primaries", "bt709", "--upper_left_maps_to_s0t0"]
    if mip_count > 1:
        options += ["--genmipmap", "--filter", "box"]
    return options


def texture_key(png: bytes, *, width: int, height: int, color_space: str, mip_count: int) -> str:
    settings = [width, height, encoding_options(color_space, mip_count)]
    return hashlib.sha256(png + json.dumps(settings, separators=(",", ":")).encode()).hexdigest()


def validate_ktx2(data: bytes, *, width: int, height: int, mip_count: int) -> bytes:
    if len(data) < 80 or data[:12] != IDENTIFIER:
        raise RuntimeError("压缩纹理不是有效的 KTX2 文件")
    if struct.unpack_from("<II", data, 20) != (width, height) or struct.unpack_from("<I", data, 40)[0] != mip_count:
        raise RuntimeError("压缩纹理尺寸或 mip 层数与输入不一致")
    # The level index points into the container, never beyond a partial write.
    if len(data) < 80 + 24 * mip_count:
        raise RuntimeError("压缩纹理的 mip 索引不完整")
    for level in range(mip_count):
        offset, size, _ = struct.unpack_from("<QQQ", data, 80 + level * 24)
        if size == 0 or offset < 80 + mip_count * 24 or offset + size > len(data):
            raise RuntimeError("压缩纹理的 mip 数据不完整")
    return data


def read_compressed_texture(png: bytes, *, width: int, height: int, color_space: str,
                            mip_count: int, root: Path | None = None) -> bytes | None:
    target = (TEXTURE_ROOT if root is None else root) / (texture_key(png, width=width, height=height,
              color_space=color_space, mip_count=mip_count) + ".ktx2")
    try:
        data = target.read_bytes()
    except FileNotFoundError:
        return None
    try:
        return validate_ktx2(data, width=width, height=height, mip_count=mip_count)
    except RuntimeError as exc:
        raise RuntimeError(f"{target}: {exc}") from exc


class EncoderUnavailableError(RuntimeError):
    pass


def encoder_path() -> str:
    executable = os.environ.get("TOKTX") or shutil.which("toktx")
    if not executable or not Path(executable).is_file():
        raise EncoderUnavailableError("纹理压缩需要 KTX-Software 的 toktx，请加入 PATH 或设置 TOKTX。")
    return str(Path(executable).resolve())


def encode_uastc(png: bytes, *, width: int, height: int, color_space: str,
                 mip_count: int, threads: int = 1, executable: str | None = None,
                 cancel_event=None) -> bytes:
    env = dict(os.environ)
    env.pop("TOKTX_OPTIONS", None)
    command = [executable or encoder_path(), *encoding_options(color_space, mip_count),
               "--threads", str(threads), "-", "-"]
    if cancel_event is None:
        run = subprocess.run(command, input=png, capture_output=True, env=env)
    else:
        from types import SimpleNamespace
        if cancel_event.is_set():
            raise RuntimeError("纹理压缩已取消")
        with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, env=env) as process:
            first = True
            while True:
                try:
                    stdout, stderr = process.communicate(input=png if first else None, timeout=1)
                    break
                except subprocess.TimeoutExpired:
                    first = False
                    if cancel_event.is_set():
                        process.terminate()
                        try:
                            process.communicate(timeout=2)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.communicate()
                        raise RuntimeError("纹理压缩已取消")
            run = SimpleNamespace(returncode=process.returncode, stdout=stdout, stderr=stderr)
    if run.returncode:
        raise RuntimeError("UASTC 纹理压缩失败：" + run.stderr.decode("utf-8", errors="replace"))
    return validate_ktx2(run.stdout, width=width, height=height, mip_count=mip_count)


def write_compressed_texture(target: Path, data: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".encoding-", suffix=".tmp", dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
