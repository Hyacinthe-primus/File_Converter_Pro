"""FileManagementMixin — File list management methods."""

import os
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (QFileDialog, QMessageBox, QDialog, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QListWidgetItem,
                               QWidget)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QIcon, QFont, QColor

from qss_helpers import _apply_dialog_btn
from dialogs import BatchRenameDialog


class FileManagementMixin:
    """Mixin: file list management for FileConverterApp."""

    ICON_MAPPING = {
        '.pdf': ('pdf.ico', '📄'),
        '.doc': ('word.ico', '📝'), '.docx': ('word.ico', '📝'),
        '.rtf': ('rtf.ico', '📝'), '.txt': ('txt.ico', '📝'),
        '.ppt': ('pptx.ico', '📎'), '.pptx': ('pptx.ico', '📎'),
        '.xlsx': ('xlsx.ico', '📎'), '.csv': ('csv.ico', '📎'),
        '.epub': ('epub.ico', '📎'), '.html': ('html.ico', '📎'),
        '.json': ('json.ico', '📎'), '.exe': ('exe.ico', '📎'),
        **{ext: ('img.ico', '🖼️') for ext in [
            '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.heic', '.jfif', '.tif',
            '.svg', '.ico', '.avif', '.heif', '.psd', '.j2k', '.jp2', '.jpx', '.dng',
            '.cr2', '.cr3', '.nef', '.arw', '.orf', '.rw2', '.raf', '.webp'
        ]},
        **{ext: ('video.ico', '📎') for ext in ['.mp4', '.avi', '.mkv', '.mov', '.webm']},
        **{ext: ('audio.ico', '📎') for ext in ['.mp3', '.wav', '.aac', '.flac', '.ogg']},
        **{ext: ('archive.ico', '🗜️') for ext in ['.zip', '.rar', '.tar', '.gz', '.7z']},
        **{ext: ('database.ico', '📎') for ext in ['.db', '.sqlite', '.sql']}
    }

    _icon_cache: dict = {}

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            self.translate_text("Sélectionner des fichiers"),
            "",
            self.translate_text(
                "Tous les fichiers supportés ("
                "*.pdf *.docx *.doc *.pptx *.ppt *.xlsx *.xls "
                "*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp *.heic *.heif *.jfif "
                "*.avif *.psd *.svg *.dng *.j2k *.jp2 *.jpx *.cr2 *.cr3 *.nef *.arw *.orf *.rw2 "
                "*.mp3 *.wav *.aac *.flac *.ogg *.m4a "
                "*.mp4 *.avi *.mkv *.webm *.mov "
                "*.html *.htm *.epub *.rtf *.txt "
                "*.csv *.json "
                "*.zip *.rar *.tar *.gz);;"
                "Documents (*.pdf *.docx *.doc *.pptx *.ppt *.xlsx *.xls *.rtf *.txt *.epub *.html *.htm);;"
                "PDF Files (*.pdf);;"
                "Word / RTF (*.docx *.doc *.rtf *.txt);;"
                "PowerPoint (*.pptx *.ppt);;"
                "Excel (*.xlsx *.xls);;"
                "EPUB (*.epub);;"
                "HTML (*.html *.htm);;"
                "Images (*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp *.heic *.heif *.jfif *.avif *.psd *.svg *.dng *.j2k *.jp2 *.jpx *.cr2 *.cr3 *.nef *.arw *.orf *.rw2);;"
                "Audio (*.mp3 *.wav *.aac *.flac *.ogg *.m4a);;"
                "Vidéo (*.mp4 *.avi *.mkv *.webm *.mov);;"
                "Données (*.csv *.json);;"
                "Archives (*.zip *.rar *.tar *.gz);;"
                "Tous les fichiers (*.*)"
            )
        )
        self.add_files_to_list(files)

    def add_folder(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(self.translate_text("Ajouter un dossier"))
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        title_label = QLabel(self.translate_text("Comment voulez-vous ajouter le dossier ?"))
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        layout.addWidget(title_label)

        option1_btn = QPushButton("📦 " + self.translate_text("Ajouter le dossier (pour compression)"))
        option1_btn.setMinimumHeight(45)
        _apply_dialog_btn(option1_btn, "BtnFolderAsItem")
        option1_btn.setToolTip(self.translate_text("Ajoute le dossier en tant qu'élément unique pour la compression"))

        option2_btn = QPushButton("📄 " + self.translate_text("Ajouter le contenu du dossier"))
        option2_btn.setMinimumHeight(45)
        _apply_dialog_btn(option2_btn, "BtnFolderContent")
        option2_btn.setToolTip(self.translate_text("Ajoute tous les fichiers du dossier individuellement"))

        cancel_btn = QPushButton(self.translate_text("Annuler"))
        cancel_btn.setMinimumHeight(35)
        _apply_dialog_btn(cancel_btn, "BtnCancelGlassy")

        layout.addWidget(option1_btn)
        layout.addWidget(option2_btn)
        layout.addSpacing(20)
        layout.addWidget(cancel_btn)

        option1_btn.clicked.connect(lambda: self.add_folder_as_item(dialog))
        option2_btn.clicked.connect(lambda: self.add_folder_contents(dialog))
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec()

    def add_folder_as_item(self, dialog=None):
        if dialog:
            dialog.accept()

        folder = QFileDialog.getExistingDirectory(self, self.translate_text("Sélectionner un dossier à ajouter"))
        if folder:
            self.files_list.append(folder)

            folder_name = Path(folder).name
            icon = self.get_file_icon(folder)

            file_count = sum(len(files) for _, _, files in os.walk(folder))
            folder_size = self.calculate_folder_size(folder)

            if isinstance(icon, QIcon):
                item = QListWidgetItem(folder_name)
                item.setIcon(icon)
            else:
                item = QListWidgetItem(icon + " " + folder_name)

            item.setData(Qt.UserRole, folder)
            item.setData(Qt.UserRole + 4, self.format_size(folder_size))

            tooltip = (f"Folder: {folder}\n"
                    f"Size: {self.format_size(folder_size)}\n"
                    f"Files: {file_count}\n"
                    f"Full structure preserved during compression")

            item.setToolTip(tooltip)

            item.setForeground(QColor(0, 85, 255))
            item.setFont(QFont("Arial", 10, QFont.Bold))

            item.setData(Qt.UserRole + 1, "folder")
            item.setData(Qt.UserRole + 2, file_count)
            item.setData(Qt.UserRole + 3, folder_size)

            self.files_list_widget.addItem(item)

            self.update_file_counter()
            self.status_bar.showMessage(self.translate_text(f"Dossier ajouté: {folder_name} ({file_count} fichiers)"))

    def calculate_folder_size(self, folder_path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    try:
                        total_size += os.path.getsize(filepath)
                    except Exception:
                        pass
        return total_size

    def format_size(self, size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def add_folder_contents(self, dialog=None):
        if dialog:
            dialog.accept()

        folder = QFileDialog.getExistingDirectory(self, self.translate_text("Sélectionner un dossier"))
        if not folder:
            return

        supported_extensions = {
            '.pdf', '.docx', '.doc', '.rtf', '.txt',
            '.pptx', '.ppt',
            '.xlsx', '.xls',
            '.epub', '.html', '.htm',
            '.csv', '.json',
            '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.gif',
            '.svg', '.ico', '.avif', '.heic', '.heif', '.psd', '.j2k', '.jp2', '.jfif',
            '.dng', '.cr2', '.cr3', '.nef', '.arw', '.orf', '.rw2', '.raf', '.jpx',
            '.mp3', '.wav', '.aac', '.flac', '.ogg',
            '.mp4', '.avi', '.mkv', '.mov', '.webm',
            '.zip', '.rar', '.tar', '.gz',
        }
        files = []

        for root, dirs, filenames in os.walk(folder):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                file_ext = Path(file_path).suffix.lower()

                if file_ext in supported_extensions:
                    files.append(file_path)

        new_files = [f for f in files if f not in self.files_list]
        if not new_files:
            return

        self.files_list.extend(new_files)

        start_index = self.files_list_widget.count() + 1

        for i, file_path in enumerate(new_files):
            display_name = Path(file_path).name
            number = start_index + i
            numbered_text = f"{number} {display_name}"

            item = QListWidgetItem(numbered_text)
            item.setData(Qt.UserRole, file_path)

            icon = self.get_file_icon(file_path)
            if isinstance(icon, QIcon):
                item.setIcon(icon)
            else:
                item.setText(f"{number} {icon} {display_name}")

            if os.path.isfile(file_path):
                item.setData(Qt.UserRole + 4, self.format_size(os.path.getsize(file_path)))

            self.files_list_widget.addItem(item)
            self._attach_preview_btn(item, file_path)

        self.update_file_counter()

    def add_files_to_list(self, files):
        new_files = []
        for file in files:
            if str(file).lower().endswith('.fcproj'):
                continue
            if file not in self.files_list:
                if os.path.isdir(file):
                    new_files.append((file, "folder"))
                else:
                    new_files.append((file, "file"))

        start_index = self.files_list_widget.count() + 1
        for i, (file_path, file_type) in enumerate(new_files):
            self.files_list.append(file_path)
            icon = self.get_file_icon(file_path)
            display_name = Path(file_path).name
            number = start_index + i

            if isinstance(icon, QIcon):
                item = QListWidgetItem(f"{number} {display_name}")
                item.setIcon(icon)
            else:
                item = QListWidgetItem(f"{number} {icon} {display_name}")

            item.setData(Qt.UserRole, file_path)
            item.setData(Qt.UserRole + 1, file_type)
            if file_type == "file" and os.path.isfile(file_path):
                item.setData(Qt.UserRole + 4, self.format_size(os.path.getsize(file_path)))
            self.files_list_widget.addItem(item)
            self._attach_preview_btn(item, file_path)

        self.update_file_counter()

    def _attach_preview_btn(self, item, file_path):
        btn = QPushButton("👁")
        btn.setFixedSize(24, 22)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setToolTip(self.translate_text("Aperçu"))
        btn.setStyleSheet("""
            QPushButton {
                background: rgba(110,190,255,0.12);
                color: rgb(110,190,255);
                border: 1px solid rgba(110,190,255,0.25);
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover { background: rgba(110,190,255,0.30); }
            QPushButton:pressed { background: rgba(110,190,255,0.45); }
        """)
        btn.clicked.connect(lambda: (self.files_list_widget.setCurrentItem(item), self.show_file_preview(item)))

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 38, 0)
        layout.addStretch()
        layout.addWidget(btn)

        self.files_list_widget.setItemWidget(item, container)

    def get_file_icon(self, file_path):
        p = Path(file_path)
        icons_dir = Path(self.get_resource_path("icons"))

        if p.is_dir():
            return self._load_icon(icons_dir / "folder.ico", "📁")

        ico_name, fallback = self.ICON_MAPPING.get(p.suffix.lower(), ("other.ico", "📎"))
        return self._load_icon(icons_dir / ico_name, fallback)

    def _load_icon(self, icon_path: Path, fallback: str):
        key = str(icon_path)
        if key not in self._icon_cache:
            self._icon_cache[key] = QIcon(key) if icon_path.exists() else fallback
        return self._icon_cache[key]

    def remove_files(self):
        selected_items = self.files_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.translate_text("Avertissement"),
                                self.translate_text("Veuillez sélectionner au moins un fichier à supprimer"))
            return

        folder_count = 0
        file_count = 0

        valid_items = []
        for item in selected_items:
            file_path = item.data(Qt.UserRole)

            if file_path is None:
                file_path = item.toolTip()

            if file_path is None:
                continue

            valid_items.append((item, file_path))

            if os.path.isdir(file_path):
                folder_count += 1
            else:
                file_count += 1

        if not valid_items:
            QMessageBox.warning(self, self.translate_text("Avertissement"),
                                self.translate_text("Aucun fichier valide sélectionné"))
            return

        if folder_count > 0:
            template = self.translate_text("confirm_remove_files_with_folders")
            message = template.format(folder_count, file_count)
        else:
            template = self.translate_text("confirm_remove_files_only")
            message = template.format(file_count)

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(self.translate_text("Confirmation"))
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Question)

        yes_button = msg_box.addButton(QMessageBox.Yes)
        no_button = msg_box.addButton(QMessageBox.No)
        msg_box.setDefaultButton(no_button)

        yes_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #218838; }
            QPushButton:pressed { background-color: #1e7e34; }
        """)
        no_button.setStyleSheet("""
            QPushButton {
                background-color: #B55454;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #A04040; }
            QPushButton:pressed { background-color: #8B3030; }
        """)

        msg_box.exec()

        if msg_box.clickedButton() == yes_button:
            for item, file_path in valid_items:
                if file_path in self.files_list:
                    self.files_list.remove(file_path)
                row = self.files_list_widget.row(item)
                if row != -1:
                    self.files_list_widget.takeItem(row)

            self.update_file_counter()
            self.update_item_numbers()

    def animate_clear_button(self):
        animation = QPropertyAnimation(self.clear_all_btn, b"geometry")
        animation.setDuration(300)

        original_geometry = self.clear_all_btn.geometry()

        animation.setKeyValueAt(0, original_geometry)
        animation.setKeyValueAt(0.5, original_geometry.adjusted(2, 2, -2, -2))
        animation.setKeyValueAt(1, original_geometry)

        animation.setEasingCurve(QEasingCurve.OutBounce)
        animation.start()

    def clear_files(self):
        if not self.files_list:
            return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(self.translate_text("Confirmation"))
        msg_box.setText(self.translate_text("confirm_delete_all").format(count=len(self.files_list)))
        msg_box.setIcon(QMessageBox.Question)

        yes_button = msg_box.addButton(QMessageBox.Yes)
        no_button = msg_box.addButton(QMessageBox.No)
        msg_box.setDefaultButton(no_button)

        yes_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #218838; }
            QPushButton:pressed { background-color: #1e7e34; }
        """)
        no_button.setStyleSheet("""
            QPushButton {
                background-color: #B55454;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #A04040; }
            QPushButton:pressed { background-color: #8B3030; }
        """)

        msg_box.exec()

        if msg_box.clickedButton() == yes_button:
            self.files_list.clear()
            self.files_list_widget.clear()

            self.update_file_counter()
            self.status_bar.showMessage(self.translate_text("Liste de fichiers effacée"))
            self.animate_clear_button()

    def update_file_order(self):
        self.files_list.clear()
        for i in range(self.files_list_widget.count()):
            item = self.files_list_widget.item(i)
            self.files_list.append(item.data(Qt.UserRole))
        self.update_item_numbers()

    def update_item_numbers(self):
        for i in range(self.files_list_widget.count()):
            item = self.files_list_widget.item(i)
            if item:
                file_path = item.data(Qt.UserRole)
                item.data(Qt.UserRole + 1)
                icon = self.get_file_icon(file_path)
                display_name = Path(file_path).name
                number = i + 1
                if isinstance(icon, QIcon):
                    item.setIcon(icon)
                    item.setText(f"{number} {display_name}")
                else:
                    item.setText(f"{number} {icon} {display_name}")

    def update_file_counter(self):
        count = len(self.files_list)
        folder_count = sum(1 for f in self.files_list if os.path.isdir(f))
        file_count = count - folder_count

        if count == 0:
            self.file_counter.setText(self.translate_text("Aucun fichier sélectionné"))
        else:
            text = ""
            if folder_count > 0:
                text += f"{folder_count} {self.translate_text('dossier(s)')}"
                if file_count > 0:
                    text += f", {file_count} {self.translate_text('fichier(s)')}"
            else:
                text = f"{file_count} {self.translate_text('fichier(s)')}"

            self.file_counter.setText(text)

        try:
            from PySide6.QtWidgets import QGraphicsOpacityEffect
            effect = QGraphicsOpacityEffect(self.file_counter)
            effect.setOpacity(0.15)
            self.file_counter.setGraphicsEffect(effect)
            QTimer.singleShot(110, lambda: self.file_counter.setGraphicsEffect(None))
        except Exception:
            pass

    def batch_rename(self):
        if not self.files_list:
            QMessageBox.warning(self, self.translate_text("Avertissement"),
                                self.translate_text("Aucun fichier sélectionné"))
            return

        dialog = BatchRenameDialog(self.files_list, self, self.current_language)
        if dialog.exec() != QDialog.Accepted:
            return

        rename_plan = dialog.get_rename_plan()

        start_time = datetime.now()
        total_size = sum(os.path.getsize(f) for f in self.files_list if os.path.exists(f))

        self.process_batch_rename(rename_plan)

        conversion_time = (datetime.now() - start_time).total_seconds()
        self.db_manager.add_conversion_record(
            source_file="Batch of files",
            source_format="Various",
            target_file="Rename",
            target_format="Same formats",
            operation_type="batch_rename",
            file_size=total_size,
            conversion_time=conversion_time,
            success=True,
            notes=f"Renamed {len(rename_plan)} files"
        )
        if self.config.get("enable_system_notifications", True):
            self.system_notifier.send("batch_rename")