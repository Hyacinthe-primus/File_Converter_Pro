"""Security tests for local resources in HTML-to-PDF conversions."""

import base64
import io
import os
import sys
import types
from pathlib import Path

import pytest

from converter.html_inline import add_image_flowable
from converter.mixins.html_renderers import HtmlRenderers


def _renderer(allow_local=False):
    renderer = HtmlRenderers()
    renderer.allow_local_html_resources = allow_local
    return renderer


def _write_file(path, content=b"file-content"):
    path.write_bytes(content)
    return path


def _weasyprint_or_skip():
    """Import WeasyPrint, skipping when its native Pango/GTK libraries are unavailable."""
    return pytest.importorskip("weasyprint", exc_type=OSError)


class TestLocalResourceSetting:
    def test_default_setting_is_disabled(self):
        from config import DEFAULT_CONFIG

        assert DEFAULT_CONFIG["allow_local_resources_in_html_to_pdf"] is False

    def test_config_manager_round_trip(self, tmp_path):
        from config import ConfigManager

        manager = ConfigManager(str(tmp_path / "config.dat"), str(tmp_path / "key.key"))
        assert manager.save_config({"allow_local_resources_in_html_to_pdf": True})
        assert manager.load_config()["allow_local_resources_in_html_to_pdf"] is True

    def test_old_config_gets_secure_default(self, tmp_path):
        from config import ConfigManager

        manager = ConfigManager(str(tmp_path / "config.dat"), str(tmp_path / "key.key"))
        manager.cipher_suite = None
        manager.save_config({"dark_mode": True})
        assert manager.load_config()["allow_local_resources_in_html_to_pdf"] is False

    def test_engine_defaults_to_disabled(self):
        from converter.converters import AdvancedConverterEngine

        assert AdvancedConverterEngine().allow_local_html_resources is False
        assert AdvancedConverterEngine(True).allow_local_html_resources is True

    def test_conversion_worker_applies_setting(self, qapp):
        from converter.converters import AdvancedConverterEngine
        from dialogs.advanced_conversions import _ConversionWorker

        engine = AdvancedConverterEngine()
        worker = _ConversionWorker(
            engine,
            None,
            "html_to_pdf",
            [],
            "",
            config={"allow_local_resources_in_html_to_pdf": True},
        )
        assert worker.engine.allow_local_html_resources is True
        assert not hasattr(worker.engine, "backup_enabled")

    def test_settings_dialog_reads_and_returns_setting(self, qapp):
        from dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog({}, None, "en")
        try:
            assert dialog.allow_local_resources_checkbox.isChecked() is False
            assert dialog.get_settings()["allow_local_resources_in_html_to_pdf"] is False

            dialog.allow_local_resources_checkbox.setChecked(True)
            assert dialog.get_settings()["allow_local_resources_in_html_to_pdf"] is True

            dialog.restore_defaults()
            assert dialog.allow_local_resources_checkbox.isChecked() is False
        finally:
            dialog.deleteLater()
            qapp.processEvents()


