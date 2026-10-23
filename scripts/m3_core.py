#!/usr/bin/env python3
"""Shared M3 metadata, QMD baseline, and assets schema helpers."""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
import uuid
import copy
from pathlib import PurePosixPath, PureWindowsPath
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from m2_identity import validate_id

CUSTOM_NS = "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
VT_NS = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
MDST_PROPS = {
    "md-slide-tool.managed", "md-slide-tool.format-version",
    "md-slide-tool.document-id", "md-slide-tool.qmd-body-sha256",
}


def split_front_matter(raw: bytes) -> tuple[bytes, bytes]:
    """Return (front matter bytes, body bytes), preserving source bytes exactly."""
    content = raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw
    prefix_len = len(raw) - len(content)
    match = re.match(rb"\A---(?:\r\n|\n)", content)
    if not match:
        return raw[:prefix_len], content
    pos = match.end()
    for line in re.finditer(rb"[^\r\n]*(?:\r\n|\n|\r|\Z)", content[pos:]):
        value = line.group(0)
        stripped = value.rstrip(b"\r\n")
        if stripped == b"---" and value.endswith((b"\n", b"\r")):
            end = pos + line.end()
            return raw[:prefix_len + end], content[end:]
    return raw[:prefix_len], content


def canonical_body(raw: bytes) -> bytes:
    _, body = split_front_matter(raw)
    # Normalize CRLF and bare CR, preserving all other bytes and trailing space.
    return body.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def qmd_body_sha256(raw: bytes) -> str:
    return hashlib.sha256(canonical_body(raw)).hexdigest()


def new_document_id() -> str:
    return f"document-{uuid.uuid4()}"


