"""Shared orchestration for format-specific conversion pipelines."""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


class ConversionCancelled(Exception):
    """Raised when a conversion is cancelled before a safe commit point."""


@dataclass(frozen=True)
class PipelineResult:
    """Outcome of one staged conversion pipeline run."""

    success: bool
    error: str = ""
    cancelled: bool = False
    output_path: str = ""
    cleanup_warning: str = ""
    failures: tuple[tuple[str, str], ...] = ()


Engine = tuple[str, Callable[[str], object]]
Validator = Callable[[str], tuple[bool, str]]


def _is_cancelled(cancel_event: threading.Event | None) -> bool:
    return cancel_event is not None and cancel_event.is_set()


def _new_target(parent: str, prefix: str, suffix: str) -> str:
    fd, path = tempfile.mkstemp(prefix=prefix, suffix=suffix, dir=parent)
    os.close(fd)
    os.unlink(path)
    return path


def _cleanup_file(path: str | None) -> str:
    if not path:
        return ""
    try:
        os.remove(path)
    except FileNotFoundError:
        return ""
    except OSError as exc:
        logger.warning("[pipeline] Could not remove temporary file %s: %s", path, exc)
        return str(exc)
    return ""


def _cleanup_dir(path: str | None) -> str:
    if not path:
        return ""
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        return ""
    except OSError as exc:
        logger.warning("[pipeline] Could not remove temporary directory %s: %s", path, exc)
        return str(exc)
    return ""


def _format_failure(label: str, detail: str, include_labels: bool) -> str:
    if include_labels:
        return f"{label}: {detail}"
    return detail