class TestDisabledLocalResources:
    def test_local_image_is_not_read(self, tmp_path):
        image = _write_file(tmp_path / "image.png")
        html = f'<img src="{image.name}">'
        output = _renderer(False)._inline_all_resources(html, tmp_path)
        assert "data:" not in output
        assert 'src=""' in output

    def test_absolute_local_path_is_blocked(self, tmp_path):
        image = _write_file(tmp_path.parent / f"{tmp_path.name}-outside.png")
        html = f'<img src="{image.as_posix()}">'
        output = _renderer(False)._inline_all_resources(html, tmp_path)
        assert "data:" not in output
        assert 'src=""' in output

    def test_parent_directory_reference_is_blocked(self, tmp_path):
        _write_file(tmp_path.parent / f"{tmp_path.name}-outside.png")
        html = f'<img src="../{tmp_path.name}-outside.png">'
        output = _renderer(False)._inline_all_resources(html, tmp_path)
        assert "data:" not in output
        assert 'src=""' in output

    def test_file_url_is_blocked(self, tmp_path):
        image = _write_file(tmp_path / "image.png")
        html = f'<img src="{image.as_uri()}">'
        output = _renderer(False)._inline_all_resources(html, tmp_path)
        assert "data:" not in output
        assert 'src=""' in output

    def test_unc_path_is_blocked(self, tmp_path):
        html = '<img src="\\\\server\\share\\secret.png">'
        output = _renderer(False)._inline_all_resources(html, tmp_path)
        assert "data:" not in output
        assert 'src=""' in output

    def test_disabled_css_local_resource_is_not_inlined(self, tmp_path):
        image = _write_file(tmp_path / "image.png")
        css = ".x { background: url('" + image.name + "'); }"
        output = _renderer(False)._inline_css_urls(css, tmp_path)
        assert "data:" not in output
        assert "url('')" in output

    def test_disabled_mode_never_reads_local_files(self, tmp_path, monkeypatch):
        _write_file(tmp_path / "image.png")
        (tmp_path / "style.css").write_text(".x { background: url('image.png'); }", encoding="utf-8")

        def fail(*args, **kwargs):
            raise AssertionError("local file read attempted while disabled")

        monkeypatch.setattr(Path, "read_bytes", fail)
        monkeypatch.setattr(Path, "read_text", fail)
        html = (
            '<link rel="stylesheet" href="style.css">'
            '<img src="image.png">'
            '<div style="background:url(image.png)">Content</div>'
        )
        output = _renderer(False)._inline_all_resources(html, tmp_path)
        assert "data:" not in output

    def test_script_and_iframe_are_removed(self, tmp_path):
        html = (
            '<script>fetch("file:///etc/passwd")</script>'
            '<iframe src="file:///etc/passwd"></iframe>'
            "<object data=\"file:///etc/passwd\"></object>"
            "<p>Content</p>"
        )
        output = _renderer(False)._inline_all_resources(html, tmp_path)
        assert "<script" not in output.lower()
        assert "<iframe" not in output.lower()
        assert "<object" not in output.lower()
        assert "<p>Content</p>" in output

    def test_html_entities_do_not_bypass_checks(self, tmp_path):
        _write_file(tmp_path.parent / f"{tmp_path.name}-outside.png")
        html = f'<img src="..&#x2f;{tmp_path.name}-outside.png">'
        output = _renderer(False)._inline_all_resources(html, tmp_path)
        assert "data:" not in output
        assert 'src=""' in output

    def test_weasyprint_fetcher_denies_file_urls(self):
        _weasyprint_or_skip()
        fetcher = HtmlRenderers._safe_weasyprint_fetcher()
        with pytest.raises(ValueError):
            fetcher.fetch("file:///C:/secret.txt")
        with pytest.raises(ValueError):
            fetcher.fetch("relative.png")
        with pytest.raises(ValueError):
            fetcher.fetch("C:/secret.txt")
        with pytest.raises(ValueError):
            fetcher.fetch("\\\\server\\share\\secret.txt")


