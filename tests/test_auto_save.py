"""Tests for auto-saved frequent configurations (templates created from frequently used configs)."""

import pytest

from templates.frequent_configs import (
    AUTO_PREFIX,
    DEFAULT_MAX_AUTO_PER_TYPE,
    DEFAULT_THRESHOLD,
    canonical_config,
    config_hash,
)

PDF_TO_WORD = "Conversion PDF→Word"
COMPRESSION = "Compression"


@pytest.fixture
def tm(tmp_path, monkeypatch):
    """A TemplateManager backed by a throw-away database."""
    import database
    from templates import TemplateManager

    monkeypatch.setattr(database, "SRC_DIR", tmp_path)
    db = database.DatabaseManager()
    yield TemplateManager(db)
    db.close()


def _templates(tm, template_type):
    tm.load_templates()
    return tm.get_templates_by_type(template_type)


def _use(tm, template_type, config, times):
    result = None
    for _ in range(times):
        result = tm.record_config_usage(template_type, config)
    return result


def _set_last_used(tm, template_id, stamp):
    tm.db_manager._conn.execute("UPDATE templates SET last_used = ? WHERE id = ?", (stamp, template_id))
    tm.db_manager._conn.commit()
    tm.load_templates()


def _comp(level="Normal", fmt="ZIP", **extra):
    return {"format": fmt, "compression_level": level, **extra}


class TestCanonicalConfig:
    def test_languages_and_keys_are_equivalent(self):
        keys = canonical_config(PDF_TO_WORD, {"mode": "text_only"})
        fr = canonical_config(PDF_TO_WORD, {"mode": "Texte brut uniquement"})
        en = canonical_config(PDF_TO_WORD, {"mode": "Plain text only"})
        assert keys == fr == en

    def test_different_options_differ(self):
        a = canonical_config(PDF_TO_WORD, {"mode": "with_images"})
        b = canonical_config(PDF_TO_WORD, {"mode": "text_only"})
        assert config_hash(a) != config_hash(b)

    def test_irrelevant_fields_are_ignored(self):
        plain = canonical_config(COMPRESSION, _comp())
        noisy = canonical_config(COMPRESSION, _comp(is_default=True, name_template="x", something=1))
        assert plain == noisy

    def test_missing_fields_use_defaults(self):
        assert canonical_config(COMPRESSION, {}) == canonical_config(COMPRESSION, _comp())

    def test_split_size_only_counts_when_split_enabled(self):
        a = canonical_config(COMPRESSION, _comp(split_archive=False, split_size=50))
        b = canonical_config(COMPRESSION, _comp())
        assert a == b

    def test_word_to_pdf_quality_labels_are_normalized(self):
        dialog = canonical_config("Conversion Word→PDF", {"quality": "Haute qualité (300 DPI)"})
        stored = canonical_config("Conversion Word→PDF", {"quality": "Haute (300 DPI)"})
        assert dialog == stored

    def test_untrackable_types_return_none(self):
        assert canonical_config("Protection PDF", {"mode": "basic"}) is None
        assert canonical_config("Division PDF", {"split_method": "Plage de pages"}) is None
        assert canonical_config("Unknown type", {}) is None


class TestThreshold:
    def test_no_template_before_threshold(self, tm):
        result = _use(tm, PDF_TO_WORD, {"mode": "text_only"}, DEFAULT_THRESHOLD - 1)
        assert result.action == "counted"
        assert _templates(tm, PDF_TO_WORD) == {}

    def test_template_created_exactly_at_threshold(self, tm):
        result = _use(tm, PDF_TO_WORD, {"mode": "text_only"}, DEFAULT_THRESHOLD)
        assert result.action == "created"
        templates = _templates(tm, PDF_TO_WORD)
        assert len(templates) == 1
        tpl = templates[result.template_id]
        assert tpl["name"].startswith(AUTO_PREFIX)
        assert tpl["config"]["mode"] == "Texte brut uniquement"

    def test_created_template_is_applicable(self, tm):
        class App:
            config = {}

            class config_manager:
                @staticmethod
                def save_config(_):
                    pass

        result = _use(tm, PDF_TO_WORD, {"mode": "text_only"}, DEFAULT_THRESHOLD)
        app = App()
        assert tm.apply_template(result.template_id, app) is True
        assert app.active_templates["pdf_to_word"]["mode"] == "text_only"

    def test_ignored_types_never_create_templates(self, tm):
        _use(tm, "Protection PDF", {"mode": "basic"}, 10)
        assert _templates(tm, "Protection PDF") == {}


