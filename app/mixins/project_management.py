"""ProjectManagementMixin — Project file management methods."""

import os
import json
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (QFileDialog, QMessageBox, QDialog, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QLineEdit,
                               QTextEdit, QListWidgetItem)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from qss_helpers import _apply_dialog_btn


class ProjectManagementMixin:
    """Mixin: project file management for FileConverterApp."""

    def _update_project_label(self):
        lbl = getattr(self, 'project_name_lbl', None)
        if lbl is None:
            return
        name = self._project_data.get('name', '') if self._project_data else ''
        notes = self._project_data.get('notes', '') if self._project_data else ''
        if name:
            lbl.setText(f'🗁  {name}')
            tip = name
            if notes:
                tip += f"\n\n{notes}"
            created = self._project_data.get('created_at', '')
            if created:
                tip += f"\n\n{self.translate_text('Créé :')} {created[:10]}"
            lbl.setToolTip(tip)
            lbl.setVisible(True)
        else:
            lbl.setVisible(False)

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
        name_input = QLineEdit(self._project_data.get('name', ''))
        name_input.setMinimumHeight(34)
        lay.addWidget(name_input)

        lay.addWidget(QLabel(self.translate_text("Notes :")))
        notes_input = QTextEdit()
        notes_input.setPlainText(self._project_data.get('notes', ''))
        notes_input.setFixedHeight(88)
        lay.addWidget(notes_input)

        created = self._project_data.get('created_at', '')[:16].replace('T', '  ')
        modified = self._project_data.get('modified_at', '')[:16].replace('T', '  ')
        if created:
            lbl_created  = self.translate_text("Créé :")
            lbl_modified = self.translate_text("Modifié :")
            lbl_files    = self.translate_text("fichier(s)")
            info_lbl = QLabel(
                f"<small style='color:gray;'>{lbl_created} {created}"
                + (f"&nbsp;&nbsp;&nbsp;{lbl_modified} {modified}" if modified else "")
                + f"&nbsp;&nbsp;&nbsp;{len(self.files_list)} {lbl_files}</small>")
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
            "QPushButton:hover{background:#0860ca;}")
        btn_cancel.clicked.connect(d.reject)
        btn_ok.clicked.connect(d.accept)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        lay.addLayout(btn_row)

        if d.exec() == QDialog.Accepted:
            new_name  = name_input.text().strip() or self._project_data.get('name', '')
            new_notes = notes_input.toPlainText().strip()
            self._project_data['name']  = new_name
            self._project_data['notes'] = new_notes
            self._update_project_label()
            if self.current_project:
                self._save_project_to(self.current_project)

    def open_last_project(self):
        if self.current_project and os.path.exists(self.current_project):
            self.open_project_file(self.current_project)

    def open_project_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw = f.read().strip()

            if raw.startswith('{'):
                data        = json.loads(raw)
                file_entries = data.get('files', [])
                all_paths   = [e['path'] if isinstance(e, dict) else e for e in file_entries]
                self._project_data = data
                self._project_data['modified_at'] = datetime.now().isoformat(timespec='seconds')
            else:
                all_paths = [line for line in raw.splitlines() if line.strip()]
                now = datetime.now().isoformat(timespec='seconds')
                self._project_data = {
                    'version':     1,
                    'name':        Path(file_path).stem,
                    'notes':       '',
                    'created_at':  now,
                    'modified_at': now,
                    'files': [
                        {'path': p, 'added_at': now,
                         'size': os.path.getsize(p) if os.path.exists(p) else 0}
                        for p in all_paths
                    ],
                }

            existing_files = [p for p in all_paths if os.path.exists(p)]
            missing_count  = len(all_paths) - len(existing_files)

            self.files_list = existing_files
            self.files_list_widget.clear()

            for file in existing_files:
                icon         = self.get_file_icon(file)
                display_name = Path(file).name
                if isinstance(icon, QIcon):
                    item = QListWidgetItem(display_name)
                    item.setIcon(icon)
                else:
                    item = QListWidgetItem(icon + " " + display_name)
                item.setData(Qt.UserRole, file)
                item.setData(Qt.UserRole + 1, "file")
                item.setToolTip(file)
                if os.path.isfile(file):
                    item.setData(Qt.UserRole + 4, self.format_size(os.path.getsize(file)))
                self.files_list_widget.addItem(item)
                self._attach_preview_btn(item, file)

            self.current_project = file_path
            self._update_project_label()
            self.update_file_counter()

            proj_name = self._project_data.get('name', Path(file_path).stem)
            self.status_bar.showMessage(
                self.translate_text("project_opened_status").format(
                    proj_name=proj_name, n=len(existing_files)))

            if missing_count > 0:
                QMessageBox.warning(
                    self, self.translate_text("Fichiers manquants"),
                    self.translate_text("project_missing_files").format(n=missing_count))

        except Exception as e:
            QMessageBox.critical(
                self, self.translate_text("Erreur"),
                self.translate_text("project_open_error").format(error=str(e)))

    def new_project(self):
        if self.files_list:
            reply = QMessageBox.question(
                self, self.translate_text("Nouveau Projet"),
                self.translate_text("Voulez-vous créer un nouveau projet ? Les fichiers actuels seront effacés."),
                QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return

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
            "QPushButton:hover{background:#0860ca;}")
        btn_cancel.clicked.connect(d.reject)
        btn_ok.clicked.connect(d.accept)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        lay.addLayout(btn_row)

        now = datetime.now().isoformat(timespec='seconds')
        proj_name  = self.translate_text("Nouveau projet")
        proj_notes = ""

        if d.exec() == QDialog.Accepted:
            proj_name  = name_input.text().strip() or self.translate_text("Nouveau projet")
            proj_notes = notes_input.toPlainText().strip()

        self.files_list.clear()
        self.files_list_widget.clear()
        self.current_project = None
        self._project_data   = {
            "version":     1,
            "name":        proj_name,
            "notes":       proj_notes,
            "created_at":  now,
            "modified_at": now,
            "files":       [],
        }
        self._update_project_label()
        self.update_file_counter()
        self.status_bar.showMessage(
            self.translate_text("Nouveau projet créé") + ":" + f" {proj_name}" if proj_name else "")

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
            QMessageBox.warning(self, self.translate_text("Avertissement"),
                                self.translate_text("Aucun fichier à sauvegarder dans le projet"))
            return

        if self.current_project and os.path.exists(self.current_project):
            self._save_project_to(self.current_project)
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, self.translate_text("Sauvegarder le projet"), "",
            self.translate_text("Projets File Converter (*.fcproj)"))

        if file_path:
            if not file_path.endswith('.fcproj'):
                file_path += '.fcproj'
            self._save_project_to(file_path)

    def _save_project_to(self, file_path):
        now  = datetime.now().isoformat(timespec='seconds')
        data = dict(self._project_data) if self._project_data else {}
        data.setdefault('version',    1)
        data.setdefault('name',       Path(file_path).stem)
        data.setdefault('notes',      '')
        data.setdefault('created_at', now)
        data['modified_at'] = now

        existing_entries = {
            (e['path'] if isinstance(e, dict) else e): (e if isinstance(e, dict) else {})
            for e in data.get('files', [])
        }
        data['files'] = []
        for p in self.files_list:
            prev = existing_entries.get(p, {})
            data['files'].append({
                'path':     p,
                'added_at': prev.get('added_at', now),
                'size':     os.path.getsize(p) if os.path.exists(p) else prev.get('size', 0),
            })

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self._project_data   = data
            self.current_project = file_path
            self._update_project_label()
            self.config["last_project"] = file_path
            self.config_manager.save_config(self.config)
            self.status_bar.showMessage(
                self.translate_text(f"Projet sauvegardé : {data['name']}"))

        except Exception as e:
            QMessageBox.critical(self, self.translate_text("Erreur"),
                                 self.translate_text(f"Impossible de sauvegarder le projet: {str(e)}"))