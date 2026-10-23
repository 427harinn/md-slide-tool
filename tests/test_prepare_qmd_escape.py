import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "prepare-qmd-for-pptx.py"
SPEC = importlib.util.spec_from_file_location("prepare_qmd_for_pptx", SCRIPT)
PREPARE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREPARE)


class PrepareQmdEscapeTests(unittest.TestCase):
    def test_render_metadata_uses_unescaped_titles_and_captions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            qmd = root / "deck.qmd"
            render_qmd = root / ".deck.render.qmd"
            images_json = root / ".deck.images.json"
            source = (
                "---\ntitle: Deck\n---\n\n"
                '## Edited \\*title\\* {slide-id="slide-123e4567-e89b-42d3-a456-426614174000"}\n\n'
                '![caption \\] and \\*literal\\*](images/picture.png) '
                '{element-id="element-123e4567-e89b-42d3-a456-426614174000"}\n'
            )
            qmd.write_text(source, encoding="utf-8")

            with patch.object(sys, "argv", [str(SCRIPT), "--input", str(qmd), "--output", str(render_qmd), "--images-json", str(images_json)]):
                self.assertEqual(PREPARE.main(), 0)

            metadata = json.loads(images_json.read_text(encoding="utf-8"))
            self.assertEqual(metadata[0]["title"], "Edited *title*")
            self.assertEqual(metadata[0]["images"][0]["caption"], "caption ] and *literal*")
            self.assertEqual(qmd.read_text(encoding="utf-8"), source)
            self.assertIn(r"## Edited \*title\*", render_qmd.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
