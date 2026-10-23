#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import sys
import unicodedata
from pathlib import Path
from typing import List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m2_identity import atomic_write_json, load_assets, valid_layout
from m3_core import new_document_id, qmd_body_sha256, read_custom_properties, write_custom_properties, valid_document_id

from PIL import Image
from pptx import Presentation
from pptx.enum.text import PP_ALIGN, MSO_AUTO_SIZE
from pptx.util import Inches, Pt


VALID_PLACES = {"right", "bottom", "bottom_right"}


# ----------------------------
# 基本ユーティリティ
# ----------------------------

def normalize_text(text: str) -> str:
    return unicodedata.normalize("NFKC", (text or "").strip())


def load_images_json(json_path: Path) -> List[dict]:
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("images json は配列形式である必要があります")

    return data


def emu(value_inch: float) -> int:
    return int(Inches(value_inch))


def rect_right(rect: Tuple[int, int, int, int]) -> int:
    return rect[0] + rect[2]


def rect_bottom(rect: Tuple[int, int, int, int]) -> int:
    return rect[1] + rect[3]


def rect_intersects(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int]) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return not (
        ax + aw <= bx or
        bx + bw <= ax or
        ay + ah <= by or
        by + bh <= ay
    )


# ----------------------------
# title / body 判定
# ----------------------------

def get_slide_title(slide) -> str:
    placeholder_candidates = []
    fallback_candidates = []

    for shape in slide.shapes:
        if not getattr(shape, "has_text_frame", False):
            continue

        text = normalize_text(shape.text if shape.text else "")
        if not text:
            continue

        top = int(shape.top)
        width = int(shape.width)

        if getattr(shape, "is_placeholder", False):
            try:
                ph_type = int(shape.placeholder_format.type)
            except Exception:
                ph_type = None

            if ph_type in (1, 3):
                score = (1000000000 - top) + width
                placeholder_candidates.append((score, text))
                continue

        score = (1000000000 - top) + width
        fallback_candidates.append((score, text))

    if placeholder_candidates:
        placeholder_candidates.sort(reverse=True)
        return placeholder_candidates[0][1]

    if fallback_candidates:
        fallback_candidates.sort(reverse=True)
        return fallback_candidates[0][1]

    return ""


def find_title_shape(slide):
    placeholder_candidates = []
    fallback_candidates = []

    for shape in slide.shapes:
        if not getattr(shape, "has_text_frame", False):
            continue

        text = normalize_text(shape.text if shape.text else "")
        if not text:
            continue

        top = int(shape.top)
        width = int(shape.width)

        if getattr(shape, "is_placeholder", False):
            try:
                ph_type = int(shape.placeholder_format.type)
            except Exception:
                ph_type = None

            if ph_type in (1, 3):
                score = (1000000000 - top) + width
                placeholder_candidates.append((score, shape))
                continue

        score = (1000000000 - top) + width
        fallback_candidates.append((score, shape))

    if placeholder_candidates:
        placeholder_candidates.sort(reverse=True)
        return placeholder_candidates[0][1]

    if fallback_candidates:
        fallback_candidates.sort(reverse=True)
        return fallback_candidates[0][1]

    return None


def find_body_shape(slide, slide_h: int):
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
        text = normalize_text(shape.text if shape.text else "")

        if getattr(shape, "is_placeholder", False):
            try:
                ph_type = int(shape.placeholder_format.type)
            except Exception:
                ph_type = None

            if ph_type in (2, 7):
                score = area
                if top < slide_h * 0.18:
                    score *= 0.9
                placeholder_candidates.append((score, shape, left, top, width, height, text))
                continue

        score = area
        if top < slide_h * 0.22:
            score *= 0.35
        if width < emu(2.5):
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


# ----------------------------
# 画像サイズ
# ----------------------------

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


# ----------------------------
# テキスト使用範囲の近似
# ----------------------------

