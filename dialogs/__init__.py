"""
dialogs/ package grouping all dialog boxes of File Converter Pro.

Re-exports public classes so that app.py can continue to write:
    from dialogs import SettingsDialog, PasswordDialog, SplitDialog, ...

"""

from .pdf_to_word_dialog import PdfToWordDialog
from .splash_screen import ModernSplashScreen
from .preview_dialog import PreviewDialog
from .password_dialog import PasswordDialog
from .split_dialog import SplitDialog
from .compression_dialog import CompressionDialog
from .batch_convert_dialog import BatchConvertDialog
from .batch_rename_dialog import BatchRenameDialog
from .settings_dialog import SettingsDialog
from .conversion_options_dialog import ConversionOptionsDialog
from .terms_dialog import TermsAndPrivacyDialog
from .word_to_pdf_dialog import WordToPdfOptionsDialog
from .pdf_protection_dialog import PdfProtectionDialog
from .merge_order_dialog import MergeOrderDialog

__all__ = [
    "PdfToWordDialog",
    "ModernSplashScreen",
    "PreviewDialog",
    "PasswordDialog",
    "SplitDialog",
    "CompressionDialog",
    "BatchConvertDialog",
    "BatchRenameDialog",
    "SettingsDialog",
    "ConversionOptionsDialog",
    "TermsAndPrivacyDialog",
    "WordToPdfOptionsDialog",
    "PdfProtectionDialog",
    "MergeOrderDialog",
]
