"""Contract fixture for the required M4 journal-first startup order.

This is a probe harness only; the repository has no M4 startup coordinator.
"""
import unittest


def probe_journal_first_startup(*, journal_phase, checkpoint_bytes):
    events = []
    checkpoint = {"bytes": checkpoint_bytes}

    events.append("journal-check")
    if journal_phase is not None:
        events.append("pair-freeze")
        events.append("recover")
        journal_phase = None
    events.append("checkpoint-reread")
    checkpoint_read = checkpoint["bytes"]
    events.append("fingerprints-reread")
    fingerprints = {"qmd": b"qmd-after-recovery", "pptx": b"pptx-after-recovery"}
    events.append("pair-evaluation")
    decision = "render" if checkpoint_read != fingerprints["qmd"] else "idle"
    return {"events": events, "decision": decision, "checkpoint": checkpoint_read, "journalPhase": journal_phase}


class JournalFirstProbeTests(unittest.TestCase):
    def test_new_checkpoint_is_not_interpreted_before_committing_journal_recovery(self):
        result = probe_journal_first_startup(journal_phase="committing", checkpoint_bytes=b"new bytes")
        self.assertEqual(result["events"], [
            "journal-check", "pair-freeze", "recover", "checkpoint-reread",
            "fingerprints-reread", "pair-evaluation",
        ])
        self.assertEqual(result["checkpoint"], b"new bytes")
        self.assertEqual(result["journalPhase"], None)
        self.assertEqual(result["decision"], "render")

    def test_no_journal_does_not_create_pair_freeze(self):
        result = probe_journal_first_startup(journal_phase=None, checkpoint_bytes=b"stable")
        self.assertEqual(result["events"], [
            "journal-check", "checkpoint-reread", "fingerprints-reread", "pair-evaluation",
        ])


if __name__ == "__main__":
    unittest.main()
