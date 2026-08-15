"""Audio/video optimization via ffmpeg."""

from __future__ import annotations

import os
from pathlib import Path


class MediaOptimizerMixin:
    """Audio/video optimization methods."""

    def optimize_av_file(self, src_path, output_path, quality_level, media_type):
        try:
            import shutil
            import subprocess

            from external_binaries import resolve_binary

            ffmpeg_bin = resolve_binary("ffmpeg")
            if not ffmpeg_bin:
                return False
            ext = Path(output_path).suffix.lower().lstrip(".")
            if media_type == "audio":
                AUDIO_PRESETS = {
                    "mp3": {
                        0: ["-codec:a", "libmp3lame", "-q:a", "2", "-ar", "44100"],
                        1: ["-codec:a", "libmp3lame", "-q:a", "4", "-ar", "44100"],
                        2: ["-codec:a", "libmp3lame", "-q:a", "7", "-ar", "44100"],
                    },
                    "aac": {
                        0: ["-codec:a", "aac", "-b:a", "192k", "-ar", "44100"],
                        1: ["-codec:a", "aac", "-b:a", "128k", "-ar", "44100"],
                        2: ["-codec:a", "aac", "-b:a", "96k", "-ar", "44100"],
                    },
                    "ogg": {
                        0: ["-codec:a", "libvorbis", "-q:a", "6"],
                        1: ["-codec:a", "libvorbis", "-q:a", "4"],
                        2: ["-codec:a", "libvorbis", "-q:a", "2"],
                    },
                    "flac": {
                        0: ["-codec:a", "flac", "-compression_level", "5"],
                        1: ["-codec:a", "flac", "-compression_level", "8"],
                        2: ["-codec:a", "flac", "-compression_level", "12"],
                    },
                    "wav": {
                        0: ["-codec:a", "pcm_s16le", "-ar", "44100"],
                        1: ["-codec:a", "pcm_s16le", "-ar", "44100"],
                        2: ["-codec:a", "pcm_s16le", "-ar", "22050"],
                    },
                }
                default_audio = {
                    0: ["-codec:a", "libmp3lame", "-q:a", "2"],
                    1: ["-codec:a", "libmp3lame", "-q:a", "4"],
                    2: ["-codec:a", "libmp3lame", "-q:a", "7"],
                }
                presets = AUDIO_PRESETS.get(ext, default_audio)
                args = presets.get(quality_level, presets[1])
            else:
                VIDEO_PRESETS = {
                    "mp4": {
                        0: [
                            "-codec:v",
                            "libx264",
                            "-crf",
                            "18",
                            "-preset",
                            "slow",
                            "-codec:a",
                            "aac",
                            "-b:a",
                            "192k",
                            "-movflags",
                            "+faststart",
                        ],
                        1: [
                            "-codec:v",
                            "libx264",
                            "-crf",
                            "23",
                            "-preset",
                            "medium",
                            "-codec:a",
                            "aac",
                            "-b:a",
                            "128k",
                            "-movflags",
                            "+faststart",
                        ],
                        2: [
                            "-codec:v",
                            "libx264",
                            "-crf",
                            "28",
                            "-preset",
                            "fast",
                            "-codec:a",
                            "aac",
                            "-b:a",
                            "96k",
                            "-movflags",
                            "+faststart",
                        ],
                    },
                    "mkv": {
                        0: ["-codec:v", "libx264", "-crf", "18", "-preset", "slow", "-codec:a", "aac", "-b:a", "192k"],
                        1: [
                            "-codec:v",
                            "libx264",
                            "-crf",
                            "23",
                            "-preset",
                            "medium",
                            "-codec:a",
                            "aac",
                            "-b:a",
                            "128k",
                        ],
                        2: ["-codec:v", "libx264", "-crf", "28", "-preset", "fast", "-codec:a", "aac", "-b:a", "96k"],
                    },
                    "webm": {
                        0: ["-codec:v", "libvpx-vp9", "-crf", "24", "-b:v", "0", "-codec:a", "libopus", "-b:a", "160k"],
                        1: ["-codec:v", "libvpx-vp9", "-crf", "33", "-b:v", "0", "-codec:a", "libopus", "-b:a", "128k"],
                        2: ["-codec:v", "libvpx-vp9", "-crf", "42", "-b:v", "0", "-codec:a", "libopus", "-b:a", "96k"],
                    },
                }
                default_video = {
                    0: ["-codec:v", "libx264", "-crf", "18", "-preset", "slow", "-codec:a", "aac", "-b:a", "192k"],
                    1: ["-codec:v", "libx264", "-crf", "23", "-preset", "medium", "-codec:a", "aac", "-b:a", "128k"],
                    2: ["-codec:v", "libx264", "-crf", "28", "-preset", "fast", "-codec:a", "aac", "-b:a", "96k"],
                }
                presets = VIDEO_PRESETS.get(ext, default_video)
                args = list(presets.get(quality_level, presets[1]))

                # CRF/bitrate tuning alone barely dents 4K/1080p source size.
                # scale=-2:min(ih,H) only ever scales DOWN (min() picks the
                # smaller of source height and the cap) and never upscales
                # smaller sources; -2 keeps width divisible by 2 for x264/vp9.
                max_height_map = {0: 1080, 1: 720, 2: 480}
                target_h = max_height_map.get(quality_level, 720)
                args += ["-vf", f"scale=-2:min(ih\\,{target_h})"]
            cmd = [ffmpeg_bin, "-y", "-i", src_path] + args + [output_path]
            _no_window = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            result = subprocess.run(cmd, capture_output=True, timeout=3600, creationflags=_no_window)
            if result.returncode != 0:
                return False
            if os.path.exists(output_path):
                orig_size = os.path.getsize(src_path)
                new_size = os.path.getsize(output_path)
                # 5% tolerance rather than a strict >=: re-encoding can add a
                # few % of container/codec overhead on already-compressed
                # source files without that being a real regression worth
                # discarding the transcode over.
                if new_size >= orig_size * 1.05:
                    shutil.copy2(src_path, output_path)
            return True
        except Exception as e:
            print(f"[optimize_av] Error {src_path}: {e}")
            return False