def extract_font_size_pt(shape) -> float:
    sizes = []

    try:
        text_frame = shape.text_frame
    except Exception:
        return 20.0

    for para in text_frame.paragraphs:
        for run in para.runs:
            if run.font and run.font.size:
                try:
                    sizes.append(float(run.font.size.pt))
                except Exception:
                    pass

        if para.font and para.font.size:
            try:
                sizes.append(float(para.font.size.pt))
            except Exception:
                pass

    if sizes:
        return max(10.0, sum(sizes) / len(sizes))

    return 20.0


def count_visual_width_units(text: str) -> float:
    units = 0.0
    for ch in text:
        if ch.isspace():
            units += 0.35
            continue

        east = unicodedata.east_asian_width(ch)
        if east in ("F", "W", "A"):
            units += 1.0
        else:
            units += 0.55

    return units


def estimate_text_content_bounds(shape) -> Tuple[int, int, int, int]:
    left = int(shape.left)
    top = int(shape.top)
    width = int(shape.width)
    height = int(shape.height)
    text = shape.text if shape.text else ""

    lines = []
    for raw in text.splitlines():
        s = raw.strip()
        if s:
            lines.append(s)

    if not lines:
        return left, top, min(width, emu(2.0)), min(height, emu(0.8))

    font_size_pt = extract_font_size_pt(shape)
    font_size_emu = font_size_pt * 12700.0

    max_units = max(count_visual_width_units(line) for line in lines)
    line_count = len(lines)

    estimated_text_w = int(max_units * font_size_emu * 0.95 + emu(0.5))
    estimated_text_h = int(line_count * font_size_emu * 1.65 + emu(0.25))

    estimated_text_w = min(max(estimated_text_w, emu(2.0)), width)
    estimated_text_h = min(max(estimated_text_h, emu(1.0)), height)

    return left, top, estimated_text_w, estimated_text_h


def get_occupied_rects(slide, slide_w: int, slide_h: int) -> List[Tuple[int, int, int, int]]:
    rects = []

    title_shape = find_title_shape(slide)
    if title_shape is not None:
        rects.append((
            int(title_shape.left),
            int(title_shape.top),
            int(title_shape.width),
            int(title_shape.height),
        ))

    body_info = find_body_shape(slide, slide_h)
    if body_info:
        body_shape, _, _, _, _ = body_info
        rects.append(estimate_text_content_bounds(body_shape))

    return rects


# ----------------------------
# caption
# ----------------------------

def estimate_caption_box_height(caption: str) -> int:
    if not caption:
        return 0

    length = len(caption.strip())
    if length <= 12:
        return emu(0.22)
    if length <= 28:
        return emu(0.34)
    return emu(0.46)


def add_caption_textbox(slide, caption: str, element_id: str, x: int, y: int, w: int, h: int) -> None:
    if not caption.strip():
        return

    textbox = slide.shapes.add_textbox(x, y, w, h)
    textbox.name = f"mdst-caption-{element_id}"
    text_frame = textbox.text_frame
    text_frame.clear()
    text_frame.word_wrap = True
    text_frame.auto_size = MSO_AUTO_SIZE.NONE
    text_frame.margin_left = 0
    text_frame.margin_right = 0
    text_frame.margin_top = 0
    text_frame.margin_bottom = 0

    p = text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER

    run = p.add_run()
    run.text = caption
    run.font.size = Pt(10)


def apply_crop(picture, crop):
    if not crop:
        return
    from m3_core import validate_crop
    crop = validate_crop(crop)
    ns = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main", "a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
    blip_fill = picture._element.find("p:blipFill", ns)
    if blip_fill is None:
        raise ValueError("picture crop target is missing blipFill")
    src_rect = blip_fill.find("a:srcRect", ns)
    if src_rect is None:
        src_rect = blip_fill.makeelement("{http://schemas.openxmlformats.org/drawingml/2006/main}srcRect", {})
        blip_fill.append(src_rect)
    # CT_BlipFill children are ordered blip, srcRect, stretch/tile. Normalize
    # existing as well as newly-created crop nodes to that order.
    children = list(blip_fill)
    src_index = children.index(src_rect)
    insertion = next((i for i, child in enumerate(children)
                      if child.tag in (f"{{{ns['a']}}}stretch", f"{{{ns['a']}}}tile")), len(children))
    if src_index > insertion:
        blip_fill.remove(src_rect)
        blip_fill.insert(insertion, src_rect)
    for key, xml_key in (("left", "l"), ("top", "t"), ("right", "r"), ("bottom", "b")):
        value = crop[key]
        if value:
            src_rect.set(xml_key, str(value))
        else:
            src_rect.attrib.pop(xml_key, None)


