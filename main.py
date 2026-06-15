"""
Entry Point

Application startup logic, CLI handling, and window management.

Modes of Execution:
    1. GUI Mode (Default):
        - Initializes QApplication with global icon
        - Checks for single instance via QLocalServer
        - Displays animated splash screen
        - Performs cross-fade transition to main window
        - Validates Terms & Privacy acceptance

    2. CLI Mode (Arguments):
        - help / -h / --help:

"""

import sys
import os
import time
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.align import Align
from rich import box
from rich.markup import escape
from rich.theme import Theme

_THEME = Theme({
    "fcp.brand"   : "bold cyan",
    "fcp.cmd"     : "bold bright_cyan",
    "fcp.arg"     : "italic bright_white",
    "fcp.dim"     : "dim white",
    "fcp.ok"      : "bold bright_green",
    "fcp.warn"    : "bold yellow",
    "fcp.err"     : "bold bright_red",
    "fcp.section" : "bold magenta",
    "fcp.debug"   : "dim cyan",
    "fcp.unlock"  : "bold bright_yellow",
    "fcp.reset"   : "bold bright_magenta",
})

_console = Console(theme=_THEME, highlight=False)


def _fcp_banner() -> Panel:
    """Big ASCII art header panel."""
    art = Text(justify="left")
    art.append(
        "      ███████╗ ██████╗██████╗\n"
        "      ██╔════╝██╔════╝██╔══██╗\n"
        "      █████╗  ██║     ██████╔╝\n"
        "      ██╔══╝  ██║     ██╔═══╝\n"
        "      ██║     ╚██████╗██║\n"
        "      ╚═╝      ╚═════╝╚═╝\n",
        style="bold cyan"
    )
    art.append("File Converter Pro", style="bold bright_white")
    art.append("  ·  CLI Reference\n", style="dim white")
    art.append("   ──── by Prime Enterprises ────", style="dim cyan")
    return Panel(
        Align.center(art),
        border_style="cyan",
        padding=(1, 4),
        box=box.DOUBLE_EDGE,
    )


def _fcp_section(title: str, icon: str = "◈", style: str = "fcp.section") -> None:
    _console.print()
    _console.print(Rule(f"[{style}]{icon}  {title}  {icon}[/{style}]", style="magenta"))


def _fcp_debug(label: str, value: str) -> None:
    _console.print(f"  [fcp.debug]⟫[/fcp.debug] [fcp.dim]{label}[/fcp.dim]  [bright_cyan]{escape(str(value))}[/bright_cyan]")


def _fcp_ok(msg: str) -> None:
    _console.print(f"  [fcp.ok]✔[/fcp.ok]  {msg}")


def _fcp_warn(msg: str) -> None:
    _console.print(f"  [fcp.warn]⚠[/fcp.warn]  {msg}")


def _fcp_err(msg: str) -> None:
    _console.print(f"  [fcp.err]✘[/fcp.err]  {msg}")


def _fcp_typewriter(text: str, style: str = "bright_white", delay: float = 0.018) -> None:
    """Print text character by character for dramatic effect."""
    for ch in text:
        _console.print(ch, style=style, end="", highlight=False)
        time.sleep(delay)
    _console.print()

if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

if "--daemon" in sys.argv:
    from daemon import run_daemon_mode
    from rich.console import Console
    from rich.text import Text
    _c = Console()
    _c.print(Text("& Daemon launched", style="bold bright_cyan"))
    run_daemon_mode()
    sys.exit(0)

from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtCore    import Qt, QTimer
from PySide6.QtGui     import QIcon

