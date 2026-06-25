"""ThemeLanguageMixin — Theme and language management methods."""

import time

from PySide6.QtWidgets import (QGroupBox, QPushButton, QLabel, QCheckBox)

from qss_helpers import _load_qss, set_theme, get_current_theme


class ThemeLanguageMixin:
    """Mixin: theme and language management for FileConverterApp."""

    def toggle_theme(self):
        self._toggle_theme_actual()

    def _toggle_theme_actual(self):
        self.config["use_system_theme"] = False
        self.config.pop("custom_theme", None)
        self.config_manager.save_config(self.config)
        if self.dark_mode:
            self.dark_mode_timer_start = time.time()
        else:
            if self.dark_mode_timer_start is not None:
                elapsed = (time.time() - self.dark_mode_timer_start) / 60
                self.achievement_system.add_dark_mode_time(elapsed)
                self.dark_mode_timer_start = None

        self.dark_mode = not self.dark_mode
        self.current_theme = "dark" if self.dark_mode else "light"
        self.apply_theme(self.dark_mode)
        self.theme_action.setText("☀️ " + self.translate_text("Mode Clair") if self.dark_mode else "🌙 " + self.translate_text("Mode Sombre"))

        self.config["dark_mode"] = self.dark_mode
        self.config_manager.save_config(self.config)

        logo = self.findChild(QLabel, "LogoLabel")
        if logo:
            logo_color = "#e8ff6b" if self.dark_mode else "#2d2dc8"
            logo.setStyleSheet(
                "font-family:'Segoe UI','SF Pro Display',Arial,sans-serif;"
                "font-size:16px;font-weight:900;"
                "letter-spacing:1.5px;background:transparent;"
                f"color:{logo_color};"
            )

    def update_dark_mode_time(self):
        if self.dark_mode:
            if self.dark_mode_timer_start is None:
                self.dark_mode_timer_start = time.time()
            else:
                elapsed = (time.time() - self.dark_mode_timer_start) / 60
                self.achievement_system.add_dark_mode_time(elapsed)
                self.dark_mode_timer_start = time.time()

    def _get_language_label(self, code: str) -> str:
        for lang in self.translation_manager.get_available_languages():
            if lang["code"] == code:
                name = lang["name"]
                if code == "fr":
                    return f"🇫🇷 {name}"
                elif code == "en":
                    return f"🇬🇧 {name}"
                else:
                    return f"🌐 {name}"
        return f"🌐 {code}"

    def toggle_language(self):
        available = [lang["code"] for lang in self.translation_manager.get_available_languages()]
        if not available:
            return
        try:
            idx = available.index(self.current_language)
        except ValueError:
            idx = 0
        new_language = available[(idx + 1) % len(available)]

        self.current_language = new_language
        self.translation_manager.set_language(new_language)
        self.system_notifier.set_language(new_language)
        if hasattr(self, 'files_list_widget'):
            self.files_list_widget.set_language(new_language)

        self.config["language"] = new_language
        self.config_manager.save_config(self.config)
        self.create_menu_bar()

        self.update_texts()

        self.language_action.setText(self._get_language_label(new_language))

    def update_texts(self):
        self.setWindowTitle("File Converter Pro - Professional File Converter")
        self.update_file_counter()
        self.status_bar.showMessage(self.translate_text("Prêt - Sélectionnez des fichiers pour commencer"))

        for widget in self.findChildren(QGroupBox):
            key = widget.property("i18n_key")
            if key:
                widget.setTitle(self.translate_text(key).upper())

        for widget in self.findChildren(QPushButton):
            key = widget.property("i18n_key")
            if key:
                parts = widget.text().split(" ", 1)
                prefix = parts[0] + " " if len(parts) == 2 else ""
                widget.setText(prefix + self.translate_text(key))

        for widget in self.findChildren(QLabel):
            key = widget.property("i18n_key")
            if key:
                widget.setText(self.translate_text(key))

        for widget in self.findChildren(QCheckBox):
            key = widget.property("i18n_key")
            if key:
                widget.setText(self.translate_text(key))

        self.theme_action.setText(("☀️ " if self.dark_mode else "🌙 ") + self.translate_text("Mode Clair" if self.dark_mode else "Mode Sombre"))
        self.new_action.setText("🆕 " + self.translate_text("Nouveau Projet"))
        self.open_action.setText("📂 " + self.translate_text("Ouvrir Projet"))
        self.save_action.setText("💾 " + self.translate_text("Enregistrer Projet"))
        self.setup_tooltips_with_shortcuts()

    def apply_theme(self, dark: bool) -> None:
        current = getattr(self, "current_theme", None)
        if current and current not in ("dark", "light"):
            theme_name = current
        else:
            theme_name = "dark" if dark else "light"
        set_theme(theme_name)
        self.setStyleSheet(_load_qss("style.qss", theme_name))