class TestNoDuplicates:
    def test_more_uses_do_not_create_more_templates(self, tm):
        _use(tm, PDF_TO_WORD, {"mode": "text_only"}, DEFAULT_THRESHOLD)
        result = _use(tm, PDF_TO_WORD, {"mode": "text_only"}, 10)
        assert result.action == "existing"
        assert len(_templates(tm, PDF_TO_WORD)) == 1

    def test_equivalent_forms_share_one_counter(self, tm):
        tm.record_config_usage(PDF_TO_WORD, {"mode": "text_only"})
        tm.record_config_usage(PDF_TO_WORD, {"mode": "Texte brut uniquement"})
        result = tm.record_config_usage(PDF_TO_WORD, {"mode": "Plain text only"})
        assert result.action == "created"
        assert len(_templates(tm, PDF_TO_WORD)) == 1

    def test_existing_user_template_prevents_auto_template(self, tm):
        tm.db_manager.save_template("Mon preset", PDF_TO_WORD, {"mode": "Texte brut uniquement"})
        tm.load_templates()
        result = _use(tm, PDF_TO_WORD, {"mode": "text_only"}, 10)
        assert result.action == "existing"
        templates = _templates(tm, PDF_TO_WORD)
        assert [t["name"] for t in templates.values()] == ["Mon preset"]

    def test_using_existing_template_bumps_last_used(self, tm):
        tm.db_manager.save_template("Mon preset", PDF_TO_WORD, {"mode": "Texte brut uniquement"})
        tm.load_templates()
        tid = next(iter(tm.current_templates))
        assert tm.get_template_by_id(tid)["last_used"] is None
        tm.record_config_usage(PDF_TO_WORD, {"mode": "text_only"})
        tm.load_templates()
        assert tm.get_template_by_id(tid)["last_used"] is not None

    def test_different_configs_are_counted_separately(self, tm):
        tm.record_config_usage(PDF_TO_WORD, {"mode": "text_only"})
        tm.record_config_usage(PDF_TO_WORD, {"mode": "with_images"})
        tm.record_config_usage(PDF_TO_WORD, {"mode": "text_only"})
        tm.record_config_usage(PDF_TO_WORD, {"mode": "with_images"})
        assert _templates(tm, PDF_TO_WORD) == {}

    def test_same_config_on_other_type_is_independent(self, tm):
        _use(tm, "Fusion PDF", {"merge_order": "alpha_az"}, DEFAULT_THRESHOLD)
        _use(tm, "Fusion Word", {"merge_order": "alpha_az"}, DEFAULT_THRESHOLD - 1)
        assert len(_templates(tm, "Fusion PDF")) == 1
        assert _templates(tm, "Fusion Word") == {}


class TestLimitPerType:
    def _make_frequent(self, tm, levels):
        for level in levels:
            _use(tm, COMPRESSION, _comp(level), DEFAULT_THRESHOLD)

    def test_cap_evicts_least_recently_used_auto_template(self, tm):
        assert DEFAULT_MAX_AUTO_PER_TYPE == 3
        self._make_frequent(tm, ["Normal", "Haute compression", "Compression maximale"])
        by_level = {t["config"]["compression_level"]: tid for tid, t in _templates(tm, COMPRESSION).items()}
        _set_last_used(tm, by_level["Normal"], "2026-01-01 10:00:00")
        _set_last_used(tm, by_level["Haute compression"], "2026-03-01 10:00:00")
        _set_last_used(tm, by_level["Compression maximale"], "2026-02-01 10:00:00")

        _use(tm, COMPRESSION, _comp("Normal", fmt="TAR"), DEFAULT_THRESHOLD)

        templates = _templates(tm, COMPRESSION)
        assert len(templates) == DEFAULT_MAX_AUTO_PER_TYPE
        assert by_level["Normal"] not in templates  # the oldest one was dropped
        assert by_level["Haute compression"] in templates

    def test_user_templates_are_never_evicted_nor_counted(self, tm):
        tm.db_manager.save_template("Mine A", COMPRESSION, _comp("Haute compression", fmt="TAR"))
        tm.db_manager.save_template("Mine B", COMPRESSION, _comp("Haute compression", fmt="7Z"))
        tm.load_templates()
        self._make_frequent(tm, ["Normal", "Haute compression", "Compression maximale"])
        _use(tm, COMPRESSION, _comp("Normal", fmt="TAR"), DEFAULT_THRESHOLD)

        names = [t["name"] for t in _templates(tm, COMPRESSION).values()]
        assert "Mine A" in names and "Mine B" in names
        assert sum(n.startswith(AUTO_PREFIX) for n in names) == DEFAULT_MAX_AUTO_PER_TYPE

    def test_evicted_config_must_become_frequent_again(self, tm):
        self._make_frequent(tm, ["Normal", "Haute compression", "Compression maximale"])
        by_level = {t["config"]["compression_level"]: tid for tid, t in _templates(tm, COMPRESSION).items()}
        _set_last_used(tm, by_level["Normal"], "2026-01-01 10:00:00")
        _use(tm, COMPRESSION, _comp("Normal", fmt="TAR"), DEFAULT_THRESHOLD)  # evicts "Normal"

        for _ in range(DEFAULT_THRESHOLD - 1):
            result = tm.record_config_usage(COMPRESSION, _comp("Normal"))
            assert result.action == "counted"
        assert tm.record_config_usage(COMPRESSION, _comp("Normal")).action == "created"

    def test_auto_names_are_unique(self, tm):
        self._make_frequent(tm, ["Normal", "Haute compression", "Compression maximale"])
        names = [t["name"] for t in _templates(tm, COMPRESSION).values()]
        assert len(set(names)) == len(names) == 3


