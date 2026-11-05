import hashlib
import contextlib
import io
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
from m3_core import read_custom_properties, write_custom_properties
from m3_transaction import FileTransaction
from m4_preview import PROBE_STATES, allocate_preview, cleanup_decision, is_preview, mark_preview
import m3_entry
from test_m3_import import DOC, make_deck

spec = importlib.util.spec_from_file_location("m3_importer", ROOT / "scripts" / "import-pptx.py")
importer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(importer)


class M4ProbeTests(unittest.TestCase):
    def test_preview_refuses_unmanaged_pair_without_bootstrapping_an_id(self):
        cases = (None, {"schemaVersion": 1, "slideSize": None, "elements": []})
        for prior_assets in cases:
            with self.subTest(prior_assets=prior_assets is not None), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                qmd = root / "deck.qmd"
                qmd.write_bytes(b"---\ntitle: Deck\n---\n")
                assets = root / "deck.assets.json"
                if prior_assets is not None:
                    assets.write_text(json.dumps(prior_assets), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "existing M3-managed"):
                    m3_entry.run_locked(qmd, ["preview"])
                self.assertEqual(assets.exists(), prior_assets is not None)
                self.assertFalse((root / ".md-slide-tool").exists())

    def test_preview_refuses_pending_journal_without_recovery_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pptx, qmd, assets = make_deck(root)
            tx = FileTransaction(root, DOC, txid="pending-preview-journal", paired_qmd_path=qmd)
            tx.stage(assets, b"candidate-assets")
            tx.manifest["phase"] = "committing"
            tx._save()
            journal = tx.root
            before = {path: path.read_bytes() for path in (qmd, assets, pptx)}
            with patch.object(m3_entry, "recover_transactions") as recover, \
                    patch.object(m3_entry.subprocess, "call") as run:
                with self.assertRaisesRegex(ValueError, "pending M3 transaction"):
                    m3_entry.run_locked(qmd, ["preview"])
                recover.assert_not_called()
                run.assert_not_called()
            self.assertEqual({path: path.read_bytes() for path in before}, before)
            self.assertTrue((journal / "manifest.json").is_file())

    def test_preview_requires_canonical_pptx_document_id_to_match_pair(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pptx, qmd, assets = make_deck(root)
            before = {path: path.read_bytes() for path in (qmd, assets, pptx)}
            other_id = "document-123e4567-e89b-42d3-a456-426614174099"
            write_custom_properties(pptx, {"md-slide-tool.document-id": other_id})
            with self.assertRaisesRegex(ValueError, "does not match"):
                m3_entry.run_locked(qmd, ["preview"])
            self.assertEqual(qmd.read_bytes(), before[qmd])
            self.assertEqual(assets.read_bytes(), before[assets])
            self.assertEqual(read_custom_properties(pptx)["md-slide-tool.document-id"], other_id)

    def test_open_editable_resolution_refuses_pending_transaction(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pptx, qmd, assets = make_deck(root)
            expected = pptx.resolve()
            self.assertEqual(m3_entry.resolve_canonical_pptx_locked(qmd), expected)
            tx = FileTransaction(root, DOC, txid="pending-editable-open", paired_qmd_path=qmd)
            tx.stage(assets, b"candidate-assets")
            tx.manifest["phase"] = "committing"
            tx._save()
            with self.assertRaisesRegex(ValueError, "pending M3 transaction"):
                m3_entry.resolve_canonical_pptx_locked(qmd)

    def test_managed_render_and_import_still_recover_before_operation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pptx, qmd, _assets = make_deck(root)
            for operation in (["render"], ["import", str(pptx)]):
                with self.subTest(operation=operation), \
                        patch.object(m3_entry, "recover_transactions") as recover, \
                        patch.object(m3_entry.subprocess, "call", return_value=0):
                    self.assertEqual(m3_entry.run_locked(qmd, operation), 0)
                    self.assertGreaterEqual(recover.call_count, 1)
                    self.assertTrue(all(call.args == (root, DOC, qmd) for call in recover.call_args_list))

    def test_preview_cli_emits_exact_path_only_after_successful_render(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _pptx, qmd, _assets = make_deck(root)
            canonical = qmd.with_suffix(".pptx")
            canonical_before = canonical.read_bytes()
            preview = root / ".md-slide-tool" / "previews" / DOC / "preview-000001.pptx"
            stdout = io.StringIO()

            def reserve(*_args, **_kwargs):
                preview.parent.mkdir(parents=True, exist_ok=True)
                preview.touch()
                return str(preview)

            def render(command, **_kwargs):
                Path(command[4]).write_bytes(b"versioned-preview-pptx")
                return 0

            with patch.object(m3_entry.subprocess, "check_output", side_effect=reserve), \
                    patch.object(m3_entry.subprocess, "call", side_effect=render), \
                    patch.object(m3_entry, "recover_transactions") as recover, \
                    contextlib.redirect_stdout(stdout):
                self.assertEqual(m3_entry.run_locked(qmd, ["preview"]), 0)
            recover.assert_not_called()
            self.assertEqual(stdout.getvalue().splitlines(), [
                f"PREVIEW_PATH={preview}", f"PREVIEW_DOCUMENT_ID={DOC}", f"PREVIEW_SOURCE_QMD={qmd}",
            ])
            self.assertEqual(canonical.read_bytes(), canonical_before)

            failed_preview = root / ".md-slide-tool" / "previews" / DOC / "preview-000002.pptx"
            failed_stdout = io.StringIO()

            def reserve_failed(*_args, **_kwargs):
                failed_preview.parent.mkdir(parents=True, exist_ok=True)
                failed_preview.touch()
                return str(failed_preview)

            with patch.object(m3_entry.subprocess, "check_output", side_effect=reserve_failed), \
                    patch.object(m3_entry.subprocess, "call", return_value=1), \
                    contextlib.redirect_stdout(failed_stdout):
                self.assertEqual(m3_entry.run_locked(qmd, ["preview"]), 1)
            self.assertNotIn("PREVIEW_PATH=", failed_stdout.getvalue())
            self.assertFalse(failed_preview.exists())

            launch_error_preview = root / ".md-slide-tool" / "previews" / DOC / "preview-000003.pptx"
            launch_error_stdout = io.StringIO()

            def reserve_launch_error(*_args, **_kwargs):
                launch_error_preview.parent.mkdir(parents=True, exist_ok=True)
                launch_error_preview.touch()
                return str(launch_error_preview)

            with patch.object(m3_entry.subprocess, "check_output", side_effect=reserve_launch_error), \
                    patch.object(m3_entry.subprocess, "call", side_effect=OSError("Bash unavailable")), \
                    contextlib.redirect_stdout(launch_error_stdout):
                with self.assertRaisesRegex(OSError, "Bash unavailable"):
                    m3_entry.run_locked(qmd, ["preview"])
            self.assertFalse(launch_error_preview.exists())
            self.assertNotIn("PREVIEW_PATH=", launch_error_stdout.getvalue())

    def test_required_internal_status_labels_are_representable(self):
        self.assertEqual(PROBE_STATES, {
            "Rendering Preview", "Preview Ready", "Importing", "Applying QMD",
            "Pending", "Conflict", "Error",
        })

    def test_preview_paths_identity_and_canonical_untouched(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "資料 with spaces"
            root.mkdir()
            canonical, qmd, assets = make_deck(root)
            before = hashlib.sha256(canonical.read_bytes()).hexdigest()
            p1, g1 = allocate_preview(root, DOC)
            p2, g2 = allocate_preview(root, DOC)
            self.assertNotEqual(p1, p2)
            self.assertEqual((g1, g2), (1, 2))
            shutil.copy2(canonical, p1)
            mark_preview(p1, qmd, DOC, g1)
            props = read_custom_properties(p1)
            self.assertEqual(props["md-slide-tool.preview"], "1")
            self.assertEqual(props["md-slide-tool.preview-generation"], "1")
            self.assertEqual(props["md-slide-tool.preview-source-qmd"], str(qmd.resolve()))
            self.assertTrue(is_preview(p1))
            self.assertEqual(hashlib.sha256(canonical.read_bytes()).hexdigest(), before)
            # Preview cannot be selected as canonical input by marker; canonical has no marker.
            self.assertFalse(is_preview(canonical))
            with self.assertRaisesRegex(ValueError, "preview PPTX"):
                importer.create_import_candidate(p1, qmd, assets)

    def test_cleanup_keeps_canonical_open_dirty_and_unknown(self):
        with tempfile.TemporaryDirectory() as temp:
            canonical = Path(temp) / "presentation.pptx"
            self.assertEqual(cleanup_decision(canonical, canonical_path=canonical, is_open=False, is_dirty=False), "keep")
            preview = Path(temp) / "preview-000001.pptx"
            self.assertEqual(cleanup_decision(preview, canonical_path=canonical, is_open=True, is_dirty=False), "keep")
            self.assertEqual(cleanup_decision(preview, canonical_path=canonical, is_open=False, is_dirty=True), "keep")
            self.assertEqual(cleanup_decision(preview, canonical_path=canonical, is_open=None, is_dirty=None), "keep")
            self.assertEqual(cleanup_decision(preview, canonical_path=canonical, is_open=False, is_dirty=False), "delete-eligible")

    def test_import_candidate_capture_does_not_mutate_qmd_or_sidecars(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pptx, qmd, assets = make_deck(root)
            Image.new("RGB", (32, 24), "blue").save(root / "source.png")
            before = {p: p.read_bytes() for p in (qmd, assets, pptx)}
            candidate = importer.create_import_candidate(pptx, qmd, assets)
            self.assertIn(qmd.resolve(), candidate["outputs"])
            self.assertIn(assets.resolve(), candidate["outputs"])
            self.assertIn(pptx.resolve(), candidate["outputs"])
            imported_images = [p for p in candidate["outputs"] if "img" in p.parts and p.suffix == ".png"]
            self.assertEqual(len(imported_images), 1)
            self.assertTrue(candidate["outputs"][imported_images[0]])
            candidate_pptx = root / "candidate-metadata.pptx"
            candidate_pptx.write_bytes(candidate["outputs"][pptx.resolve()])
            self.assertEqual(read_custom_properties(candidate_pptx)["md-slide-tool.document-id"], DOC)
            self.assertIn("md-slide-tool.qmd-body-sha256", read_custom_properties(candidate_pptx))
            self.assertEqual(qmd.read_bytes(), before[qmd])
            self.assertEqual(assets.read_bytes(), before[assets])
            self.assertEqual(pptx.read_bytes(), before[pptx])
            self.assertNotEqual(candidate["outputs"][qmd.resolve()], before[qmd])

    def test_actual_filetransaction_failures_expose_editor_split_states(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pptx, qmd, assets = make_deck(root)
            Image.new("RGB", (32, 24), "blue").save(root / "source.png")
            candidate = importer.create_import_candidate(pptx, qmd, assets)
            outputs = candidate["outputs"]
            image_targets = [path for path in outputs if "img" in path.parts and outputs[path] is not None]
            targets = [assets.resolve(), pptx.resolve(), *image_targets]
            old = {path: path.read_bytes() if path.exists() else None for path in [qmd.resolve(), *targets]}
            qmd_candidate = outputs[qmd.resolve()]

            def reset_canonical_files():
                for path in [qmd.resolve(), *targets]:
                    prior = old[path]
                    if prior is None:
                        path.unlink(missing_ok=True)
                    else:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(prior)

            def new_transaction():
                tx = FileTransaction(root, DOC, txid="probe-split-state")
                for target in targets:
                    tx.stage(target, outputs[target])
                return tx

            # Case 1: VS Code already saved QMD; Core sidecar transaction fails
            # on its first replace and rolls all M3-owned outputs back.
            qmd.write_bytes(qmd_candidate)
            tx = new_transaction()
            with self.assertRaises(OSError):
                tx.commit(fail_after=1)
            self.assertEqual(qmd.read_bytes(), qmd_candidate)
            self.assertEqual(assets.read_bytes(), old[assets.resolve()])
            self.assertEqual(pptx.read_bytes(), old[pptx.resolve()])
            self.assertEqual(qmd.read_bytes(), qmd_candidate)  # Core rollback cannot undo editor save.

            # Reset QMD. Case 2: Core sidecars commit, then editor-mediated apply
            # rejects; QMD remains old while assets/PPTX/image outputs are new.
            reset_canonical_files()
            tx = new_transaction()
            tx.commit()
            self.assertEqual(qmd.read_bytes(), old[qmd.resolve()])
            self.assertEqual(assets.read_bytes(), outputs[assets.resolve()])
            self.assertEqual(pptx.read_bytes(), outputs[pptx.resolve()])
            if image_targets:
                self.assertEqual(image_targets[0].read_bytes(), outputs[image_targets[0]])

            # Case 3: editor QMD save succeeds; PPTX metadata operation fails
            # after replacement. Core transaction rolls back assets and PPTX.
            reset_canonical_files()
            qmd.write_bytes(qmd_candidate)
            tx = FileTransaction(root, DOC, txid="probe-split-state")
            tx.stage(assets, outputs[assets.resolve()])
            tx.stage(pptx, outputs[pptx.resolve()])
            with self.assertRaises(OSError):
                tx.commit(fail_after=2)
            self.assertEqual(qmd.read_bytes(), qmd_candidate)
            self.assertEqual(assets.read_bytes(), old[assets.resolve()])
            self.assertEqual(pptx.read_bytes(), old[pptx.resolve()])

            # Case 4: sidecars and editor QMD save succeed while an existing
            # checkpoint sentinel remains old. This branch has no checkpoint
            # writer, so the fixture does not claim an injected checkpoint failure.
            reset_canonical_files()
            checkpoint = root / ".md-slide-tool" / "checkpoint.json"
            checkpoint.parent.mkdir(parents=True, exist_ok=True)
            checkpoint.write_bytes(b"old-checkpoint")
            tx = new_transaction()
            tx.commit()
            qmd.write_bytes(qmd_candidate)
            self.assertEqual(qmd.read_bytes(), qmd_candidate)
            self.assertEqual(assets.read_bytes(), outputs[assets.resolve()])
            self.assertEqual(pptx.read_bytes(), outputs[pptx.resolve()])
            self.assertEqual(checkpoint.read_bytes(), b"old-checkpoint")


if __name__ == "__main__":
    unittest.main()
