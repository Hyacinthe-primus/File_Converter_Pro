"""
dialogs/ package grouping all dialog boxes of File Converter Pro.

Re-exports public classes so that app.py can continue to write:
    from dialogs import SettingsDialog, PasswordDialog, SplitDialog, ...

"""

from .dialogs import (
    PdfToWordDialog,
    SettingsDialog,
    PasswordDialog,
    SplitDialog,
    CompressionDialog,
    BatchConvertDialog,
    BatchRenameDialog,
    ConversionOptionsDialog,
    PreviewDialog,
    ModernSplashScreen,
)
from .terms_dialog import TermsAndPrivacyDialog
from .word_to_pdf_dialog import WordToPdfOptionsDialog

__all__ = [
    "PdfToWordDialog",
    "SettingsDialog",
    "PasswordDialog",
    "SplitDialog",
    "CompressionDialog",
    "BatchConvertDialog",
    "BatchRenameDialog",
    "ConversionOptionsDialog",
    "PreviewDialog",
    "ModernSplashScreen",
    "TermsAndPrivacyDialog",
    "WordToPdfOptionsDialog",
]