from config  import ConfigManager, is_dark_mode_qt
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

    HELP_TEXT = ""  # rendered via _cmd_help()

    @staticmethod
    def _build_commands_table() -> Table:
        tbl = Table(
            show_header=True,
            header_style="bold magenta",
            box=box.SIMPLE_HEAVY,
            border_style="cyan",
            padding=(0, 1),
            show_lines=False,
        )
        tbl.add_column("Command", style="bright_cyan", no_wrap=True, min_width=42)
        tbl.add_column("What it does", style="white")
        tbl.add_column("", style="dim cyan", no_wrap=True)

        rows = [
            ("main.py",                                         "Launch GUI mode",                          ">>"),
            ("main.py status",                                  "Show all achievement statuses",            "::"),
            ("main.py reset [italic]<id>[/italic]",             "Reset a specific achievement",              "↺"),
            ("main.py unlock [italic]<id>[/italic]",            "Force-unlock an achievement",               "★"),
            ("main.py reset-all",                               "Nuke every achievement",                  "<!>"),
            ("main.py help / -h / --help",                      "This glorious screen",                      "?"),
            ("main.py --lang [italic]<code>[/italic]",          "Override UI language",                      "@"),
            ("main.py --theme [italic]dark|light[/italic]",     "Override UI theme",                         "~"),
            ("main.py --lang … --theme …",                      "Override both at once",                     "⚡"),
            ("main.py --daemon",                                "Headless daemon mode",                      "&"),
        ]
        for cmd, desc, icon in rows:
            tbl.add_row(cmd, desc, icon)
        return tbl

    @staticmethod
    def _build_context_panel() -> Panel:
        content = Text()
        content.append("main.py --context-menu --files ", style="bright_cyan")
        content.append("<file1> [file2 …]", style="italic white")
        content.append("  [--conversion-type ", style="dim white")
        content.append("type", style="italic white")
        content.append("]\n\n", style="dim white")
        content.append("Files must share the same category (image / audio / video).", style="dim white")
        return Panel(content, title="[bold cyan]Context Menu – Quick Convert[/bold cyan]", border_style="cyan", padding=(0, 2))

    @staticmethod
    def _build_examples_table() -> Table:
        tbl = Table(box=None, show_header=False, padding=(0, 1))
        tbl.add_column("", style="dim magenta", no_wrap=True)
        tbl.add_column("", style="dim white")

        examples = [
            "main.py status",
            "main.py reset  first_adventure",
            "main.py unlock apprentice",
            "main.py reset-all",
            "main.py --lang fr",
            "main.py --theme dark",
            "main.py --lang en --theme light",
            r'main.py --context-menu --files "C:\Users\UserName\Desktop\sample.pdf"',
            r'main.py --context-menu --files "C:\...\sample.pdf" --conversion-type pdf_to_docx',
        ]
        for ex in examples:
            tbl.add_row("$", ex)
        return tbl

    def __init__(self, argv: list[str]) -> None:
        self.argv    = argv
        self.command = argv[1].lower() if len(argv) > 1 else None
        self._mgr    = None

    def is_cli_mode(self) -> bool:
        return self.command in CLI_COMMANDS

    def run(self) -> None:
        """Dispatch to the matching handler, then exit."""
        _fcp_debug("command", self.command)
        _fcp_debug("args   ", " ".join(self.argv))

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
            _fcp_err(f"Unknown command: [bold]{escape(str(self.command))}[/bold]")
            _console.print("  [fcp.dim]Run[/fcp.dim] [fcp.cmd]main.py -h[/fcp.cmd] [fcp.dim]for help.[/fcp.dim]")
            sys.exit(1)

        sys.exit(0)

    def _cmd_status(self) -> None:
        _fcp_section("ACHIEVEMENTS STATUS", icon="◈", style="fcp.section")
        self._mgr_show_status()

    def _cmd_reset(self) -> None:
        self._require_arg("reset")
        _console.print()
        _console.print(Panel(
            f"[fcp.reset]↺  Resetting:[/fcp.reset]  [bold bright_white]{escape(self.argv[2])}[/bold bright_white]",
            border_style="magenta",
            padding=(0, 2),
        ))
        self._mgr_reset_one(self.argv[2])

    def _cmd_unlock(self) -> None:
        self._require_arg("unlock")
        _console.print()
        _console.print(Panel(
            f"[fcp.unlock]★  Unlocking:[/fcp.unlock]  [bold bright_white]{escape(self.argv[2])}[/bold bright_white]",
            border_style="yellow",
            padding=(0, 2),
        ))
        self._mgr_unlock_one(self.argv[2])

    def _cmd_reset_all(self) -> None:
        _console.print()
        _console.print(Panel(
            "[bold bright_red]<!>  DANGER ZONE  <!>[/bold bright_red]\n"
            "[dim white]This will wipe ALL achievement progress.[/dim white]",
            border_style="red",
            box=box.DOUBLE_EDGE,
            padding=(0, 3),
        ))
        answer = input("\n  ⚠  Are you sure? Type YES to confirm: ").strip()
        if answer == "YES":
            with Progress(
                SpinnerColumn(spinner_name="dots"),
                TextColumn("[bold bright_red]Resetting all achievements...[/bold bright_red]"),
                transient=True,
                console=_console,
            ) as progress:
                progress.add_task("reset", total=None)
                self._mgr_reset_all()
        else:
            _fcp_ok("Aborted. Your achievements are safe.")

    def _cmd_help(self) -> None:
        _console.print()
        _console.print(_fcp_banner())
        _console.print()
        _fcp_section("Commands", icon="◈")
        _console.print(self._build_commands_table())
        _console.print()
        _console.print(self._build_context_panel())
        _fcp_section("Examples", icon="◈")
        _console.print(self._build_examples_table())
        _console.print()

    def _require_arg(self, command: str) -> None:
        if len(self.argv) < 3:
            _fcp_err(f"Usage: [bright_cyan]main.py {command}[/bright_cyan] [italic white]<achievement_id>[/italic white]")
            sys.exit(1)

    @staticmethod
    def _print_section(title: str) -> None:
        _fcp_section(title)

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
            _console.print()
            _fcp_err(f"Unable to execute CLI command: {escape(str(exc))}")
            _console.print("  [dim]Make sure achievements.db exists in the current directory.[/dim]")
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
                _console.print()
                _fcp_warn("Another instance of File Converter Pro is already running.")
                sys.exit(0)

            self._server = QLocalServer()
            self._server.listen(SOCKET_NAME)

        except ImportError:
            _fcp_warn("Single-instance guard [dim]unavailable[/dim] — QtNetwork missing.")


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
        import signal
        app = QApplication(sys.argv)
        signal.signal(signal.SIGINT, lambda *_: app.quit())
        icon_path = self._resolve_icon()

        if icon_path:
            icon = QIcon(icon_path)
            app.setWindowIcon(icon)
            QApplication.setWindowIcon(icon)
        else:
            _fcp_warn("icon.ico not found — using system default.")

        return app

    def _load_config(self) -> dict:
        config = self.config_manager.load_config()

        # Forced language (--fr / --en / --en-revisited / --lang <code>)
        if self.forced_language:
            config["language"] = self.forced_language
            self.config_manager.save_config(config)
            _fcp_debug("lang  →", self.forced_language)
        elif "language" not in config:
            config["language"] = "fr"
            self.config_manager.save_config(config)

        if self.forced_theme is not None:
            config["dark_mode"]         = (self.forced_theme == "dark")
            config["use_system_theme"]  = False
            self.config_manager.save_config(config)
            _fcp_debug("theme →", self.forced_theme)
        elif config.get("use_system_theme", True):
            config["dark_mode"] = is_dark_mode_qt()
            self.config_manager.save_config(config)

        return config

    @classmethod
    def _resolve_icon(cls) -> str | None:
        from utils import get_icon_path
        path = get_icon_path("icon.ico")
        return path if path and os.path.exists(path) else None


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
        else:
            self.config["terms_acceptance_timestamp"] = now

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

        from threading import Thread
        from system_notifier import SystemNotifier
        notifier = SystemNotifier()
        Thread(target=notifier.check_and_notify_update, daemon=True).start()

        from daemon import is_autostart_enabled
        if not is_autostart_enabled():
            from tasks import WatcherManager, SchedulerManager

            def _start_services(win):
                from daemon import _trim_log_if_clean
                _trim_log_if_clean()
                win._watcher = WatcherManager()
                win._watcher.start()
                win._scheduler = SchedulerManager()
                win._scheduler.start()

            Thread(target=_start_services, args=[win], daemon=True).start()

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
            _fcp_warn(f"add_files_to_list not found — dropped files ignored: {self.dropped_files}")


def main() -> None:
    if "--context-menu" in sys.argv:
        files, collecting = [], False
        conversion_type = None
        for arg in sys.argv[1:]:
            if arg == "--files":
                collecting = True
                continue
            if arg == "--conversion-type":
                collecting = False
                continue
            if arg.startswith("--conversion-type="):
                conversion_type = arg.split("=", 1)[1]
                continue
            prev = sys.argv[sys.argv.index(arg) - 1] if sys.argv.index(arg) > 0 else ""
            if prev == "--conversion-type":
                conversion_type = arg
                continue
            if collecting and os.path.exists(arg):
                files.append(arg)
        if files:
            from PySide6.QtWidgets import QApplication
            _app = QApplication(sys.argv)
            from context_menu.window import run_context_menu
            run_context_menu(files, conversion_type=conversion_type)
            return

    cli = CLIHandler(sys.argv)
    if cli.is_cli_mode():
        cli.run()

    dropped_files = get_dropped_files(sys.argv)
    if dropped_files:
        _fcp_debug("dropped files", dropped_files)

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