"""ArchiveEnginesMixin - ZIP, 7Z, TAR archive creation methods."""

import os
import queue
import re
import shutil
import subprocess
import tempfile
import threading
import time
import zipfile
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from external_binaries import resolve_binary

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0


class ArchiveEnginesMixin:
    """Mixin: archive creation engines (ZIP, 7Z, TAR) for FileConverterApp."""

    def _find_sevenzip(self):
        sevenzip = resolve_binary("7z")
        if sevenzip:
            print(f"[DEBUG] 7-Zip found: {sevenzip}")
            return sevenzip
        QMessageBox.warning(
            self,
            self.translate_text("Information"),
            self.translate_text("7-Zip not found for archive creation.\nInstallation required."),
        )
        return None

    def _write_archive_list(self, files_to_compress):
        list_file = None
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8") as f:
            for file_path in files_to_compress:
                if os.path.exists(file_path):
                    escaped_path = file_path.replace('"', '\\"')
                    f.write(f'"{escaped_path}"\n')
            list_file = f.name
        print(f"[DEBUG] List file created: {list_file}")
        return list_file

    def _compression_target_exists(self, archive_path, split_size):
        if split_size > 0:
            base = Path(archive_path)
            stem = base.stem
            ext = base.suffix.lstrip(".").lower()
            patterns = [f"{stem}.{ext}.*", f"{stem}.z*", f"{stem}.{ext}"]
            for pattern in patterns:
                if any(base.parent.glob(pattern)):
                    return True
        return os.path.exists(archive_path)

    def _archive_total_size(self, archive_path, split_size):
        total = 0
        try:
            if split_size > 0:
                base = Path(archive_path)
                stem = base.stem
                ext = base.suffix.lstrip(".").lower()
                for pattern in (f"{stem}.{ext}.*", f"{stem}.z*", f"{stem}.{ext}"):
                    for part in base.parent.glob(pattern):
                        try:
                            total += os.path.getsize(part)
                        except OSError:
                            pass
            elif os.path.exists(archive_path):
                total = os.path.getsize(archive_path)
        except OSError:
            total = 0
        return total

    def _run_sevenzip_with_progress(self, cmd):
        cmd = list(cmd) + ["-bsp2"]

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=_NO_WINDOW,
        )

        progress_queue = queue.Queue()

        def _read_progress():
            buf = b""
            try:
                while True:
                    chunk = proc.stderr.read(65536)
                    if not chunk:
                        break
                    buf += chunk
                    match = re.findall(rb"(\d{1,3})%", buf)
                    if match:
                        progress_queue.put(int(match[-1]))
            except Exception:
                pass

        threading.Thread(target=_read_progress, daemon=True).start()

        last_pct = 0
        while proc.poll() is None:
            try:
                while True:
                    last_pct = progress_queue.get_nowait()
            except queue.Empty:
                pass
            if last_pct:
                self.progress_bar.setValue(max(last_pct, self.progress_bar.value()))
            QApplication.processEvents()
            time.sleep(0.02)

        try:
            while True:
                last_pct = progress_queue.get_nowait()
        except queue.Empty:
            pass

        if proc.returncode == 0:
            self.progress_bar.setValue(100)
        else:
            self.progress_bar.setValue(0)

        stdout_text = ""
        try:
            if proc.stdout:
                stdout_text = proc.stdout.read().decode("utf-8", errors="replace")
                proc.stdout.close()
        except Exception:
            pass

        return proc.returncode, stdout_text


    def _sevenzip_level_args(self, compression_level, method):
        if method == "zip":
            level_map = {
                self.translate_text("Normal"): "-mx=3",
                self.translate_text("Haute compression"): "-mx=7",
                self.translate_text("Compression maximale"): "-mx=9",
            }
        else:
            level_map = {
                self.translate_text("Normal"): "-mx=3",
                self.translate_text("Haute compression"): "-mx=7",
                self.translate_text("Compression maximale"): "-mx=9 -md128M",
            }
        return level_map.get(compression_level, "-mx=3")

    def create_structured_zip_archive(
        self, archive_path, folders, additional_files, compression_level, password, split_size
    ):
        try:
            print(f"[DEBUG] Creating structured ZIP: {archive_path}")

            compression_map = {
                self.translate_text("Normal"): zipfile.ZIP_STORED,
                self.translate_text("Haute compression"): zipfile.ZIP_DEFLATED,
                self.translate_text("Compression maximale"): zipfile.ZIP_LZMA,
            }

            compression_method = compression_map.get(compression_level, zipfile.ZIP_DEFLATED)

            os.makedirs(os.path.dirname(archive_path), exist_ok=True)

            if password:
                try:
                    import pyzipper

                    print("[DEBUG] Using pyzipper with AES-256 encryption and structure")

                    with pyzipper.AESZipFile(
                        archive_path, "w", compression=compression_method, encryption=pyzipper.WZ_AES
                    ) as zipf:
                        zipf.setpassword(password.encode("utf-8"))

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

            with zipfile.ZipFile(archive_path, "w", compression=compression_method) as zipf:
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
        elif archive_format in ["7Z", self.translate_text("7Z"), "RAR", self.translate_text("RAR")]:
            patterns = [
                f"{base_stem}{extension}",
                f"{base_stem}{extension}.*",
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

    def create_split_zip_archive(
        self, base_archive_path, files_to_compress, compression_level, password, split_size_mb
    ):
        try:
            print(
                f"[DEBUG SPLIT ZIP] Starting - max size: {split_size_mb}MB, files: {len(files_to_compress)}, password: {'Yes' if password else 'No'}"  # noqa: E501
            )

            sevenzip = self._find_sevenzip()
            if not sevenzip:
                return False

            list_file = self._write_archive_list(files_to_compress)

            try:
                cmd = [sevenzip, "a"]

                cmd.append(self._sevenzip_level_args(compression_level, "zip"))

                cmd.append("-tzip")

                cmd.append(f"-v{split_size_mb}M")
                print(f"[DEBUG] Splitting enabled: {split_size_mb}MB per part")

                if password:
                    cmd.append(f"-p{password}")
                    cmd.append("-mem=AES256")
                    print("[DEBUG] Using password with AES-256 encryption")

                cmd.append("-y")

                cmd.append(base_archive_path)
                cmd.append(f"@{list_file}")

                print(f"[DEBUG] 7-Zip command for split ZIP: {' '.join(cmd)}")

                result_returncode, stdout_text = self._run_sevenzip_with_progress(cmd)

                try:
                    os.unlink(list_file)
                except Exception:
                    pass

                if result_returncode == 0:
                    print(f"[DEBUG] Split ZIP archive successfully created: {base_archive_path}")

                    base_path = Path(base_archive_path)
                    base_dir = base_path.parent
                    base_stem = base_path.stem

                    parts_created = []

                    pattern_zip_num = f"{base_stem}.zip.*"
                    zip_num_parts = sorted(base_dir.glob(pattern_zip_num))
                    if zip_num_parts:
                        parts_created.extend(zip_num_parts)

                    pattern_z = f"{base_stem}.z*"
                    z_parts = sorted(base_dir.glob(pattern_z))
                    if z_parts:
                        parts_created.extend(z_parts)

                    if os.path.exists(base_archive_path):
                        parts_created.append(Path(base_archive_path))

                    parts_created = sorted(set(parts_created))

                    if parts_created:
                        print(f"[DEBUG] Split ZIP archive created: {len(parts_created)} parts")
                        for part in sorted(parts_created):
                            size_mb = os.path.getsize(part) / (1024 * 1024)
                            print(f"[DEBUG] Part: {part.name} - {size_mb:.1f}MB")
                        return True
                    else:
                        print("[ERROR] No archive created")
                        return False
                else:
                    print(f"[ERROR] 7-Zip error (code {result_returncode}):")
                    print(f"[ERROR] stdout: {stdout_text}")

                    try:
                        base_path = Path(base_archive_path)
                        base_dir = base_path.parent
                        base_stem = base_path.stem

                        patterns_to_clean = [
                            f"{base_stem}.zip",
                            f"{base_stem}.z*",
                            f"{base_stem}.zip.*",
                            f"{base_stem}.part*.zip",
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
                print(f"[ERROR] Exception creating split ZIP with 7-Zip: {e}")

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
            print(
                f"[DEBUG CREATE ZIP] Creating: {archive_path}, files: {len(files_to_compress)}, password: {'Yes' if password else 'No'}"  # noqa: E501
            )

            os.makedirs(os.path.dirname(archive_path), exist_ok=True)

            if password:
                try:
                    import pyzipper

                    print("[DEBUG] Using pyzipper with AES-256 encryption")

                    with pyzipper.AESZipFile(
                        archive_path, "w", compression=compression_method, encryption=pyzipper.WZ_AES
                    ) as zipf:
                        zipf.setpassword(password.encode("utf-8"))

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
                    QMessageBox.warning(
                        self,
                        self.translate_text("Information"),
                        self.translate_text("pyzipper is not installed. Encryption not available."),
                    )
                    password = None

                except Exception as e:
                    print(f"[ERROR] pyzipper error: {e}")
                    password = None

            try:
                with zipfile.ZipFile(archive_path, "w", compression=compression_method) as zipf:
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
            "7Z": "7z",
            "RAR": "rar",
            "TAR.GZ": "tar.gz",
            "TAR": "tar",
            self.translate_text("ZIP"): "zip",
            self.translate_text("7Z"): "7z",
            self.translate_text("TAR.GZ"): "tar.gz",
            self.translate_text("TAR"): "tar",
            self.translate_text("RAR"): "rar",
        }
        return extensions.get(archive_format, "zip")

    def create_zip_archive(self, archive_path, files_to_compress, compression_level, password):
        try:
            compression_map = {
                self.translate_text("Normal"): zipfile.ZIP_STORED,
                self.translate_text("Haute compression"): zipfile.ZIP_DEFLATED,
                self.translate_text("Compression maximale"): zipfile.ZIP_LZMA,
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
                        archive_path, "w", compression=compression_method, encryption=pyzipper.WZ_AES
                    ) as zipf:
                        zipf.setpassword(password.encode("utf-8"))

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
                    QMessageBox.warning(
                        self,
                        self.translate_text("Information"),
                        self.translate_text("pyzipper is not installed. Encryption not available."),
                    )
                    password = None

            try:
                with zipfile.ZipFile(archive_path, "w", compression=compression_method) as zipf:
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

    def create_7z_archive(self, archive_path, files_to_compress, compression_level, password, split_size=0):
        try:
            print(f"[DEBUG] Creating 7Z: {archive_path}")
            print(f"[DEBUG] Split size: {split_size}MB")

            sevenzip = self._find_sevenzip()
            if not sevenzip:
                return False

            list_file = self._write_archive_list(files_to_compress)

            try:
                cmd = [sevenzip, "a"]

                cmd.append(self._sevenzip_level_args(compression_level, "7z"))

                cmd.append("-t7z")

                if split_size > 0:
                    cmd.append(f"-v{split_size}M")
                    print(f"[DEBUG] Splitting enabled: {split_size}MB per part")

                if password:
                    cmd.append(f"-p{password}")
                    cmd.append("-mhe=on")
                    print("[DEBUG] Using password with header encryption")
                else:
                    cmd.append("-p-")

                cmd.append("-y")

                cmd.append(archive_path)
                cmd.append(f"@{list_file}")

                print(f"[DEBUG] 7-Zip command: {' '.join(cmd)}")

                result_returncode, stdout_text = self._run_sevenzip_with_progress(cmd)

                try:
                    os.unlink(list_file)
                except Exception:
                    pass

                if result_returncode == 0:
                    print(f"[DEBUG] 7Z archive successfully created: {archive_path}")

                    if split_size > 0:
                        base_name = Path(archive_path).stem
                        base_dir = Path(archive_path).parent
                        parts = list(base_dir.glob(f"{base_name}.7z.*"))
                        if parts:
                            print(f"[DEBUG] Split archive created: {len(parts)} parts")
                            return True
                        elif os.path.exists(archive_path):
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
                    print(f"[ERROR] 7-Zip error (code {result_returncode}):")
                    print(f"[ERROR] stdout: {stdout_text}")

                    try:
                        if os.path.exists(archive_path):
                            os.remove(archive_path)
                        if split_size > 0:
                            base_name = Path(archive_path).stem
                            base_dir = Path(archive_path).parent
                            for part in base_dir.glob(f"{base_name}.7z.*"):
                                try:
                                    os.remove(part)
                                except Exception:
                                    pass
                    except Exception:
                        pass

                    return False

            except Exception as e:
                print(f"[ERROR] Exception creating 7Z: {e}")

                try:
                    if os.path.exists(list_file):
                        os.unlink(list_file)
                except Exception:
                    pass

                return False

        except Exception as e:
            print(f"[ERROR] General error creating 7Z: {e}")
            return False

    def create_structured_7z_archive(
        self, archive_path, folders, additional_files, compression_level, password, split_size
    ):
        try:
            print(f"[DEBUG] Creating structured 7Z: {archive_path}")

            sevenzip = self._find_sevenzip()
            if not sevenzip:
                return False

            os.makedirs(os.path.dirname(archive_path), exist_ok=True)

            list_file = None
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8") as f:
                for folder in folders:
                    escaped_path = folder.replace('"', '\\"')
                    f.write(f'"{escaped_path}"\n')
                for file_path in additional_files:
                    if os.path.exists(file_path):
                        escaped_path = file_path.replace('"', '\\"')
                        f.write(f'"{escaped_path}"\n')
                list_file = f.name

            try:
                cmd = [sevenzip, "a"]

                cmd.append(self._sevenzip_level_args(compression_level, "7z"))

                cmd.append("-t7z")

                if split_size > 0:
                    cmd.append(f"-v{split_size}M")
                    print(f"[DEBUG] Splitting enabled: {split_size}MB per part")

                if password:
                    cmd.append(f"-p{password}")
                    cmd.append("-mhe=on")
                    print("[DEBUG] Using password with header encryption")

                cmd.append("-y")

                cmd.append(archive_path)
                cmd.append(f"@{list_file}")

                print(f"[DEBUG] 7-Zip command for structured archive: {' '.join(cmd)}")

                result_returncode, stdout_text = self._run_sevenzip_with_progress(cmd)

                try:
                    os.unlink(list_file)
                except Exception:
                    pass

                if result_returncode == 0:
                    print(f"[SUCCESS] Structured 7Z archive created: {archive_path}")
                    return True
                else:
                    print(f"[ERROR] 7-Zip error (code {result_returncode}):")
                    print(f"[ERROR] stdout: {stdout_text}")
                    return False

            except Exception as e:
                print(f"[ERROR] Exception creating structured 7Z: {e}")

                try:
                    if list_file and os.path.exists(list_file):
                        os.unlink(list_file)
                except Exception:
                    pass

                return False

        except Exception as e:
            print(f"[ERROR] Error creating structured 7Z: {e}")
            import traceback

            traceback.print_exc()
            return False

    def process_compression(
        self, files, output_dir, archive_name, archive_format, compression_level, password, delete_originals, split_size
    ):
        try:
            extension = self.get_archive_extension(archive_format)
            archive_path = os.path.join(output_dir, f"{archive_name}.{extension}")

            counter = 1
            base_name = Path(archive_path).stem
            while self._compression_target_exists(archive_path, split_size):
                archive_path = os.path.join(output_dir, f"{base_name}_{counter}.{extension}")
                counter += 1

            print(f"[DEBUG] Final archive: {archive_path}")

            if archive_format in ["ZIP", self.translate_text("ZIP")]:
                if split_size and split_size > 0:
                    success = self.create_split_zip_archive(
                        archive_path, files, compression_level, password, split_size
                    )
                else:
                    success = self.create_zip_archive(archive_path, files, compression_level, password)
            elif archive_format in ["7Z", self.translate_text("7Z"), "RAR", self.translate_text("RAR")]:
                success = self.create_7z_archive(archive_path, files, compression_level, password, split_size)
            elif archive_format in ["TAR.GZ", self.translate_text("TAR.GZ"), "TAR", self.translate_text("TAR")]:
                success = self.create_tar_archive(archive_path, files, archive_format, compression_level)
            else:
                success = self.create_zip_archive(archive_path, files, compression_level, password)

            if success and delete_originals:
                deleted_count = 0
                for item in files:
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

            return archive_path if success else False

        except Exception as e:
            print(f"[ERROR] Error processing compression: {e}")
            import traceback

            traceback.print_exc()
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