class TestEnabledLocalResources:
    def test_absolute_path_inside_directory_is_inlined(self, tmp_path):
        image = _write_file(tmp_path / "image.png")
        html = f'<img src="{image.as_posix()}">'
        output = _renderer(True)._inline_all_resources(html, tmp_path)
        assert "data:image/png;base64," in output

    def test_resource_inside_html_directory_is_inlined(self, tmp_path):
        image = _write_file(tmp_path / "image.png")
        html = f'<img src="{image.name}">'
        output = _renderer(True)._inline_all_resources(html, tmp_path)
        assert "data:image/png;base64," in output

    def test_nested_relative_resource_is_inlined(self, tmp_path):
        subdir = tmp_path / "images"
        subdir.mkdir()
        image = _write_file(subdir / "image.png")
        html = f'<img src="images/{image.name}">'
        output = _renderer(True)._inline_all_resources(html, tmp_path)
        assert "data:image/png;base64," in output

    def test_local_stylesheet_and_its_image_are_inlined(self, tmp_path):
        _write_file(tmp_path / "image.png")
        (tmp_path / "style.css").write_text(
            ".x { background: url('image.png'); }",
            encoding="utf-8",
        )
        html = '<link rel="stylesheet" href="style.css"><p class="x">Content</p>'
        output = _renderer(True)._inline_all_resources(html, tmp_path)
        assert "<style>" in output
        assert "data:image/png;base64," in output
        assert "<link" not in output

    def test_css_url_inside_directory_is_inlined(self, tmp_path):
        _write_file(tmp_path / "image.png")
        css = ".x { background: url('image.png'); }"
        output = _renderer(True)._inline_css_urls(css, tmp_path)
        assert "data:image/png;base64," in output

    def test_css_in_subdirectory_can_reference_root(self, tmp_path):
        image = _write_file(tmp_path / "image.png")
        css_dir = tmp_path / "css"
        css_dir.mkdir()
        css = ".x { background: url('../" + image.name + "'); }"
        output = _renderer(True)._inline_css_urls(css, css_dir, _root_dir=tmp_path)
        assert "data:image/png;base64," in output

    def test_css_in_subdirectory_cannot_escape_root(self, tmp_path):
        outside = _write_file(tmp_path.parent / f"{tmp_path.name}-outside.png")
        css_dir = tmp_path / "css"
        css_dir.mkdir()
        css = ".x { background: url('../../" + outside.name + "'); }"
        output = _renderer(True)._inline_css_urls(css, css_dir, _root_dir=tmp_path)
        assert "data:" not in output
        assert "url('')" in output

    def test_file_url_inside_directory_is_inlined(self, tmp_path):
        image = _write_file(tmp_path / "image.png")
        css = f".x {{ background: url('{image.as_uri()}'); }}"
        output = _renderer(True)._inline_css_urls(css, tmp_path)
        assert "data:image/png;base64," in output

    def test_absolute_path_outside_directory_is_blocked(self, tmp_path):
        image = _write_file(tmp_path.parent / f"{tmp_path.name}-outside.png")
        html = f'<img src="{image.as_posix()}">'
        output = _renderer(True)._inline_all_resources(html, tmp_path)
        assert "data:" not in output
        assert 'src=""' in output

    def test_traversal_outside_directory_is_blocked(self, tmp_path):
        _write_file(tmp_path.parent / f"{tmp_path.name}-outside.png")
        html = f'<img src="../{tmp_path.name}-outside.png">'
        output = _renderer(True)._inline_all_resources(html, tmp_path)
        assert "data:" not in output
        assert 'src=""' in output

    def test_file_url_outside_directory_is_blocked(self, tmp_path):
        image = _write_file(tmp_path.parent / f"{tmp_path.name}-outside.png")
        css = f".x {{ background: url('{image.as_uri()}'); }}"
        output = _renderer(True)._inline_css_urls(css, tmp_path)
        assert "data:" not in output
        assert "url('')" in output

    def test_symlink_escape_is_blocked(self, tmp_path):
        outside = _write_file(tmp_path.parent / f"{tmp_path.name}-outside.png")
        link = tmp_path / "link.png"
        try:
            link.symlink_to(outside)
        except OSError as exc:
            pytest.skip(f"symlinks unavailable: {exc}")

        html = f'<img src="{link.name}">'
        output = _renderer(True)._inline_all_resources(html, tmp_path)
        assert "data:" not in output
        assert 'src=""' in output

    def test_reportlab_fallback_ignores_local_media_paths(self, tmp_path, monkeypatch):
        import converter.mixins.html_renderers as html_renderers

        calls = []
        monkeypatch.setattr(
            html_renderers,
            "add_image_flowable",
            lambda story, src, max_w, tmp_imgs: calls.append(src),
        )
        output = tmp_path / "out.pdf"
        _renderer(True)._reportlab_html_to_pdf(
            '<p>Content</p><img src="C:/Windows/win.ini">',
            str(output),
        )
        assert calls == []
        assert output.exists()


