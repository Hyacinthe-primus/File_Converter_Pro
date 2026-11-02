"""PDF protection template prefill, encryption, and permission tests."""

import io
from pathlib import Path

import fitz
import pytest
from pypdf import PdfReader
from pypdf.constants import UserAccessPermissions as P
from PySide6.QtWidgets import QDialog

import dialogs
from app.mixins import pdf_operations
from app.mixins.pdf_operations import (
    PdfOperationsMixin,
    _protect_pdf_file,
    _protection_permission_flags,
)
from dialogs.pdf_protection_dialog import PdfProtectionDialog
from templates import semantic_keys as sk


def _make_pdf(path):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "protection test")
    doc.save(path)
    doc.close()


def _reader(path):
    return PdfReader(io.BytesIO(Path(path).read_bytes()))


def _flags(allow_printing, allow_copying, allow_modifications):
    return _protection_permission_flags(
        allow_printing,
        allow_copying,
        allow_modifications,
    )


def _has(flags, permission):
    return bool(flags & permission)


class _FakeWidget:
    def selectedItems(self):
        return []


class _FakeProgress:
    def __init__(self):
        self.values = []

    def setValue(self, value):
        self.values.append(value)


class _FakeAchievements:
    def __init__(self):
        self.calls = []

    def record_pdf_protection(self, *args, **kwargs):
        self.calls.append((args, kwargs))


def _fake_self(tmp_path, active_templates):
    source = tmp_path / "source.pdf"
    _make_pdf(source)

    obj = PdfOperationsMixin.__new__(PdfOperationsMixin)
    obj.files_list_widget = _FakeWidget()
    obj.files_list = [str(source)]
    obj.current_language = "en"
    obj.active_templates = active_templates
    obj.translate_text = lambda key: key
    obj.get_output_directory = lambda: str(tmp_path)
    obj.show_progress = lambda *args, **kwargs: None
    obj.progress_bar = _FakeProgress()
    obj.achievement_system = _FakeAchievements()
    return obj, source


def _install_dialog(
    monkeypatch,
    mode,
    password,
    permissions,
    accepted=True,
    warnings=None,
):
    captured = {}

    class FakeDialog:
        def __init__(
            self,
            parent=None,
            language="fr",
            pre_select_mode=None,
            allow_printing=None,
            allow_copying=None,
            allow_modifications=None,
        ):
            captured.update(
                {
                    "parent": parent,
                    "language": language,
                    "pre_select_mode": pre_select_mode,
                    "allow_printing": allow_printing,
                    "allow_copying": allow_copying,
                    "allow_modifications": allow_modifications,
                }
            )

        def exec(self):
            return QDialog.Accepted if accepted else QDialog.Rejected

        def get_mode(self):
            return mode

        def get_password(self):
            return password

        def get_permissions(self):
            return dict(permissions)

    monkeypatch.setattr(dialogs, "PdfProtectionDialog", FakeDialog)
    monkeypatch.setattr(
        pdf_operations.QMessageBox,
        "information",
        staticmethod(lambda *args, **kwargs: None),
    )
    monkeypatch.setattr(
        pdf_operations.QMessageBox,
        "warning",
        staticmethod(lambda *args, **kwargs: warnings.append(args) if warnings is not None else None),
    )
    return captured


def _all_permissions():
    return {
        "allow_printing": True,
        "allow_copying": True,
        "allow_modifications": True,
    }


def _assert_permissions(flags, printing, copying, modifications):
    assert _has(flags, P.PRINT) is printing
    assert _has(flags, P.PRINT_TO_REPRESENTATION) is printing
    assert _has(flags, P.EXTRACT) is copying
    assert _has(flags, P.EXTRACT_TEXT_AND_GRAPHICS) is True
    assert _has(flags, P.MODIFY) is modifications
    assert _has(flags, P.ADD_OR_MODIFY) is modifications
    assert _has(flags, P.FILL_FORM_FIELDS) is modifications
    assert _has(flags, P.ASSEMBLE_DOC) is modifications


def test_dialog_defaults_to_advanced_and_allows_all_permissions(qapp):
    dialog = PdfProtectionDialog(None, "en")
    try:
        assert dialog.get_mode() == sk.PROTECTION_ADVANCED
        assert dialog.is_advanced()
        assert dialog.get_permissions() == _all_permissions()
        assert dialog.get_password() == ""
        assert not hasattr(dialog, "allow_annotations_check")
        assert not hasattr(dialog, "allow_forms_check")
        assert not hasattr(dialog, "allow_assemble_check")
        assert not hasattr(dialog, "allow_copy_accessibility_check")
    finally:
        dialog.deleteLater()
        qapp.processEvents()


def test_dialog_prefills_template_values(qapp):
    dialog = PdfProtectionDialog(
        None,
        "en",
        pre_select_mode=sk.PROTECTION_BASIC,
        allow_printing=False,
        allow_copying=False,
        allow_modifications=False,
    )
    try:
        assert dialog.get_mode() == sk.PROTECTION_BASIC
        assert not dialog.is_advanced()
        assert dialog.get_password() is None
        assert dialog.get_permissions() == {
            "allow_printing": False,
            "allow_copying": False,
            "allow_modifications": False,
        }
    finally:
        dialog.deleteLater()
        qapp.processEvents()


