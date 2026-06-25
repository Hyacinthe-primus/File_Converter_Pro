"""CompressionMixin — File compression (ZIP, RAR, TAR) methods."""

import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0

from PySide6.QtWidgets import (QMessageBox, QDialog, QVBoxLayout, QLabel,
                               QGroupBox, QRadioButton, QTextEdit,
                               QDialogButtonBox)

from dialogs import PasswordDialog, CompressionDialog
from app.mixins.archive_engines import ArchiveEnginesMixin


class CompressionMixin(ArchiveEnginesMixin):
    """Mixin: file compression (ZIP, RAR, TAR) for FileConverterApp."""

    def compress_files(self):
        if not (hasattr(self, 'active_templates') and 'compression' in self.active_templates):
            _def_id, _ = (self._ensure_template_manager() or object()).get_default_template('Compression')
            if _def_id:
                (self._ensure_template_manager() or object()).apply_template(_def_id, self)

        selected_items = self.files_list_widget.selectedItems()
        files_to_process = []

        if selected_items:
            for i in range(self.files_list_widget.count()):
                item = self.files_list_widget.item(i)
                if item.isSelected():
                    files_to_process.append(item.data(0x0100))
        else:
            files_to_process = self.files_list

        files_to_process = [f for f in files_to_process if f is not None]

        if not files_to_process:
            if selected_items:
                msg = self.translate_text("Aucun fichier sélectionné")
            else:
                msg = self.translate_text("La liste de fichiers est vide")
            QMessageBox.warning(self, self.translate_text("Avertissement"), msg)
            return

        folders_to_compress = []
        files_to_compress = []

        for item_path in files_to_process:
            if item_path is not None:
                if os.path.isdir(item_path):
                    folders_to_compress.append(item_path)
                else:
                    files_to_compress.append(item_path)

        compression_mode = "files"

        if folders_to_compress:
            dialog = QDialog(self)
            dialog.setWindowTitle(self.translate_text("Mode de compression des dossiers"))
            dialog.setMinimumWidth(500)

            layout = QVBoxLayout(dialog)

            folder_info = QLabel(self.translate_text("Dossiers sélectionnés pour compression:"))
            folder_info.setStyleSheet("font-weight: bold;")
            layout.addWidget(folder_info)

            folder_list = QTextEdit()
            folder_list.setReadOnly(True)
            folder_list.setMaximumHeight(150)

            folder_text = ""
            for folder in folders_to_compress:
                folder_name = Path(folder).name
                file_count = sum(len(files) for _, _, files in os.walk(folder))
                folder_size = self.calculate_folder_size(folder)
                folder_text += self.translate_text("fld_txt").format(folder_name, file_count, self.format_size(folder_size))

            folder_list.setText(folder_text)
            layout.addWidget(folder_list)

            options_group = QGroupBox(self.translate_text("Options de compression"))
            options_layout = QVBoxLayout(options_group)

            option1 = QRadioButton(self.translate_text("Compresser les dossiers avec leur structure (recommandé)"))
            option1.setChecked(True)
            option1.setToolTip(self.translate_text("Crée des archives avec la structure complète des dossiers"))

            option2 = QRadioButton(self.translate_text("Traiter les dossiers comme des fichiers individuels"))
            option2.setToolTip(self.translate_text("Ajoute tous les fichiers des dossiers sans conserver la structure"))

            options_layout.addWidget(option1)
            options_layout.addWidget(option2)
            layout.addWidget(options_group)

            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

            def set_mode_and_close():
                nonlocal compression_mode
                if option1.isChecked():
                    compression_mode = "folders_with_structure"
                else:
                    compression_mode = "files_only"
                dialog.accept()

            button_box.accepted.connect(set_mode_and_close)
            button_box.rejected.connect(dialog.reject)

            layout.addWidget(button_box)

            if dialog.exec() != QDialog.Accepted:
                return

        if hasattr(self, 'active_templates') and 'compression' in self.active_templates:
            tpl = self.active_templates['compression']
            _fmt_map = {
                'ZIP': self.translate_text('ZIP'), 'RAR': self.translate_text('RAR'),
                'TAR.GZ': self.translate_text('TAR.GZ'), 'TAR': self.translate_text('TAR'),
            }
            _lvl_map = {
                'Normal': self.translate_text('Normal'),
                'Haute compression': self.translate_text('Haute compression'),
                'Compression maximale': self.translate_text('Compression maximale'),
            }
            _fmt = tpl.get('format', 'ZIP')
            _lvl = tpl.get('compression_level', 'Normal')
            _split = tpl.get('split_archive', False)
            _split_size = tpl.get('split_size', 0) if _split else 0
            _encrypt = tpl.get('encrypt', False)
            _delete = tpl.get('delete_originals', False)

            if compression_mode == "folders_with_structure" and folders_to_compress:
                _name = Path(folders_to_compress[0]).name if len(folders_to_compress) == 1 else f"folders_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            else:
                _name = f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            settings = {
                'format':          _fmt_map.get(_fmt, _fmt),
                'level':           _lvl_map.get(_lvl, _lvl),
                'name':            _name,
                'password':        _encrypt,
                'split':           _split,
                'split_size':      _split_size,
                'delete_originals': _delete,
            }

            if _encrypt:
                pwd_dialog = PasswordDialog(self, self.current_language)
                if pwd_dialog.exec() != QDialog.Accepted:
                    return
                password = pwd_dialog.get_password()
                if not password:
                    QMessageBox.warning(self, self.translate_text("Avertissement"),
                                        self.translate_text("Veuillez entrer un mot de passe"))
                    return
                if pwd_dialog.password_input.text() != pwd_dialog.confirm_input.text():
                    QMessageBox.warning(self, self.translate_text("Erreur"),
                                        self.translate_text("Les mots de passe ne correspondent pas"))
                    return

            output_dir = self.get_output_directory()
            if not output_dir:
                return

            archive_format    = settings['format']
            compression_level = settings['level']
            archive_name      = settings['name']
            use_password      = settings['password']
            settings['split']
            split_size        = settings['split_size']
            delete_originals  = settings['delete_originals']
            password          = password if _encrypt else None

        else:
            dialog = CompressionDialog(self, self.current_language)
            dialog.split_checkbox.setEnabled(True)
            if compression_mode == "folders_with_structure" and folders_to_compress:
                _dn = Path(folders_to_compress[0]).name if len(folders_to_compress) == 1 \
                    else f"folders_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                dialog.filename_input.setText(_dn)

            if dialog.exec() != QDialog.Accepted:
                return

            settings          = dialog.get_compression_settings()
            archive_format    = settings['format']
            compression_level = settings['level']
            archive_name      = settings['name']
            use_password      = settings['password']
            settings['split']
            split_size        = settings['split_size']
            delete_originals  = settings['delete_originals']

            if not archive_name:
                QMessageBox.warning(self, self.translate_text("Erreur"),
                                    self.translate_text("Veuillez entrer un nom pour l'archive"))
                return

            output_dir = self.get_output_directory()
            if not output_dir:
                return

            password = None
            if use_password:
                pwd_dialog = PasswordDialog(self, self.current_language)
                if pwd_dialog.exec() == QDialog.Accepted:
                    password = pwd_dialog.get_password()
                    if not password:
                        QMessageBox.warning(self, self.translate_text("Avertissement"),
                                            self.translate_text("Veuillez entrer un mot de passe"))
                        return
                    if pwd_dialog.password_input.text() != pwd_dialog.confirm_input.text():
                        QMessageBox.warning(self, self.translate_text("Erreur"),
                                            self.translate_text("Les mots de passe ne correspondent pas"))
                        return
                else:
                    return

        archive_format = archive_format.lower()
        norm_map = {
            'tar.gz': 'gz',
            'tar': 'tar',
            'zip': 'zip',
            'rar': 'rar'
        }
        fmt_to_record = norm_map.get(archive_format, archive_format)
        self.achievement_system.mark_format_as_used(fmt_to_record)
        archive_format = settings['format']
        compression_level = settings['level']
        archive_name = settings['name']
        use_password = settings['password']
        settings['split']
        split_size = settings['split_size']
        delete_originals = settings['delete_originals']

        if not archive_name:
            QMessageBox.warning(self, self.translate_text("Erreur"),
                            self.translate_text("Veuillez entrer un nom pour l'archive"))
            return

        output_dir = self.get_output_directory()
        if not output_dir:
            return

        password = None
        if use_password:
            pwd_dialog = PasswordDialog(self, self.current_language)
            if pwd_dialog.exec() == QDialog.Accepted:
                password = pwd_dialog.get_password()
                if not password:
                    QMessageBox.warning(self, self.translate_text("Avertissement"),
                                    self.translate_text("Veuillez entrer un mot de passe"))
                    return
                if pwd_dialog.password_input.text() != pwd_dialog.confirm_input.text():
                    QMessageBox.warning(self, self.translate_text("Erreur"),
                                    self.translate_text("Les mots de passe ne correspondent pas"))
                    return
            else:
                return

        start_time = datetime.now()

        if compression_mode == "folders_with_structure":
            success = self.compress_folders_with_structure(
                folders_to_compress,
                files_to_compress,
                output_dir,
                archive_name,
                archive_format,
                compression_level,
                password,
                delete_originals,
                split_size
            )
        else:
            all_files = files_to_compress.copy()
            for folder in folders_to_compress:
                for root, dirs, files in os.walk(folder):
                    for file in files:
                        all_files.append(os.path.join(root, file))

            success = self.process_compression(
                all_files,
                output_dir,
                archive_name,
                archive_format,
                compression_level,
                password,
                delete_originals,
                split_size
            )

        if success:
            conversion_time = (datetime.now() - start_time).total_seconds()

            operation_type = "Compression (selection)" if selected_items else "Compression (all)"

            notes = f"Format: {archive_format}, Level: {compression_level}"

            if compression_mode == "folders_with_structure":
                notes += self.translate_text("nt_cmp1").format(len(folders_to_compress))
                if files_to_compress:
                    notes += self.translate_text("nt_cmp2").format(len(files_to_compress))
            else:
                notes += self.translate_text("nt_cmp3").format(len(files_to_process))
            total_size = 0
            for item_path in files_to_process:
                if os.path.isfile(item_path):
                    total_size += os.path.getsize(item_path)
                elif os.path.isdir(item_path):
                    total_size += self.calculate_folder_size(item_path)

            self.db_manager.add_conversion_record(
                source_file=", ".join([Path(f).name for f in files_to_process[:3]]),
                source_format="Various",
                target_file=os.path.join(output_dir, f"{archive_name}.{self.get_archive_extension(archive_format)}"),
                target_format=archive_format,
                operation_type=operation_type,
                file_size=total_size,
                conversion_time=conversion_time,
                success=True,
                notes=notes
            )
            self.achievement_system.record_conversion("compression", total_size, True)
            if password:
                self.achievement_system.record_archive_protection(1, len(password), archive_format)
            if self.config.get("enable_system_notifications", True):
                self.system_notifier.send("file_compression")

    def compress_folders_with_structure(self, folders, additional_files, output_dir, archive_name,
                                        archive_format, compression_level, password, delete_originals, split_size):
        try:
            print(f"[DEBUG] Compressing folders with structure: {len(folders)} folders, {len(additional_files)} additional files")

            total_size = 0
            for folder in folders:
                total_size += self.calculate_folder_size(folder)
            for file in additional_files:
                if os.path.exists(file):
                    total_size += os.path.getsize(file)

            total_size_gb = total_size / (1024**3)
            self.achievement_system.record_compression(total_size_gb)

            folder_names = ", ".join([Path(f).name for f in folders])
            message = self.translate_text(f"Compression of {len(folders)} folder(s) with structure: {folder_names}")
            if additional_files:
                message += f" and {len(additional_files)} additional file(s)"

            self.show_progress(True, message)

            extension = self.get_archive_extension(archive_format)
            archive_path = os.path.join(output_dir, f"{archive_name}.{extension}")

            counter = 1
            base_name = Path(archive_path).stem
            while os.path.exists(archive_path):
                archive_path = os.path.join(output_dir, f"{base_name}_{counter}.{extension}")
                counter += 1

            print(f"[DEBUG] Final archive: {archive_path}")

            if archive_format in ["ZIP", self.translate_text("ZIP")]:
                success = self.create_structured_zip_archive(
                    archive_path, folders, additional_files, compression_level, password, split_size
                )
            elif archive_format in ["RAR", self.translate_text("RAR")]:
                success = self.create_structured_rar_archive(
                    archive_path, folders, additional_files, compression_level, password, split_size
                )
            else:
                all_files = []
                for folder in folders:
                    for root, dirs, files in os.walk(folder):
                        for file in files:
                            all_files.append(os.path.join(root, file))

                all_files.extend(additional_files)
                success = self.process_compression(
                    all_files, output_dir, archive_name, archive_format,
                    compression_level, password, delete_originals, split_size
                )

            self.show_progress(False)

            if success:
                compressed_size = os.path.getsize(archive_path) if os.path.exists(archive_path) else 0

                message = self.translate_text("creat_succ").format(len(folders))

                for i, folder in enumerate(folders):
                    folder_name = Path(folder).name
                    file_count = sum(len(files) for _, _, files in os.walk(folder))
                    message += self.translate_text("fl_nc").format(folder_name, file_count)

                if additional_files:
                    message += self.translate_text("fl_ad").format(len(additional_files))

                message += self.translate_text("fmt_ar").format(archive_format, Path(archive_path).name, self.format_size(compressed_size))

                QMessageBox.information(self, self.translate_text("Succès"), self.translate_text(message))

                total_size = 0
                for folder in folders:
                    total_size += self.calculate_folder_size(folder)
                for f in additional_files:
                    if os.path.isfile(f):
                        total_size += os.path.getsize(f)
                self.achievement_system.record_conversion("compression", total_size, True)
                if password:
                    self.achievement_system.record_archive_protection(1, len(password), archive_format)

                if self.config.get("enable_system_notifications", True):
                    self.system_notifier.send("file_compression")

                if delete_originals:
                    deleted_count = 0
                    for item in folders + additional_files:
                        try:
                            if os.path.exists(item):
                                if os.path.isdir(item):
                                    shutil.rmtree(item)
                                else:
                                    os.remove(item)
                                deleted_count += 1
                        except Exception as e:
                            print(f"[ERROR] Cannot delete {item}: {e}")

                    if deleted_count > 0:
                        self.status_bar.showMessage(self.translate_text("org_el_del").format(deleted_count))

                return True
            else:
                QMessageBox.critical(self, self.translate_text("Erreur"),
                                self.translate_text("Compression failed"))
                return False

        except Exception as e:
            self.show_progress(False)
            print(f"[ERROR] Error compressing folders with structure: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, self.translate_text("Erreur"),
                            self.translate_text(f"Error during compression: {str(e)}"))
            return False