class TestPdfKitOptions:
    @staticmethod
    def _install_fake_pdfkit(monkeypatch):
        captured = {}

        def from_file(src, dst, options=None, configuration=None):
            with open(src, "r", encoding="utf-8") as f:
                captured["html"] = f.read()
            captured["options"] = options
            with open(dst, "wb") as f:
                f.write(b"%PDF-1.4\n")
            return b""

        fake = types.SimpleNamespace(configuration=lambda **kwargs: object(), from_file=from_file)
        monkeypatch.setitem(sys.modules, "pdfkit", fake)
        monkeypatch.setattr("external_binaries.resolve_binary", lambda name: "wkhtmltopdf")
        return captured

    @staticmethod
    def _write_source(tmp_path, html):
        src = tmp_path / "source.html"
        src.write_text(html, encoding="utf-8")
        return src, tmp_path / "output.pdf"

    def test_disabled_mode_disables_both_layers(self, tmp_path, monkeypatch):
        captured = self._install_fake_pdfkit(monkeypatch)
        image = _write_file(tmp_path / "image.png")
        src, dst = self._write_source(tmp_path, f'<img src="{image.name}">')

        _renderer(False)._html_to_pdf(str(src), str(dst))

        options = captured["options"]
        assert "enable-local-file-access" not in options
        assert "disable-local-file-access" in options
        assert "disable-javascript" in options
        assert "data:" not in captured["html"]

    def test_enabled_mode_still_blocks_binary_local_reads(self, tmp_path, monkeypatch):
        captured = self._install_fake_pdfkit(monkeypatch)
        image = _write_file(tmp_path / "image.png")
        src, dst = self._write_source(tmp_path, f'<img src="{image.name}">')

        _renderer(True)._html_to_pdf(str(src), str(dst))

        options = captured["options"]
        assert "enable-local-file-access" not in options
        assert "disable-local-file-access" in options
        assert "disable-javascript" in options
        assert "data:image/png;base64," in captured["html"]


class TestLocalFileHardening:
    def test_hardlink_inside_root_reads_outside_when_enabled(self, tmp_path):
        outside = tmp_path / "outside.txt"
        outside.write_text("HARDLINK_SENTINEL", encoding="utf-8")
        root = tmp_path / "root"
        root.mkdir()
        link = root / "hard.txt"
        try:
            os.link(outside, link)
        except OSError as exc:
            pytest.skip(f"hardlinks unavailable: {exc}")

        html = '<img src="hard.txt">'
        disabled = _renderer(False)._inline_all_resources(html, root)
        assert "data:" not in disabled

        enabled = _renderer(True)._inline_all_resources(html, root)
        assert "data:" in enabled
        payload = enabled.split("base64,", 1)[1].split('"', 1)[0]
        assert base64.b64decode(payload) == b"HARDLINK_SENTINEL"

    def test_read_revalidates_after_path_swap(self, tmp_path):
        root = tmp_path / "root"
        root.mkdir()
        inside = root / "inside.txt"
        inside.write_text("inside", encoding="utf-8")
        outside = tmp_path / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        renderer = _renderer(True)
        resolved = renderer._resolve_local_path("inside.txt", root)
        assert resolved is not None

        inside.unlink()
        try:
            inside.symlink_to(outside)
        except OSError as exc:
            pytest.skip(f"symlinks unavailable: {exc}")

        with pytest.raises(OSError):
            renderer._read_local_file(resolved, root)

    def test_read_rejects_path_outside_root(self, tmp_path):
        root = tmp_path / "root"
        root.mkdir()
        outside = tmp_path / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        with pytest.raises(OSError):
            _renderer(True)._read_local_file(outside, root)


