"""Frequent configurations -> auto-created templates.

Logic (see FrequentConfigTracker.record):

1. Every successful operation reports the configuration it really used.
2. The config is reduced to a semantic, language-independent form.  Legacy
   French/English labels and internal values are normalized by
   ``templates.semantic_keys``.
3. If a template of that type (auto-created *or* made by the user) already has
   the same canonical config, no template is created; that template is just
   marked as used.
4. Otherwise the use is counted. When the same config has been used
   ``threshold`` times, one template is created.
5. At most ``max_auto`` auto templates exist per type. Creating another one
   removes the least recently used auto template. Templates made or renamed by
   the user (anything not starting with AUTO_PREFIX) are never touched.
6. A deleted auto template is remembered as "dismissed" and is never created
   again.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import NamedTuple

from . import semantic_keys as sk

AUTO_PREFIX = "[Auto] "
DEFAULT_THRESHOLD = 3
DEFAULT_MAX_AUTO_PER_TYPE = 3


def canonical_config(template_type: str, config: dict | None) -> dict | None:
    """Return the semantic canonical form of ``config`` for ``template_type``.

    Returns None when the type cannot be tracked (no real, reusable options).
    """
    key = sk.normalize_type(template_type)
    cfg = sk.normalize_config(key, config)

    if key == sk.PDF_TO_WORD:
        return {"mode": cfg["mode"]}

    if key == sk.WORD_TO_PDF:
        return {
            "mode": cfg["mode"],
            "quality": cfg["quality"],
            "compress_images": cfg["compress_images"],
            "include_metadata": cfg["include_metadata"],
        }

    if key == sk.IMAGES_TO_PDF:
        return {"separate": cfg["separate"]}

    if key in (sk.PDF_MERGE, sk.WORD_MERGE):
        return {"merge_order": cfg["merge_order"]}

    if key == sk.PDF_SPLIT:
        if cfg["split_method"] == sk.SPLIT_PAGE_RANGE:
            return None  # a page range only makes sense for one specific document
        return {
            "split_method": cfg["split_method"],
            "pages_per_file": cfg["pages_per_file"] if cfg["split_method"] == sk.SPLIT_BY_PAGES else 1,
        }

    if key == sk.COMPRESSION:
        return {
            "format": cfg["format"],
            "compression_level": cfg["compression_level"],
            "encrypt": cfg["encrypt"],
            "delete_originals": cfg["delete_originals"],
            "split_archive": cfg["split_archive"],
            "split_size": cfg["split_size"],
        }

    if key == sk.FILE_OPTIMIZATION:
        return {
            "optimization_type": cfg["optimization_type"],
            "quality_level": cfg["quality_level"],
            "remove_metadata": cfg["remove_metadata"],
            "compress_images": cfg["compress_images"],
            "keep_backup": cfg["keep_backup"],
        }

    return None


def config_hash(canonical: dict) -> str:
    """Stable fingerprint of a canonical config."""
    payload = json.dumps(canonical, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


class RecordResult(NamedTuple):
    action: str  # "ignored" | "dismissed" | "existing" | "counted" | "created"
    template_id: int | None = None
    count: int = 0


class FrequentConfigTracker:
    """Counts used configurations and turns frequent ones into templates."""

    def __init__(
        self,
        template_manager,
        threshold: int = DEFAULT_THRESHOLD,
        max_auto: int = DEFAULT_MAX_AUTO_PER_TYPE,
    ):
        self.tm = template_manager
        self.db = template_manager.db_manager
        self.threshold = max(1, threshold)
        self.max_auto = max(1, max_auto)

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def is_auto_template(template: dict) -> bool:
        return str(template.get("name", "")).startswith(AUTO_PREFIX)

    def _find_equivalent(self, template_type: str, canonical: dict):
        """Return the id of any template of this type whose config is equivalent."""
        for tid, tpl in self.tm.get_templates_by_type(template_type).items():
            if canonical_config(self.tm.normalize_type(tpl["type"]), tpl["config"]) == canonical:
                return tid
        return None

    def _next_auto_name(self, template_type: str, label: str) -> str:
        used = set()
        for tpl in self.tm.get_templates_by_type(template_type).values():
            if self.is_auto_template(tpl):
                m = re.search(r" #(\d+)$", tpl["name"])
                if m:
                    used.add(int(m.group(1)))
        n = 1
        while n in used:
            n += 1
        return f"{AUTO_PREFIX}{label} #{n}"

    def _make_room(self, template_type: str) -> None:
        """Delete the least recently used auto templates until one more fits."""
        autos = [
            (tid, tpl)
            for tid, tpl in self.tm.get_templates_by_type(template_type).items()
            if self.is_auto_template(tpl)
        ]
        # oldest first; ids break ties because timestamps only have 1-second resolution
        autos.sort(key=lambda item: (item[1].get("last_used") or item[1].get("created_at") or "", item[0]))
        while len(autos) >= self.max_auto:
            tid, tpl = autos.pop(0)
            canonical = canonical_config(self.tm.normalize_type(tpl["type"]), tpl["config"])
            self.db.delete_template(tid)
            if canonical is not None:
                # evicted, not rejected: it has to become frequent again to come back
                self.db.set_config_usage_status(
                    template_type, config_hash(canonical), "counting", canonical, reset_count=True
                )
        self.tm.load_templates()

    # -- public API --------------------------------------------------------

    def record(self, template_type: str, config: dict, label: str | None = None) -> RecordResult:
        """Register one successful use of ``config`` and create a template if it became frequent."""
        template_type = self.tm.normalize_type(template_type)
        canonical = canonical_config(template_type, config)
        if canonical is None:
            return RecordResult("ignored")
        digest = config_hash(canonical)

        existing_id = self._find_equivalent(template_type, canonical)
        if existing_id is not None:
            self.db.update_template_usage(existing_id)
            return RecordResult("existing", existing_id)

        row = self.db.get_config_usage(template_type, digest)
        if row and row[1] == "dismissed":
            return RecordResult("dismissed")

        self.db.prune_config_usage()
        count = self.db.increment_config_usage(template_type, digest, canonical)
        if count < self.threshold:
            return RecordResult("counted", None, count)

        self._make_room(template_type)
        name = self._next_auto_name(template_type, label or template_type)
        self.db.save_template(name, template_type, canonical)
        self.tm.load_templates()
        self.db.set_config_usage_status(template_type, digest, "promoted", canonical)
        created = self._find_equivalent(template_type, canonical)
        return RecordResult("created", created, count)

    def dismiss(self, template_type: str, config: dict) -> None:
        """Never auto-create a template for this config again (used when an auto template is deleted)."""
        template_type = self.tm.normalize_type(template_type)
        canonical = canonical_config(template_type, config)
        if canonical is not None:
            self.db.set_config_usage_status(template_type, config_hash(canonical), "dismissed", canonical)
