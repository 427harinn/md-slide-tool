#!/usr/bin/env python3
"""M3 per-document locks and recoverable file transactions.

All persistent writes performed by render/import are expected to run while the
document lock returned by ``acquire_document_lock`` is held.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Callable


class DocumentBusy(RuntimeError):
    pass


class ManualRecoveryRequired(RuntimeError):
    pass


def canonical_qmd(path: Path) -> Path:
    # strict=False resolves dot segments and normalizes the runtime's absolute
    # path without requiring the QMD to exist yet.
    return path.expanduser().resolve(strict=False)


def bootstrap_key(qmd_path: Path) -> str:
    canonical = os.path.normcase(str(canonical_qmd(qmd_path)))
    return hashlib.sha256(os.fsencode(canonical)).hexdigest()


@contextlib.contextmanager
def _atomic_lock(lock_path: Path):
    """Acquire a kernel-owned advisory lock (released on process death)."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    stream = lock_path.open("a+b")
    try:
        if os.name == "nt":
            import msvcrt
            try:
                stream.seek(0, os.SEEK_END)
                if stream.tell() == 0:
                    stream.write(b"\0")
                    stream.flush()
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise DocumentBusy("DOCUMENT_BUSY") from exc
        else:
            import fcntl
            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise DocumentBusy("DOCUMENT_BUSY") from exc
        stream.seek(0)
        stream.truncate()
        stream.write(json.dumps({"pid": os.getpid(), "path": str(lock_path)}).encode())
        stream.flush()
        os.fsync(stream.fileno())
        yield stream
    finally:
        try:
            if os.name == "nt":
                import msvcrt
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        stream.close()


