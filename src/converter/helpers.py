"""Shared conversion helpers: result object, path building, encoding utilities."""

from __future__ import annotations

import base64
import os
import stat
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path


class ConversionResult:
    __slots__ = ("success", "source", "target", "elapsed", "error", "file_size", "engine_used", "degraded")

    def __init__(self, success, source, target, elapsed=0.0, error="", file_size=0, engine_used="", degraded=False):
        self.success = success
        self.source = source
        self.target = target
        self.elapsed = elapsed
        self.error = error
        self.file_size = file_size
        self.engine_used = engine_used
        self.degraded = degraded

    def __repr__(self):
        s = "OK" if self.success else f"ERR({self.error})"
        engine = f" [{self.engine_used}]" if self.engine_used else ""
        return f"<ConversionResult {s}{engine} {self.source!r}→{self.target!r}>"



def _build_dst(src, dst_dir, new_ext):
    return str(Path(dst_dir) / f"{Path(src).stem}.{new_ext.lstrip('.')}")


def _img_to_b64(data, mime="image/png"):
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


def _mime_for_ext(ext):
    return {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
        "svg": "image/svg+xml",
        "bmp": "image/bmp",
        "tiff": "image/tiff",
    }.get(ext.lower(), "image/png")


def _safe_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class BackupError(RuntimeError):
    """A backup policy or source-preparation failure that blocks the operation."""

    def __init__(self, message: str, result: "SourceBackupResult | None" = None) -> None:
        super().__init__(message)
        self.result = result


@dataclass(frozen=True)
class SourceBackupResult:
    """Outcome of preparing source backups for one operation.

    ``backups`` maps each source path to its created backup path.
    ``errors`` maps each failed source path to a human-readable reason.
    """

    success: bool
    backups: dict[str, str]
    errors: dict[str, str]
    cleanup_errors: dict[str, str] = field(default_factory=dict)
    enabled: bool = True


def _source_backup_error(src: str) -> str:
    try:
        source_stat = os.stat(src)
    except FileNotFoundError:
        return "source does not exist"
    except (OSError, ValueError) as exc:
        return f"source is inaccessible: {exc}"

    if not stat.S_ISREG(source_stat.st_mode):
        return "source is not a file"

    try:
        with open(src, "rb"):
            pass
    except OSError as exc:
        return f"source is unreadable: {exc}"
    return ""


@dataclass(frozen=True)
class _BackupOutcome:
    path: str | None
    error: str = ""
    cleanup_error: str = ""


def _remove_backup_temp(path: str) -> str:
    try:
        os.unlink(path)
    except FileNotFoundError:
        return ""
    except OSError as exc:
        return str(exc)
    return ""


def _copy_with_metadata(src: str, dst: str) -> None:
    import shutil

    with open(src, "rb") as src_file, open(dst, "wb") as dst_file:
        shutil.copyfileobj(src_file, dst_file)
    shutil.copystat(src, dst)


def _publish_exclusive(temp_path: str, final_path: str) -> bool:
    """Publish a completed temp file without overwriting an existing path.

    Windows rename is atomic and fails when the destination exists. POSIX
    hard-link creation is atomic with the same no-clobber guarantee. The
    return value indicates whether the temporary path was consumed.
    """
    if os.name == "nt":
        os.rename(temp_path, final_path)
        return True
    os.link(temp_path, final_path)
    return False


def _create_backup_atomic(
    src: str,
    suffix: str,
    overwrite: bool,
    copy_file=None,
) -> _BackupOutcome:
    if not os.path.isfile(src):
        return _BackupOutcome(None, "source is not a file")
    if copy_file is None:
        copy_file = _copy_with_metadata

    parent = os.path.dirname(os.path.abspath(src))
    try:
        fd, temp_path = tempfile.mkstemp(prefix=".fcp_backup_", suffix=".tmp", dir=parent)
        os.close(fd)
    except OSError as exc:
        return _BackupOutcome(None, f"temporary file creation failed: {exc}")

    try:
        copy_file(src, temp_path)
    except Exception as exc:
        cleanup_error = _remove_backup_temp(temp_path)
        return _BackupOutcome(None, str(exc), cleanup_error)

    if overwrite:
        final_path = f"{src}{suffix}"
        try:
            os.replace(temp_path, final_path)
        except Exception as exc:
            cleanup_error = _remove_backup_temp(temp_path)
            return _BackupOutcome(None, str(exc), cleanup_error)
        return _BackupOutcome(final_path)

    counter = 0
    while True:
        final_path = f"{src}{suffix}" if counter == 0 else f"{src}{suffix}.{counter}"
        try:
            temp_consumed = _publish_exclusive(temp_path, final_path)
        except FileExistsError:
            counter += 1
            continue
        except OSError as exc:
            if os.path.lexists(final_path):
                counter += 1
                continue
            cleanup_error = _remove_backup_temp(temp_path)
            return _BackupOutcome(None, str(exc), cleanup_error)
        except Exception as exc:
            cleanup_error = _remove_backup_temp(temp_path)
            return _BackupOutcome(None, str(exc), cleanup_error)

        if temp_consumed:
            return _BackupOutcome(final_path)
        cleanup_error = _remove_backup_temp(temp_path)
        return _BackupOutcome(final_path, "", cleanup_error)


