import contextlib
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import m3_transaction
from m3_transaction import FileTransaction, recover_transactions


def digest(path: Path):
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ProbeBroker:
    """Temporary mutation interception used only by T-401 transaction fixtures."""

    def __init__(self, targets):
        self.targets = {Path(target).resolve() for target in targets}
        self.results = []
        self.original_replace = m3_transaction._atomic_replace

    def replace(self, source: Path, target: Path):
        target = Path(target).resolve()
        if target not in self.targets:
            return self.original_replace(source, target)
        expected_old = digest(target)
        expected_new = digest(Path(source))
        if expected_new is None:
            raise AssertionError("broker source is missing")
        os.replace(source, target)
        resulting = digest(target)
        status = "MUTATED" if resulting == expected_new else "UNKNOWN"
        self.results.append({
            "documentId": "t401-document",
            "freezeSessionId": "fixture-session",
            "transactionId": "fixture-transaction",
            "operationIndex": len(self.results),
            "target": str(target),
            "expectedOldHash": expected_old,
            "stagedSource": str(source),
            "resultingHash": resulting,
            "status": status,
        })

    @contextlib.contextmanager
    def installed(self):
        original_unlink = Path.unlink

        def unlink(path, *args, **kwargs):
            target = Path(path).resolve()
            if target not in self.targets:
                return original_unlink(path, *args, **kwargs)
            expected_old = digest(target)
            missing_ok = kwargs.get("missing_ok", False)
            try:
                result = original_unlink(path, *args, **kwargs)
            except FileNotFoundError:
                if missing_ok:
                    return None
                raise
            self.results.append({
                "documentId": "t401-document",
                "freezeSessionId": "fixture-session",
                "transactionId": "fixture-transaction",
                "operationIndex": len(self.results),
                "target": str(target),
                "expectedOldHash": expected_old,
                "expectedAbsence": False,
                "resultingHash": None,
                "status": "MUTATED",
                "operation": "delete",
            })
            return result

        with patch.object(m3_transaction, "_atomic_replace", side_effect=self.replace), patch.object(Path, "unlink", new=unlink):
            yield self.results


class BrokerTransactionProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.project = Path(self.temp.name)
        self.document_id = "document-t401"

    def tearDown(self):
        self.temp.cleanup()

    def test_commit_failure_rolls_back_through_same_injected_broker(self):
        first = self.project / "one.qmd"
        second = self.project / "two.pptx"
        first.write_bytes(b"old-qmd")
        second.write_bytes(b"old-pptx")
        tx = FileTransaction(self.project, self.document_id)
        tx.stage(first, b"new-qmd")
        tx.stage(second, b"new-pptx")
        broker = ProbeBroker([first, second])
        with broker.installed():
            with self.assertRaisesRegex(OSError, "injected commit failure"):
                tx.commit(fail_after=1)
        self.assertEqual(first.read_bytes(), b"old-qmd")
        self.assertEqual(second.read_bytes(), b"old-pptx")
        self.assertEqual([item["status"] for item in broker.results], ["MUTATED", "MUTATED"])
        self.assertEqual(broker.results[0]["resultingHash"], hashlib.sha256(b"new-qmd").hexdigest())
        self.assertEqual(broker.results[1]["resultingHash"], hashlib.sha256(b"old-qmd").hexdigest())

    def test_create_replace_and_delete_operations_share_broker_hook(self):
        created = self.project / "created.qmd"
        replaced = self.project / "replaced.qmd"
        deleted = self.project / "deleted.pptx"
        replaced.write_bytes(b"old")
        deleted.write_bytes(b"remove")
        tx = FileTransaction(self.project, self.document_id)
        tx.stage(created, b"create")
        tx.stage(replaced, b"replace")
        tx.stage(deleted, None)
        broker = ProbeBroker([created, replaced, deleted])
        with broker.installed():
            tx.commit()
        self.assertEqual(created.read_bytes(), b"create")
        self.assertEqual(replaced.read_bytes(), b"replace")
        self.assertFalse(deleted.exists())
        self.assertEqual([item.get("operation", "replace") for item in broker.results], ["replace", "replace", "delete"])
        self.assertTrue(all(item["status"] == "MUTATED" for item in broker.results))

    def test_committing_and_rolling_back_recovery_use_the_same_replace_hook(self):
        target = self.project / "slides.qmd"
        target.write_bytes(b"old")
        tx = FileTransaction(self.project, self.document_id)
        tx.stage(target, b"new")
        tx._save()
        tx.manifest["phase"] = "committing"
        tx._save()
        os.replace(tx.root / "new" / "0", target)
        broker = ProbeBroker([target])
        with broker.installed():
            recover_transactions(self.project, self.document_id)
        self.assertEqual(target.read_bytes(), b"old")
        self.assertEqual(len(broker.results), 1)
        self.assertEqual(broker.results[0]["resultingHash"], hashlib.sha256(b"old").hexdigest())

    def test_final_replace_before_committed_marker_is_not_inferred_as_success(self):
        target = self.project / "slides.qmd"
        target.write_bytes(b"old")
        tx = FileTransaction(self.project, self.document_id)
        tx.stage(target, b"new")
        tx._save()
        tx.manifest["phase"] = "committing"
        tx._save()
        os.replace(tx.root / "new" / "0", target)
        journal = json.loads(tx.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(journal["phase"], "committing")
        self.assertEqual(digest(target), journal["operations"][0]["newHash"])
        with ProbeBroker([target]).installed():
            recover_transactions(self.project, self.document_id)
        self.assertEqual(target.read_bytes(), b"old")

    def test_current_m3_catches_transaction_suspended_and_rolls_back(self):
        target = self.project / "slides.qmd"
        target.write_bytes(b"old")
        tx = FileTransaction(self.project, self.document_id)
        tx.stage(target, b"new")

        class TransactionSuspended(BaseException):
            pass

        broker = ProbeBroker([target])
        with broker.installed():
            with patch.object(FileTransaction, "_verify_new", side_effect=TransactionSuspended()):
                with self.assertRaises(TransactionSuspended):
                    tx.commit()
        self.assertEqual(target.read_bytes(), b"old")
        self.assertFalse(tx.root.exists())

    def test_suspend_before_second_operation_is_caught_and_immediately_rolled_back(self):
        first = self.project / "one.qmd"
        second = self.project / "two.pptx"
        first.write_bytes(b"old-one")
        second.write_bytes(b"old-two")
        tx = FileTransaction(self.project, self.document_id)
        tx.stage(first, b"new-one")
        tx.stage(second, b"new-two")

        class TransactionSuspended(BaseException):
            pass

        broker = ProbeBroker([first, second])
        real_replace = m3_transaction._atomic_replace
        calls = 0

        def suspend_on_second(source, target):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise TransactionSuspended()
            return real_replace(source, target)

        with broker.installed(), patch.object(m3_transaction, "_atomic_replace", side_effect=suspend_on_second):
            with self.assertRaises(TransactionSuspended):
                tx.commit()
        self.assertEqual(first.read_bytes(), b"old-one")
        self.assertEqual(second.read_bytes(), b"old-two")
        self.assertFalse(tx.root.exists())

    def test_suspend_during_rollback_preserves_rolling_back_journal_for_recovery(self):
        first = self.project / "one.qmd"
        second = self.project / "two.pptx"
        first.write_bytes(b"old-one")
        second.write_bytes(b"old-two")
        tx = FileTransaction(self.project, self.document_id)
        tx.stage(first, b"new-one")
        tx.stage(second, b"new-two")

        class TransactionSuspended(BaseException):
            pass

        broker = ProbeBroker([first, second])
        real_replace = m3_transaction._atomic_replace

        def suspend_when_restoring_backup(source, target):
            if Path(source) == tx.root / "old" / "0":
                raise TransactionSuspended()
            return real_replace(source, target)

        with broker.installed(), patch.object(m3_transaction, "_atomic_replace", side_effect=suspend_when_restoring_backup):
            with self.assertRaises(TransactionSuspended):
                tx.commit(fail_after=1)
        journal = json.loads(tx.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(journal["phase"], "rolling_back")
        self.assertEqual(first.read_bytes(), b"new-one")
        self.assertEqual(second.read_bytes(), b"old-two")

        with broker.installed():
            recover_transactions(self.project, self.document_id)
        self.assertEqual(first.read_bytes(), b"old-one")
        self.assertEqual(second.read_bytes(), b"old-two")
        self.assertFalse(tx.root.exists())

    def test_rolling_back_recovery_routes_create_replace_and_delete_through_hook(self):
        created = self.project / "created.qmd"
        replaced = self.project / "replaced.qmd"
        deleted = self.project / "deleted.pptx"
        replaced.write_bytes(b"old-replaced")
        deleted.write_bytes(b"old-deleted")
        tx = FileTransaction(self.project, self.document_id)
        tx.stage(created, b"new-created")
        tx.stage(replaced, b"new-replaced")
        tx.stage(deleted, None)
        tx.manifest["phase"] = "rolling_back"
        tx._save()
        os.replace(tx.root / "new" / "0", created)
        os.replace(tx.root / "new" / "1", replaced)
        deleted.unlink()

        broker = ProbeBroker([created, replaced, deleted])
        with broker.installed():
            recover_transactions(self.project, self.document_id)
        self.assertFalse(created.exists())
        self.assertEqual(replaced.read_bytes(), b"old-replaced")
        self.assertEqual(deleted.read_bytes(), b"old-deleted")
        self.assertEqual(
            [item.get("operation", "replace") for item in broker.results],
            ["replace", "replace", "delete"],
        )


if __name__ == "__main__":
    unittest.main()
