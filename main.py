"""
Entry Point - File Converter Pro

Application startup logic, CLI handling, and window management.

Modes of Execution:
    1. GUI Mode (Default):
        - Initializes QApplication with global icon
        - Checks for single instance via QLocalServer
        - Displays animated splash screen
        - Performs cross-fade transition to main window
        - Validates Terms & Privacy acceptance

    2. CLI Mode (Arguments):
        - status:                 Display all achievement states
        - reset <id>:             Reset specific achievement
        - unlock <id>:            Manually unlock achievement
        - reset-all:              Wipe all achievement progress
        - help / -h:              Display CLI usage instructions
        --lang fr                 Force language (e.g. fr, en, en-revisited, or any .lang name)
        --theme dark/light        Force theme (dark or light)
        --lang fr --theme dark    Force both language and theme

Author: Hyacinthe
Version: 1.0
"""

import sys
import os
from datetime import datetime

if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

# Third-Party
from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtCore    import Qt, QTimer
from PySide6.QtGui     import QIcon

from config  import ConfigManager, is_dark_mode, is_dark_mode_qt
from app     import FadingMainWindow
from dialogs import ModernSplashScreen, TermsAndPrivacyDialog

SOCKET_NAME         = "FileConverterPro_SingleInstance"

SPLASH_DELAY        = 3000
FADEIN_DELAY        = 100
STATUSBAR_DELAY     = 700
SPLASH_DELETE_DELAY = 1100

CLI_COMMANDS = frozenset({"status", "reset", "unlock", "reset-all", "-h", "--help", "help"})

def get_dropped_files(argv: list[str]) -> list[str]:
    """
    Returns file paths passed via drag-and-drop onto the exe icon.
    Windows passes them as sys.argv[1], sys.argv[2], etc.
    Only returns paths that actually exist on disk.
    Ignores CLI commands, language flags, and theme flags.
    """
    skip_next = False
    result = []
    for arg in argv[1:]:
        if skip_next:
            skip_next = False
            continue
        if arg in ("--lang", "--theme"):
            skip_next = True
            continue
        if (arg in CLI_COMMANDS
                or arg.startswith("--lang=")
                or arg.startswith("--lang:")
                or arg.startswith("--theme=")
                or arg.startswith("--theme:")
                or _is_lang_flag(arg)):
            continue
        if os.path.exists(arg) and not arg.lower().endswith('.fcproj'):
            result.append(arg)
    return result

def _is_lang_flag(arg: str) -> bool:
    """Return True for  --fr  --en  --de  --en-revisited  etc."""
    if not arg.startswith("--"):
        return False
    code = arg[2:].strip('"').strip("'")
    return bool(code) and all(c.isalnum() or c in "-_." for c in code)

def get_forced_language(argv: list[str]) -> str | None:
    """
    Parse a forced-language flag from the command line.

    Accepted forms

    --fr                          → "fr"
    --en                          → "en"
    --en-revisited                → "en-revisited"
    --"en revisited"              → "en revisited"   (name with space, quoted by shell)
    --lang fr                     → "fr"             (installer / generic form)
    --lang=fr                     → "fr"
    --lang en-revisited           → "en-revisited"

    The value is returned as-is (lowercased).  The caller decides whether it
    maps to a built-in code or a .lang file name.
    """
    args = argv[1:]
    i = 0
    while i < len(args):
        a = args[i]

        if a == "--lang":
            if i + 1 < len(args):
                return args[i + 1].strip().lower()
            i += 1
            continue
        if a.startswith("--lang="):
            return a.split("=", 1)[1].strip().lower()
        if a.startswith("--lang:"):
            return a.split(":", 1)[1].strip().lower()

        if a.startswith(("--theme=", "--theme:")):
            i += 1
            continue
        if a == "--theme":
            i += 2
            continue
        if a.startswith("--") and a not in CLI_COMMANDS:
            code = a[2:].strip('"').strip("'").strip().lower()
            if code and all(c.isalnum() or c in "-_. " for c in code):
                return code

        i += 1
    return None

