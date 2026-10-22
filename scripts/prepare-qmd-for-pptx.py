#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m2_identity import atomic_write_text, new_id, validate_id


HEADING_PATTERN = re.compile(r'^\s*##\s+(.+?)\s*$')
IMAGE_ONLY_LINE_PATTERN = re.compile(
    r'^\s*!\[(?P<alt>[^\]]*)\]\((?P<path>[^)]+)\)\s*(?:\{(?P<attrs>[^}]*)\})?\s*$'
)
FENCE_PATTERN = re.compile(r"^\s*(`{3,}|~{3,})")


@dataclass
class ImageSpec:
    path: str
    element_id: str
    caption: str = ""
    place: str = ""


@dataclass
class SlideSpec:
    slide_index: int
    title: str
    slide_id: str
    images: List[ImageSpec] = field(default_factory=list)


def parse_attrs(attr_text: Optional[str]) -> dict:
    attrs = {}
    if not attr_text:
        return attrs

    for token in attr_text.split():
        token = token.strip()
        if not token:
            continue
        if "=" in token:
            key, value = token.split("=", 1)
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            attrs[key.strip()] = value

    return attrs


def set_attr(line: str, key: str, value: str) -> str:
    ending = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
    body = line[:-len(ending)] if ending else line
    match = re.search(r"\s*\{([^{}]*)\}\s*$", body)
    if match:
        prefix = body[:match.start()]
        separator = re.match(r"\s*", match.group(0)).group(0)
        attrs = match.group(1).strip()
        body = prefix.rstrip()
        attrs = f'{attrs} {key}="{value}"'.strip()
    else:
        separator = " "
        attrs = f'{key}="{value}"'
    return f"{body}{separator}{{{attrs}}}{ending}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="元のQMDファイル")
    parser.add_argument("--output", required=True, help="画像行を除いたレンダリング用QMD")
    parser.add_argument("--images-json", required=True, help="画像情報を書き出すJSON")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    images_json_path = Path(args.images_json).resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"入力QMDが見つかりません: {input_path}")

    with input_path.open("r", encoding="utf-8", newline="") as source_file:
        text = source_file.read()
    lines = text.splitlines(keepends=True)

    output_lines: List[str] = []
    source_lines: List[str] = []
    slides: List[SlideSpec] = []

    current_slide: Optional[SlideSpec] = None
    in_front_matter = False
    slide_ids = set()
    element_ids = set()
    in_fence = False
    fence_token = ""

    # Validate IDs already present before generating any replacements.
    for i, line in enumerate(lines):
        stripped = line.strip()
        if i == 0 and stripped == "---":
            in_front_matter = True
            continue
        if in_front_matter:
            if stripped == "---":
                in_front_matter = False
            continue
        fence_match = FENCE_PATTERN.match(line)
        if in_fence:
            if fence_match and fence_match.group(1)[0] == fence_token[0] and len(fence_match.group(1)) >= len(fence_token):
                in_fence = False
                fence_token = ""
            continue
        if fence_match:
            in_fence = True
            fence_token = fence_match.group(1)
            continue
        heading_match = HEADING_PATTERN.match(line)
        if heading_match:
            attrs_match = re.search(r"\{([^{}]*)\}\s*$", heading_match.group(1))
            attrs = parse_attrs(attrs_match.group(1) if attrs_match else None)
            sid = attrs.get("slide-id")
            if sid:
                if not validate_id(sid, "slide"):
                    raise ValueError(f"invalid slide-id: {sid}")
                if sid in slide_ids:
                    raise ValueError(f"duplicate slide-id: {sid}")
                slide_ids.add(sid)
        image_match = IMAGE_ONLY_LINE_PATTERN.match(line)
        if image_match:
            eid = parse_attrs(image_match.group("attrs")).get("element-id")
            if eid:
                if not validate_id(eid, "element"):
                    raise ValueError(f"invalid element-id: {eid}")
                if eid in element_ids:
                    raise ValueError(f"duplicate element-id: {eid}")
                element_ids.add(eid)

    in_front_matter = False
    in_fence = False
    fence_token = ""
    for i, line in enumerate(lines):
        stripped = line.strip()

        if i == 0 and stripped == "---":
            in_front_matter = True
            output_lines.append(line)
            source_lines.append(line)
            continue

        if in_front_matter:
            output_lines.append(line)
            source_lines.append(line)
            if stripped == "---":
                in_front_matter = False
            continue

        fence_match = FENCE_PATTERN.match(line)
        if in_fence:
            output_lines.append(line)
            source_lines.append(line)
            if fence_match and fence_match.group(1)[0] == fence_token[0] and len(fence_match.group(1)) >= len(fence_token):
                in_fence = False
                fence_token = ""
            continue
        if fence_match:
            in_fence = True
            fence_token = fence_match.group(1)
            output_lines.append(line)
            source_lines.append(line)
            continue

        heading_match = HEADING_PATTERN.match(line)
        if heading_match:
            raw_heading = heading_match.group(1).strip()
            attrs_match = re.search(r"\s+\{([^{}]*)\}\s*$", raw_heading)
            attrs = parse_attrs(attrs_match.group(1) if attrs_match else None)
            title = raw_heading[:attrs_match.start()].strip() if attrs_match else raw_heading
            slide_id = attrs.get("slide-id") or new_id("slide")
            if not attrs.get("slide-id"):
                line = set_attr(line, "slide-id", slide_id)
            current_slide = SlideSpec(
                slide_index=len(slides),
                title=title,
                slide_id=slide_id,
            )
            slides.append(current_slide)
            output_lines.append(line)
            source_lines.append(line)
            continue

        image_match = IMAGE_ONLY_LINE_PATTERN.match(line)
        if image_match and current_slide is not None:
            attrs = parse_attrs(image_match.group("attrs"))
            place = attrs.get("place", "").strip().lower()
            caption = image_match.group("alt").strip()
            element_id = attrs.get("element-id") or new_id("element")
            if not attrs.get("element-id"):
                line = set_attr(line, "element-id", element_id)
            source_lines.append(line)

            current_slide.images.append(
                ImageSpec(
                    path=image_match.group("path").strip(),
                    element_id=element_id,
                    caption=caption,
                    place=place,
                )
            )

            # 画像行は render 用 QMD には書かない
            continue

        output_lines.append(line)
        source_lines.append(line)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    images_json_path.parent.mkdir(parents=True, exist_ok=True)

    # Persist only identity attribute additions; all source text is otherwise retained.
    updated_source = "".join(source_lines)
    if updated_source != text:
        atomic_write_text(input_path, updated_source)
    atomic_write_text(output_path, "".join(output_lines))

    json_data = [
        {
            "slide_index": slide.slide_index,
            "title": slide.title,
            "slide_id": slide.slide_id,
            "images": [asdict(image) for image in slide.images],
        }
        for slide in slides
    ]

    atomic_write_text(images_json_path, json.dumps(json_data, ensure_ascii=False, indent=2) + "\n")

    print(f"input qmd   : {input_path}")
    print(f"output qmd  : {output_path}")
    print(f"images json : {images_json_path}")
    print(f"slide count : {len(slides)}")

    for slide in slides:
        print(
            f"[slide {slide.slide_index + 1}] "
            f"title='{slide.title}' images={len(slide.images)}"
        )
        for image in slide.images:
            print(
                f"  - path={image.path}, "
                f"caption={image.caption!r}, "
                f"place={image.place or '(auto)'}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
