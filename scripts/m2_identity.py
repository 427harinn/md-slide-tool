#!/usr/bin/env python3
"""Shared M2 identity and assets helpers for the QMD -> PPTX pipeline."""

import json
import os
import re
import tempfile
import uuid
from pathlib import Path
from typing import Any


ID_PATTERN = re.compile(r"^(slide|element)-([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12})$")


def new_id(kind: str) -> str:
    return f"{kind}-{uuid.uuid4()}"


def validate_id(value: str, kind: str) -> bool:
    match = ID_PATTERN.fullmatch(str(value))
    return bool(match and match.group(1) == kind)


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def load_assets(path: Path) -> dict:
    if not path.exists():
        return {"schemaVersion": 1, "slideSize": None, "elements": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[WARN] invalid assets file {path}: {exc}; starting with empty layout")
        return {"schemaVersion": 1, "slideSize": None, "elements": []}
    if not isinstance(data, dict) or data.get("schemaVersion") != 1 or not isinstance(data.get("elements"), list):
        print(f"[WARN] invalid assets schema in {path}; starting with empty layout")
        return {"schemaVersion": 1, "slideSize": None, "elements": []}
    return data


def valid_layout(entry: Any, slide_width: int, slide_height: int, image_count: int = 1) -> bool:
    if not isinstance(entry, dict):
        return False
    values = [entry.get(key) for key in ("x", "y", "width", "height")]
    if any(type(value) is not int for value in values):
        return False
    x, y, width, height = values
    if width <= 0 or height <= 0 or x < 0 or y < 0:
        return False
    if x + width <= slide_width and y + height <= slide_height:
        return True

    # The existing no-fit fallback puts pictures at this fixed x and stacks
    # them vertically using bounded image/caption/margin sizes.
    emu_per_inch = 914400
    offslide_x = slide_width + int(0.08 * emu_per_inch)
    max_width = int(2.5 * emu_per_inch)
    max_height = int(1.8 * emu_per_inch)
    max_stack_step = int((1.8 + 0.46 + 0.18) * emu_per_inch)
    count = max(1, image_count)
    max_y = slide_height + (count - 1) * max_stack_step
    max_bottom = slide_height + count * max_stack_step
    return (
        x == offslide_x and width <= max_width and height <= max_height and
        y <= max_y and y + height <= max_bottom
    )


def atomic_write_json(path: Path, data: dict) -> None:
    atomic_write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
