import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import sys
import types


class _DummyPresentation:
    pass


def _dummy_inches(value):
    return int(value * 914400)


def _dummy_pt(value):
    return value


sys.modules.setdefault("PIL", types.SimpleNamespace(Image=types.SimpleNamespace(open=None)))
sys.modules.setdefault("PIL.Image", types.SimpleNamespace(open=None))
sys.modules.setdefault("pptx", types.SimpleNamespace(Presentation=_DummyPresentation))
sys.modules.setdefault("pptx.enum", types.SimpleNamespace())
sys.modules.setdefault("pptx.enum.text", types.SimpleNamespace(PP_ALIGN=types.SimpleNamespace(CENTER=1), MSO_AUTO_SIZE=types.SimpleNamespace(TEXT_TO_FIT_SHAPE=1)))
sys.modules.setdefault("pptx.util", types.SimpleNamespace(Inches=_dummy_inches, Pt=_dummy_pt))


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "postprocess-pptx.py"
spec = importlib.util.spec_from_file_location("postprocess_pptx", MODULE_PATH)
postprocess = importlib.util.module_from_spec(spec)
spec.loader.exec_module(postprocess)


def cand(name, mode="vertical"):
    return {"name": name, "mode": mode, "rect": (0, 0, 100, 100)}


class ResolveRequestedPlaceTests(unittest.TestCase):
    def test_no_place_uses_auto(self):
        self.assertIsNone(postprocess.resolve_requested_place([{"place": ""}]))

    def test_first_valid_place_is_used(self):
        self.assertEqual(
            postprocess.resolve_requested_place([
                {"place": ""},
                {"place": "right"},
                {"place": "right"},
            ]),
            "right",
        )

    def test_invalid_place_warns_and_uses_auto(self):
        with patch("builtins.print") as mocked_print:
            self.assertIsNone(postprocess.resolve_requested_place([{"place": "center"}]))

        self.assertTrue(any("invalid place" in str(call) for call in mocked_print.call_args_list))

    def test_mixed_places_warns_and_uses_first(self):
        with patch("builtins.print") as mocked_print:
            actual = postprocess.resolve_requested_place([
                {"place": "bottom"},
                {"place": "right"},
            ])

        self.assertEqual(actual, "bottom")
        self.assertTrue(any("mixed place values" in str(call) for call in mocked_print.call_args_list))

    def test_bottom_right_with_multiple_images_warns_and_uses_auto(self):
        with patch("builtins.print") as mocked_print:
            actual = postprocess.resolve_requested_place([
                {"place": "bottom_right"},
                {"place": ""},
            ])

        self.assertIsNone(actual)
        self.assertTrue(any("bottom_right" in str(call) and "single image" in str(call) for call in mocked_print.call_args_list))


class ChooseBestLayoutTests(unittest.TestCase):
    def test_without_preferred_place_keeps_score_based_auto_selection(self):
        candidates = [cand("right"), cand("bottom")]
        candidates[0]["mode"] = "right_mode"
        candidates[1]["mode"] = "bottom_mode"
        with patch.object(postprocess, "score_layout", side_effect=lambda images, rect, mode: {"score": 10 if mode == "right_mode" else 20, "placements": []}):
            layout = postprocess.choose_best_layout([{}], candidates, [])

        self.assertEqual(layout["candidate_name"], "bottom")

    def test_preferred_right_is_used_even_when_score_is_lower(self):
        layout = self._choose_with_preferred_place("right")

        self.assertEqual(layout["candidate_name"], "right")

    def test_preferred_bottom_is_used_even_when_score_is_lower(self):
        layout = self._choose_with_preferred_place("bottom")

        self.assertEqual(layout["candidate_name"], "bottom")

    def test_preferred_bottom_right_is_used_for_single_image(self):
        candidates = [
            {"name": "bottom_right", "mode": "single", "rect": (0, 0, 100, 100)},
            {"name": "bottom", "mode": "bottom_mode", "rect": (0, 0, 100, 100)},
        ]

        with patch.object(postprocess, "score_layout", return_value={"score": 10, "placements": []}):
            layout = postprocess.choose_best_layout([{}], candidates, [], preferred_place="bottom_right")

        self.assertEqual(layout["candidate_name"], "bottom_right")

    def _choose_with_preferred_place(self, preferred_place):
        candidates = [
            {"name": "right", "mode": "right_mode", "rect": (0, 0, 100, 100)},
            {"name": "bottom", "mode": "bottom_mode", "rect": (0, 0, 100, 100)},
        ]

        with patch.object(postprocess, "score_layout", side_effect=lambda images, rect, mode: {"score": 10 if mode == f"{preferred_place}_mode" else 20, "placements": []}):
            return postprocess.choose_best_layout([{}], candidates, [], preferred_place=preferred_place)

    def test_preferred_place_falls_back_to_auto_when_it_does_not_fit(self):
        candidates = [
            {"name": "right", "mode": "right_mode", "rect": (0, 0, 100, 100)},
            {"name": "bottom", "mode": "bottom_mode", "rect": (0, 0, 100, 100)},
        ]

        def fake_score(_images, _rect, mode):
            if mode == "right_mode":
                return None
            return {"score": 20, "placements": []}

        with patch.object(postprocess, "score_layout", side_effect=fake_score), patch("builtins.print") as mocked_print:
            layout = postprocess.choose_best_layout([{}], candidates, [], preferred_place="right")

        self.assertEqual(layout["candidate_name"], "bottom")
        self.assertTrue(any("requested place 'right' does not fit" in str(call) for call in mocked_print.call_args_list))


if __name__ == "__main__":
    unittest.main()
