"""Audio/video conversions via ffmpeg."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0

class MediaConverters:
    """Audio/video conversion methods for AdvancedConverterEngine."""

    def _find_ffmpeg() -> str | None:
        """Locate ffmpeg binary in PATH or common install dirs."""
        import shutil
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg:
            return ffmpeg
        candidates = [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            "/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg",
        ]
        for c in candidates:
            if c and os.path.isfile(c):
                return c
        return None

    def _has_audio_stream(self, src: str, ffmpeg_bin: str) -> bool:
        try:
            cmd = [ffmpeg_bin, "-i", src]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, creationflags=_NO_WINDOW)
            return "Audio:" in result.stderr
        except Exception:
            return False

    def _ffmpeg_convert(self, src: str, dst: str, conversion_type: str) -> bool:
        ffmpeg = self._find_ffmpeg()
        if not ffmpeg:
            print("[ffmpeg] ffmpeg not found")
            return False

        ext = Path(dst).suffix.lower().lstrip('.')

        AUDIO_PRESETS = {
            'mp3': ['-codec:a', 'libmp3lame', '-q:a', '2'],
            'wav': ['-codec:a', 'pcm_s16le'],
            'aac': ['-codec:a', 'aac', '-b:a', '192k'],
            'ogg': ['-codec:a', 'libvorbis', '-q:a', '4'],
            'flac': ['-codec:a', 'flac'],
            'm4a': ['-codec:a', 'aac', '-b:a', '192k'],
        }

        VIDEO_PRESETS = {
            'mp4': ['-codec:v', 'libx264', '-crf', '23', '-codec:a', 'aac'],
            'webm': ['-codec:v', 'libvpx-vp9', '-crf', '30', '-codec:a', 'libopus'],
            'mkv': ['-codec:v', 'libx264', '-crf', '23', '-codec:a', 'aac'],
            'mov': ['-codec:v', 'libx264', '-crf', '23', '-codec:a', 'aac'],
            'avi': ['-codec:v', 'libxvid', '-qscale:v', '4', '-codec:a', 'libmp3lame'],
        }

        cmd = [ffmpeg, '-y', '-i', src]

        if ext in AUDIO_PRESETS:
            cmd.extend(AUDIO_PRESETS[ext])
        elif ext in VIDEO_PRESETS:
            cmd.extend(VIDEO_PRESETS[ext])
        else:
            cmd.extend(['-codec:v', 'copy', '-codec:a', 'copy'])

        cmd.append(dst)

        try:
            result = subprocess.run(cmd, capture_output=True, timeout=3600, creationflags=_NO_WINDOW)
            if result.returncode != 0:
                print(f"[ffmpeg] error: {result.stderr.decode(errors='replace')[-300:]}")
                return False
            return os.path.exists(dst)
        except Exception as e:
            print(f"[ffmpeg] {e}")
            return False