@pytest.mark.parametrize(
    "mode,printing,copying,modifications",
    [
        ("invalid", "yes", None, 0),
        (None, None, None, None),
    ],
)
def test_dialog_invalid_or_missing_template_values_fall_back(
    qapp, mode, printing, copying, modifications
):
    dialog = PdfProtectionDialog(
        None,
        "en",
        pre_select_mode=mode,
        allow_printing=printing,
        allow_copying=copying,
        allow_modifications=modifications,
    )
    try:
        assert dialog.get_mode() == sk.PROTECTION_ADVANCED
        assert dialog.get_permissions() == _all_permissions()
    finally:
        dialog.deleteLater()
        qapp.processEvents()


def test_dialog_manual_changes_override_template_values(qapp):
    dialog = PdfProtectionDialog(
        None,
        "en",
        pre_select_mode=sk.PROTECTION_BASIC,
        allow_printing=False,
        allow_copying=False,
        allow_modifications=False,
    )
    try:
        dialog.mode_combo.setCurrentIndex(1)
        dialog.allow_print_check.setChecked(True)
        dialog.allow_copy_check.setChecked(True)
        dialog.allow_modify_check.setChecked(True)

        assert dialog.get_mode() == sk.PROTECTION_ADVANCED
        assert dialog.get_permissions() == _all_permissions()
    finally:
        dialog.deleteLater()
        qapp.processEvents()


def test_advanced_password_validation(monkeypatch, qapp):
    warnings = []
    monkeypatch.setattr(
        dialogs.pdf_protection_dialog.QMessageBox,
        "warning",
        staticmethod(lambda *args, **kwargs: warnings.append(args)),
    )

    dialog = PdfProtectionDialog(None, "en")
    try:
        dialog.password_input.setText("")
        dialog._validate()
        assert dialog.result() != QDialog.Accepted

        dialog.password_input.setText("secret")
        dialog.confirm_input.setText("different")
        dialog._validate()
        assert dialog.result() != QDialog.Accepted

        dialog.confirm_input.setText("secret")
        dialog._validate()
        assert dialog.result() == QDialog.Accepted
        assert len(warnings) == 2
    finally:
        dialog.deleteLater()
        qapp.processEvents()


def test_basic_mode_does_not_require_a_password(qapp):
    dialog = PdfProtectionDialog(None, "en", pre_select_mode=sk.PROTECTION_BASIC)
    try:
        dialog._validate()
        assert dialog.result() == QDialog.Accepted
        assert dialog.get_password() is None
    finally:
        dialog.deleteLater()
        qapp.processEvents()


def test_exact_permission_bit_mapping():
    _assert_permissions(_flags(True, True, True), True, True, True)
    _assert_permissions(_flags(False, True, True), False, True, True)
    _assert_permissions(_flags(True, False, True), True, False, True)
    _assert_permissions(_flags(True, True, False), True, True, False)
    _assert_permissions(_flags(False, False, False), False, False, False)


def test_no_template_defaults_to_advanced_and_all_permissions(monkeypatch, tmp_path):
    obj, source = _fake_self(tmp_path, {})
    captured = _install_dialog(
        monkeypatch,
        sk.PROTECTION_ADVANCED,
        "secret",
        _all_permissions(),
    )

    obj.protect_pdf()

    assert captured["pre_select_mode"] == sk.PROTECTION_ADVANCED
    assert captured["allow_printing"] is True
    assert captured["allow_copying"] is True
    assert captured["allow_modifications"] is True

    output = tmp_path / f"protected_{source.name}"
    assert output.exists()
    reader = _reader(output)
    assert reader.is_encrypted
    assert reader.decrypt("wrong") == 0
    assert reader.decrypt("secret") == 1
    _assert_permissions(reader.user_access_permissions, True, True, True)
    assert obj.achievement_system.calls == [((1, len("secret")), {})]


def test_template_prefills_dialog_and_protect_pdf_uses_final_values(
    monkeypatch, tmp_path
):
    obj, source = _fake_self(
        tmp_path,
        {
            sk.PDF_PROTECTION: {
                "protection_level": sk.PROTECTION_BASIC,
                "allow_printing": False,
                "allow_copying": True,
                "allow_modifications": False,
            }
        },
    )
    captured = _install_dialog(
        monkeypatch,
        sk.PROTECTION_ADVANCED,
        "manual-password",
        _all_permissions(),
    )

    obj.protect_pdf()

    assert captured["pre_select_mode"] == sk.PROTECTION_BASIC
    assert captured["allow_printing"] is False
    assert captured["allow_copying"] is True
    assert captured["allow_modifications"] is False

    output = tmp_path / f"protected_{source.name}"
    reader = _reader(output)
    assert reader.is_encrypted
    assert reader.decrypt("manual-password") == 1
    _assert_permissions(reader.user_access_permissions, True, True, True)


