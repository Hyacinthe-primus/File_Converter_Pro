"""
Frequent configurations -> auto-created templates.

Logic (see FrequentConfigTracker.record):

1. Every successful operation reports the configuration it really used.
2. The config is reduced to a *canonical* form: only the fields that matter,
   with language-independent values (French / English / internal keys all map
   to the same thing). Two configs that behave the same therefore compare equal.
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

AUTO_PREFIX = "[Auto] "
DEFAULT_THRESHOLD = 3
DEFAULT_MAX_AUTO_PER_TYPE = 3

# --------------------------------------------------------------------------
# Canonical values (French label is the canonical form, as stored in templates)
# --------------------------------------------------------------------------

_PDF_TO_WORD_MODES = {
    "with_images": "Conserver les images et la mise en page",
    "text_only": "Texte brut uniquement",
}
_PDF_TO_WORD_ALIASES = {
    "Keep images and layout": "with_images",
    "Plain text only": "text_only",
}

_WORD_TO_PDF_MODES = {
    "preserve_all": "Conserver toute la mise en page",
    "text_only": "Texte uniquement",
}
_WORD_TO_PDF_ALIASES = {
    "Preserve all layout": "preserve_all",
    "Text only": "text_only",
}
_WORD_TO_PDF_QUALITY = {
    "Haute (300 DPI)": "Haute (300 DPI)",
    "Standard (150 DPI)": "Standard (150 DPI)",
    "Basse (72 DPI)": "Basse (72 DPI)",
    # labels shown by the conversion dialog
    "Haute qualité (300 DPI)": "Haute (300 DPI)",
    "Qualité standard (150 DPI)": "Standard (150 DPI)",
    "Optimisé (96 DPI)": "Basse (72 DPI)",
}

_MERGE_ORDERS = {
    "alpha_az": "Alphabétique (A→Z)",
    "alpha_za": "Alphabétique (Z→A)",
    "num_asc": "Numérique (1→9)",
    "num_desc": "Numérique (9→1)",
    "date_asc": "Date (ancien→nouveau)",
    "date_desc": "Date (nouveau→ancien)",
    "manual": "Manuel (glisser-déposer)",
    "current": "Ordre actuel (liste principale)",
}
_MERGE_ORDER_ALIASES = {
    "Alphabetical (A→Z)": "alpha_az",
    "Alphabetical (Z→A)": "alpha_za",
    "Numeric (1→9)": "num_asc",
    "Numeric (9→1)": "num_desc",
    "Date (oldest→newest)": "date_asc",
    "Date (newest→oldest)": "date_desc",
    "Manual (drag and drop)": "manual",
    "Current order (main list)": "current",
}

_SPLIT_METHODS = {
    "Par pages": "Par pages",
    "Toutes les pages": "Toutes les pages",
    "Plage de pages": "Plage de pages",
    "By pages": "Par pages",
    "All pages": "Toutes les pages",
    "Page range": "Plage de pages",
}

_COMPRESSION_LEVELS = {
    "Normal": "Normal",
    "Haute compression": "Haute compression",
    "Compression maximale": "Compression maximale",
    "High compression": "Haute compression",
    "Maximum compression": "Compression maximale",
}

_OPTIMIZATION_TYPES = {
    "Compression  –  réduit la taille du fichier": 0,
    "Nettoyage  –  supprime uniquement les métadonnées": 1,
    "Compression + Nettoyage  –  recommandé": 2,
    "Compression  —  reduces file size": 0,
    "Cleaning  —  removes metadata only": 1,
    "Compression + Cleaning  —  recommended": 2,
    "compression": 0,
    "nettoyage": 1,
    "les deux": 2,
}


def _from_keyed(value, labels: dict, aliases: dict, default):
    """Resolve internal key / French label / English alias to the French label."""
    if value in labels:
        return labels[value]
    if value in labels.values():
        return value
    if value in aliases:
        return labels[aliases[value]]
    return labels[default] if value in (None, "") else value


def _as_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _optimization_type(value) -> int:
    if isinstance(value, str) and value in _OPTIMIZATION_TYPES:
        return _OPTIMIZATION_TYPES[value]
    return _as_int(value, 2)


def canonical_config(template_type: str, config: dict | None) -> dict | None:
    """Return the canonical form of ``config`` for ``template_type``.

    Returns None when the type cannot be tracked (no real, reusable options).
    """
    cfg = config or {}

    if template_type == "Conversion PDF→Word":
        return {"mode": _from_keyed(cfg.get("mode"), _PDF_TO_WORD_MODES, _PDF_TO_WORD_ALIASES, "with_images")}

    if template_type == "Conversion Word→PDF":
        return {
            "mode": _from_keyed(cfg.get("mode"), _WORD_TO_PDF_MODES, _WORD_TO_PDF_ALIASES, "preserve_all"),
            "quality": _WORD_TO_PDF_QUALITY.get(cfg.get("quality"), "Standard (150 DPI)"),
            "compress_images": bool(cfg.get("compress_images", cfg.get("compress", True))),
            "include_metadata": bool(cfg.get("include_metadata", True)),
        }

    if template_type == "Conversion Images→PDF":
        return {"separate": bool(cfg.get("separate", False))}

    if template_type in ("Fusion PDF", "Fusion Word"):
        return {"merge_order": _from_keyed(cfg.get("merge_order"), _MERGE_ORDERS, _MERGE_ORDER_ALIASES, "current")}

    if template_type == "Division PDF":
        method = _SPLIT_METHODS.get(cfg.get("split_method", "Par pages"), cfg.get("split_method"))
        if method == "Plage de pages":
            return None  # a page range only makes sense for one specific document
        return {
            "split_method": method,
            "pages_per_file": max(1, _as_int(cfg.get("pages_per_file"), 1)) if method == "Par pages" else 1,
        }

    if template_type == "Compression":
        split_size = max(0, _as_int(cfg.get("split_size"), 0))
        split = bool(cfg.get("split_archive", split_size > 0)) and split_size > 0
        return {
            "format": str(cfg.get("format", "ZIP")).upper(),
            "compression_level": _COMPRESSION_LEVELS.get(cfg.get("compression_level", "Normal"), "Normal"),
            "encrypt": bool(cfg.get("encrypt", False)),
            "delete_originals": bool(cfg.get("delete_originals", False)),
            "split_archive": split,
            "split_size": split_size if split else 0,
        }

    if template_type == "Optimisation de fichiers":
        return {
            "optimization_type": _optimization_type(cfg.get("optimization_type", 2)),
            "quality_level": _as_int(cfg.get("quality_level"), 1),
            "remove_metadata": bool(cfg.get("remove_metadata", True)),
            "compress_images": bool(cfg.get("compress_images", True)),
            "keep_backup": bool(cfg.get("keep_backup", True)),
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
