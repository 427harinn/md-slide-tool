# M2: Stable IDs and Element Layout

## Purpose

M2 introduces stable identity and persistent layout for slide elements so future PPTX -> QMD import can identify the same logical slide and element without relying on titles, file names, or slide order.

M2 implements layout persistence for **image elements only**, but the identity model is deliberately generalized to `element-id` so shapes and other PowerPoint elements can be added later without replacing the ID system.

## Core decisions

### 1. Stable identity lives in QMD

QMD is the source of identity for QMD -> PPTX generation.

Use dedicated attributes:

```md
## System overview {slide-id="slide-<uuid>"}

![Architecture](images/system.png){element-id="element-<uuid>" place="right"}
```

Do not reuse generic Markdown anchor IDs for this purpose.

- `slide-id`: identifies one logical slide.
- `element-id`: identifies one logical element on a slide.
- IDs are opaque generated values, not human-readable names.
- Renaming a title, changing an image path, or reordering slides must not change the existing ID.

### 2. Missing IDs are generated, existing IDs are preserved

When rendering a QMD that lacks required IDs:

- generate only the missing IDs;
- write them back to the source QMD;
- never regenerate an existing valid ID;
- use an atomic source-file update;
- do not alter title/body/image path/caption while adding IDs.

Duplicate `slide-id` or duplicate `element-id` is an error. Do not guess which duplicate should be changed.

The generated ID format should use UUID-based opaque identifiers, e.g. `slide-<uuid>` and `element-<uuid>`.

### 3. Element model is general; M2 implementation supports images only

M2 supports:

```text
element.type = image
```

The stable identity is called `element-id`, not `image-id`.

Future versions may add:

- shape
- line / arrow
- icon
- other PowerPoint-native visual elements

without changing the identity model.

M2 does **not** define the final QMD syntax or full persistence schema for those future element types.

### 4. Persistent layout file

For `presentation.qmd`, use:

```text
presentation.qmd
presentation.pptx
presentation.assets.json
```

Initial schema:

```json
{
  "schemaVersion": 1,
  "slideSize": {
    "width": 12192000,
    "height": 6858000,
    "unit": "emu"
  },
  "elements": [
    {
      "slideId": "slide-...",
      "elementId": "element-...",
      "type": "image",
      "path": "images/system.png",
      "x": 8200000,
      "y": 1400000,
      "width": 3200000,
      "height": 2400000
    }
  ]
}
```

The exact slide-size values are taken from the actual presentation. The example above is illustrative.

### 5. Use EMU for coordinates

Store `x`, `y`, `width`, and `height` as integer EMU values, matching PowerPoint/Open XML shape coordinates.

Do not persist floating-point inches as the canonical layout unit.

### 6. assets.json stores layout, not document text

Do not store title/body text in `assets.json`.

For M2, do not persist:

- slide title;
- body text;
- speaker notes;
- caption text as an independent canonical copy.

QMD remains the source for document text.

The image `path` may appear in `assets.json` as element metadata, but it is not the identity key. `elementId` is the identity key.

### 7. Layout precedence during QMD -> PPTX render

For each image element:

1. Match by `slide-id` + `element-id`.
2. If valid layout exists in `assets.json`, apply it.
3. If no valid layout exists, use the existing `place=` preference and current automatic image-placement engine.
4. Persist the resulting image rectangle to `assets.json`.

The existing placement engine remains the initial/fallback layout engine.

A title string, slide order, image path, or caption must not be the primary identity match after stable IDs are available.

### 8. PPTX receives the same stable IDs

The generated PPTX must carry the md-slide-tool stable IDs so M3 can later recover identity from a PowerPoint-edited file.

Design direction:

- slide identity: store the md-slide-tool `slide-id` in slide-level metadata that survives ordinary PowerPoint editing/save;
- element identity: store the md-slide-tool `element-id` on the corresponding PowerPoint shape metadata/name.

The implementation must test the chosen metadata locations for save/reopen preservation. Do not use PowerPoint's package-internal numeric slide ID as the md-slide-tool stable ID.

### 9. Image replacement semantics

Identity represents the logical element, not the image bytes or file path.

If PowerPoint replaces the picture **while preserving the same identified shape**, future import should treat it as the same element:

```text
element-123
old image -> replacement image
layout remains associated with element-123
```

M3 may then update the QMD image source while preserving `element-id`.

If the user deletes the old shape and inserts a new picture shape, the new shape has no md-slide-tool element ID. Future import must treat it as a new element and generate a new `element-id`; it must not guess that it replaces the deleted element.

M2 does not implement PPTX -> QMD import, but it must choose metadata that makes this distinction possible.

### 10. Stale and invalid layout

On successful render:

- QMD elements without layout receive automatic layout and a new assets entry.
- Assets entries whose `slideId` / `elementId` no longer exist in the current QMD are removed.
- Invalid layout data for an otherwise valid image element produces a warning and falls back to automatic placement for that element.
- Duplicate stable IDs are fatal and must not be silently repaired.

### 11. Backward compatibility

Existing QMD files without stable IDs must remain renderable. First M2 render may add the missing IDs and create `presentation.assets.json`.

Existing `place=right|bottom|bottom_right` behavior remains meaningful as an initial/fallback preference.

Existing docx behavior must not change.

## M2 scope

M2 includes:

- `slide-id`;
- `element-id`;
- ID generation/validation;
- image elements only;
- `assets.json` schema version 1;
- EMU image rectangles;
- PPTX stable-ID embedding;
- applying saved image layout;
- falling back to the current automatic placement engine;
- persisting initial/fallback layout;
- stale assets cleanup;
- regression tests.

M2 does not include:

- PPTX -> QMD import;
- PowerPoint save watcher;
- QMD save watcher;
- automatic sync;
- conflict handling;
- shape layout persistence;
- shape creation/editing syntax;
- crop;
- rotation;
- z-order;
- text-box layout persistence;
- Marketplace publication;
- PPTX -> Word.

## Completion behavior

After M2, a QMD can be rendered repeatedly without losing image identity or re-randomizing/recomputing a previously persisted image rectangle.

Changing a slide title must not break image-to-slide association.

Changing an image source path while keeping its `element-id` must preserve the saved layout.

The resulting data model must be ready for M3 to import PowerPoint edits by stable identity.
