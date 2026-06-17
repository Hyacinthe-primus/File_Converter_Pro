"""
tasks/watcher.py
Monitors folders defined in automation/*.toml and automatically converts
any new file that matches a configured rule.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
import time
from collections import defaultdict
from pathlib import Path
from threading import Lock, Timer

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

logger = logging.getLogger(__name__)

MERGE_IMAGE_ACTION = "merged_images_to_pdf"
MERGE_PDF_ACTION   = "merged_pdf"
MERGE_DOCX_ACTION  = "merged_docx"

MERGE_ACTIONS = {MERGE_IMAGE_ACTION, MERGE_PDF_ACTION, MERGE_DOCX_ACTION}

MERGE_DEBOUNCE_SECONDS = 2.0

IMAGE_EXTENSIONS = {
    "jpg", "jpeg", "png", "webp", "bmp", "tiff", "tif", "heic", "heif",
    "jfif", "avif", "gif", "psd", "svg", "j2k", "jp2", "jpx",
    "dng", "raw", "cr2", "cr3", "nef", "arw", "orf", "rw2", "raf",
}
PDF_EXTENSIONS  = {"pdf"}
DOCX_EXTENSIONS = {"docx", "doc"}
_TEMP_PREFIXES = ("~$", "~")
_TEMP_SUFFIXES = (".tmp", ".~tmp")

def _is_temp_file(path: str | Path) -> bool:
    """Return True for temporary/lock files that should never be processed."""
    name = Path(path).name
    return (
        name.startswith(_TEMP_PREFIXES)
        or name.lower().endswith(_TEMP_SUFFIXES)
    )

def _get_automation_dir() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).resolve().parent.parent
    return base / "automation"


def _load_all_toml() -> dict:
    """Load and merge all *.toml files found in the automation/ directory."""
    if tomllib is None:
        logger.error("[Watcher] tomllib/tomli not available")
        return {}

    automation_dir = _get_automation_dir()
    if not automation_dir.is_dir():
        logger.info("[Watcher] No automation/ directory found at %s", automation_dir)
        return {}

    merged: dict = {}
    for toml_file in sorted(automation_dir.glob("*.toml")):
        try:
            with open(toml_file, "rb") as f:
                data = tomllib.load(f)
            for section in ("watch_folders", "scheduled_tasks"):
                if section in data:
                    merged.setdefault(section, {}).update(data[section])
        except Exception as e:
            logger.error("[Watcher] Failed to parse %s: %s", toml_file.name, e)

    return merged


def _normalise_rule_value(raw) -> list:
    """
    Convert any raw TOML rule value into a canonical list of rule dicts:

    Accepted TOML forms:
        png = "pdf"
        png = ["pdf", "webp"]
        png = ["merged_images_to_pdf"]
        docx = [{ action = "merged_docx", sort = "date_desc" }]
        pdf  = [{ action = "merged_pdf",  sort = "numerical_asc" }, "docx"]
    """
    if isinstance(raw, str):
        raw = [raw]

    result = []
    for item in raw:
        if isinstance(item, str):
            stripped = item.strip().lower()
            if stripped in MERGE_ACTIONS:
                result.append({"kind": "merge", "action": stripped, "sort": "none"})
            else:
                result.append({"kind": "convert", "fmt": stripped})
        elif isinstance(item, dict):
            action = item.get("action", "").strip().lower()
            sort   = item.get("sort",   "none").strip().lower()
            if action in MERGE_ACTIONS:
                result.append({"kind": "merge", "action": action, "sort": sort})
            else:
                logger.warning("[Watcher] Unknown merge action '%s' — skipped", action)
        else:
            logger.warning("[Watcher] Unexpected rule item type %s — skipped", type(item))
    return result


def _normalise_rules(raw_rules: dict) -> dict:
    """Return {ext: [rule_dict, ...]} with all values normalised."""
    return {k.lower(): _normalise_rule_value(v) for k, v in raw_rules.items()}


def get_watch_folder_configs() -> list:
    folders = _load_all_toml().get("watch_folders", {})
    result = []
    for name, cfg in folders.items():
        if not cfg.get("enabled", True):
            continue
        path = cfg.get("path", "").strip()
        rules = cfg.get("rules", {})
        if not path or not rules:
            logger.warning("[Watcher] Skipping '%s': missing path or rules", name)
            continue
        result.append({
            "name":             name,
            "path":             path,
            "output_dir":       cfg.get("output_dir", "").strip(),
            "rules":            _normalise_rules(rules),
            "recursive":        cfg.get("recursive", False),
            "convert_existing": cfg.get("convert_existing", False),
        })
    return result


def get_all_watch_folder_configs() -> list:
    folders = _load_all_toml().get("watch_folders", {})
    result = []
    for name, cfg in folders.items():
        path  = cfg.get("path", "").strip()
        rules = cfg.get("rules", {})
        if not path or not rules:
            continue
        result.append({
            "name":             name,
            "path":             path,
            "output_dir":       cfg.get("output_dir", "").strip(),
            "rules":            _normalise_rules(rules),
            "recursive":        cfg.get("recursive", False),
            "convert_existing": cfg.get("convert_existing", False),
            "enabled":          cfg.get("enabled", True),
        })
    return result


def _resolve_output_dir(output_dir_cfg: str, src: str, watch_root: str) -> str:
    """
    Resolve the output directory for a given source file, preserving the
    relative sub-folder structure under watch_root inside output_dir_cfg.

    Examples (watch_root=C:/In, output_dir_cfg=C:/Out):
        C:/In/file.png          → C:/Out
        C:/In/sub/file.png      → C:/Out/sub
        C:/In/a/b/file.png      → C:/Out/a/b
    If output_dir_cfg is empty, watch_root itself is used as the base.
    """
    base = output_dir_cfg if output_dir_cfg else watch_root
    rel = os.path.relpath(os.path.dirname(src), watch_root)
    if rel == ".":
        return base
    return os.path.join(base, rel)


def _wait_for_file_ready(path: str, timeout: float = 10.0, interval: float = 0.3) -> bool:
    deadline = time.monotonic() + timeout
    last_size = -1
    while time.monotonic() < deadline:
        try:
            size = os.path.getsize(path)
        except OSError:
            time.sleep(interval)
            continue
        if size == last_size and size > 0:
            return True
        last_size = size
        time.sleep(interval)
    return False


def _build_conversion_type(src_ext: str, dst_fmt: str) -> str | None:
    try:
        from context_menu.formats import CONVERSION_MAP
    except ImportError as e:
        logger.error("[Watcher] Cannot import CONVERSION_MAP: %s", e)
        return None
    entries = CONVERSION_MAP.get(src_ext, [])
    logger.debug("[Watcher] CONVERSION_MAP[%s] = %s", src_ext, entries)
    dst_suffix = f"_{dst_fmt}"
    for ct in entries:
        if ct.endswith(dst_suffix):
            return ct
    return None


def _run_conversion(conversion_type: str, src: str, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)
    if conversion_type == "image_to_pdf":
        from context_menu.window import _convert_image_to_pdf
        _convert_image_to_pdf(src, output_dir)
    elif conversion_type == "docx_to_pdf":
        from context_menu.window import _convert_docx_to_pdf
        _convert_docx_to_pdf(src, output_dir)
    elif conversion_type == "pdf_to_docx":
        from context_menu.window import _convert_pdf_to_docx
        _convert_pdf_to_docx(src, output_dir)
    else:
        from converter.converters import AdvancedConverterEngine
        result = AdvancedConverterEngine().convert(conversion_type, src, output_dir)
        if not result.success:
            raise RuntimeError(result.error)


_SORT_TO_ORDER: dict[str, str] = {
    "none":             "none",
    "alphabetical_asc": "alpha_asc",
    "alphabetical_desc":"alpha_desc",
    "numerical_asc":    "num_asc",
    "numerical_desc":   "num_desc",
    "date_asc":         "date_asc",
    "date_desc":        "date_desc",
}


def _merge_conversion_type(action: str, sort: str) -> str | None:
    """
    Build the conversion_type string that matches MERGE_DISPATCH, e.g.:
        action="merged_pdf",  sort="date_desc"  → "merge_pdf_date_desc"
        action="merged_docx", sort="none"        → "merge_docx_none"
        action="merged_images_to_pdf"            → "images_to_pdf_merged"
    """
    order = _SORT_TO_ORDER.get(sort, "none")
    if action == MERGE_IMAGE_ACTION:
        return "images_to_pdf_merged"
    if action == MERGE_PDF_ACTION:
        return f"merge_pdf_{order}"
    if action == MERGE_DOCX_ACTION:
        return f"merge_docx_{order}"
    return None


def _run_merge(conversion_type: str, file_paths: list[str], output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)

    from context_menu.formats import MERGE_DISPATCH
    from context_menu.window import _merge_images_to_pdf, _merge_pdfs, _merge_docx

    if conversion_type == "images_to_pdf_merged":
        _merge_images_to_pdf(file_paths, output_dir)
        return

    if conversion_type in MERGE_DISPATCH:
        kind, order = MERGE_DISPATCH[conversion_type]
        if kind == "pdf":
            _merge_pdfs(file_paths, output_dir, order)
        else:
            _merge_docx(file_paths, output_dir, order)
        return

    raise RuntimeError(f"Unknown type: {conversion_type}")


def _collect_merge_files(
    folder: str,
    action: str,
    recursive: bool,
) -> list[str]:
    """
    Collect all files inside *folder* that belong to the merge family
    indicated by *action*.  Returns absolute path strings.
    """
    if action == MERGE_IMAGE_ACTION:
        valid_exts = IMAGE_EXTENSIONS
    elif action == MERGE_PDF_ACTION:
        valid_exts = PDF_EXTENSIONS
    elif action == MERGE_DOCX_ACTION:
        valid_exts = DOCX_EXTENSIONS
    else:
        return []

    iterator = Path(folder).rglob("*") if recursive else Path(folder).iterdir()
    return [
        str(f) for f in iterator
        if f.is_file() and f.suffix.lstrip(".").lower() in valid_exts
    ]


def _merge_state_path(output_dir: str, action: str) -> Path:
    safe = action.replace("/", "_")
    return Path(output_dir) / f".merge_state_{safe}.json"


def _merge_fingerprint(files: list[str]) -> str:
    entries = sorted((f, os.path.getmtime(f)) for f in files)
    raw = json.dumps(entries, separators=(",", ":"))
    return hashlib.sha1(raw.encode()).hexdigest()


def _merge_already_done(output_dir: str, action: str, files: list[str]) -> bool:
    state_file = _merge_state_path(output_dir, action)
    if not state_file.exists():
        return False
    try:
        saved = json.loads(state_file.read_text())
        return saved.get("fingerprint") == _merge_fingerprint(files)
    except Exception:
        return False


def _save_merge_state(output_dir: str, action: str, files: list[str]) -> None:
    state_file = _merge_state_path(output_dir, action)
    try:
        os.makedirs(output_dir, exist_ok=True)
        state_file.write_text(json.dumps({
            "fingerprint": _merge_fingerprint(files),
            "files": sorted(files),
        }))
    except Exception as e:
        logger.warning("[Watcher] Could not save merge state: %s", e)


class _FolderEventHandler(FileSystemEventHandler):
    """
    Handles file-created events for a single watched folder config.

    1-to-1 conversions are dispatched immediately after the file is ready.
    Merge operations are debounced: a short timer is (re)started each time a
    qualifying file arrives; the merge fires once the folder has been quiet
    for MERGE_DEBOUNCE_SECONDS.
    """

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self._lock  = Lock()
        self._seen: set[str] = set()

        self._merge_timers: dict[tuple, Timer] = {}

    def on_created(self, event: FileCreatedEvent):
        if event.is_directory:
            return
        src = event.src_path
        with self._lock:
            if src in self._seen:
                return
            self._seen.add(src)

        if _is_temp_file(src):
            return
        ext   = Path(src).suffix.lstrip(".").lower()
        rules = self.config["rules"]

        if ext not in rules:
            with self._lock:
                self._seen.discard(src)
            return

        if not _wait_for_file_ready(src):
            logger.warning("[Watcher] File not ready after timeout: %s", src)
            with self._lock:
                self._seen.discard(src)
            return

        output_dir = _resolve_output_dir(
            self.config["output_dir"], src, self.config["path"]
        )

        for rule in rules[ext]:
            if rule["kind"] == "convert":
                self._dispatch_convert(src, ext, rule["fmt"], output_dir)
            else:
                self._schedule_merge(src, rule["action"], rule["sort"], output_dir)

        with self._lock:
            self._seen.discard(src)

    def _dispatch_convert(self, src: str, ext: str, fmt: str, output_dir: str) -> None:
        conversion_type = _build_conversion_type(ext, fmt)
        if conversion_type is None:
            logger.warning("[Watcher] No conversion found for %s → %s", ext, fmt)
            return
        try:
            logger.info("[Watcher] %s → %s", Path(src).name, fmt)
            _run_conversion(conversion_type, src, output_dir)
        except Exception as e:
            logger.error("[Watcher] %s → %s failed: %s", Path(src).name, fmt, e)

    def _schedule_merge(
        self, src: str, action: str, sort: str, output_dir: str
    ) -> None:
        """
        (Re)start a debounce timer for the (output_dir, action, sort) group.
        The sub-folder of the file is the grouping unit so that recursive
        watching merges per sub-folder, not the entire tree at once.
        """
        key = (output_dir, action, sort)
        with self._lock:
            existing = self._merge_timers.pop(key, None)
            if existing is not None:
                existing.cancel()
            t = Timer(
                MERGE_DEBOUNCE_SECONDS,
                self._fire_merge,
                args=[action, sort, output_dir],
            )
            self._merge_timers[key] = t
        t.start()
        logger.debug(
            "[Watcher] Merge debounce (re)started: action=%s sort=%s dir=%s",
            action, sort, output_dir,
        )

    def _fire_merge(self, action: str, sort: str, output_dir: str) -> None:
        key = (output_dir, action, sort)
        with self._lock:
            self._merge_timers.pop(key, None)

        watch_root  = self.config["path"]
        recursive = self.config["recursive"]

        out_base = self.config["output_dir"] if self.config["output_dir"] else watch_root
        rel = os.path.relpath(output_dir, out_base)
        src_folder = watch_root if rel == "." else os.path.join(watch_root, rel)

        files = _collect_merge_files(src_folder, action, recursive=recursive)
        if not files:
            logger.warning("[Watcher] Merge fired but no files found in %s", src_folder)
            return

        if _merge_already_done(output_dir, action, files):
            logger.info("[Watcher] Merge skip (unchanged): action=%s dir=%s", action, output_dir)
            return

        conversion_type = _merge_conversion_type(action, sort)
        if conversion_type is None:
            logger.error("[Watcher] Cannot build merge conversion_type for action=%s sort=%s", action, sort)
            return

        try:
            logger.info(
                "[Watcher] Merge %s (%d files, sort=%s) → %s",
                action, len(files), sort, output_dir,
            )
            _run_merge(conversion_type, files, output_dir)
            _save_merge_state(output_dir, action, files)
        except Exception as e:
            logger.error("[Watcher] Merge %s failed: %s", action, e)


class WatcherManager:
    """
    Manages watchdog observers for all watch_folders in automation/*.toml.

    manager = WatcherManager()
    manager.start()   # app startup
    manager.reload()  # after user edits a .toml
    manager.stop()    # app shutdown
    """

    def __init__(self):
        self._observers: list = []
        self._running = False

    def start(self) -> None:
        if not WATCHDOG_AVAILABLE:
            logger.error("[Watcher] watchdog not installed")
            return
        if tomllib is None:
            logger.error("[Watcher] tomli not installed")
            return
        self._running = True
        self._start_observers()

    def stop(self) -> None:
        self._running = False
        self._stop_observers()

    def reload(self) -> None:
        self._stop_observers()
        if self._running:
            self._start_observers()

    def is_running(self) -> bool:
        return self._running and bool(self._observers)

    def _start_observers(self) -> None:
        for cfg in get_watch_folder_configs():
            path = cfg["path"]
            if not os.path.isdir(path):
                logger.warning("[Watcher] Folder not found, skipping: %s", path)
                continue
            handler  = _FolderEventHandler(cfg)
            observer = Observer()
            observer.schedule(handler, path, recursive=cfg["recursive"])
            observer.start()
            if cfg.get("convert_existing", False):
                self._process_existing(cfg)
            self._observers.append(observer)
            logger.info("[Watcher] Watching '%s' → %s", cfg["name"], path)

    def _stop_observers(self) -> None:
        for obs in self._observers:
            try:
                obs.stop()
                obs.join(timeout=3)
            except Exception as e:
                logger.debug("[Watcher] Error stopping observer: %s", e)
        self._observers.clear()

    def _process_existing(self, cfg: dict) -> None:
        """
        Process files already present when the watcher starts.
        """
        path      = cfg["path"]
        rules     = cfg["rules"]
        recursive = cfg.get("recursive", False)

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
                        continue
                    try:
                        logger.info("[Watcher] Existing: %s → %s", f.name, fmt)
                        _run_conversion(conversion_type, str(f), output_dir)
                    except Exception as e:
                        logger.error("[Watcher] Existing: %s → %s failed: %s", f.name, fmt, e)

                else:
                    key = (output_dir, rule["action"], rule["sort"])
                    merge_groups[key].append(str(f))

        for (output_dir, action, sort), files in merge_groups.items():
            if not files:
                continue
            if _merge_already_done(output_dir, action, files):
                logger.info("[Watcher] Existing merge skip (unchanged): action=%s dir=%s", action, output_dir)
                continue
            conversion_type = _merge_conversion_type(action, sort)
            if conversion_type is None:
                continue
            try:
                logger.info(
                    "[Watcher] Existing merge %s (%d files, sort=%s) → %s",
                    action, len(files), sort, output_dir,
                )
                _run_merge(conversion_type, files, output_dir)
                _save_merge_state(output_dir, action, files)
            except Exception as e:
                logger.error("[Watcher] Existing merge %s failed: %s", action, e)