def valid_m3_layout(entry):
    if not isinstance(entry, dict):
        return False
    values = [entry.get(key) for key in ("x", "y", "width", "height")]
    if any(type(value) is not int or abs(value) > 10**12 for value in values):
        return False
    return values[2] > 0 and values[3] > 0


# ----------------------------
# 候補矩形
# ----------------------------

def make_candidate_rects(
    slide_w: int,
    slide_h: int,
    occupied_rects: List[Tuple[int, int, int, int]],
) -> List[dict]:
    margin = emu(0.25)
    safe_left = emu(0.45)
    safe_top = emu(0.35)
    safe_right = slide_w - emu(0.45)
    safe_bottom = slide_h - emu(0.35)

    if occupied_rects:
        occ_right = max(rect_right(r) for r in occupied_rects)
        occ_bottom = max(rect_bottom(r) for r in occupied_rects)
    else:
        occ_right = int(slide_w * 0.55)
        occ_bottom = int(slide_h * 0.45)

    right_rect = {
        "name": "right",
        "mode": "vertical",
        "rect": (
            occ_right + margin,
            safe_top,
            max(0, safe_right - (occ_right + margin)),
            max(0, safe_bottom - safe_top),
        ),
    }

    bottom_right_rect = {
        "name": "bottom_right",
        "mode": "single",
        "rect": (
            occ_right + margin,
            occ_bottom + margin,
            max(0, safe_right - (occ_right + margin)),
            max(0, safe_bottom - (occ_bottom + margin)),
        ),
    }

    bottom_rect = {
        "name": "bottom",
        "mode": "horizontal",
        "rect": (
            safe_left,
            occ_bottom + margin,
            max(0, safe_right - safe_left),
            max(0, safe_bottom - (occ_bottom + margin)),
        ),
    }

    return [right_rect, bottom_right_rect, bottom_rect]


# ----------------------------
# レイアウト評価
# ----------------------------

