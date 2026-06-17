"""
tasks/scheduler.py
File Converter Pro

Reads scheduled_tasks from automation/*.toml and runs them at the
configured time using APScheduler.

"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from pathlib import Path

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False

from tasks.watcher import (
    _is_temp_file,
    _load_all_toml,
    _normalise_rules,
    _build_conversion_type,
    _run_conversion,
    _merge_conversion_type,
    _run_merge,
    _resolve_output_dir,
    _merge_already_done,
    _save_merge_state,
)

logger = logging.getLogger(__name__)


def _load_toml_with_paths() -> list[tuple[Path, dict]]:
    """
    Return [(toml_path, parsed_dict), ...] for every automation/*.toml file.

    We re-parse here instead of reusing _load_all_toml() because the watcher
    helper merges all files into one dict and drops the file provenance.
    """
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib 
        except ImportError:
            logger.error("[Scheduler] No TOML library available (tomllib / tomli)")
            return []

    automation_dir = Path(__file__).resolve().parent.parent / "automation"
    if not automation_dir.is_dir():
        return []

    results = []
    for toml_file in sorted(automation_dir.glob("*.toml")):
        try:
            with open(toml_file, "rb") as fh:
                data = tomllib.load(fh)
            results.append((toml_file, data))
        except Exception as e:
            logger.warning("[Scheduler] Could not parse %s: %s", toml_file, e)
    return results


def _find_toml_for_task(task_name: str) -> Path | None:
    """Return the TOML file that defines *task_name* as an enabled task."""
    fallback = None
    for toml_path, data in _load_toml_with_paths():
        task_cfg = data.get("scheduled_tasks", {}).get(task_name)
        if task_cfg is None:
            continue
        if task_cfg.get("enabled", True):
            return toml_path
        if fallback is None:
            fallback = toml_path
    return fallback


def _disable_date_task_in_toml(toml_path: Path, task_name: str) -> None:
    """
    Set  enabled = false  for *task_name* inside *toml_path*.

    Uses a line-by-line rewrite so comments and formatting are preserved.
    The rewrite is limited to the [scheduled_tasks.<task_name>] section:
    it flips the first  enabled = true  line it encounters after the section
    header, then stops (doesn't touch sub-tables or other sections).
    """
    try:
        text = toml_path.read_text(encoding="utf-8")
    except OSError as e:
        logger.error("[Scheduler] Cannot read %s for auto-disable: %s", toml_path, e)
        return

    section_header = f"[scheduled_tasks.{task_name}]"
    lines          = text.splitlines(keepends=True)
    inside         = False
    patched        = False
    out            = []

    enabled_re = re.compile(r'^(\s*enabled\s*=\s*)true(\s*(?:#.*)?)$', re.IGNORECASE)

    for line in lines:
        stripped = line.strip()

        if stripped == section_header:
            inside = True
            out.append(line)
            continue

        if inside and not patched:
            if stripped.startswith("[") and not stripped.startswith(
                f"[scheduled_tasks.{task_name}."
            ):
                inside = False
                out.append(line)
                continue

            m = enabled_re.match(line.rstrip("\n\r"))
            if m:
                new_line = m.group(1) + "false" + m.group(2)
                ending   = line[len(line.rstrip("\n\r")):]
                out.append(new_line + ending)
                patched = True
                logger.info(
                    "[Scheduler] Auto-disabled task '%s' in %s", task_name, toml_path
                )
                continue

        out.append(line)

    if not patched:
        logger.warning(
            "[Scheduler] Could not find 'enabled = true' for task '%s' in %s — "
            "file left unchanged.",
            task_name, toml_path,
        )
        return

    try:
        toml_path.write_text("".join(out), encoding="utf-8")
    except OSError as e:
        logger.error("[Scheduler] Cannot write %s after auto-disable: %s", toml_path, e)


def get_scheduled_task_configs() -> list:
    tasks = _load_all_toml().get("scheduled_tasks", {})
    result = []
    for name, cfg in tasks.items():
        if not cfg.get("enabled", True):
            continue
        path    = cfg.get("path", "").strip()
        rules   = cfg.get("rules", {})
        trigger = cfg.get("trigger", {})
        if not path or not rules or not trigger:
            logger.warning("[Scheduler] Skipping '%s': missing path, rules or trigger", name)
            continue
        result.append({
            "name":       name,
            "path":       path,
            "output_dir": cfg.get("output_dir", "").strip(),
            "rules":      _normalise_rules(rules),
            "recursive":  cfg.get("recursive", False),
            "trigger":    trigger,
            "toml_file":  _find_toml_for_task(name),
        })
    return result


def get_all_scheduled_task_configs() -> list:
    tasks = _load_all_toml().get("scheduled_tasks", {})
    result = []
    for name, cfg in tasks.items():
        path    = cfg.get("path", "").strip()
        rules   = cfg.get("rules", {})
        trigger = cfg.get("trigger", {})
        if not path or not rules or not trigger:
            continue
        result.append({
            "name":       name,
            "path":       path,
            "output_dir": cfg.get("output_dir", "").strip(),
            "rules":      _normalise_rules(rules),
            "recursive":  cfg.get("recursive", False),
            "trigger":    trigger,
            "enabled":    cfg.get("enabled", True),
            "toml_file":  _find_toml_for_task(name),
        })
    return result


def _build_trigger(trigger_cfg: dict):
    """Build an APScheduler trigger from the toml trigger block."""
    t = trigger_cfg.get("type", "").lower()

    if t == "cron":
        return CronTrigger(
            day_of_week = trigger_cfg.get("day_of_week", "*"),
            day         = trigger_cfg.get("day",         "*"),
            hour        = trigger_cfg.get("hour",         0),
            minute      = trigger_cfg.get("minute",       0),
        )

    if t == "interval":
        return IntervalTrigger(
            hours   = trigger_cfg.get("hours",   0),
            minutes = trigger_cfg.get("minutes", 0),
        )

    if t == "date":
        from apscheduler.triggers.date import DateTrigger
        run_at = trigger_cfg.get("run_at", "")
        if not run_at:
            logger.error("[Scheduler] 'date' trigger missing 'run_at'")
            return None
        try:
            from datetime import datetime
            return DateTrigger(run_date=datetime.fromisoformat(run_at))
        except ValueError as e:
            logger.error("[Scheduler] Invalid 'run_at' value '%s': %s", run_at, e)
            return None


def _run_task(cfg: dict) -> None:
    """
    Execute all conversions/merges for a scheduled task.

    - 1-to-1 conversions: processed per file (skip if output exists).
    - Merge actions: files are grouped by (output_dir, action, sort) and the
      merge is run once per group.

    After a successful run of a  type = "date"  task, enabled is set to false
    in the originating TOML file so the job is not re-queued on next startup.
    """
    path      = cfg["path"]
    rules     = cfg["rules"]
    recursive = cfg["recursive"]

    iterator = Path(path).rglob("*") if recursive else Path(path).iterdir()

    merge_groups: dict[tuple, list[str]] = defaultdict(list)

    for f in iterator:
        if f.is_dir() or _is_temp_file(f):
            continue
        ext = f.suffix.lstrip(".").lower()
        if ext not in rules:
            continue

        output_dir = _resolve_output_dir(cfg["output_dir"], str(f), path)

        for rule in rules[ext]:
            if rule["kind"] == "convert":
                fmt      = rule["fmt"]
                expected = Path(output_dir) / f"{f.stem}.{fmt}"
                if expected.exists():
                    continue
                conversion_type = _build_conversion_type(ext, fmt)
                if conversion_type is None:
                    logger.warning("[Scheduler] No conversion for %s → %s", ext, fmt)
                    continue
                try:
                    logger.info("[Scheduler] %s → %s (%s)", f.name, fmt, cfg["name"])
                    _run_conversion(conversion_type, str(f), output_dir)
                except Exception as e:
                    logger.error("[Scheduler] %s → %s failed: %s", f.name, fmt, e)

            else:
                key = (output_dir, rule["action"], rule["sort"])
                merge_groups[key].append(str(f))

    for (output_dir, action, sort), files in merge_groups.items():
        if not files:
            continue
        if _merge_already_done(output_dir, action, files):
            logger.info("[Scheduler] Merge skip (unchanged): action=%s dir=%s", action, output_dir)
            continue
        conversion_type = _merge_conversion_type(action, sort)
        if conversion_type is None:
            logger.error(
                "[Scheduler] Cannot build merge conversion_type for action=%s sort=%s",
                action, sort,
            )
            continue
        try:
            logger.info(
                "[Scheduler] Merge %s (%d files, sort=%s) → %s (%s)",
                action, len(files), sort, output_dir, cfg["name"],
            )
            _run_merge(conversion_type, files, output_dir)
            _save_merge_state(output_dir, action, files)
        except Exception as e:
            logger.error("[Scheduler] Merge %s failed: %s", action, e)

    if cfg.get("trigger", {}).get("type", "").lower() == "date":
        toml_file = cfg.get("toml_file")
        if toml_file:
            _disable_date_task_in_toml(Path(toml_file), cfg["name"])
        else:
            logger.warning(
                "[Scheduler] Task '%s' is a date trigger but its TOML source "
                "could not be located — 'enabled' not updated.",
                cfg["name"],
            )


class SchedulerManager:
    """
    Manages APScheduler jobs for all scheduled_tasks in automation/*.toml.

    manager = SchedulerManager()
    manager.start()   # daemon startup
    manager.reload()  # after toml edit
    manager.stop()    # daemon shutdown
    """

    def __init__(self):
        self._scheduler = None
        self._running   = False

    def start(self) -> None:
        if not APSCHEDULER_AVAILABLE:
            logger.error("[Scheduler] apscheduler not installed")
            return
        self._scheduler = BackgroundScheduler()
        self._load_jobs()
        self._scheduler.start()
        self._running = True
        logger.info("[Scheduler] Started with %d job(s).", len(self._scheduler.get_jobs()))

    def stop(self) -> None:
        if self._scheduler and self._running:
            self._scheduler.shutdown(wait=False)
        self._running = False
        logger.info("[Scheduler] Stopped.")

    def reload(self) -> None:
        if not self._scheduler:
            return
        self._scheduler.remove_all_jobs()
        self._load_jobs()
        logger.info("[Scheduler] Reloaded — %d job(s).", len(self._scheduler.get_jobs()))

    def is_running(self) -> bool:
        return self._running

    def _load_jobs(self) -> None:
        for cfg in get_scheduled_task_configs():
            trigger = _build_trigger(cfg["trigger"])
            if trigger is None:
                continue
            try:
                self._scheduler.add_job(
                    func             = _run_task,
                    trigger          = trigger,
                    args             = [cfg],
                    id               = cfg["name"],
                    name             = cfg["name"],
                    replace_existing = True,
                )
                logger.info("[Scheduler] Job registered: '%s'", cfg["name"])
            except Exception as e:
                logger.error("[Scheduler] Failed to register job '%s': %s", cfg["name"], e)