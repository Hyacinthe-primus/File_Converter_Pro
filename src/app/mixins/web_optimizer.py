"""Web file optimization (json/html minification)."""

from __future__ import annotations


class WebOptimizerMixin:
    """json/html optimization methods."""

    def optimize_web_file(self, src_path, output_path, file_ext):
        try:
            with open(src_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            if file_ext == ".json":
                import json as _json

                data = _json.loads(content)
                minified = _json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            else:
                import re as _re

                minified = _re.sub(r"<!--.*?-->", "", content, flags=_re.DOTALL)
                minified = _re.sub(r">\s+<", "><", minified)
                minified = _re.sub(r"[ \t]{2,}", " ", minified)
                lines = [line.strip() for line in minified.splitlines()]
                minified = "\n".join(line for line in lines if line)
            orig_bytes = content.encode("utf-8")
            new_bytes = minified.encode("utf-8")
            if len(new_bytes) < len(orig_bytes):
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(minified)
            else:
                import shutil as _sh

                _sh.copy2(src_path, output_path)
            return True
        except Exception as e:
            print(f"Web file optimization error {src_path}: {e}")
            return False