def get_forced_theme(argv: list[str]) -> str | None:
    """
    Parse a forced-theme flag from the command line.

    Accepted forms

    --theme dark          → "dark"
    --theme=dark          → "dark"
    --theme light         → "light"
    --theme=light         → "light"

    Returns "dark", "light", or None if no flag is present.
    Unknown values are ignored (returns None).
    """
    VALID_THEMES = {"dark", "light"}
    args = argv[1:]
    i = 0
    while i < len(args):
        a = args[i]

        if a == "--theme":
            if i + 1 < len(args):
                value = args[i + 1].strip().lower()
                return value if value in VALID_THEMES else None
            i += 1
            continue
        if a.startswith("--theme="):
            value = a.split("=", 1)[1].strip().lower()
            return value if value in VALID_THEMES else None
        if a.startswith("--theme:"):
            value = a.split(":", 1)[1].strip().lower()
            return value if value in VALID_THEMES else None

        i += 1
    return None


class CLIHandler:
    """Parses and dispatches CLI achievement commands."""

    HELP_TEXT = """
==================================================
 CLI USAGE - FILE CONVERTER PRO
==================================================
  main.py status                  — Display status of all achievements
  main.py reset <achievement_id>  — Reset a specific achievement
  main.py unlock <achievement_id> — Unlock a specific achievement
  main.py reset-all               — Reset all achievements
  main.py -h / --help             — Display this help
  main.py --lang fr               — Force language (e.g. fr, en, en-revisited, or any .lang name)
  main.py --theme dark/light      — Force theme (dark or light)
  main.py --lang fr --theme dark  — Force both language and theme

Examples:
  main.py status
  main.py reset  first_adventure
  main.py unlock apprentice
  main.py reset-all
"""

    def __init__(self, argv: list[str]) -> None:
        self.argv    = argv
        self.command = argv[1].lower() if len(argv) > 1 else None
        self._mgr    = None

    def is_cli_mode(self) -> bool:
        return self.command in CLI_COMMANDS

    def run(self) -> None:
        """Dispatch to the matching handler, then exit."""
        print(f"[DEBUG] CLI command : {self.command}")
        print(f"[DEBUG] Arguments   : {self.argv}")

        dispatch = {
            "status"   : self._cmd_status,
            "reset"    : self._cmd_reset,
            "unlock"   : self._cmd_unlock,
            "reset-all": self._cmd_reset_all,
            "-h"       : self._cmd_help,
            "--help"   : self._cmd_help,
            "help"     : self._cmd_help,
        }

        handler = dispatch.get(self.command)
        if handler:
            handler()
        else:
            print(f"Unknown command: {self.command}")
            print("Use 'main.py -h' for help.")
            sys.exit(1)

        sys.exit(0)

    def _cmd_status(self) -> None:
        self._print_section("ACHIEVEMENTS STATUS - FILE CONVERTER PRO")
        self._mgr_show_status()

    def _cmd_reset(self) -> None:
        self._require_arg("reset")
        print(f"\nRESETTING ACHIEVEMENT: {self.argv[2]}")
        self._mgr_reset_one(self.argv[2])

    def _cmd_unlock(self) -> None:
        self._require_arg("unlock")
        print(f"\nUNLOCKING ACHIEVEMENT: {self.argv[2]}")
        self._mgr_unlock_one(self.argv[2])

    def _cmd_reset_all(self) -> None:
        self._print_section("WARNING: RESETTING ALL ACHIEVEMENTS")
        if input("Are you sure? (yes/no): ").lower() == "yes":
            self._mgr_reset_all()

    def _cmd_help(self) -> None:
        print(self.HELP_TEXT)

    def _require_arg(self, command: str) -> None:
        if len(self.argv) < 3:
            print(f"Usage: main.py {command} <achievement_id>")
            sys.exit(1)

    @staticmethod
    def _print_section(title: str) -> None:
        print("\n" + "=" * 50)
        print(title)
        print("=" * 50)

    def _load_manager(self) -> None:
        """Lazy-load achievement CLI functions from achievements_manager."""
        if self._mgr is not None:
            return
        try:
            from achievements.achievements_manager import (
                show_achievements_status_cli    as show_status,
                reset_specific_achievement_cli  as reset_one,
                unlock_specific_achievement_cli as unlock_one,
                reset_all_achievements_cli      as reset_all,
            )
            self._mgr = (show_status, reset_one, unlock_one, reset_all)
        except Exception as exc:
            print(f"\n[ERROR] Unable to execute CLI command: {exc}")
            print("Make sure achievements.db exists in the current directory.")
            sys.exit(1)

    def _mgr_show_status(self)         : self._load_manager(); self._mgr[0]()
    def _mgr_reset_one(self, aid: str) : self._load_manager(); self._mgr[1](aid)
    def _mgr_unlock_one(self, aid: str): self._load_manager(); self._mgr[2](aid)
    def _mgr_reset_all(self)           : self._load_manager(); self._mgr[3]()