def score_layout(
    images: List[dict],
    rect: Tuple[int, int, int, int],
    mode: str,
) -> Optional[dict]:
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return None

    gap = emu(0.12)
    count = len(images)

    if count == 0:
        return None

    if count == 1 and mode == "single":
        img = images[0]
        caption_h = estimate_caption_box_height(img.get("caption", ""))
        usable_h = h - caption_h - emu(0.06)
        if usable_h <= 0:
            return None

        orig_w, orig_h = get_image_size_emu(img["resolved_path"])
        pic_w, pic_h = fit_size(orig_w, orig_h, w, usable_h)

        if pic_w < emu(1.3) or pic_h < emu(1.0):
            return None

        px = x + (w - pic_w) // 2
        py = y + max(0, (usable_h - pic_h) // 2)

        return {
            "mode": "single",
            "rect": rect,
            "placements": [{
                "img_x": px,
                "img_y": py,
                "img_w": pic_w,
                "img_h": pic_h,
                "caption_x": x,
                "caption_y": py + pic_h + emu(0.04),
                "caption_w": w,
                "caption_h": caption_h,
            }],
            "score": pic_w * pic_h,
        }

    if mode == "vertical":
        total_gap = gap * max(0, count - 1)
        slot_h = (h - total_gap) // count
        if slot_h <= 0:
            return None

        placements = []
        total_area = 0
        cy = y

        for img in images:
            caption_h = estimate_caption_box_height(img.get("caption", ""))
            usable_h = slot_h - caption_h - emu(0.05)
            if usable_h <= 0:
                return None

            orig_w, orig_h = get_image_size_emu(img["resolved_path"])
            pic_w, pic_h = fit_size(orig_w, orig_h, w, usable_h)

            if pic_w < emu(1.2) or pic_h < emu(0.8):
                return None

            px = x + (w - pic_w) // 2
            py = cy + max(0, (usable_h - pic_h) // 2)

            placements.append({
                "img_x": px,
                "img_y": py,
                "img_w": pic_w,
                "img_h": pic_h,
                "caption_x": x,
                "caption_y": py + pic_h + emu(0.04),
                "caption_w": w,
                "caption_h": caption_h,
            })

            total_area += pic_w * pic_h
            cy += slot_h + gap

        return {
            "mode": "vertical",
            "rect": rect,
            "placements": placements,
            "score": total_area,
        }

    if mode == "horizontal":
        total_gap = gap * max(0, count - 1)
        slot_w = (w - total_gap) // count
        if slot_w <= 0:
            return None

        placements = []
        total_area = 0
        cx = x

        for img in images:
            caption_h = estimate_caption_box_height(img.get("caption", ""))
            usable_h = h - caption_h - emu(0.05)
            if usable_h <= 0:
                return None

            orig_w, orig_h = get_image_size_emu(img["resolved_path"])
            pic_w, pic_h = fit_size(orig_w, orig_h, slot_w, usable_h)

            if pic_w < emu(1.2) or pic_h < emu(0.8):
                return None

            px = cx + (slot_w - pic_w) // 2
            py = y + max(0, (usable_h - pic_h) // 2)

            placements.append({
                "img_x": px,
                "img_y": py,
                "img_w": pic_w,
                "img_h": pic_h,
                "caption_x": cx,
                "caption_y": py + pic_h + emu(0.04),
                "caption_w": slot_w,
                "caption_h": caption_h,
            })

            total_area += pic_w * pic_h
            cx += slot_w + gap

        return {
            "mode": "horizontal",
            "rect": rect,
            "placements": placements,
            "score": total_area,
        }

    return None


def choose_best_layout_auto(
    images: List[dict],
    candidate_rects: List[dict],
    occupied_rects: List[Tuple[int, int, int, int]],
) -> Optional[dict]:
    best = None

    for cand in candidate_rects:
        rect = cand["rect"]
        name = cand["name"]
        mode = cand["mode"]

        if any(rect_intersects(rect, occ) for occ in occupied_rects):
            continue

        if mode == "single" and len(images) != 1:
            continue

        layout = score_layout(images, rect, mode)
        if layout is None:
            continue

        layout["candidate_name"] = name

        if best is None or layout["score"] > best["score"]:
            best = layout

    return best


def choose_best_layout(
    images: List[dict],
    candidate_rects: List[dict],
    occupied_rects: List[Tuple[int, int, int, int]],
    preferred_place: Optional[str] = None,
) -> Optional[dict]:
    if preferred_place:
        preferred_candidates = [
            cand for cand in candidate_rects
            if cand["name"] == preferred_place
        ]
        preferred_layout = choose_best_layout_auto(
            images=images,
            candidate_rects=preferred_candidates,
            occupied_rects=occupied_rects,
        )
        if preferred_layout is not None:
            return preferred_layout

        print(
            f"  fallback: requested place '{preferred_place}' does not fit; "
            "using auto placement"
        )

    return choose_best_layout_auto(
        images=images,
        candidate_rects=candidate_rects,
        occupied_rects=occupied_rects,
    )


# ----------------------------
# 画像配置
# ----------------------------

def resolve_requested_place(images: List[dict]) -> Optional[str]:
    requested_places = []
    seen_places = set()

    for image in images:
        place = str(image.get("place", "")).strip().lower()
        if not place:
            continue

        if place not in VALID_PLACES:
            print(
                f"  [WARN] invalid place '{place}' for image "
                f"'{image.get('raw_path', '')}'; using auto placement"
            )
            continue

        if place not in seen_places:
            requested_places.append(place)
            seen_places.add(place)

    if not requested_places:
        return None

    selected_place = requested_places[0]

    if len(requested_places) > 1:
        print(
            "  [WARN] mixed place values in slide: "
            f"{', '.join(requested_places)}; using first: {selected_place}"
        )

    if selected_place == "bottom_right" and len(images) > 1:
        print(
            "  [WARN] place 'bottom_right' is only supported for a single image; "
            "using auto placement"
        )
        return None

    return selected_place


def collect_target_images(slide_info: dict, base_dir: Path, assets_by_key: dict, slide_w: int, slide_h: int) -> List[dict]:
    images = slide_info.get("images", [])
    result = []

    for image in images:
        raw_path = str(image.get("path", "")).strip()
        resolved_path = (base_dir / raw_path).resolve()

        if not raw_path:
            continue

        if not resolved_path.exists():
            print(f"  missing image: {raw_path}")
            continue

        result.append({
            "raw_path": raw_path,
            "resolved_path": resolved_path,
            "caption": str(image.get("caption", "")).strip(),
            "place": str(image.get("place", "")).strip().lower(),
            "element_id": image.get("element_id", ""),
            "slide_id": slide_info.get("slide_id", ""),
            "saved_layout": assets_by_key.get((slide_info.get("slide_id", ""), image.get("element_id", ""))),
        })

    return result


def add_offslide_images_near_target_slide(slide, images: List[dict], slide_w: int, anchor_top: int) -> List[dict]:
    margin = emu(0.18)
    x = slide_w + emu(0.08)
    y = anchor_top
    max_w = emu(2.5)
    max_h = emu(1.8)
    placements = []

    for image in images:
        caption_h = estimate_caption_box_height(image.get("caption", ""))
        usable_h = max_h - caption_h - emu(0.05)

        orig_w, orig_h = get_image_size_emu(image["resolved_path"])
        pic_w, pic_h = fit_size(orig_w, orig_h, max_w, usable_h)

        picture = slide.shapes.add_picture(str(image["resolved_path"]), x, y, width=pic_w, height=pic_h)
        picture.name = image["element_id"]
        placements.append({"slideId": image["slide_id"], "elementId": image["element_id"], "type": "image", "path": image["raw_path"], "x": int(picture.left), "y": int(picture.top), "width": int(picture.width), "height": int(picture.height)})

        if caption_h > 0:
            add_caption_textbox(
                slide,
                image["caption"],
                image["element_id"],
                x,
                y + pic_h + emu(0.04),
                max_w,
                caption_h,
            )

        y += pic_h + caption_h + margin

    return placements


def add_images_to_slide(prs: Presentation, slide, slide_info: dict, base_dir: Path, assets_by_key: dict, is_m3_assets: bool = False) -> List[dict]:
    slide_w = int(prs.slide_width)
    slide_h = int(prs.slide_height)
    target_images = collect_target_images(slide_info, base_dir, assets_by_key, slide_w, slide_h)
    if not target_images:
        return []

    layouts = []
    auto_images = []
    occupied_rects = get_occupied_rects(slide, slide_w, slide_h)
    for image in target_images:
        saved = image.get("saved_layout")
        if saved is not None:
            if (isinstance(saved, dict) and saved.get("slideId") == image["slide_id"] and
                    saved.get("elementId") == image["element_id"] and
                    saved.get("type") == "image" and (
                        valid_m3_layout(saved) if is_m3_assets else
                        valid_layout(saved, slide_w, slide_h, len(slide_info.get("images", [])))
                    )):
                picture = slide.shapes.add_picture(
                    str(image["resolved_path"]), int(saved["x"]), int(saved["y"]),
                    width=int(saved["width"]), height=int(saved["height"]),
                )
                picture.name = image["element_id"]
                apply_crop(picture, saved.get("crop"))
                rect = (int(picture.left), int(picture.top), int(picture.width), int(picture.height))
                occupied_rects.append(rect)
                entry = {"slideId": image["slide_id"], "elementId": image["element_id"], "type": "image", "path": image["raw_path"], "x": rect[0], "y": rect[1], "width": rect[2], "height": rect[3]}
                if saved.get("crop") is not None:
                    entry["crop"] = saved["crop"]
                layouts.append(entry)
                caption = image.get("caption", "").strip()
                caption_h = estimate_caption_box_height(caption)
                if caption_h > 0:
                    add_caption_textbox(
                        slide,
                        caption,
                        image["element_id"],
                        int(saved["x"]),
                        int(saved["y"]) + int(saved["height"]) + emu(0.04),
                        int(saved["width"]),
                        caption_h,
                    )
                continue
            print(f"[WARN] invalid saved layout for element {image['element_id']}; using automatic placement")
        auto_images.append(image)

    if not auto_images:
        return layouts

    body_info = find_body_shape(slide, slide_h)
    if body_info:
        _, _, body_top, _, _ = body_info
        offslide_anchor_top = body_top
    else:
        offslide_anchor_top = emu(1.4)

    candidate_rects = make_candidate_rects(
        slide_w=slide_w,
        slide_h=slide_h,
        occupied_rects=occupied_rects,
    )

    requested_place = resolve_requested_place(target_images)

    if requested_place:
        print(f"  requested place: {requested_place}")

    best_layout = choose_best_layout(
        images=auto_images,
        candidate_rects=candidate_rects,
        occupied_rects=occupied_rects,
        preferred_place=requested_place,
    )

    if best_layout is None:
        print("  fallback: off-slide (no candidate fits)")
        layouts.extend(add_offslide_images_near_target_slide(
            slide=slide,
            images=auto_images,
            slide_w=slide_w,
            anchor_top=offslide_anchor_top,
        ))
        return layouts

    print(f"  place: {best_layout['candidate_name']} / {best_layout['mode']}")

    for image, placement in zip(auto_images, best_layout["placements"]):
        picture = slide.shapes.add_picture(
            str(image["resolved_path"]),
            placement["img_x"],
            placement["img_y"],
            width=placement["img_w"],
            height=placement["img_h"],
        )
        picture.name = image["element_id"]
        layouts.append({"slideId": image["slide_id"], "elementId": image["element_id"], "type": "image", "path": image["raw_path"], "x": int(picture.left), "y": int(picture.top), "width": int(picture.width), "height": int(picture.height)})

        if placement["caption_h"] > 0 and image.get("caption", "").strip():
            add_caption_textbox(
                slide,
                image["caption"],
                image["element_id"],
                placement["caption_x"],
                placement["caption_y"],
                placement["caption_w"],
                placement["caption_h"],
            )
    return layouts


# ----------------------------
# main
# ----------------------------

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pptx", required=True, help="後処理対象のPPTXファイル")
    parser.add_argument("--images-json", required=True, help="画像情報JSON")
    parser.add_argument("--assets", help="永続化するassets.json")
    parser.add_argument("--qmd", help="M3 managed-render baseline source QMD")
    args = parser.parse_args()

    pptx_path = Path(args.pptx).resolve()
    images_json_path = Path(args.images_json).resolve()

    if not pptx_path.exists():
        raise FileNotFoundError(f"PPTXが見つかりません: {pptx_path}")

    if not images_json_path.exists():
        raise FileNotFoundError(f"images json が見つかりません: {images_json_path}")

    slide_infos = load_images_json(images_json_path)
    prs = Presentation(str(pptx_path))
    assets_path = Path(args.assets).resolve() if args.assets else images_json_path.with_name(images_json_path.name.replace(".images.json", ".assets.json"))
    if args.qmd:
        import json
        from m3_core import validate_assets
        if assets_path.exists():
            assets = validate_assets(json.loads(assets_path.read_text(encoding="utf-8")))
        else:
            assets = {"schemaVersion": 1, "slideSize": None, "elements": []}
    else:
        assets = load_assets(assets_path)
    assets_by_key = {}
    for entry in assets.get("elements", []):
        if isinstance(entry, dict):
            assets_by_key[(entry.get("slideId"), entry.get("elementId"))] = entry
    rendered_layouts = []
    matched_slide_ids = set()

    print(f"PPTX slide count : {len(prs.slides)}")
    print(f"JSON slide count : {len(slide_infos)}")
    print(f"Process count    : {min(len(prs.slides), len(slide_infos))}")

    base_dir = images_json_path.parent

    for i, slide_info in enumerate(slide_infos):
        target_title = normalize_text(slide_info.get("title", ""))
        target_slide_id = slide_info.get("slide_id", "")

        matched_slide = None

        for slide in prs.slides:
            if getattr(slide, "name", "") == target_slide_id:
                matched_slide = slide
                break
        if matched_slide is None:
            # Quarto creates fresh slides on every render; title is only the initial association.
            # Once matched, the stable ID is written into the public slide name metadata.
            for slide in prs.slides:
                ppt_slide_id = getattr(slide, "name", "")
                if ppt_slide_id in matched_slide_ids or ppt_slide_id.startswith("slide-"):
                    continue
                ppt_title = normalize_text(get_slide_title(slide))
                if ppt_title == target_title:
                    matched_slide = slide
                    break

        if matched_slide is None:
            print(f"[WARN] slide not found: {target_title}")
            continue

        print(
            f"[match] slide {i + 1}: "
            f"title='{target_title}' "
            f"images={len(slide_info.get('images', []))}"
        )

        matched_slide.name = target_slide_id
        matched_slide_ids.add(target_slide_id)
        rendered_layouts.extend(add_images_to_slide(prs, matched_slide, slide_info, base_dir, assets_by_key, bool(args.qmd)))

    document_id = None
    if args.qmd:
        existing_props = read_custom_properties(pptx_path)
        asset_document_id = assets.get("documentId") if isinstance(assets, dict) else None
        property_document_id = existing_props.get("md-slide-tool.document-id")
        if asset_document_id and property_document_id and asset_document_id != property_document_id:
            raise ValueError("managed PPTX/assets document-id mismatch")
        document_id = asset_document_id or property_document_id or new_document_id()
        if not valid_document_id(document_id):
            raise ValueError("invalid managed document-id")
        title_candidates = []
        for slide in prs.slides:
            has_layout_title = any(
                getattr(shape, "is_placeholder", False) and int(shape.placeholder_format.type) == 3
                for shape in slide.slide_layout.shapes
            )
            has_slide_title = any(
                getattr(shape, "is_placeholder", False) and int(shape.placeholder_format.type) == 3
                for shape in slide.shapes
            )
            if has_layout_title and has_slide_title:
                title_candidates.append(slide)
        if len(title_candidates) > 1:
            raise ValueError("ambiguous title-slide layout classification")
        for slide in title_candidates:
            slide.name = f"mdst-title-{document_id.removeprefix('document-')}"
    prs.save(str(pptx_path))
    if args.qmd:
        write_custom_properties(pptx_path, {
            "md-slide-tool.managed": "1",
            "md-slide-tool.format-version": "1",
            "md-slide-tool.document-id": document_id,
            "md-slide-tool.qmd-body-sha256": qmd_body_sha256(Path(args.qmd).read_bytes()),
        })
    current_keys = {
        (slide_info.get("slide_id"), image.get("element_id"))
        for slide_info in slide_infos for image in slide_info.get("images", [])
    }
    updated_by_key = {(entry["slideId"], entry["elementId"]): entry for entry in rendered_layouts}
    for key, old_entry in assets_by_key.items():
        if key in current_keys and key not in updated_by_key:
            updated_by_key[key] = old_entry
    final_assets = {
        "schemaVersion": 2 if args.qmd else 1,
        "slideSize": {"width": int(prs.slide_width), "height": int(prs.slide_height), "unit": "emu"},
        "elements": list(updated_by_key.values()),
    }
    if args.qmd:
        final_assets["documentId"] = document_id
    atomic_write_json(assets_path, final_assets)
    print(f"saved: {pptx_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
