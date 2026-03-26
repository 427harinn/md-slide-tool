#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional


HEADING_PATTERN = re.compile(r'^\s*##\s+(.+?)\s*$')
IMAGE_ONLY_LINE_PATTERN = re.compile(
    r'^\s*!\[[^\]]*\]\((?P<path>[^)]+)\)\s*(?:\{(?P<attrs>[^}]*)\})?\s*$'
)


@dataclass
class ImageSpec:
    path: str
    place: str = "right"


@dataclass
class SlideSpec:
    slide_index: int
    title: str
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
            attrs[key.strip()] = value.strip()

    return attrs


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

    text = input_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    output_lines: List[str] = []
    slides: List[SlideSpec] = []

    current_slide: Optional[SlideSpec] = None
    in_front_matter = False
    front_matter_done = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # YAML front matter の開始
        if i == 0 and stripped == "---":
            in_front_matter = True
            output_lines.append(line)
            continue

        # YAML front matter の終了
        if in_front_matter:
            output_lines.append(line)
            if stripped == "---":
                in_front_matter = False
                front_matter_done = True
            continue

        heading_match = HEADING_PATTERN.match(line)
        if heading_match:
            current_slide = SlideSpec(
                slide_index=len(slides),
                title=heading_match.group(1).strip()
            )
            slides.append(current_slide)
            output_lines.append(line)
            continue

        image_match = IMAGE_ONLY_LINE_PATTERN.match(line)
        if image_match and current_slide is not None:
            attrs = parse_attrs(image_match.group("attrs"))
            place = attrs.get("place", "right").strip().lower()

            current_slide.images.append(
                ImageSpec(
                    path=image_match.group("path").strip(),
                    place=place
                )
            )

            # 画像行は render 用 QMD には書かない
            continue

        output_lines.append(line)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    images_json_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text("".join(output_lines), encoding="utf-8")

    json_data = [
        {
            "slide_index": slide.slide_index,
            "title": slide.title,
            "images": [asdict(image) for image in slide.images],
        }
        for slide in slides
    ]

    images_json_path.write_text(
        json.dumps(json_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

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
            print(f"  - path={image.path}, place={image.place}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())