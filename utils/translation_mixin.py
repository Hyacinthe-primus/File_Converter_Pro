"""TranslationMixin — shared translate_text for all dialogs and widgets."""



class TranslationMixin:
    """Mixin providing translate_text() via self._tm.

    Subclasses must set self._tm = TranslationManager() in __init__
    (or use self.translation_manager / self._translation_manager).
    """

    def translate_text(self, text: str) -> str:
        tm = getattr(self, '_tm', None) or getattr(self, 'translation_manager', None) or getattr(self, '_translation_manager', None)
        if tm is None:
            return text
        return tm.translate_text(text)