class SingleInstanceGuard:
    """Exits if another instance of the application is already running."""

    def __init__(self) -> None:
        self._server = None

    def acquire(self) -> None:
        try:
            from PySide6.QtNetwork import QLocalSocket, QLocalServer

            sock = QLocalSocket()
            sock.connectToServer(SOCKET_NAME)
            if sock.waitForConnected(1000):
                print("An instance of the application is already running.")
                sys.exit(0)

            self._server = QLocalServer()
            self._server.listen(SOCKET_NAME)

        except ImportError:
            print("[WARN] Single-instance feature not available (QtNetwork missing).")


class AppBootstrap:
    """Creates the QApplication and loads initial configuration."""

    _ICON_CANDIDATES = [
        lambda: os.path.join(os.path.dirname(__file__), "icon.ico"),
        lambda: "icon.ico",
        lambda: os.path.join(os.getcwd(), "icon.ico"),
        lambda: os.path.join(getattr(sys, "_MEIPASS", ""), "icon.ico"),
    ]

    def __init__(self, forced_language: str | None = None, forced_theme: str | None = None) -> None:
        self.config_manager  = ConfigManager()
        self.forced_language = forced_language
        self.forced_theme    = forced_theme
        self.app    = None
        self.config = None

    def setup(self) -> "AppBootstrap":
        self.app    = self._create_app()
        self.config = self._load_config()
        return self

    def _create_app(self) -> QApplication:
        app       = QApplication(sys.argv)
        icon_path = self._resolve_icon()

        if icon_path:
            icon = QIcon(icon_path)
            app.setWindowIcon(icon)
            QApplication.setWindowIcon(icon)
        else:
            print("[WARN] icon.ico not found — default icon used.")

        return app

    def _load_config(self) -> dict:
        config = self.config_manager.load_config()

        # Forced language (--fr / --en / --en-revisited / --lang <code>)
        if self.forced_language:
            config["language"] = self.forced_language
            self.config_manager.save_config(config)
            print(f"[LANG] Language forced to: {self.forced_language!r}")
        elif "language" not in config:
            config["language"] = "fr"
            self.config_manager.save_config(config)

        if self.forced_theme is not None:
            config["dark_mode"]         = (self.forced_theme == "dark")
            config["use_system_theme"]  = False
            self.config_manager.save_config(config)
            print(f"[THEME] Theme forced to: {self.forced_theme!r}")
        elif config.get("use_system_theme", True):
            config["dark_mode"] = is_dark_mode()
            self.config_manager.save_config(config)

        return config

    @classmethod
    def _resolve_icon(cls) -> str | None:
        return next(
            (path for c in cls._ICON_CANDIDATES if os.path.exists(path := c())),
            None,
        )