def _report_backup_outcome(src: str, outcome: _BackupOutcome) -> None:
    if outcome.error:
        print(f"[BACKUP] Could not create backup for {src}: {outcome.error}")
    if outcome.cleanup_error:
        print(f"[BACKUP] Could not remove temporary backup file: {outcome.cleanup_error}")


def _create_backup_exclusive(src: str, suffix: str) -> str | None:
    outcome = _create_backup_atomic(src, suffix, overwrite=False)
    _report_backup_outcome(src, outcome)
    return outcome.path


def create_backup(src: str, suffix: str = ".bak", overwrite: bool = True) -> str | None:
    """
    Create a backup copy of *src* with the given suffix appended.
    Returns the backup path, or None if the source doesn't exist or copy fails.
    Both modes copy to a same-directory temporary file and publish only after
    the copy completes. Exclusive mode never replaces an existing backup.
    """
    import shutil

    if not os.path.isfile(src):
        return None
    if overwrite:
        outcome = _create_backup_atomic(src, suffix, overwrite=True, copy_file=shutil.copy2)
    else:
        outcome = _create_backup_atomic(src, suffix, overwrite=False, copy_file=_copy_with_metadata)
    _report_backup_outcome(src, outcome)
    return outcome.path


def _validate_backup_suffix(suffix: str) -> None:
    if not isinstance(suffix, str) or not suffix:
        raise ValueError("backup suffix must be a non-empty string")
    if not suffix.startswith("."):
        raise ValueError("backup suffix must start with '.'")
    if any(character in suffix for character in ("/", "\\", "\0")):
        raise ValueError("backup suffix must not contain path separators or NUL characters")


def prepare_source_backups(
    sources: Iterable[str | os.PathLike[str]],
    *,
    suffix: str = ".bak",
) -> SourceBackupResult:
    """Create one exclusive backup for each unique source path.

    Sources are deduplicated by normalized real path. A failed aliased source
    does not prevent a later alias of the same real path from being tried.
    Missing, non-file, unreadable, or otherwise unbackupable sources are
    reported individually; remaining sources are still attempted. Existing
    backups are never overwritten.
    """
    _validate_backup_suffix(suffix)

    backups: dict[str, str] = {}
    errors: dict[str, str] = {}
    cleanup_errors: dict[str, str] = {}
    successful_keys: set[str] = set()
    failure_details: dict[str, tuple[str, str]] = {}
    unkeyed_errors: dict[str, str] = {}

    for raw_source in sources:
        try:
            source = os.fsdecode(os.fspath(raw_source))
            dedupe_key = os.path.normcase(os.path.realpath(source))
        except Exception as exc:
            unkeyed_errors[str(raw_source)] = f"invalid source path: {exc}"
            continue

        if dedupe_key in successful_keys:
            continue

        reason = _source_backup_error(source)
        if reason:
            failure_details.setdefault(dedupe_key, (source, reason))
            continue

        outcome = _create_backup_atomic(source, suffix, overwrite=False)
        if outcome.path is None:
            detail = outcome.error or "backup creation failed"
            if outcome.cleanup_error:
                detail = f"{detail}; temporary cleanup failed: {outcome.cleanup_error}"
            failure_details.setdefault(dedupe_key, (source, detail))
            continue

        backups[source] = outcome.path
        successful_keys.add(dedupe_key)
        failure_details.pop(dedupe_key, None)
        if outcome.cleanup_error:
            cleanup_errors[source] = outcome.cleanup_error

    errors.update(unkeyed_errors)
    for failure_source, reason in failure_details.values():
        errors[failure_source] = reason

    return SourceBackupResult(
        success=not errors,
        backups=backups,
        errors=errors,
        cleanup_errors=cleanup_errors,
    )


def _load_operation_config() -> dict:
    try:
        from config import ConfigManager
    except Exception as exc:
        raise BackupError(f"Backup configuration unavailable: {exc}") from exc

    manager = ConfigManager()
    try:
        loader = getattr(manager, "load_config_strict", None)
        config = loader() if loader is not None else manager.load_config()
    except Exception as exc:
        raise BackupError(f"Backup configuration unavailable: {exc}") from exc
    if not isinstance(config, dict):
        raise BackupError("Backup configuration is not a mapping")
    return config


def _enabled_from_config(config: dict) -> bool:
    if "backup_before_conversion" not in config:
        raise BackupError("Backup policy is missing from the configuration")
    value = config["backup_before_conversion"]
    if not isinstance(value, bool):
        raise BackupError("Backup policy is not a boolean")
    return value


def prepare_operation_backups(
    sources: Iterable[str | os.PathLike[str]],
    *,
    config: dict | None = None,
) -> SourceBackupResult:
    """Resolve the backup policy and prepare all required source backups.

    A disabled policy returns successfully without creating backups. An
    indeterminate policy or any required backup failure raises ``BackupError``
    so callers cannot proceed by accident.
    """
    if config is None:
        config = _load_operation_config()
    elif not isinstance(config, dict):
        raise BackupError("Backup configuration is not a mapping")

    if not _enabled_from_config(config):
        return SourceBackupResult(True, {}, {}, enabled=False)

    result = prepare_source_backups(sources)
    if not result.success:
        details = "; ".join(f"{source}: {reason}" for source, reason in result.errors.items())
        raise BackupError(f"Backup failed: {details}", result)
    return result