class TestHtmlSanitizationHardening:
    def test_quoted_gt_outside_ref_is_blocked(self, tmp_path):
        outside = _write_file(tmp_path.parent / f"{tmp_path.name}-outside.svg")
        html = f'<img src="{outside.as_uri()}?x=>">'
        for allow in (False, True):
            output = _renderer(allow)._inline_all_resources(html, tmp_path)
            assert "file:" not in output
            assert 'src=""' in output

    def test_quoted_gt_inside_ref_is_inlined(self, tmp_path):
        image = _write_file(tmp_path / "image.png")
        html = f'<img src="{image.as_uri()}?x=>">'
        output = _renderer(True)._inline_all_resources(html, tmp_path)
        assert "data:image/png;base64," in output

    def test_quoted_gt_active_tag_is_removed(self, tmp_path):
        html = '<iframe src="file:///C:/secret?x=>"></iframe><p>Safe</p>'
        output = _renderer(False)._inline_all_resources(html, tmp_path)
        assert "<iframe" not in output.lower()
        assert "<p>Safe</p>" in output

    @pytest.mark.parametrize(
        "meta",
        [
            '<meta http-equiv="ref&#114;esh" content="0;url=file:///C:/secret">',
            '<meta http&#45;equiv="refresh" content="0;url=file:///C:/secret">',
            '<meta HTTP-EQUIV="REFRESH" content="0;url=file:///C:/secret">',
        ],
    )
    def test_encoded_meta_refresh_is_removed(self, tmp_path, meta):
        output = _renderer(False)._inline_all_resources(meta + "<p>Safe</p>", tmp_path)
        assert "<meta" not in output.lower()
        assert "<p>Safe</p>" in output

    def test_normal_meta_is_preserved(self, tmp_path):
        html = '<meta charset="utf-8"><meta http-equiv="content-type" content="text/html"><p>Safe</p>'
        output = _renderer(False)._inline_all_resources(html, tmp_path)
        assert '<meta charset="utf-8">' in output
        assert 'http-equiv="content-type"' in output
        assert "<p>Safe</p>" in output

    def test_remote_resource_is_preserved(self, tmp_path):
        html = '<img src="https://example.com/image.png"><p>Safe</p>'
        output = _renderer(False)._inline_all_resources(html, tmp_path)
        assert 'src="https://example.com/image.png"' in output
        assert "<p>Safe</p>" in output

    @pytest.mark.skipif(os.name != "nt", reason="Windows UNC classification")
    def test_forward_slash_unc_is_local_and_blocked(self, tmp_path):
        renderer = _renderer(True)
        assert renderer._resource_kind("//server/share/secret.png")[0] == "local"
        assert renderer._resource_kind("https://example.com/image.png")[0] == "remote"

        html = '<img src="//server/share/secret.png">'
        for allow in (False, True):
            output = _renderer(allow)._inline_all_resources(html, tmp_path)
            assert "data:" not in output
            assert 'src=""' in output


class TestCssImportHardening:
    def test_data_import_and_following_rule_are_preserved(self, tmp_path):
        css = '@import url("data:text/css;base64,QUJD"); .x { color: red; }'
        output = _renderer(False)._inline_css_urls(css, tmp_path)
        assert output == css

    def test_bare_data_import_is_preserved(self, tmp_path):
        css = '@import "data:text/css;base64,QUJD"; .x { color: red; }'
        output = _renderer(False)._inline_css_urls(css, tmp_path)
        assert output == css

    def test_data_import_followed_by_local_import(self, tmp_path):
        css_dir = tmp_path / "css"
        css_dir.mkdir()
        (css_dir / "local.css").write_text(".y { color: blue; }", encoding="utf-8")
        css = (
            '@import url("data:text/css;base64,QUJD"); '
            '@import url("local.css"); '
            ".x { color: red; }"
        )
        output = _renderer(True)._inline_css_urls(css, css_dir, _root_dir=tmp_path)
        assert '@import url("data:text/css;base64,QUJD");' in output
        assert ".x { color: red; }" in output
        assert "local.css" not in output
        assert output.count("data:text/css;base64,") == 2

    def test_data_import_survives_disabled_local_import(self, tmp_path):
        css_dir = tmp_path / "css"
        css_dir.mkdir()
        (css_dir / "local.css").write_text(".y { color: blue; }", encoding="utf-8")
        css = (
            '@import url("data:text/css;base64,QUJD"); '
            '@import url("local.css"); '
            ".x { color: red; }"
        )
        output = _renderer(False)._inline_css_urls(css, css_dir, _root_dir=tmp_path)
        assert '@import url("data:text/css;base64,QUJD");' in output
        assert ".x { color: red; }" in output
        assert "local.css" not in output
        assert output.count("data:text/css;base64,") == 1

    def test_depth_limit_still_blocks_local_imports(self, tmp_path):
        (tmp_path / "local.css").write_text(".y { color: blue; }", encoding="utf-8")
        local_css = '@import url("local.css");'
        assert _renderer(True)._inline_css_urls(local_css, tmp_path, _depth=5) == ""

        data_css = '@import url("data:text/css;base64,QUJD");'
        assert _renderer(True)._inline_css_urls(data_css, tmp_path, _depth=5) == data_css