def test_missing_or_invalid_template_values_are_ignored(monkeypatch, tmp_path):
    obj, _ = _fake_self(
        tmp_path,
        {
            sk.PDF_PROTECTION: {
                "protection_level": "not-a-mode",
                "allow_printing": "yes",
                "allow_copying": None,
                "allow_modifications": 0,
            }
        },
    )
    captured = _install_dialog(
        monkeypatch,
        sk.PROTECTION_ADVANCED,
        "secret",
        _all_permissions(),
    )

    obj.protect_pdf()

    assert captured["pre_select_mode"] == "not-a-mode"
    assert captured["allow_printing"] is None
    assert captured["allow_copying"] is None
    assert captured["allow_modifications"] is None


def test_basic_pdf_round_trip(monkeypatch, tmp_path):
    obj, source = _fake_self(tmp_path, {})
    permissions = {
        "allow_printing": False,
        "allow_copying": False,
        "allow_modifications": False,
    }
    _install_dialog(monkeypatch, sk.PROTECTION_BASIC, None, permissions)

    obj.protect_pdf()

    output = tmp_path / f"protected_{source.name}"
    reader = _reader(output)
    assert reader.is_encrypted
    assert reader.decrypt("") == 1
    _assert_permissions(reader.user_access_permissions, False, False, False)
    encryption = reader.trailer["/Encrypt"]
    assert encryption["/V"] == 5
    assert encryption["/R"] == 6
    assert encryption["/Length"] == 256

    pdf_doc = fitz.open(output)
    try:
        assert pdf_doc.needs_pass == 0
        assert pdf_doc.is_encrypted is False
    finally:
        pdf_doc.close()
    assert obj.achievement_system.calls == [((1, 0), {})]


def test_advanced_pdf_round_trip(monkeypatch, tmp_path):
    obj, source = _fake_self(tmp_path, {})
    permissions = {
        "allow_printing": True,
        "allow_copying": False,
        "allow_modifications": False,
    }
    _install_dialog(monkeypatch, sk.PROTECTION_ADVANCED, "correct", permissions)

    obj.protect_pdf()

    output = tmp_path / f"protected_{source.name}"
    reader = _reader(output)
    assert reader.is_encrypted
    assert reader.decrypt("incorrect") == 0
    assert reader.decrypt("correct") == 1
    _assert_permissions(reader.user_access_permissions, True, False, False)
    encryption = reader.trailer["/Encrypt"]
    assert encryption["/V"] == 5
    assert encryption["/R"] == 6


def test_random_owner_passwords_differ_between_documents(monkeypatch, tmp_path):
    source = tmp_path / "source.pdf"
    _make_pdf(source)
    generated = []

    def fake_token_urlsafe(length):
        value = f"owner-{len(generated)}"
        generated.append(value)
        return value

    monkeypatch.setattr(pdf_operations.secrets, "token_urlsafe", fake_token_urlsafe)

    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"
    _protect_pdf_file(str(source), str(first), "", True, True, True)
    _protect_pdf_file(str(source), str(second), "", True, True, True)

    assert generated == ["owner-0", "owner-1"]
    assert len(set(generated)) == 2


def test_advanced_owner_password_is_not_the_user_password(monkeypatch, tmp_path):
    source = tmp_path / "source.pdf"
    _make_pdf(source)
    generated = []
    monkeypatch.setattr(
        pdf_operations.secrets,
        "token_urlsafe",
        lambda length: generated.append("owner-password") or "owner-password",
    )

    output = tmp_path / "protected.pdf"
    _protect_pdf_file(str(source), str(output), "user-password", True, True, True)

    assert generated == ["owner-password"]
    assert generated[0] != "user-password"


def test_cancellation_does_not_create_output(monkeypatch, tmp_path):
    obj, source = _fake_self(tmp_path, {})
    _install_dialog(
        monkeypatch,
        sk.PROTECTION_ADVANCED,
        "secret",
        _all_permissions(),
        accepted=False,
    )

    obj.protect_pdf()

    assert not (tmp_path / f"protected_{source.name}").exists()
    assert not list(tmp_path.glob(".fcp_protect_*"))


def test_advanced_without_password_does_not_create_output(monkeypatch, tmp_path):
    obj, source = _fake_self(tmp_path, {})
    warnings = []
    _install_dialog(
        monkeypatch,
        sk.PROTECTION_ADVANCED,
        None,
        _all_permissions(),
        warnings=warnings,
    )

    obj.protect_pdf()

    assert warnings
    assert not (tmp_path / f"protected_{source.name}").exists()
    assert not list(tmp_path.glob(".fcp_protect_*"))


def test_protection_failure_leaves_no_unencrypted_output(monkeypatch, tmp_path):
    obj, source = _fake_self(tmp_path, {})
    source.write_bytes(b"not a pdf")
    _install_dialog(
        monkeypatch,
        sk.PROTECTION_BASIC,
        None,
        _all_permissions(),
    )

    obj.protect_pdf()

    assert not (tmp_path / f"protected_{source.name}").exists()
    assert not list(tmp_path.glob(".fcp_protect_*"))
    assert obj.achievement_system.calls == []