@contextlib.contextmanager
def acquire_document_lock(
    project_dir: Path, qmd_path: Path, document_id: str | None,
    migrate: Callable[[], str] | None = None,
):
    """Acquire the normal lock, or bootstrap and hand off without an unlock gap.

    ``migrate`` runs under bootstrap ownership and must complete the schema v2
    and PPTX package migration before returning a document id.
    """
    locks = project_dir / ".md-slide-tool" / "locks"
    if document_id:
        with _atomic_lock(locks / "document" / document_id / "owner.lock"):
            yield document_id
        return

    bootstrap = locks / "bootstrap" / bootstrap_key(qmd_path) / "owner.lock"
    with _atomic_lock(bootstrap):
        # Migration callback must reread state and return the canonical id.
        current_id = migrate() if migrate else None
        if not current_id:
            raise ValueError("bootstrap migration did not return a document id")
        # Important: document lock acquisition precedes bootstrap release.
        with _atomic_lock(locks / "document" / current_id / "owner.lock"):
            yield current_id


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_durable(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _atomic_replace(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    os.replace(source, target)


class FileTransaction:
    """Recoverable create/replace/delete transaction with hash guarded rollback."""

    def __init__(self, project_dir: Path, document_id: str, txid: str | None = None,
                 paired_qmd_path: Path | None = None):
        self.project_dir = project_dir.resolve(strict=False)
        self.root = project_dir / ".md-slide-tool" / "transactions" / document_id / (txid or str(uuid.uuid4()))
        self.manifest_path = self.root / "manifest.json"
        self.paired_qmd_path = canonical_qmd(paired_qmd_path) if paired_qmd_path else None
        self.owner_key = bootstrap_key(self.paired_qmd_path) if self.paired_qmd_path else None
        self.manifest: dict = {"version": 1, "phase": "prepared", "operations": []}
        if self.paired_qmd_path is not None:
            self.manifest["pairedQmd"] = str(self.paired_qmd_path)
            self.manifest["ownerKey"] = self.owner_key

    def stage(self, target: Path, new_bytes: bytes | None) -> None:
        target = target.resolve(strict=False)
        if not target.is_relative_to(self.project_dir):
            raise ValueError(f"transaction target escapes project directory: {target}")
        # Establish a recoverable prepared journal before materializing any
        # transaction blobs. A crash during staging then leaves a valid empty
        # or partial prepared transaction that recovery can safely discard.
        if not self.manifest_path.exists():
            self._save()
        index = len(self.manifest["operations"])
        old_hash = sha256_file(target)
        if new_bytes is None:
            operation = "delete"
            new_hash = None
        else:
            operation = "replace" if old_hash is not None else "create"
            new_hash = hashlib.sha256(new_bytes).hexdigest()
            _write_durable(self.root / "new" / str(index), new_bytes)
        if old_hash is not None:
            _write_durable(self.root / "old" / str(index), target.read_bytes())
        self.manifest["operations"].append({
            "target": str(target), "operation": operation, "existed": old_hash is not None,
            "oldHash": old_hash, "newHash": new_hash,
        })
        self._save()

    def _save(self) -> None:
        data = (json.dumps(self.manifest, indent=2) + "\n").encode()
        if not self.root.exists():
            # Publish a complete initial journal directory in one rename.
            # No observable transaction root can exist without its manifest.
            self.root.parent.mkdir(parents=True, exist_ok=True)
            owner_suffix = f"{self.owner_key}." if self.owner_key else "unowned."
            initial = Path(tempfile.mkdtemp(prefix=f".{self.root.name}.init.{owner_suffix}", dir=self.root.parent))
            try:
                _write_durable(initial / "manifest.json", data)
                os.replace(initial, self.root)
            finally:
                if initial.exists():
                    shutil.rmtree(initial, ignore_errors=True)
            return
        temp = self.root / f"manifest.{uuid.uuid4().hex}.tmp"
        _write_durable(temp, data)
        os.replace(temp, self.manifest_path)

    def commit(self, fail_after: int | None = None) -> None:
        self._save()
        self.manifest["phase"] = "committing"
        self._save()
        try:
            for index, op in enumerate(self.manifest["operations"]):
                target = Path(op["target"])
                if op["operation"] == "delete":
                    target.unlink(missing_ok=True)
                else:
                    staged = self.root / "new" / str(index)
                    _atomic_replace(staged, target)
                if fail_after is not None and index + 1 == fail_after:
                    raise OSError("injected commit failure")
            self._verify_new()
            self.manifest["phase"] = "committed"
            self._save()
            shutil.rmtree(self.root, ignore_errors=True)
        except BaseException:
            self.manifest["phase"] = "rolling_back"
            self._save()
            rollback(self.root, self.manifest)
            self.manifest["phase"] = "rolled_back"
            self._save()
            shutil.rmtree(self.root, ignore_errors=True)
            raise

    def _verify_new(self):
        for op in self.manifest["operations"]:
            actual = sha256_file(Path(op["target"]))
            if actual != op["newHash"]:
                raise ManualRecoveryRequired(f"transaction target has unknown hash: {op['target']}")


def rollback(root: Path, manifest: dict) -> None:
    for index, op in reversed(list(enumerate(manifest["operations"]))):
        target = Path(op["target"])
        current = sha256_file(target)
        if current not in (op["oldHash"], op["newHash"]):
            raise ManualRecoveryRequired(f"unknown post-crash file state: {target}")
        if op["existed"]:
            if current == op["oldHash"]:
                continue
            old = root / "old" / str(index)
            if sha256_file(old) != op["oldHash"]:
                raise ManualRecoveryRequired(f"transaction backup is missing or corrupt: {target}")
            _atomic_replace(old, target)
        elif current == op["newHash"]:
            target.unlink()


def _validated_operations(project_dir: Path, manifest: dict) -> list[dict]:
    """Validate journal targets before recovery reads, replaces, or deletes them.

    The manifest is durable but may have been edited or corrupted outside this
    process. Never let recovery use it as authority to touch paths outside the
    project tree (including paths escaping through a symlinked parent).
    """
    if not isinstance(manifest, dict) or manifest.get("version") != 1:
        raise ManualRecoveryRequired("unknown transaction manifest version")
    operations = manifest.get("operations")
    if not isinstance(operations, list):
        raise ManualRecoveryRequired("corrupt transaction operations")
    root = project_dir.resolve(strict=False)
    validated = []
    seen = set()
    for op in operations:
        if not isinstance(op, dict) or not isinstance(op.get("target"), str):
            raise ManualRecoveryRequired("corrupt transaction target")
        raw_target = Path(op["target"])
        if not raw_target.is_absolute():
            raise ManualRecoveryRequired("transaction target is not absolute")
        target = raw_target.resolve(strict=False)
        if not target.is_relative_to(root):
            raise ManualRecoveryRequired(f"transaction target escapes project directory: {raw_target}")
        if target in seen:
            raise ManualRecoveryRequired(f"duplicate transaction target: {target}")
        seen.add(target)
        operation = op.get("operation")
        existed = op.get("existed")
        old_hash, new_hash = op.get("oldHash"), op.get("newHash")
        if operation not in ("create", "replace", "delete") or type(existed) is not bool:
            raise ManualRecoveryRequired(f"corrupt transaction operation: {target}")
        if old_hash is not None and (not isinstance(old_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", old_hash)):
            raise ManualRecoveryRequired(f"corrupt old hash: {target}")
        if new_hash is not None and (not isinstance(new_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", new_hash)):
            raise ManualRecoveryRequired(f"corrupt new hash: {target}")
        if (existed != (old_hash is not None) or
                (operation == "create" and (existed or new_hash is None)) or
                (operation == "replace" and (not existed or new_hash is None)) or
                (operation == "delete" and (not existed or new_hash is not None))):
            raise ManualRecoveryRequired(f"inconsistent transaction operation: {target}")
        normalized = dict(op)
        normalized["target"] = str(target)
        validated.append(normalized)
    return validated


def recover_transactions(project_dir: Path, document_id: str,
                         paired_qmd_path: Path | None = None) -> None:
    base = project_dir / ".md-slide-tool" / "transactions" / document_id
    if not base.exists():
        return
    requested_qmd = canonical_qmd(paired_qmd_path) if paired_qmd_path else None
    for tx in sorted(base.iterdir()):
        if tx.name.startswith(".") and ".init." in tx.name:
            # Initial journal directories are atomically renamed into their
            # final txid only after manifest.json is durable. Any leftover
            # .init directory therefore cannot have staged target mutations.
            if requested_qmd is not None:
                owner_key = bootstrap_key(requested_qmd)
                if f".init.{owner_key}." not in tx.name:
                    continue
            shutil.rmtree(tx, ignore_errors=True)
            continue
        manifest_path = tx / "manifest.json"
        if not manifest_path.exists():
            raise ManualRecoveryRequired(f"transaction manifest is missing: {tx}")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ManualRecoveryRequired(f"corrupt transaction manifest: {manifest_path}") from exc
        if requested_qmd is not None:
            paired_owner = manifest.get("pairedQmd")
            owner_key = manifest.get("ownerKey")
            if paired_owner is not None:
                try:
                    paired_owner = str(canonical_qmd(Path(paired_owner)))
                except (TypeError, ValueError, OSError):
                    raise ManualRecoveryRequired(f"invalid paired QMD owner: {manifest_path}")
                if paired_owner != str(requested_qmd) or owner_key != bootstrap_key(requested_qmd):
                    continue
            else:
                # Compatibility for complete pre-owner journals only: target
                # matching is deterministic and the document lock is held.
                paired = {requested_qmd, requested_qmd.with_suffix(".pptx"),
                          requested_qmd.with_name(requested_qmd.stem + ".assets.json")}
                raw_ops = manifest.get("operations", [])
                if not any(isinstance(op, dict) and isinstance(op.get("target"), str) and
                           Path(op["target"]).resolve(strict=False) in paired for op in raw_ops):
                    continue
        # Validate all targets before even reading their hashes, so no phase
        # can use a tampered journal to inspect or mutate an external file.
        manifest["operations"] = _validated_operations(project_dir, manifest)
        phase = manifest.get("phase")
        if phase == "prepared":
            for op in manifest["operations"]:
                if sha256_file(Path(op["target"])) != op["oldHash"]:
                    raise ManualRecoveryRequired(f"prepared transaction target changed: {op['target']}")
        elif phase in ("committing", "rolling_back"):
            rollback(tx, manifest)
        elif phase == "committed":
            for op in manifest["operations"]:
                if sha256_file(Path(op["target"])) != op["newHash"]:
                    raise ManualRecoveryRequired(f"committed transaction target changed: {op['target']}")
        elif phase == "rolled_back":
            for op in manifest["operations"]:
                if sha256_file(Path(op["target"])) != op["oldHash"]:
                    raise ManualRecoveryRequired(f"rolled back transaction target changed: {op['target']}")
        else:
            raise ManualRecoveryRequired(f"unknown transaction phase: {phase}")
        shutil.rmtree(tx)
    try:
        base.rmdir()
    except OSError:
        pass


def recover_bootstrap_transactions(project_dir: Path, qmd_path: Path) -> None:
    """Recover interrupted first-render transactions while bootstrap is held.

    Before the first PPTX replacement neither final asset nor PPTX may contain
    the chosen document ID. Discover only journals with durable ownership of
    this canonical QMD (or complete legacy journals with matching paired
    targets), then take that journal's document lock before recovery. Init
    directory names carry the QMD key so an interrupted pre-manifest journal
    can be cleaned without sweeping another concurrent first render.
    """
    from m3_core import valid_document_id

    project_dir = project_dir.resolve(strict=False)
    qmd_path = canonical_qmd(qmd_path)
    requested_owner = bootstrap_key(qmd_path)
    pair = {qmd_path, qmd_path.with_suffix(".pptx").resolve(strict=False),
            qmd_path.with_name(qmd_path.stem + ".assets.json").resolve(strict=False)}
    transaction_root = project_dir / ".md-slide-tool" / "transactions"
    if not transaction_root.exists():
        return
    for doc_dir in sorted(transaction_root.iterdir()):
        if not doc_dir.is_dir() or not valid_document_id(doc_dir.name):
            continue
        for tx in sorted(doc_dir.iterdir()):
            if tx.name.startswith(".") and ".init." in tx.name:
                # Init dirs can be live in another concurrent first render.
                # Their encoded owner is durable before any manifest exists;
                # unknown/unowned directories are never swept here.
                if f".init.{requested_owner}." not in tx.name:
                    continue
                lock_path = project_dir / ".md-slide-tool" / "locks" / "document" / doc_dir.name / "owner.lock"
                with _atomic_lock(lock_path):
                    shutil.rmtree(tx, ignore_errors=True)
                continue
            manifest_path = tx / "manifest.json"
            if not manifest_path.is_file():
                continue
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                operations = manifest.get("operations", [])
                owner_matches = (manifest.get("pairedQmd") == str(qmd_path) and
                                 manifest.get("ownerKey") == requested_owner)
                legacy_matches = any(
                    isinstance(op, dict) and isinstance(op.get("target"), str) and
                    Path(op["target"]).resolve(strict=False) in pair
                    for op in operations
                )
            except (OSError, json.JSONDecodeError, TypeError):
                raise ManualRecoveryRequired(f"corrupt bootstrap transaction manifest: {manifest_path}")
            if not owner_matches and not legacy_matches:
                continue
            lock_path = project_dir / ".md-slide-tool" / "locks" / "document" / doc_dir.name / "owner.lock"
            with _atomic_lock(lock_path):
                recover_transactions(project_dir, doc_dir.name, qmd_path)
