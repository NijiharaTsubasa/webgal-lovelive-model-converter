"""Consistent UTF-8 console output, including redirected Windows build logs."""

import sys


def configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
