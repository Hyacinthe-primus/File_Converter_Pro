"""ProjectManagementMixin — Project file management methods."""

import json
import os
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from qss_helpers import _apply_dialog_btn
from widgets import ProjectTabButton


class ProjectManagementMixin:
    """Mixin: project file management for FileConverterApp."""

    MAX_PROJECT_TABS = 5

    def _update_project_label(self):
        lbl = getattr(self, "project_name_lbl", None)
        if lbl is None:
            return
        name = self._project_data.get("name", "") if self._project_data else ""
        notes = self._project_data.get("notes", "") if self._project_data else ""
        if name:
            lbl.setText(f"🗁  {name}")
            tip = name
            if notes:
                tip += f"\n\n{notes}"
            created = self._project_data.get("created_at", "")
            if created:
                tip += f"\n\n{self.translate_text('Créé :')} {created[:10]}"
            lbl.setToolTip(tip)
            lbl.setVisible(True)
        else:
            lbl.setVisible(False)

    def _active_tab_state(self):
        return self._active_tab

    def _tab_label(self, name):
        return f"🗁  {name}"

    def _on_tab_clicked(self, state):
        if state is self._active_tab:
            self.edit_project_info()
        else:
            self._switch_project_tab(state)

    def _on_tab_double_clicked(self, state):
        if state is not self._active_tab:
            self._switch_project_tab(state)
        self.edit_project_info()

    def _show_tab_context_menu(self, state, global_pos):
        menu = QMenu(self)
        act_info = menu.addAction(self.translate_text("Informations du projet"))
        act_close = menu.addAction(self.translate_text("Fermer l'onglet"))
        chosen = menu.exec(global_pos)
        if chosen is act_info:
            if state is not self._active_tab:
                self._switch_project_tab(state)
            self.edit_project_info()
        elif chosen is act_close:
            self._close_project_tab(state)

    def _add_project_tab(self, files_list=None, current_project=None, project_data=None):
        if len(self._project_tabs) >= self.MAX_PROJECT_TABS:
            QMessageBox.warning(
                self,
                self.translate_text("Limite de projets"),
                self.translate_text("project_tabs_limit"),
            )
            return None

        name = (project_data or {}).get("name") or self.translate_text("Nouveau projet")
        container = QWidget()
        container.setObjectName("ProjectTab")
        lay = QHBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)

        btn = ProjectTabButton(self._tab_label(name))
        btn.setObjectName("ProjectTabBtn")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMaximumWidth(170)
        lay.addWidget(btn)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("ProjectTabClose")
        close_btn.setFixedSize(18, 18)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton#ProjectTabClose {
                padding: 0px;
                font-weight: normal;
                background: transparent;
                border: none;
                font-size: 13px;
            }
            QPushButton#ProjectTabClose:hover { color: #ff6b6b; }
        """)
        lay.addWidget(close_btn)

        state = {
            "files_list": files_list if files_list is not None else [],
            "current_project": current_project,
            "project_data": project_data,
            "widget": container,
        }

        btn.clicked.connect(lambda checked=False, s=state: self._on_tab_clicked(s))
        btn.double_clicked.connect(lambda s=state: self._on_tab_double_clicked(s))
        close_btn.clicked.connect(lambda checked=False, s=state: self._close_project_tab(s))

        btn.setContextMenuPolicy(Qt.CustomContextMenu)
        btn.customContextMenuRequested.connect(
            lambda pos, s=state: self._show_tab_context_menu(s, btn.mapToGlobal(pos))
        )
        container.setContextMenuPolicy(Qt.CustomContextMenu)
        container.customContextMenuRequested.connect(
            lambda pos, s=state: self._show_tab_context_menu(s, container.mapToGlobal(pos))
        )

        self._project_tabs.append(state)
        self._active_tab = state
        self.project_tab_layout.addWidget(container)
        self._refresh_tab_bar()
        return state

    def _ensure_project_tab(self):
        return self._add_project_tab()

    def _repopulate_files_list(self):
        self.files_list_widget.clear()
        for idx, file in enumerate(self.files_list, 1):
            icon = self.get_file_icon(file)
            display_name = Path(file).name
            if isinstance(icon, QIcon):
                item = QListWidgetItem(f"{idx}. {display_name}")
                item.setIcon(icon)
            else:
                item = QListWidgetItem(f"{idx}. {icon} {display_name}")
            item.setData(Qt.UserRole, file)
            item.setData(Qt.UserRole + 1, "file")
            item.setToolTip(file)
            if os.path.isfile(file):
                item.setData(Qt.UserRole + 4, self.format_size(os.path.getsize(file)))
            self.files_list_widget.addItem(item)
            self._attach_preview_btn(item, file)

    def _load_tab_state(self, state):
        if state is None:
            return
        self.files_list = state["files_list"]
        self.current_project = state["current_project"]
        self._project_data = state["project_data"]
        self._repopulate_files_list()

    def _sync_active_tab_state(self):
        if self._active_tab is None:
            return
        self._active_tab["files_list"] = self.files_list
        self._active_tab["current_project"] = self.current_project
        self._active_tab["project_data"] = self._project_data

    def _switch_project_tab(self, state):
        if state is None or state is self._active_tab:
            return
        self._active_tab = state
        self._load_tab_state(state)
        self._update_project_label()
        self.update_file_counter()
        self._refresh_tab_bar()

    def _close_project_tab(self, state):
        if state not in self._project_tabs:
            return
        was_active = state is self._active_tab
        idx = self._project_tabs.index(state)
        self._project_tabs.remove(state)
        container = state["widget"]
        self.project_tab_layout.removeWidget(container)
        container.setParent(None)
        container.deleteLater()

        if was_active:
            if self._project_tabs:
                self._active_tab = self._project_tabs[max(0, idx - 1)]
                self._load_tab_state(self._active_tab)
            else:
                self._active_tab = None
                self.files_list = []
                self.current_project = None
                self._project_data = {}
                self.files_list_widget.clear()

        self._update_project_label()
        self.update_file_counter()
        self._refresh_tab_bar()

    def _refresh_tab_bar(self):
        bar = getattr(self, "project_tab_bar", None)
        if bar is None:
            return
        for state in self._project_tabs:
            name = (state["project_data"] or {}).get("name") or self.translate_text("Nouveau projet")
            container = state["widget"]
            btn = container.findChild(ProjectTabButton, "ProjectTabBtn")
            if btn is None:
                continue
            btn.setText(self._tab_label(name))
            active = state is self._active_tab
            for w in (btn, container):
                w.setProperty("active", active)
                w.style().unpolish(w)
                w.style().polish(w)
            tip = state["current_project"] or ""
            if tip:
                btn.setToolTip(tip)
            else:
                btn.setToolTip(self.translate_text("Cliquez pour renommer / ajouter des notes"))
        bar.setVisible(bool(self._project_tabs))
        if self._project_tabs:
            lbl = getattr(self, "project_name_lbl", None)
            if lbl is not None:
                lbl.setVisible(False)

    def _update_tab_title(self):
        self._refresh_tab_bar()

    def _refresh_all_tab_titles(self):
        self._refresh_tab_bar()

    def edit_project_info(self):
        if not self._project_data:
            return

        d = QDialog(self)
        d.setWindowTitle(self.translate_text("Informations du projet"))
        d.setMinimumWidth(380)
        lay = QVBoxLayout(d)
        lay.setSpacing(12)
        lay.setContentsMargins(18, 18, 18, 18)

        lay.addWidget(QLabel(self.translate_text("Nom du projet :")))
        name_input = QLineEdit(self._project_data.get("name", ""))
        name_input.setMinimumHeight(34)
        lay.addWidget(name_input)

        lay.addWidget(QLabel(self.translate_text("Notes :")))
        notes_input = QTextEdit()
        notes_input.setPlainText(self._project_data.get("notes", ""))
        notes_input.setFixedHeight(88)
        lay.addWidget(notes_input)

        created = self._project_data.get("created_at", "")[:16].replace("T", "  ")
        modified = self._project_data.get("modified_at", "")[:16].replace("T", "  ")
        if created:
            lbl_created = self.translate_text("Créé :")
            lbl_modified = self.translate_text("Modifié :")
            lbl_files = self.translate_text("fichier(s)")
            info_lbl = QLabel(
                f"<small style='color:gray;'>{lbl_created} {created}"
                + (f"&nbsp;&nbsp;&nbsp;{lbl_modified} {modified}" if modified else "")
                + f"&nbsp;&nbsp;&nbsp;{len(self.files_list)} {lbl_files}</small>"
            )
            info_lbl.setTextFormat(Qt.RichText)
            lay.addWidget(info_lbl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_cancel = QPushButton(self.translate_text("Annuler"))
        btn_cancel.setMinimumHeight(36)
        _apply_dialog_btn(btn_cancel, "BtnCancelGlassy")
        btn_ok = QPushButton(self.translate_text("✓  Enregistrer"))
        btn_ok.setMinimumHeight(36)
        btn_ok.setStyleSheet(
            "QPushButton{background:#0969da;color:white;border:none;"
            "border-radius:7px;font-weight:bold;padding:0 16px;}"
            "QPushButton:hover{background:#0860ca;}"
        )
        btn_cancel.clicked.connect(d.reject)
        btn_ok.clicked.connect(d.accept)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        lay.addLayout(btn_row)

        if d.exec() == QDialog.Accepted:
            new_name = name_input.text().strip() or self._project_data.get("name", "")
            new_notes = notes_input.toPlainText().strip()
            self._project_data["name"] = new_name
            self._project_data["notes"] = new_notes
            self._update_project_label()
            self._update_tab_title()
            if self.current_project:
                self._save_project_to(self.current_project)

    def open_last_project(self):
        if self.current_project and os.path.exists(self.current_project):
            self.open_project_file(self.current_project)

    def _find_tab_for_project(self, file_path):
        norm = os.path.normcase(os.path.normpath(str(file_path)))
        for state in self._project_tabs:
            cur = state.get("current_project")
            if cur and os.path.normcase(os.path.normpath(str(cur))) == norm:
                return state
        return None

    def open_project_file(self, file_path):
        existing_tab = self._find_tab_for_project(file_path)
        if existing_tab is not None:
            if existing_tab is not self._active_tab:
                self._switch_project_tab(existing_tab)
            QMessageBox.information(
                self,
                self.translate_text("Projet déjà ouvert"),
                self.translate_text("project_already_open"),
            )
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw = f.read().strip()

            if raw.startswith("{"):
                data = json.loads(raw)
                file_entries = data.get("files", [])
                all_paths = [e["path"] if isinstance(e, dict) else e for e in file_entries]
                data["modified_at"] = datetime.now().isoformat(timespec="seconds")
            else:
                all_paths = [line for line in raw.splitlines() if line.strip()]
                now = datetime.now().isoformat(timespec="seconds")
                data = {
                    "version": 1,
                    "name": Path(file_path).stem,
                    "notes": "",
                    "created_at": now,
                    "modified_at": now,
                    "files": [
                        {"path": p, "added_at": now, "size": os.path.getsize(p) if os.path.exists(p) else 0}
                        for p in all_paths
                    ],
                }

            existing_files = [p for p in all_paths if os.path.exists(p)]
            missing_count = len(all_paths) - len(existing_files)

            if self._ensure_project_tab() is None:
                return

            self.files_list = existing_files
            self._repopulate_files_list()
            self.current_project = file_path
            self._project_data = data
            self._sync_active_tab_state()
            self._update_project_label()
            self.update_file_counter()
            self._update_tab_title()

            proj_name = data.get("name", Path(file_path).stem)
            self.status_bar.showMessage(
                self.translate_text("project_opened_status").format(proj_name=proj_name, n=len(existing_files))
            )

            if missing_count > 0:
                QMessageBox.warning(
                    self,
                    self.translate_text("Fichiers manquants"),
                    self.translate_text("project_missing_files").format(n=missing_count),
                )

        except Exception as e:
            QMessageBox.critical(
                self, self.translate_text("Erreur"), self.translate_text("project_open_error").format(error=str(e))
            )

    def new_project(self):
        d = QDialog(self)
        d.setWindowTitle(self.translate_text("Nouveau projet"))
        d.setMinimumWidth(360)
        lay = QVBoxLayout(d)
        lay.setSpacing(12)
        lay.setContentsMargins(18, 18, 18, 18)

        lay.addWidget(QLabel(self.translate_text("Nom du projet :")))
        name_input = QLineEdit()
        name_input.setPlaceholderText(self.translate_text("Mon projet"))
        name_input.setMinimumHeight(34)
        lay.addWidget(name_input)

        lay.addWidget(QLabel(self.translate_text("Notes (optionnel) :")))
        notes_input = QTextEdit()
        notes_input.setPlaceholderText(self.translate_text("Description, contexte…"))
        notes_input.setFixedHeight(72)
        lay.addWidget(notes_input)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_cancel = QPushButton(self.translate_text("Annuler"))
        btn_cancel.setMinimumHeight(36)
        _apply_dialog_btn(btn_cancel, "BtnCancelGlassy")
        btn_ok = QPushButton("✓  " + self.translate_text("Créer"))
        btn_ok.setMinimumHeight(36)
        btn_ok.setStyleSheet(
            "QPushButton{background:#0969da;color:white;border:none;"
            "border-radius:7px;font-weight:bold;padding:0 16px;}"
            "QPushButton:hover{background:#0860ca;}"
        )
        btn_cancel.clicked.connect(d.reject)
        btn_ok.clicked.connect(d.accept)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        lay.addLayout(btn_row)

        if d.exec() != QDialog.Accepted:
            return

        proj_name = name_input.text().strip() or self.translate_text("Nouveau projet")
        proj_notes = notes_input.toPlainText().strip()
        now = datetime.now().isoformat(timespec="seconds")

        tab = self._add_project_tab(
            files_list=[],
            current_project=None,
            project_data={
                "version": 1,
                "name": proj_name,
                "notes": proj_notes,
                "created_at": now,
                "modified_at": now,
                "files": [],
            },
        )
        if tab is None:
            return

        self._load_tab_state(tab)
        self._update_project_label()
        self.update_file_counter()
        self._update_tab_title()
        self.status_bar.showMessage(
            self.translate_text("Nouveau projet créé") + ":" + f" {proj_name}" if proj_name else ""
        )

    def open_project(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, self.translate_text("Ouvrir un projet"), "", self.translate_text("Projets File Converter (*.fcproj)")
        )
        if file_path:
            self.open_project_file(file_path)
            self.config["last_project"] = file_path
            self.config_manager.save_config(self.config)

    def save_project(self):
        if not self.files_list:
            QMessageBox.warning(
                self,
                self.translate_text("Avertissement"),
                self.translate_text("Aucun fichier à sauvegarder dans le projet"),
            )
            return

        if self.current_project and os.path.exists(self.current_project):
            self._save_project_to(self.current_project)
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self.translate_text("Sauvegarder le projet"),
            "",
            self.translate_text("Projets File Converter (*.fcproj)"),
        )

        if file_path:
            if not file_path.endswith(".fcproj"):
                file_path += ".fcproj"
            self._save_project_to(file_path)

    def _save_project_to(self, file_path):
        now = datetime.now().isoformat(timespec="seconds")
        data = dict(self._project_data) if self._project_data else {}
        data.setdefault("version", 1)
        data.setdefault("name", Path(file_path).stem)
        data.setdefault("notes", "")
        data.setdefault("created_at", now)
        data["modified_at"] = now

        existing_entries = {
            (e["path"] if isinstance(e, dict) else e): (e if isinstance(e, dict) else {}) for e in data.get("files", [])
        }
        data["files"] = []
        for p in self.files_list:
            prev = existing_entries.get(p, {})
            data["files"].append(
                {
                    "path": p,
                    "added_at": prev.get("added_at", now),
                    "size": os.path.getsize(p) if os.path.exists(p) else prev.get("size", 0),
                }
            )

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self._project_data = data
            self.current_project = file_path
            self._update_project_label()
            self._sync_active_tab_state()
            self._update_tab_title()
            self.config["last_project"] = file_path
            self.config_manager.save_config(self.config)
            self.status_bar.showMessage(self.translate_text(f"Projet sauvegardé : {data['name']}"))

        except Exception as e:
            QMessageBox.critical(
                self,
                self.translate_text("Erreur"),
                self.translate_text(f"Impossible de sauvegarder le projet: {str(e)}"),
            )