class TermsGuard:
    """Shows the Terms & Privacy dialog when user acceptance is required."""

    def __init__(self, config: dict, config_manager: ConfigManager) -> None:
        self.config         = config
        self.config_manager = config_manager

    def enforce(self) -> None:
        """Show the dialog if needed; exit the process if user refuses."""
        if self._already_accepted():
            return

        dialog = TermsAndPrivacyDialog(language=self.config.get("language", "fr"), dark_mode=self.config.get("dark_mode", False))
        if dialog.exec() != QDialog.Accepted:
            sys.exit(0)

        self._record_acceptance()

    def _already_accepted(self) -> bool:
        return (
            self.config.get("accepted_terms",   False)
            and self.config.get("accepted_privacy", False)
        )

    def _record_acceptance(self) -> None:
        now = datetime.now().isoformat()
        self.config["accepted_terms"]   = True
        self.config["accepted_privacy"] = True

        if self.config.get("terms_acceptance_timestamp") is not None:
            self.config["terms_reacceptance_timestamp"] = now
            print(f"[TERMS] ✅ Re-acceptance — timestamp: {now}")
        else:
            self.config["terms_acceptance_timestamp"] = now
            print(f"[TERMS] ℹ️  First acceptance — timestamp: {now}")

        self.config_manager.save_config(self.config)


class WindowTransition:
    """Animated crossfade from the splash screen to the main window."""

    def __init__(
        self,
        splash: ModernSplashScreen,
        config_manager: ConfigManager,
        dropped_files: list[str] | None = None,
    ) -> None:
        self.splash         = splash
        self.config_manager = config_manager
        self.dropped_files  = dropped_files or []

    def start(self) -> None:
        win = self._build_main_window()
        self._schedule(win)

    def _build_main_window(self) -> FadingMainWindow:
        win = FadingMainWindow(self.config_manager)
        win.hide()
        win.setAttribute(Qt.WA_TranslucentBackground)
        win.setWindowOpacity(0.0)
        win.show()
        win.raise_()
        win.activateWindow()
        return win

    def _schedule(self, win: FadingMainWindow) -> None:
        """
        Schedule the startup UI transitions:
        - Crossfade between the splash screen and the main window.
        - Safely fade out and delete the splash screen after the animation.
        - Display a ready message in the status bar after a delay.
        - Load dropped files (if any) once the UI is ready.

        Timings are coordinated to avoid visual glitches and ensure smooth transitions.
        """
        FADE_OUT_DURATION = 500

        def _crossfade():
            win.fade_in(600)
            try:
                self.splash.fade_out(FADE_OUT_DURATION)
            except RuntimeError:
                return
            QTimer.singleShot(FADE_OUT_DURATION + 100, self.splash.deleteLater)

        QTimer.singleShot(FADEIN_DELAY, _crossfade)

        QTimer.singleShot(STATUSBAR_DELAY, lambda:
            win.status_bar.showMessage(
                win.translate_text("Prêt - Sélectionnez des fichiers pour commencer")
            )
        )

        if self.dropped_files:
            QTimer.singleShot(
                FADEIN_DELAY + FADE_OUT_DURATION + 200,
                lambda: self._load_dropped_files(win),
            )

    def _load_dropped_files(self, win: FadingMainWindow) -> None:
        """Pass dragged files to the main window file list."""
        if hasattr(win, 'add_files_to_list'):
            win.add_files_to_list(self.dropped_files)
            win.status_bar.showMessage(
                f"{len(self.dropped_files)} file(s) loaded automatically"
            )
        else:
            print(f"[WARN] add_files_to_list not found — dropped files ignored: {self.dropped_files}")


def main() -> None:
    cli = CLIHandler(sys.argv)
    if cli.is_cli_mode():
        cli.run()

    dropped_files = get_dropped_files(sys.argv)
    if dropped_files:
        print(f"[INFO] Files dropped on icon: {dropped_files}")

    forced_language = get_forced_language(sys.argv)

    forced_theme = get_forced_theme(sys.argv)

    _guard = SingleInstanceGuard()
    _guard.acquire()

    bootstrap = AppBootstrap(forced_language=forced_language, forced_theme=forced_theme).setup()

    TermsGuard(bootstrap.config, bootstrap.config_manager).enforce()

    splash = ModernSplashScreen(bootstrap.config)
    splash.show()
    splash.start_animation()

    QTimer.singleShot(
        SPLASH_DELAY,
        lambda: WindowTransition(splash, bootstrap.config_manager, dropped_files).start(),
    )

    sys.exit(bootstrap.app.exec())

if __name__ == "__main__":
    main()