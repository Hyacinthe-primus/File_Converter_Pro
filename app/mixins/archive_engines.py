"""ArchiveEnginesMixin — ZIP, RAR, TAR archive creation methods."""

import os
import subprocess
import tempfile
import zipfile
from pathlib import Path

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0

from PySide6.QtWidgets import QMessageBox


class ArchiveEnginesMixin:
    """Mixin: archive creation engines (ZIP, RAR, TAR) for FileConverterApp."""

    def create_structured_zip_archive(self, archive_path, folders, additional_files, compression_level, password, split_size):
        try:
            print(f"[DEBUG] Creating structured ZIP: {archive_path}")

            compression_map = {
                self.translate_text("Normal"): zipfile.ZIP_STORED,
                self.translate_text("Haute compression"): zipfile.ZIP_DEFLATED,
                self.translate_text("Compression maximale"): zipfile.ZIP_LZMA
            }

            compression_method = compression_map.get(compression_level, zipfile.ZIP_DEFLATED)

            os.makedirs(os.path.dirname(archive_path), exist_ok=True)

            if password:
                try:
                    import pyzipper
                    print("[DEBUG] Using pyzipper with AES-256 encryption and structure")

                    with pyzipper.AESZipFile(
                        archive_path,
                        'w',
                        compression=compression_method,
                        encryption=pyzipper.WZ_AES
                    ) as zipf:
                        zipf.setpassword(password.encode('utf-8'))

                        for folder in folders:
                            folder_name = Path(folder).name
                            print(f"[DEBUG] Adding folder: {folder_name}")

                            for root, dirs, files in os.walk(folder):
                                for file in files:
                                    full_path = os.path.join(root, file)
                                    rel_path = os.path.relpath(full_path, os.path.dirname(folder))
                                    arcname = os.path.join(folder_name, rel_path)

                                    try:
                                        zipf.write(full_path, arcname)
                                        print(f"[DEBUG] Added: {arcname}")
                                    except Exception as e:
                                        print(f"[WARNING] Cannot add {full_path}: {e}")

                        for file_path in additional_files:
                            if os.path.exists(file_path):
                                arcname = Path(file_path).name
                                zipf.write(file_path, arcname)
                                print(f"[DEBUG] Additional file added: {arcname}")

                    print(f"[SUCCESS] Structured ZIP archive created: {archive_path}")
                    return True

                except ImportError:
                    print("[WARNING] pyzipper not installed, using standard zipfile")
                    password = None

            with zipfile.ZipFile(archive_path, 'w', compression=compression_method) as zipf:
                for folder in folders:
                    folder_name = Path(folder).name
                    print(f"[DEBUG] Adding folder: {folder_name}")

                    for root, dirs, files in os.walk(folder):
                        for file in files:
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_path, os.path.dirname(folder))
                            arcname = os.path.join(folder_name, rel_path)

                            try:
                                zipf.write(full_path, arcname)
                                print(f"[DEBUG] Added: {arcname}")
                            except Exception as e:
                                print(f"[WARNING] Cannot add {full_path}: {e}")

                for file_path in additional_files:
                    if os.path.exists(file_path):
                        arcname = Path(file_path).name
                        zipf.write(file_path, arcname)
                        print(f"[DEBUG] Additional file added: {arcname}")

            print(f"[SUCCESS] Structured ZIP archive created (without encryption): {archive_path}")
            return True

        except Exception as e:
            print(f"[ERROR] Error creating structured ZIP: {e}")
            import traceback
            traceback.print_exc()
            return False

    def find_split_archive_parts(self, base_archive_path, archive_format):
        base_path = Path(base_archive_path)
        base_dir = base_path.parent
        base_stem = base_path.stem
        extension = base_path.suffix.lower()

        parts_created = []

        if archive_format in ["ZIP", self.translate_text("ZIP")]:
            patterns = [
                f"{base_stem}{extension}",
                f"{base_stem}.z*",
                f"{base_stem}{extension}.*",
                f"{base_stem}.part*{extension}",
            ]
        elif archive_format in ["RAR", self.translate_text("RAR")]:
            patterns = [
                f"{base_stem}{extension}",
                f"{base_stem}.r*",
                f"{base_stem}.part*{extension}",
            ]
        else:
            patterns = [f"{base_stem}{extension}"]

        for pattern in patterns:
            try:
                files = list(base_dir.glob(pattern))
                for file in files:
                    if file not in parts_created:
                        parts_created.append(file)
            except Exception:
                continue

        parts_created.sort()

        return parts_created

    def create_split_zip_archive(self, base_archive_path, files_to_compress, compression_level, password, split_size_mb):
        try:
            print(f"[DEBUG SPLIT ZIP] Starting - max size: {split_size_mb}MB, files: {len(files_to_compress)}, password: {'Yes' if password else 'No'}")

            winrar_paths = [
                r"C:\Program Files\WinRAR\WinRAR.exe",
                r"C:\Program Files (x86)\WinRAR\WinRAR.exe",
                r"C:\Program Files\WinRAR\Rar.exe",
                "rar",
                "winrar"
            ]

            winrar_exe = None
            for path in winrar_paths:
                if path in ["rar", "winrar"]:
                    try:
                        result = subprocess.run([path, "--version"], capture_output=True, creationflags=_NO_WINDOW)
                        if result.returncode == 0 or result.returncode == 1:
                            winrar_exe = path
                            break
                    except Exception:
                        continue
                elif os.path.exists(path):
                    winrar_exe = path
                    break

            if not winrar_exe:
                QMessageBox.warning(self, self.translate_text("Information"),
                                self.translate_text("WinRAR not found for ZIP splitting.\n"
                                                    "Installation required for splitting."))
                return False

            print(f"[DEBUG] WinRAR found: {winrar_exe}")

            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
                for file_path in files_to_compress:
                    if os.path.exists(file_path):
                        escaped_path = file_path.replace('"', '\\"')
                        f.write(f'"{escaped_path}"\n')
                list_file = f.name

            print(f"[DEBUG] List file created: {list_file}")

            try:
                compression_map = {
                    self.translate_text("Normal"): "-m3",
                    self.translate_text("Haute compression"): "-m5",
                    self.translate_text("Compression maximale"): "-m5 -md128M"
                }

                compression_args = compression_map.get(compression_level, "-m3")

                cmd = [winrar_exe, 'a']

                cmd.append(compression_args)

                cmd.append("-afzip")

                cmd.append(f"-v{split_size_mb}M")
                print(f"[DEBUG] Splitting enabled: {split_size_mb}MB per part")

                if password:
                    cmd.append(f"-p{password}")
                    cmd.append("-hp")
                    print("[DEBUG] Using password with header encryption")
                else:
                    print("[DEBUG] No password, no encryption options")

                cmd.append("-ep1")
                cmd.append("-idq")
                cmd.append("-r")

                cmd.append(base_archive_path)
                cmd.append(f"@{list_file}")

                print(f"[DEBUG] WinRAR command for split ZIP: {' '.join(cmd)}")

                result = subprocess.run(cmd, capture_output=True, text=True, creationflags=_NO_WINDOW)

                try:
                    os.unlink(list_file)
                except Exception:
                    pass

                if result.returncode == 0:
                    print(f"[DEBUG] Split ZIP archive successfully created: {base_archive_path}")

                    base_path = Path(base_archive_path)
                    base_dir = base_path.parent
                    base_stem = base_path.stem

                    parts_created = []

                    if os.path.exists(base_archive_path):
                        parts_created.append(Path(base_archive_path))

                    pattern_z = f"{base_stem}.z*"
                    z_parts = sorted(base_dir.glob(pattern_z))
                    if z_parts:
                        parts_created.extend(z_parts)

                    pattern_zip_num = f"{base_stem}.zip.*"
                    zip_num_parts = sorted(base_dir.glob(pattern_zip_num))
                    if zip_num_parts:
                        parts_created.extend(zip_num_parts)

                    pattern_part = f"{base_stem}.part*.zip"
                    part_parts = sorted(base_dir.glob(pattern_part))
                    if part_parts:
                        parts_created.extend(part_parts)

                    parts_created = sorted(set(parts_created))

                    if parts_created:
                        print(f"[DEBUG] Split ZIP archive created: {len(parts_created)} parts")
                        for part in sorted(parts_created):
                            size_mb = os.path.getsize(part) / (1024 * 1024)
                            print(f"[DEBUG] Part: {part.name} - {size_mb:.1f}MB")
                        return True
                    else:
                        if os.path.exists(base_archive_path):
                            size_mb = os.path.getsize(base_archive_path) / (1024 * 1024)
                            print(f"[DEBUG] Single ZIP archive created: {base_archive_path} - {size_mb:.1f}MB")
                            return True
                        else:
                            print("[ERROR] No archive created")
                            return False
                else:
                    print(f"[ERROR] WinRAR error (code {result.returncode}):")
                    print(f"[ERROR] stdout: {result.stdout}")
                    print(f"[ERROR] stderr: {result.stderr}")

                    try:
                        base_path = Path(base_archive_path)
                        base_dir = base_path.parent
                        base_stem = base_path.stem

                        patterns_to_clean = [
                            f"{base_stem}.zip",
                            f"{base_stem}.z*",
                            f"{base_stem}.zip.*",
                            f"{base_stem}.part*.zip"
                        ]

                        for pattern in patterns_to_clean:
                            for file in base_dir.glob(pattern):
                                try:
                                    os.remove(file)
                                    print(f"[DEBUG] Cleaning: {file.name}")
                                except Exception:
                                    pass
                    except Exception:
                        pass

                    return False

            except Exception as e:
                print(f"[ERROR] Exception creating split ZIP with WinRAR: {e}")

                try:
                    if os.path.exists(list_file):
                        os.unlink(list_file)
                except Exception:
                    pass

                return False

        except Exception as e:
            print(f"[ERROR] General error creating split ZIP: {e}")
            import traceback
            traceback.print_exc()
            return False

    def create_single_zip_archive(self, archive_path, files_to_compress, compression_method, password):
        try:
            print(f"[DEBUG CREATE ZIP] Creating: {archive_path}, files: {len(files_to_compress)}, password: {'Yes' if password else 'No'}")

            os.makedirs(os.path.dirname(archive_path), exist_ok=True)

            if password:
                try:
                    import pyzipper
                    print("[DEBUG] Using pyzipper with AES-256 encryption")

                    with pyzipper.AESZipFile(
                        archive_path,
                        'w',
                        compression=compression_method,
                        encryption=pyzipper.WZ_AES
                    ) as zipf:
                        zipf.setpassword(password.encode('utf-8'))

                        for i, file_path in enumerate(files_to_compress):
                            try:
                                if os.path.exists(file_path):
                                    arcname = Path(file_path).name
                                    zipf.write(file_path, arcname)

                                    progress = int((i + 1) / len(files_to_compress) * 100)
                                    self.progress_bar.setValue(progress)
                                    print(f"[DEBUG] Added to ZIP: {arcname}")
                                else:
                                    print(f"[WARNING] File not found: {file_path}")
                            except Exception as e:
                                print(f"[ERROR] Error adding {file_path}: {e}")
                                return False

                    print(f"[SUCCESS] ZIP archive successfully created: {archive_path}")
                    return True

                except ImportError:
                    print("[WARNING] pyzipper not installed, using standard zipfile")
                    QMessageBox.warning(self, self.translate_text("Information"),
                                    self.translate_text("pyzipper is not installed. Encryption not available."))
                    password = None

                except Exception as e:
                    print(f"[ERROR] pyzipper error: {e}")
                    password = None

            try:
                with zipfile.ZipFile(archive_path, 'w', compression=compression_method) as zipf:
                    for i, file_path in enumerate(files_to_compress):
                        try:
                            if os.path.exists(file_path):
                                arcname = Path(file_path).name
                                zipf.write(file_path, arcname)

                                progress = int((i + 1) / len(files_to_compress) * 100)
                                self.progress_bar.setValue(progress)
                                print(f"[DEBUG] Added to ZIP: {arcname}")
                            else:
                                print(f"[WARNING] File not found: {file_path}")
                        except Exception as e:
                            print(f"[ERROR] Error adding {file_path}: {e}")
                            return False

                print(f"[SUCCESS] ZIP archive created (without encryption): {archive_path}")
                return True

            except Exception as e:
                print(f"[ERROR] Error creating ZIP: {e}")
                return False

        except Exception as e:
            print(f"[ERROR] Error creating ZIP: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_archive_extension(self, archive_format):
        extensions = {
            "ZIP": "zip",
            "RAR": "rar",
            "TAR.GZ": "tar.gz",
            "TAR": "tar",
            self.translate_text("ZIP"): "zip",
            self.translate_text("TAR.GZ"): "tar.gz",
            self.translate_text("TAR"): "tar",
            self.translate_text("RAR"): "rar"
        }
        return extensions.get(archive_format, "zip")

    def create_zip_archive(self, archive_path, files_to_compress, compression_level, password):
        try:
            compression_map = {
                self.translate_text("Normal"): zipfile.ZIP_STORED,
                self.translate_text("Haute compression"): zipfile.ZIP_DEFLATED,
                self.translate_text("Compression maximale"): zipfile.ZIP_LZMA
            }

            compression_method = compression_map.get(compression_level, zipfile.ZIP_DEFLATED)

            print(f"[DEBUG] Creating ZIP: {archive_path}")
            print(f"[DEBUG] Compression method: {compression_method}")
            print(f"[DEBUG] Number of files: {len(files_to_compress)}")
            print(f"[DEBUG] Password: {'Yes' if password else 'No'}")

            if password:
                try:
                    import pyzipper
                    print("[DEBUG] Using pyzipper with AES encryption")

                    with pyzipper.AESZipFile(
                        archive_path,
                        'w',
                        compression=compression_method,
                        encryption=pyzipper.WZ_AES
                    ) as zipf:
                        zipf.setpassword(password.encode('utf-8'))

                        for i, file_path in enumerate(files_to_compress):
                            try:
                                if os.path.exists(file_path):
                                    arcname = Path(file_path).name
                                    zipf.write(file_path, arcname)

                                    progress = int((i + 1) / len(files_to_compress) * 100)
                                    self.progress_bar.setValue(progress)
                                    print(f"[DEBUG] Added: {arcname}")
                            except Exception as e:
                                print(f"[ERROR] Error adding {file_path}: {e}")

                    print(f"[DEBUG] ZIP archive successfully created: {archive_path}")
                    return True

                except ImportError:
                    print("[WARNING] pyzipper not installed, using standard zipfile")
                    QMessageBox.warning(self, self.translate_text("Information"),
                                        self.translate_text("pyzipper is not installed. Encryption not available."))
                    password = None

            try:
                with zipfile.ZipFile(archive_path, 'w', compression=compression_method) as zipf:
                    for i, file_path in enumerate(files_to_compress):
                        try:
                            if os.path.exists(file_path):
                                arcname = Path(file_path).name
                                zipf.write(file_path, arcname)

                                progress = int((i + 1) / len(files_to_compress) * 100)
                                self.progress_bar.setValue(progress)
                                print(f"[DEBUG] Added: {arcname}")
                        except Exception as e:
                            print(f"[ERROR] Error adding {file_path}: {e}")

                print(f"[DEBUG] ZIP archive successfully created: {archive_path}")
                return True

            except Exception as e:
                print(f"[ERROR] Error creating ZIP: {e}")
                return False

        except Exception as e:
            print(f"[ERROR] Error creating ZIP: {e}")
            return False

    def create_rar_archive(self, archive_path, files_to_compress, compression_level, password, split_size=0):
        try:
            print(f"[DEBUG] Creating RAR: {archive_path}")
            print(f"[DEBUG] Split size: {split_size}MB")

            winrar_paths = [
                r"C:\Program Files\WinRAR\WinRAR.exe",
                r"C:\Program Files (x86)\WinRAR\WinRAR.exe",
                r"C:\Program Files\WinRAR\Rar.exe",
                "rar",
                "winrar"
            ]

            winrar_exe = None
            for path in winrar_paths:
                if path in ["rar", "winrar"]:
                    try:
                        result = subprocess.run([path, "--version"], capture_output=True, creationflags=_NO_WINDOW)
                        if result.returncode == 0 or result.returncode == 1:
                            winrar_exe = path
                            break
                    except Exception:
                        continue
                elif os.path.exists(path):
                    winrar_exe = path
                    break

            if not winrar_exe:
                QMessageBox.warning(self, self.translate_text("Information"),
                                self.translate_text("WinRAR not found. Installation required:\n"
                                                    "1. Download WinRAR from win-rar.com\n"
                                                    "2. Install it\n"
                                                    "3. Add WinRAR to PATH or restart the application"))
                return False

            print(f"[DEBUG] WinRAR found: {winrar_exe}")

            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
                for file_path in files_to_compress:
                    if os.path.exists(file_path):
                        escaped_path = file_path.replace('"', '\\"')
                        f.write(f'"{escaped_path}"\n')
                list_file = f.name

            print(f"[DEBUG] List file created: {list_file}")

            try:
                compression_map = {
                    self.translate_text("Normal"): "-m3",
                    self.translate_text("Haute compression"): "-m5",
                    self.translate_text("Compression maximale"): "-m5 -md128M"
                }

                compression_args = compression_map.get(compression_level, "-m3")

                cmd = [winrar_exe, 'a']

                cmd.append(compression_args)

                if split_size > 0:
                    cmd.append(f"-v{split_size}M")
                    print(f"[DEBUG] Splitting enabled: {split_size}MB per part")

                if password:
                    cmd.append(f"-p{password}")
                    cmd.append("-hp")
                    print("[DEBUG] Using password with header encryption")
                else:
                    cmd.append("-p-")

                cmd.append("-ep1")
                cmd.append("-idq")

                cmd.append(archive_path)
                cmd.append(f"@{list_file}")

                print(f"[DEBUG] WinRAR command: {' '.join(cmd)}")

                result = subprocess.run(cmd, capture_output=True, text=True, creationflags=_NO_WINDOW)

                try:
                    os.unlink(list_file)
                except Exception:
                    pass

                if result.returncode == 0:
                    print(f"[DEBUG] RAR archive successfully created: {archive_path}")

                    if split_size > 0:
                        base_name = Path(archive_path).stem
                        base_dir = Path(archive_path).parent
                        parts = list(base_dir.glob(f"{base_name}.part*.rar"))
                        if parts:
                            print(f"[DEBUG] Split archive created: {len(parts)} parts")
                            return True
                        else:
                            if os.path.exists(archive_path):
                                print(f"[DEBUG] Single archive created: {archive_path}")
                                return True
                            else:
                                print("[ERROR] No archive created")
                                return False
                    else:
                        if os.path.exists(archive_path):
                            print(f"[DEBUG] Single archive created: {archive_path}")
                            return True
                        else:
                            print("[ERROR] Archive not created")
                            return False
                else:
                    print(f"[ERROR] WinRAR error (code {result.returncode}):")
                    print(f"[ERROR] stdout: {result.stdout}")
                    print(f"[ERROR] stderr: {result.stderr}")

                    try:
                        if os.path.exists(archive_path):
                            os.remove(archive_path)
                        if split_size > 0:
                            base_name = Path(archive_path).stem
                            base_dir = Path(archive_path).parent
                            for part in base_dir.glob(f"{base_name}.part*.rar"):
                                try:
                                    os.remove(part)
                                except Exception:
                                    pass
                    except Exception:
                        pass

                    return False

            except Exception as e:
                print(f"[ERROR] Exception creating RAR: {e}")

                try:
                    if os.path.exists(list_file):
                        os.unlink(list_file)
                except Exception:
                    pass

                return False

        except Exception as e:
            print(f"[ERROR] General error creating RAR: {e}")
            return False

    def create_tar_archive(self, archive_path, files_to_compress, archive_format, compression_level):
        import tarfile
        compression_map = {"TAR.GZ": "gz", "TAR": None}
        compression_type = compression_map[archive_format]
        mode = "w:gz" if compression_type == "gz" else "w"
        try:
            with tarfile.open(archive_path, mode) as tar:
                for i, file_path in enumerate(files_to_compress):
                    try:
                        if os.path.exists(file_path):
                            tar.add(file_path, arcname=Path(file_path).name)
                            self.progress_bar.setValue(int((i + 1) / len(files_to_compress) * 100))
                    except Exception as e:
                        print(f"Error adding {file_path}: {e}")
            return True
        except Exception as e:
            print(f"Error creating TAR: {e}")
            return False