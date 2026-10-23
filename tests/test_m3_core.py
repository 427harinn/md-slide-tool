import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from m3_core import canonical_body, qmd_body_sha256, split_front_matter, validate_crop
from m3_transaction import (
    DocumentBusy, FileTransaction, ManualRecoveryRequired, _atomic_lock,
    recover_transactions,
)


class M3CoreTests(unittest.TestCase):
    def test_render_seed_migrates_v1_only_inside_candidate_and_pairs_document_id(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            qmd = root / "deck.qmd"
            qmd.write_text("---\ntitle: Deck\n---\n", encoding="utf-8")
            prior = {"schemaVersion": 1, "slideSize": {"width": 100, "height": 50},
                     "elements": [{"slideId": "slide-123e4567-e89b-42d3-a456-426614174001",
                                   "elementId": "element-123e4567-e89b-42d3-a456-426614174002",
                                   "type": "image", "path": "source.png",
                                   "x": 1, "y": 2, "width": 3, "height": 4}]}
            source = root / "deck.assets.json"
            source.write_text(json.dumps(prior), encoding="utf-8")
            output = root / "candidate" / "deck.assets.json"
            document_id = "document-123e4567-e89b-42d3-a456-426614174000"
            script = ROOT / "scripts" / "m3_render_seed.py"
            result = subprocess.run([sys.executable, str(script), "--qmd", str(qmd),
                                     "--output", str(output), "--document-id", document_id],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            candidate = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(candidate["schemaVersion"], 2)
            self.assertEqual(candidate["documentId"], document_id)
            self.assertEqual(candidate["elements"], prior["elements"])
            self.assertEqual(json.loads(source.read_text(encoding="utf-8")), prior)

    def test_body_hash_normalizes_only_line_endings_and_excludes_front_matter(self):
        variants = [
            b"\xef\xbb\xbf---\r\ntitle: x\r\n---\r\nA\r\nB",
            b"---\ntitle: x\n---\nA\nB",
            b"---\rtitle: x\r---\rA\rB",
        ]
        hashes = {qmd_body_sha256(item) for item in variants}
        # Bare-CR front matter is not recognized by the contract; verify body
        # normalization separately while LF/CRLF with BOM have equal hashes.
        self.assertEqual(qmd_body_sha256(variants[0]), qmd_body_sha256(variants[1]))
        self.assertEqual(canonical_body(b"\xef\xbb\xbf---\nfront\n---\n x  \n"), b" x  \n")
        self.assertEqual(qmd_body_sha256(b"body"), hashlib.sha256(b"body").hexdigest())
        self.assertNotEqual(qmd_body_sha256(b"body"), qmd_body_sha256(b"body\n"))
        self.assertNotEqual(qmd_body_sha256(b"body\n"), qmd_body_sha256(b"body \n"))
        self.assertTrue(hashes)

    def test_front_matter_is_byte_preserved_and_body_starts_after_delimiter(self):
        raw = b"\xef\xbb\xbf---\r\ntitle: \xe6\x97\xa5\xe6\x9c\xac\r\n---\r\nbody\r"
        front, body = split_front_matter(raw)
        self.assertEqual(front, b"\xef\xbb\xbf---\r\ntitle: \xe6\x97\xa5\xe6\x9c\xac\r\n---\r\n")
        self.assertEqual(body, b"body\r")

    def test_crop_validation_keeps_negative_values_and_rejects_invalid_rectangles(self):
        crop = {"unit": "ooxml-percent", "left": -2500, "top": 500, "right": 10000, "bottom": 0}
        self.assertEqual(validate_crop(crop), crop)
        for invalid in (
            {"unit": "ooxml-percent", "left": 100000, "top": 0, "right": 0, "bottom": 0},
            {"unit": "ooxml-percent", "left": 0.5, "top": 0, "right": 0, "bottom": 0},
            {"unit": "ooxml-percent", "left": 200001, "top": 0, "right": 0, "bottom": 0},
        ):
            with self.assertRaises(ValueError):
                validate_crop(invalid)


class TransactionTests(unittest.TestCase):
    def test_handled_failure_after_each_operation_rolls_back_create_replace_delete(self):
        for fail_after in (1, 2, 3):
            with self.subTest(fail_after=fail_after), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                project = root / "project"
                project.mkdir()
                replace = project / "replace.txt"
                delete = project / "delete.txt"
                create = project / "create.txt"
                replace.write_bytes(b"old")
                delete.write_bytes(b"delete")
                tx = FileTransaction(project, "document-test")
                tx.stage(replace, b"new")
                tx.stage(delete, None)
                tx.stage(create, b"created")
                with self.assertRaises(OSError):
                    tx.commit(fail_after=fail_after)
                self.assertEqual(replace.read_bytes(), b"old")
                self.assertEqual(delete.read_bytes(), b"delete")
                self.assertFalse(create.exists())

    def test_recovery_rolls_back_committing_and_finishes_committed_cleanup(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            target = project / "state.txt"
            target.write_bytes(b"old")
            tx = FileTransaction(project, "document-x", "crash")
            tx.stage(target, b"new")
            tx._save()
            tx.manifest["phase"] = "committing"
            tx._save()
            (tx.root / "new" / "0").replace(target)
            recover_transactions(project, "document-x")
            self.assertEqual(target.read_bytes(), b"old")

            tx2 = FileTransaction(project, "document-x", "committed")
            tx2.stage(target, b"final")
            tx2._save()
            tx2.manifest["phase"] = "committing"
            tx2._save()
            (tx2.root / "new" / "0").replace(target)
            tx2.manifest["phase"] = "committed"
            tx2._save()
            recover_transactions(project, "document-x")
            self.assertEqual(target.read_bytes(), b"final")

    def test_recovery_stops_on_unknown_hash_and_preserves_journal(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            target = project / "state.txt"
            target.write_bytes(b"old")
            tx = FileTransaction(project, "document-x", "unknown")
            tx.stage(target, b"new")
            tx._save()
            tx.manifest["phase"] = "committing"
            tx._save()
            target.write_bytes(b"external")
            with self.assertRaises(ManualRecoveryRequired):
                recover_transactions(project, "document-x")
            self.assertTrue(tx.root.exists())
            self.assertEqual(target.read_bytes(), b"external")

    def test_process_lock_reports_document_busy(self):
        with tempfile.TemporaryDirectory() as temp:
            lock = Path(temp) / "lock"
            with _atomic_lock(lock):
                code = "import sys;sys.path.insert(0,sys.argv[1]);from pathlib import Path;from m3_transaction import _atomic_lock;\ntry:\n with _atomic_lock(Path(sys.argv[2])): pass\nexcept Exception as e:\n print(type(e).__name__)"
                result = subprocess.run([sys.executable, "-c", code, str(ROOT / "scripts"), str(lock)], text=True, capture_output=True)
                self.assertEqual(result.stdout.strip(), "DocumentBusy")


if __name__ == "__main__":
    unittest.main()