def run_conversion_pipeline(
    destination: str,
    engines: Sequence[Engine],
    validator: Validator,
    *,
    cancel_event: threading.Event | None = None,
    stage_mode: str = "directory",
    stage_dir_prefix: str = "~fcp_stage_",
    staged_prefix: str = "~fcp_stage_",
    staged_suffix: str | None = None,
    progress_callback: Callable[[int], None] | None = None,
    attempt_progress: Sequence[int] | None = None,
    postprocess: Callable[[str], None] | None = None,
    include_engine_labels: bool = True,
) -> PipelineResult:
    """Run engines in order and commit *destination* only after validation.

    Engines receive an isolated target path. The first engine whose output
    validates is atomically moved into place. Existing output is untouched
    until that point. Cancellation is checked before each engine, immediately
    after it returns, after post-processing, and immediately before commit.
    """
    final_path = os.path.abspath(destination)
    parent = os.path.dirname(final_path)
    if not os.path.isdir(parent):
        return PipelineResult(False, "output directory missing", output_path=final_path)

    engine_list = list(engines)
    if not engine_list:
        return PipelineResult(False, "no conversion engines configured", output_path=final_path)

    if stage_mode not in {"file", "directory"}:
        return PipelineResult(False, f"invalid staging mode: {stage_mode}", output_path=final_path)

    suffix = staged_suffix if staged_suffix is not None else (Path(final_path).suffix or ".tmp")
    if not suffix.startswith("."):
        suffix = f".{suffix}"

    if _is_cancelled(cancel_event):
        return PipelineResult(False, "conversion cancelled", cancelled=True, output_path=final_path)

    stage_root: str | None = None
    attempt_dir: str | None = None
    staged_target: str | None = None
    cleanup_warnings: list[str] = []
    failures: list[tuple[str, str]] = []

    def cleanup_attempt() -> None:
        nonlocal attempt_dir, staged_target
        warning = ""
        if stage_root is None and staged_target is not None:
            warning = _cleanup_file(staged_target)
        staged_target = None
        warning = _cleanup_dir(attempt_dir) or warning
        attempt_dir = None
        if warning:
            cleanup_warnings.append(warning)

    def finish(result: PipelineResult) -> PipelineResult:
        cleanup_attempt()
        warning = _cleanup_dir(stage_root)
        if warning:
            cleanup_warnings.append(warning)
        if not cleanup_warnings:
            return result
        return PipelineResult(
            success=result.success,
            error=result.error,
            cancelled=result.cancelled,
            output_path=result.output_path,
            cleanup_warning="; ".join(cleanup_warnings),
            failures=result.failures,
        )

    if stage_mode == "directory":
        try:
            stage_root = tempfile.mkdtemp(prefix=stage_dir_prefix, dir=parent)
        except OSError as exc:
            return PipelineResult(False, f"staging failed: {exc}", output_path=final_path)

    try:
        for index, (label, engine) in enumerate(engine_list):
            if _is_cancelled(cancel_event):
                return finish(PipelineResult(False, "conversion cancelled", cancelled=True, output_path=final_path))

            target_parent = parent
            if stage_root is not None:
                try:
                    attempt_dir = tempfile.mkdtemp(prefix=f"~fcp_attempt_{index}_", dir=stage_root)
                except OSError as exc:
                    return finish(PipelineResult(False, f"staging failed: {exc}", output_path=final_path))
                target_parent = attempt_dir

            try:
                target = _new_target(target_parent, staged_prefix, suffix)
                staged_target = target
            except OSError as exc:
                failures.append((label, f"staging failed: {exc}"))
                cleanup_attempt()
                return finish(
                    PipelineResult(
                        False,
                        _format_failure(label, f"staging failed: {exc}", include_engine_labels),
                        output_path=final_path,
                        failures=tuple(failures),
                    )
                )

            if progress_callback is not None and attempt_progress is not None and index < len(attempt_progress):
                progress_callback(attempt_progress[index])

            try:
                result = engine(target)
            except ConversionCancelled:
                return finish(PipelineResult(False, "conversion cancelled", cancelled=True, output_path=final_path))
            except Exception as exc:
                detail = f"engine error: {exc}"
                failures.append((label, detail))
                cleanup_attempt()
                continue

            if _is_cancelled(cancel_event):
                return finish(PipelineResult(False, "conversion cancelled", cancelled=True, output_path=final_path))

            try:
                valid, reason = validator(target)
            except ConversionCancelled:
                return finish(PipelineResult(False, "conversion cancelled", cancelled=True, output_path=final_path))
            except Exception as exc:
                valid, reason = False, f"validation error: {exc}"

            if result is False:
                detail = reason or "engine reported failure"
                failures.append((label, detail))
                cleanup_attempt()
                continue

            if not valid:
                failures.append((label, reason or "invalid output"))
                cleanup_attempt()
                continue

            if postprocess is not None:
                try:
                    postprocess(target)
                except ConversionCancelled:
                    return finish(PipelineResult(False, "conversion cancelled", cancelled=True, output_path=final_path))
                except Exception as exc:
                    failures.append((label, f"postprocess error: {exc}"))
                    cleanup_attempt()
                    continue

                if _is_cancelled(cancel_event):
                    return finish(PipelineResult(False, "conversion cancelled", cancelled=True, output_path=final_path))

                try:
                    valid, reason = validator(target)
                except ConversionCancelled:
                    return finish(PipelineResult(False, "conversion cancelled", cancelled=True, output_path=final_path))
                except Exception as exc:
                    valid, reason = False, f"validation error: {exc}"

                if not valid:
                    failures.append((label, reason or "invalid output"))
                    cleanup_attempt()
                    continue

            if _is_cancelled(cancel_event):
                return finish(PipelineResult(False, "conversion cancelled", cancelled=True, output_path=final_path))

            try:
                os.replace(target, final_path)
            except OSError as exc:
                cleanup_attempt()
                detail = f"could not replace destination: {exc}"
                failures.append((label, detail))
                return finish(
                    PipelineResult(
                        False,
                        _format_failure(label, detail, include_engine_labels),
                        output_path=final_path,
                        failures=tuple(failures),
                    )
                )

            return finish(PipelineResult(True, output_path=final_path, failures=tuple(failures)))

        if failures:
            error = "; ".join(
                _format_failure(label, detail, include_engine_labels) for label, detail in failures
            )
        else:
            error = "conversion failed"
        return finish(PipelineResult(False, error, output_path=final_path, failures=tuple(failures)))
    finally:
        cleanup_attempt()
        _cleanup_dir(stage_root)