class TestReportLabImageHardening:
    def test_local_path_is_rejected(self, tmp_path):
        image = _write_file(tmp_path / "image.png")
        story = []
        tmp_imgs = []
        assert add_image_flowable(story, str(image), 100, tmp_imgs) is False
        assert story == []
        assert tmp_imgs == []

    def test_eps_data_uris_are_rejected(self):
        eps = b"%!PS-Adobe-3.0 EPSF-3.0\n%%BoundingBox: 0 0 1 1\nshowpage\n"
        encoded = base64.b64encode(eps).decode()
        for mime in ("image/eps", "application/postscript"):
            tmp_imgs = []
            assert add_image_flowable([], f"data:{mime};base64,{encoded}", 100, tmp_imgs) is False
            assert tmp_imgs == []

        tmp_imgs = []
        assert add_image_flowable([], f"data:image/png;base64,{encoded}", 100, tmp_imgs) is False
        assert tmp_imgs == []

    def test_png_data_uri_still_works(self):
        from PIL import Image

        buf = io.BytesIO()
        Image.new("RGB", (2, 2), "red").save(buf, format="PNG")
        uri = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
        story = []
        tmp_imgs = []
        try:
            assert add_image_flowable(story, uri, 100, tmp_imgs) is True
            assert story
            assert tmp_imgs
            assert Path(tmp_imgs[0]).exists()
        finally:
            for path in tmp_imgs:
                Path(path).unlink(missing_ok=True)


class TestWeasyPrintCompatibility:
    @staticmethod
    def _render_with_weasyprint(html, root, output):
        weasyprint = _weasyprint_or_skip()
        renderer = _renderer(True)
        sanitized = renderer._inline_all_resources(html, root)
        weasyprint.HTML(
            string=sanitized,
            url_fetcher=HtmlRenderers._safe_weasyprint_fetcher(),
        ).write_pdf(str(output))
        return sanitized

    @staticmethod
    def _pdf_text(path):
        fitz = pytest.importorskip("fitz")
        with fitz.open(path) as doc:
            return "\n".join(page.get_text() for page in doc)

    def test_safe_fetcher_uses_weasyprint_70_api(self):
        weasyprint = _weasyprint_or_skip()
        fetcher = HtmlRenderers._safe_weasyprint_fetcher()
        assert isinstance(fetcher, weasyprint.urls.URLFetcher)
        assert fetcher._allowed_protocols == ("http", "https", "data")
        assert fetcher._fail_on_errors is False

        with pytest.raises(ValueError):
            fetcher.fetch("ftp://example.com/image.png")
        with pytest.raises(ValueError):
            fetcher.fetch("file:///C:/secret.txt")

    def test_approved_local_resource_renders_with_weasyprint(self, tmp_path):
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="300" height="80">'
            '<text x="10" y="50" font-size="22">LOCAL_SENTINEL</text>'
            "</svg>"
        )
        (tmp_path / "inside.svg").write_text(svg, encoding="utf-8")
        output = tmp_path / "approved.pdf"
        sanitized = self._render_with_weasyprint(
            '<html><body><p>SAFE</p><img src="inside.svg"></body></html>',
            tmp_path,
            output,
        )
        assert "data:image/svg+xml;base64," in sanitized
        text = self._pdf_text(output)
        assert "SAFE" in text
        assert "LOCAL_SENTINEL" in text

    @pytest.mark.parametrize("kind", ["outside", "traversal", "file_url"])
    def test_unauthorized_local_resources_do_not_render_with_weasyprint(self, tmp_path, kind):
        outside = tmp_path.parent / f"{tmp_path.name}-outside.svg"
        outside.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="300" height="80">'
            '<text x="10" y="50" font-size="22">OUTSIDE_SENTINEL</text>'
            "</svg>",
            encoding="utf-8",
        )
        if kind == "outside":
            ref = outside.as_posix()
        elif kind == "traversal":
            ref = f"../{outside.name}"
        else:
            ref = outside.as_uri()

        output = tmp_path / f"{kind}.pdf"
        sanitized = self._render_with_weasyprint(
            f'<html><body><p>SAFE</p><img src="{ref}"></body></html>',
            tmp_path,
            output,
        )
        assert "OUTSIDE_SENTINEL" not in sanitized
        assert "data:image/svg+xml;base64," not in sanitized
        text = self._pdf_text(output)
        assert "SAFE" in text
        assert "OUTSIDE_SENTINEL" not in text
