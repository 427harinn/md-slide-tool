#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image
from pptx import Presentation
from pptx.util import Inches

def get_slide_title(slide) -> str:
    for shape in slide.shapes:
        if not getattr(shape, "has_text_frame", False):
            continue

        text = shape.text.strip()
        if text:
            return text

    return ""


def load_images_json(json_path: Path) -> List[dict]:
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("images json は配列形式である必要があります")

    return data


def find_body_text_shape(slide, slide_height: int):
    """
    まず本文プレースホルダを優先して返す。
    見つからない場合のみ、通常の text shape から本文っぽいものを推定する。
    戻り値: (shape, left, top, width, height) or None
    """
    placeholder_candidates = []
    fallback_candidates = []

    for shape in slide.shapes:
        if not getattr(shape, "has_text_frame", False):
            continue

        width = int(shape.width)
        height = int(shape.height)
        left = int(shape.left)
        top = int(shape.top)
        area = width * height
        text = shape.text.strip() if shape.text else ""

        # --- 1. プレースホルダ優先 ---
        if getattr(shape, "is_placeholder", False):
            try:
                phf = shape.placeholder_format
                ph_type = int(phf.type)
            except Exception:
                ph_type = None

            # 本文系 placeholder を最優先
            # BODY=2, OBJECT=7 あたりを優先候補にする
            if ph_type in (2, 7):
                score = area

                # 上の方にあっても本文placeholderならそこまで減点しない
                if top < slide_height * 0.18:
                    score *= 0.9

                placeholder_candidates.append((score, shape, left, top, width, height, text))
                continue

        # --- 2. fallback: 通常の推定 ---
        score = area

        # タイトルっぽい位置は大きく減点
        if top < slide_height * 0.22:
            score *= 0.35

        # 横幅が狭いものも減点
        if width < int(Inches(2.5)):
            score *= 0.6

        fallback_candidates.append((score, shape, left, top, width, height, text))

    if placeholder_candidates:
        placeholder_candidates.sort(key=lambda x: x[0], reverse=True)
        _, shape, left, top, width, height, _ = placeholder_candidates[0]
        return shape, left, top, width, height

    if fallback_candidates:
        fallback_candidates.sort(key=lambda x: x[0], reverse=True)
        _, shape, left, top, width, height, _ = fallback_candidates[0]
        return shape, left, top, width, height

    return None


def get_image_size_emu(image_path: Path) -> Tuple[int, int]:
    with Image.open(image_path) as img:
        width_px, height_px = img.size
        dpi = img.info.get("dpi", (96, 96))
        dpi_x = dpi[0] if dpi and dpi[0] else 96
        dpi_y = dpi[1] if dpi and dpi[1] else 96

        width_in = width_px / dpi_x
        height_in = height_px / dpi_y

        return int(Inches(width_in)), int(Inches(height_in))


def fit_size(orig_w: int, orig_h: int, max_w: int, max_h: int) -> Tuple[int, int]:
    if orig_w <= 0 or orig_h <= 0:
        return max_w, max_h

    scale = min(max_w / orig_w, max_h / orig_h)
    scale = min(scale, 1.0)

    return max(1, int(orig_w * scale)), max(1, int(orig_h * scale))


def classify_density_by_slide(slide) -> str:
    bullet_lines = 0
    char_count = 0
    paragraph_count = 0

    for shape in slide.shapes:
        if not getattr(shape, "has_text_frame", False):
            continue

        text = shape.text.strip() if shape.text else ""
        if not text:
            continue

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        paragraph_count += len(lines)
        char_count += len("".join(lines))

        for line in lines:
            if line.startswith(("•", "-", "*")):
                bullet_lines += 1

    score = bullet_lines * 18 + char_count + paragraph_count * 10

    if score < 140:
        return "low"
    if score < 260:
        return "medium"
    return "high"


def try_shrink_body_shape_for_right_images(
    slide_w: int,
    body_shape,
    body_left: int,
    body_top: int,
    body_width: int,
    body_height: int,
    desired_image_col_width: int,
    margin: int,
    outer_margin: int,
) -> Tuple[int, int, int, int]:
    """
    本文プレースホルダを必要に応じて縮め、右画像用の幅を確保する。
    ただし本文の座標(left/top)は維持し、幅だけ変更する。
    """
    if body_shape is None:
        return body_left, body_top, body_width, body_height

    min_image_col_width = int(Inches(1.6))
    required_image_col_width = max(desired_image_col_width, min_image_col_width)

    # 本文は最低限これくらい残したい
    min_body_width = max(int(slide_w * 0.50), int(Inches(3.2)))

    max_body_width_for_layout = slide_w - outer_margin - margin - required_image_col_width - body_left

    if max_body_width_for_layout < min_body_width:
        return body_left, body_top, body_width, body_height

    current_right_space = slide_w - (body_left + body_width) - outer_margin
    if current_right_space >= required_image_col_width:
        return body_left, body_top, body_width, body_height

    new_body_width = max_body_width_for_layout

    if new_body_width >= body_width:
        return body_left, body_top, body_width, body_height

    print(f"  shrink body width only: {body_width} -> {new_body_width}")

    # 元の位置と高さを必ず保持
    original_left = int(body_shape.left)
    original_top = int(body_shape.top)
    original_height = int(body_shape.height)

    # いったん幅変更
    body_shape.width = new_body_width

    # その後、座標を明示的に戻す
    body_shape.left = original_left
    body_shape.top = original_top
    body_shape.height = original_height

    return (
        int(body_shape.left),
        int(body_shape.top),
        int(body_shape.width),
        int(body_shape.height),
    )


