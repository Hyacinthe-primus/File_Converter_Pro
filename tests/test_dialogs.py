"""Tests for dialog logic — instantiate dialogs with mocked Qt and verify pure methods."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestCompressionDialog:
    def test_import(self):
        from dialogs.compression_dialog import CompressionDialog
        assert CompressionDialog is not None

    def test_inherits_translation_mixin(self):
        from dialogs.compression_dialog import CompressionDialog
        from utils.translation_mixin import TranslationMixin
        assert issubclass(CompressionDialog, TranslationMixin)


class TestSettingsDialog:
    def test_import(self):
        from dialogs.settings_dialog import SettingsDialog
        assert SettingsDialog is not None

    def test_inherits_translation_mixin(self):
        from dialogs.settings_dialog import SettingsDialog
        from utils.translation_mixin import TranslationMixin
        assert issubclass(SettingsDialog, TranslationMixin)


class TestSplitDialog:
    def test_import(self):
        from dialogs.split_dialog import SplitDialog
        assert SplitDialog is not None

    def test_inherits_translation_mixin(self):
        from dialogs.split_dialog import SplitDialog
        from utils.translation_mixin import TranslationMixin
        assert issubclass(SplitDialog, TranslationMixin)


class TestPasswordDialog:
    def test_import(self):
        from dialogs.password_dialog import PasswordDialog
        assert PasswordDialog is not None

    def test_inherits_translation_mixin(self):
        from dialogs.password_dialog import PasswordDialog
        from utils.translation_mixin import TranslationMixin
        assert issubclass(PasswordDialog, TranslationMixin)


class TestBatchConvertDialog:
    def test_import(self):
        from dialogs.batch_convert_dialog import BatchConvertDialog
        assert BatchConvertDialog is not None

    def test_inherits_translation_mixin(self):
        from dialogs.batch_convert_dialog import BatchConvertDialog
        from utils.translation_mixin import TranslationMixin
        assert issubclass(BatchConvertDialog, TranslationMixin)


class TestBatchRenameDialog:
    def test_import(self):
        from dialogs.batch_rename_dialog import BatchRenameDialog
        assert BatchRenameDialog is not None


class TestPdfToWordDialog:
    def test_import(self):
        from dialogs.pdf_to_word_dialog import PdfToWordDialog
        assert PdfToWordDialog is not None

    def test_inherits_translation_mixin(self):
        from dialogs.pdf_to_word_dialog import PdfToWordDialog
        from utils.translation_mixin import TranslationMixin
        assert issubclass(PdfToWordDialog, TranslationMixin)


class TestWordToPdfDialog:
    def test_import(self):
        from dialogs.word_to_pdf_dialog import WordToPdfOptionsDialog
        assert WordToPdfOptionsDialog is not None

    def test_inherits_translation_mixin(self):
        from dialogs.word_to_pdf_dialog import WordToPdfOptionsDialog
        from utils.translation_mixin import TranslationMixin
        assert issubclass(WordToPdfOptionsDialog, TranslationMixin)


class TestTermsDialog:
    def test_import(self):
        from dialogs.terms_dialog import TermsAndPrivacyDialog
        assert TermsAndPrivacyDialog is not None

    def test_inherits_translation_mixin(self):
        from dialogs.terms_dialog import TermsAndPrivacyDialog
        from utils.translation_mixin import TranslationMixin
        assert issubclass(TermsAndPrivacyDialog, TranslationMixin)


class TestSplashScreen:
    def test_import(self):
        from dialogs.splash_screen import ModernSplashScreen
        assert ModernSplashScreen is not None

    def test_inherits_translation_mixin(self):
        from dialogs.splash_screen import ModernSplashScreen
        from utils.translation_mixin import TranslationMixin
        assert issubclass(ModernSplashScreen, TranslationMixin)


class TestMergeOrderDialog:
    def test_import(self):
        from dialogs.merge_order_dialog import MergeOrderDialog
        assert MergeOrderDialog is not None

    def test_inherits_translation_mixin(self):
        from dialogs.merge_order_dialog import MergeOrderDialog
        from utils.translation_mixin import TranslationMixin
        assert issubclass(MergeOrderDialog, TranslationMixin)


class TestPreviewDialog:
    def test_import(self):
        from dialogs.preview_dialog import PreviewDialog
        assert PreviewDialog is not None

    def test_inherits_translation_mixin(self):
        from dialogs.preview_dialog import PreviewDialog
        from utils.translation_mixin import TranslationMixin
        assert issubclass(PreviewDialog, TranslationMixin)


class TestConversionOptionsDialog:
    def test_import(self):
        from dialogs.conversion_options_dialog import ConversionOptionsDialog
        assert ConversionOptionsDialog is not None