class TestDeletedAutoTemplates:
    def test_deleted_auto_template_is_never_recreated(self, tm):
        result = _use(tm, PDF_TO_WORD, {"mode": "text_only"}, DEFAULT_THRESHOLD)
        tm.delete_template(result.template_id)
        assert _templates(tm, PDF_TO_WORD) == {}

        again = _use(tm, PDF_TO_WORD, {"mode": "text_only"}, 20)
        assert again.action == "dismissed"
        assert _templates(tm, PDF_TO_WORD) == {}

    def test_dismissing_one_config_does_not_block_others(self, tm):
        result = _use(tm, PDF_TO_WORD, {"mode": "text_only"}, DEFAULT_THRESHOLD)
        tm.delete_template(result.template_id)
        other = _use(tm, PDF_TO_WORD, {"mode": "with_images"}, DEFAULT_THRESHOLD)
        assert other.action == "created"

    def test_deleting_user_template_does_not_dismiss(self, tm):
        tm.db_manager.save_template("Mine", PDF_TO_WORD, {"mode": "Texte brut uniquement"})
        tm.load_templates()
        tid = next(iter(tm.current_templates))
        tm.delete_template(tid)
        result = _use(tm, PDF_TO_WORD, {"mode": "text_only"}, DEFAULT_THRESHOLD)
        assert result.action == "created"

    def test_renamed_auto_template_becomes_user_owned(self, tm):
        result = _use(tm, COMPRESSION, _comp("Normal"), DEFAULT_THRESHOLD)
        conn = tm.db_manager._conn
        conn.execute("UPDATE templates SET name = 'Archives rapides' WHERE id = ?", (result.template_id,))
        conn.commit()
        tm.load_templates()
        for level in ("Haute compression", "Compression maximale"):
            _use(tm, COMPRESSION, _comp(level), DEFAULT_THRESHOLD)
        _use(tm, COMPRESSION, _comp("Normal", fmt="TAR"), DEFAULT_THRESHOLD)
        _use(tm, COMPRESSION, _comp("Normal", fmt="7Z"), DEFAULT_THRESHOLD)
        names = [t["name"] for t in _templates(tm, COMPRESSION).values()]
        assert "Archives rapides" in names


class TestAppIntegration:
    """AppLogicMixin.record_config_usage: the entry point every operation calls."""

    class _App:
        def __init__(self, tm, enabled=True):
            self.config = {"auto_save_configs": enabled}
            self._tm = tm

        def _ensure_template_manager(self):
            return self._tm

        def translate_text(self, key):
            return {"Compression": "Archive"}.get(key, key)

        _ui_label_to_key = None  # bound below

    @pytest.fixture
    def app(self, tm):
        from app.logic import AppLogicMixin

        app = self._App(tm)
        app.record_config_usage = lambda t, c: AppLogicMixin.record_config_usage(app, t, c)
        app._ui_label_to_key = lambda v, keys: AppLogicMixin._ui_label_to_key(app, v, keys)
        return app

    def test_frequent_config_creates_one_named_template(self, app, tm):
        for _ in range(DEFAULT_THRESHOLD + 3):
            app.record_config_usage(COMPRESSION, _comp("Haute compression"))
        templates = _templates(tm, COMPRESSION)
        assert len(templates) == 1
        assert next(iter(templates.values()))["name"] == f"{AUTO_PREFIX}Archive #1"

    def test_setting_off_records_nothing(self, tm):
        from app.logic import AppLogicMixin

        app = self._App(tm, enabled=False)
        for _ in range(DEFAULT_THRESHOLD * 2):
            AppLogicMixin.record_config_usage(app, COMPRESSION, _comp())
        assert _templates(tm, COMPRESSION) == {}
        assert tm.db_manager.get_config_usage(COMPRESSION, config_hash(canonical_config(COMPRESSION, _comp()))) is None

    def test_errors_never_break_the_operation(self, app):
        class Broken:
            def record_config_usage(self, *args):
                raise RuntimeError("db locked")

        app._tm = Broken()
        app.record_config_usage(COMPRESSION, _comp())  # must not raise

    def test_ui_label_is_mapped_back_to_its_source_key(self, app):
        keys = ["Normal", "Haute compression"]
        assert app._ui_label_to_key("Haute compression", keys) == "Haute compression"
        assert app._ui_label_to_key("Unknown", keys) == "Unknown"


class TestPruning:
    def test_stale_counters_are_pruned(self, tm):
        tm.record_config_usage(PDF_TO_WORD, {"mode": "text_only"})
        tm.db_manager._conn.execute("UPDATE config_usage SET last_used = datetime('now', '-200 days')")
        tm.db_manager._conn.commit()
        tm.db_manager.prune_config_usage(90)
        digest = config_hash(canonical_config(PDF_TO_WORD, {"mode": "text_only"}))
        assert tm.db_manager.get_config_usage(PDF_TO_WORD, digest) is None