def add_offslide_images_near_target_slide(
    slide,
    images: List[dict],
    anchor_top: int,
    slide_w: int,
    margin: int,
):
    """
    そのスライドのすぐ右外に退避する。
    遠くに飛ばしすぎないよう、右端の少し外にだけ置く。
    """
    x = slide_w + int(Inches(0.08))
    y = anchor_top
    max_w = int(Inches(2.5))
    max_h = int(Inches(1.8))

    for image in images:
        orig_w, orig_h = get_image_size_emu(image["resolved_path"])
        pic_w, pic_h = fit_size(orig_w, orig_h, max_w, max_h)
        slide.shapes.add_picture(
            str(image["resolved_path"]),
            x,
            y,
            width=pic_w,
            height=pic_h,
        )
        y += pic_h + margin


def add_images_to_slide(prs: Presentation, slide, slide_info: dict, base_dir: Path) -> None:
    images = slide_info.get("images", [])
    right_images = []

    for image in images:
        place = str(image.get("place", "right")).strip().lower()
        if place != "right":
            continue

        raw_path = str(image.get("path", "")).strip()
        resolved_path = (base_dir / raw_path).resolve()

        if resolved_path.exists():
            right_images.append(
                {
                    "raw_path": raw_path,
                    "resolved_path": resolved_path,
                }
            )
        else:
            print(f"  missing image: {raw_path}")

    if not right_images:
        return

    slide_w = int(prs.slide_width)
    slide_h = int(prs.slide_height)
    density = classify_density_by_slide(slide)

    margin = int(Inches(0.25))
    outer_margin = int(Inches(0.35))
    gap = int(Inches(0.15))

    body_info = find_body_text_shape(slide, slide_h)

    if body_info:
        body_shape, body_left, body_top, body_width, body_height = body_info
    else:
        body_shape = None
        body_left = int(Inches(0.8))
        body_top = int(Inches(1.5))
        body_width = int(slide_w * 0.65)
        body_height = int(slide_h * 0.68)

    if density == "low":
        image_col_ratio = 0.35
    elif density == "medium":
        image_col_ratio = 0.28
    else:
        image_col_ratio = 0.22

    desired_col_width = int(slide_w * image_col_ratio)

    # まず本文プレースホルダ縮小を試みる
    body_left, body_top, body_width, body_height = try_shrink_body_shape_for_right_images(
        slide_w=slide_w,
        body_shape=body_shape,
        body_left=body_left,
        body_top=body_top,
        body_width=body_width,
        body_height=body_height,
        desired_image_col_width=desired_col_width,
        margin=margin,
        outer_margin=outer_margin,
    )

    available_right_space = slide_w - (body_left + body_width) - outer_margin
    image_col_width = min(desired_col_width, available_right_space)

    # 画像列の最低幅
    min_usable_col_width = int(Inches(1.5))

    # 画像が多いときは必要高さも見たい
    count = len(right_images)
    total_gap = gap * max(count - 1, 0)
    image_col_height = body_height
    slot_h = max(int(Inches(0.95)), (image_col_height - total_gap) // max(count, 1))

    # 幅が足りない場合は退避
    if image_col_width < min_usable_col_width:
        print("  fallback: off-slide (not enough width after shrink)")
        add_offslide_images_near_target_slide(
            slide=slide,
            images=right_images,
            anchor_top=body_top,
            slide_w=slide_w,
            margin=margin,
        )
        return

    # 画像が多すぎて1枚あたり高さが厳しすぎる場合も退避
    if slot_h < int(Inches(0.75)):
        print("  fallback: off-slide (not enough height)")
        add_offslide_images_near_target_slide(
            slide=slide,
            images=right_images,
            anchor_top=body_top,
            slide_w=slide_w,
            margin=margin,
        )
        return

    image_x = body_left + body_width + margin
    image_y = body_top

    for image in right_images:
        orig_w, orig_h = get_image_size_emu(image["resolved_path"])
        pic_w, pic_h = fit_size(orig_w, orig_h, image_col_width, slot_h)

        centered_x = image_x + max(0, (image_col_width - pic_w) // 2)
        centered_y = image_y + max(0, (slot_h - pic_h) // 2)

        slide.shapes.add_picture(
            str(image["resolved_path"]),
            centered_x,
            centered_y,
            width=pic_w,
            height=pic_h,
        )

        image_y += slot_h + gap


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pptx", required=True, help="後処理対象のPPTXファイル")
    parser.add_argument("--images-json", required=True, help="画像情報JSON")
    args = parser.parse_args()

    pptx_path = Path(args.pptx).resolve()
    images_json_path = Path(args.images_json).resolve()

    if not pptx_path.exists():
        raise FileNotFoundError(f"PPTXが見つかりません: {pptx_path}")

    if not images_json_path.exists():
        raise FileNotFoundError(f"images json が見つかりません: {images_json_path}")

    slide_infos = load_images_json(images_json_path)
    prs = Presentation(str(pptx_path))

    target_count = min(len(slide_infos), len(prs.slides))

    print(f"PPTX slide count : {len(prs.slides)}")
    print(f"JSON slide count : {len(slide_infos)}")
    print(f"Process count    : {target_count}")

    base_dir = images_json_path.parent

    for i, slide_info in enumerate(slide_infos):
        target_title = slide_info.get("title", "").strip()

        matched_slide = None

        for slide in prs.slides:
            ppt_title = get_slide_title(slide)

            if ppt_title.strip() == target_title:
                matched_slide = slide
                break

        if not matched_slide:
            print(f"[WARN] slide not found: {target_title}")
            continue

        print(
            f"[match] slide {i + 1}: "
            f"title='{target_title}' "
            f"density={classify_density_by_slide(matched_slide)} "
            f"images={len(slide_info.get('images', []))}"
        )

        add_images_to_slide(prs, matched_slide, slide_info, base_dir)

    prs.save(str(pptx_path))
    print(f"saved: {pptx_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())