def valid_document_id(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(
        r"document-[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}", value
    ) is not None


def read_custom_properties(pptx_path: Path) -> dict[str, str]:
    try:
        with zipfile.ZipFile(pptx_path) as package:
            xml = package.read("docProps/custom.xml")
    except KeyError:
        return {}
    root = ET.fromstring(xml)
    result = {}
    for prop in root.findall(f"{{{CUSTOM_NS}}}property"):
        child = next(iter(prop), None)
        if child is not None:
            result[prop.attrib.get("name", "")] = child.text or ""
    return result


def write_custom_properties(pptx_path: Path, values: dict[str, str]) -> None:
    """Update standard docProps/custom.xml in-place while preserving other ZIP parts."""
    ET.register_namespace("", CUSTOM_NS)
    ET.register_namespace("vt", VT_NS)
    props = {}
    try:
        with zipfile.ZipFile(pptx_path) as package:
            names = package.namelist()
            blobs = {name: package.read(name) for name in names}
        if "docProps/custom.xml" in blobs:
            root = ET.fromstring(blobs["docProps/custom.xml"])
            for prop in root.findall(f"{{{CUSTOM_NS}}}property"):
                child = next(iter(prop), None)
                props[prop.attrib.get("name", "")] = (
                    dict(prop.attrib), copy.deepcopy(child) if child is not None else None,
                )
        else:
            names = list(blobs)
            root = ET.Element(f"{{{CUSTOM_NS}}}Properties")
    except zipfile.BadZipFile as exc:
        raise ValueError("invalid PPTX package") from exc
    used_pids = [int(attrs.get("pid", "1")) for attrs, _ in props.values()]
    pid = max(used_pids + [1]) + 1
    for name, value in values.items():
        if name in props:
            attrs, _ = props[name]
            pid_value = attrs.get("pid", str(pid))
        else:
            attrs = {"fmtid": "{D5CDD505-2E9C-101B-9397-08002B2CF9AE}", "pid": str(pid), "name": name}
            pid_value = str(pid)
            pid += 1
        # Managed properties are strings. Replacing only their value child
        # leaves unrelated Office custom-property types untouched.
        value_child = ET.Element(f"{{{VT_NS}}}lpwstr")
        value_child.text = str(value)
        props[name] = (attrs, value_child)
    root_attributes = dict(root.attrib)
    root.clear()
    root.attrib.update(root_attributes)
    for attrs, value_child in props.values():
        prop = ET.SubElement(root, f"{{{CUSTOM_NS}}}property", attrs)
        if value_child is not None:
            prop.append(value_child)
    blobs["docProps/custom.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    # Ensure package relationships and content types advertise the custom part.
    rels_path = "_rels/.rels"
    rel_root = ET.fromstring(blobs[rels_path])
    rel_type = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties"
    if not any(item.attrib.get("Type") == rel_type for item in rel_root):
        ids = {item.attrib.get("Id", "") for item in rel_root}
        index = 1
        while f"rId{index}" in ids:
            index += 1
        ET.SubElement(rel_root, f"{{{PKG_REL_NS}}}Relationship", {"Id": f"rId{index}", "Type": rel_type, "Target": "docProps/custom.xml"})
    blobs[rels_path] = ET.tostring(rel_root, encoding="utf-8", xml_declaration=True)
    ct_path = "[Content_Types].xml"
    ct_root = ET.fromstring(blobs[ct_path])
    part = "/docProps/custom.xml"
    if not any(item.attrib.get("PartName") == part for item in ct_root):
        ET.SubElement(ct_root, "{http://schemas.openxmlformats.org/package/2006/content-types}Override", {"PartName": part, "ContentType": "application/vnd.openxmlformats-officedocument.custom-properties+xml"})
    blobs[ct_path] = ET.tostring(ct_root, encoding="utf-8", xml_declaration=True)
    fd, temp = tempfile.mkstemp(prefix=f".{pptx_path.name}.", suffix=".tmp", dir=pptx_path.parent)
    import os
    os.close(fd)
    try:
        with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as package:
            for name, blob in blobs.items():
                package.writestr(name, blob)
        os.replace(temp, pptx_path)
    finally:
        Path(temp).unlink(missing_ok=True)


def validate_crop(crop: object) -> dict | None:
    if crop is None:
        return None
    if not isinstance(crop, dict) or crop.get("unit") != "ooxml-percent":
        raise ValueError("invalid crop object")
    values = [crop.get(key) for key in ("left", "top", "right", "bottom")]
    if any(type(value) is not int or abs(value) > 200000 for value in values):
        raise ValueError("invalid crop integer/range")
    left, top, right, bottom = values
    if left + right >= 100000 or top + bottom >= 100000:
        raise ValueError("crop has non-positive effective source rectangle")
    return {"unit": "ooxml-percent", "left": left, "top": top, "right": right, "bottom": bottom}


def validate_assets(data: object, expected_document_id: str | None = None) -> dict:
    if not isinstance(data, dict) or data.get("schemaVersion") not in (1, 2) or not isinstance(data.get("elements"), list):
        raise ValueError("invalid assets schema")
    schema = data["schemaVersion"]
    if schema == 2:
        document_id = data.get("documentId")
        if not valid_document_id(document_id) or (expected_document_id and document_id != expected_document_id):
            raise ValueError("assets documentId mismatch")
    seen = set()
    clean = []
    for item in data["elements"]:
        if not isinstance(item, dict) or not validate_id(item.get("slideId", ""), "slide") or not validate_id(item.get("elementId", ""), "element"):
            raise ValueError("invalid stable element metadata")
        key = item["elementId"]
        if key in seen:
            raise ValueError("duplicate element-id")
        seen.add(key)
        if item.get("type") != "image" or any(type(item.get(k)) is not int for k in ("x", "y", "width", "height")):
            raise ValueError("invalid image layout")
        if (abs(item["x"]) > 10**12 or abs(item["y"]) > 10**12 or
                item["width"] <= 0 or item["height"] <= 0 or
                item["width"] > 10**12 or item["height"] > 10**12):
            raise ValueError("invalid image geometry")
        source_path = item.get("path")
        if (not isinstance(source_path, str) or not source_path or
                PurePosixPath(source_path).is_absolute() or PureWindowsPath(source_path).is_absolute() or
                "\\" in source_path or ":" in source_path or ".." in PurePosixPath(source_path).parts):
            raise ValueError("invalid image source path")
        crop = validate_crop(item.get("crop")) if schema == 2 else None
        clean_item = dict(item)
        clean_item.pop("crop", None)
        if crop is not None:
            clean_item["crop"] = crop
        clean.append(clean_item)
    return {"schemaVersion": schema, **({"documentId": data["documentId"]} if schema == 2 else {}), "slideSize": data.get("slideSize"), "elements": clean}
