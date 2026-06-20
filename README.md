<div align="center">
<img src="icon.png" alt="File Converter Pro" width="110"/>
<h1>File Converter Pro</h1>

<p><em>A free, offline, all-in-one file converter for Windows built to feel premium.</em></p>

[![Version](https://img.shields.io/badge/version-1.0.6-4dabf7?style=flat-square)](#)
[![Platform](https://img.shields.io/badge/Windows%2010%2F11-0078D4?style=flat-square&logo=windows)](#)
[![PySide6](https://img.shields.io/badge/PySide6-41CD52?style=flat-square&logo=qt&logoColor=white)](#)
[![License](https://img.shields.io/badge/license-GPLv3%20%2F%20Commercial-blue?style=flat-square)](#license)
[![Status](https://img.shields.io/badge/status-active-brightgreen?style=flat-square)](#)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.13-3776AB?style=flat-square&logo=python&logoColor=white)](#)
[![Downloads](https://img.shields.io/github/downloads/Hyacinthe-primus/File_Converter_Pro/total.svg)](https://github.com/Hyacinthe-primus/File_Converter_Pro/releases)
[![Last Commit](https://img.shields.io/github/last-commit/Hyacinthe-primus/File_Converter_Pro)](https://github.com/Hyacinthe-primus/File_Converter_Pro)

<br/>

> ![Demo - main window, drag & drop, conversion flow](previews/preview.gif)

<br/>

**[Download](#-download)** · **[Wiki](https://github.com/Hyacinthe-primus/File_Converter_Pro/wiki)** · **[Contributing](CONTRIBUTING.md)** · **[Support](#-support-the-project)**

</div>

---

## What is File Converter Pro?

File Converter Pro is a **free, fully offline Windows desktop application** that converts documents, images, audio, and video, all from one polished tool, without a browser or uploading your files anywhere.

Built with Python and PySide6. Animated startup, system-aware dark/light theme, statistics dashboard, gamified achievements, multi-language support. Lightweight: ~250 MB as an exe, ~125 MB from source.

Core philosophy: **ship nothing until it runs perfectly on a clean machine, with zero preinstalled dependencies.**

---

## Highlights

- **All-in-one**: documents, images, audio, video, batch supported
- **100% offline & private**: no telemetry, no uploads, no internet required
- **Statistics & achievements**: animated dashboard and SQLite-backed gamification
- **Automation**: watch folders and scheduled tasks, runs as a background daemon
- **Windows context menu**: right-click any supported file → Convert with FCP
- **Community i18n**: drop a `.lang` JSON file to add a language, no code needed

> Full feature list and detailed guides in the **[Wiki](https://github.com/Hyacinthe-primus/File_Converter_Pro/wiki)**.

---

## Download

| | Link |
|---|---|
| **Installer** *(recommended)* | [Latest Release](../../releases/latest) → `FileConverterPro_Setup_v1.0.6.exe` |
| **Portable** | [Latest Release](../../releases/latest) → `File_Converter_Pro_v1.0.6.zip` |
| **Official Website** | [file-converter-pro](https://file-converter-pro.org/) |
| **Itch** | [hyacinthe-primus.itch.io/file-converter-pro](https://hyacinthe-primus.itch.io/file-converter-pro) |

Windows 10 / 11 (64-bit). No Python, no dependencies. Just run the installer.

> System requirements, antivirus notes, and PowerShell one-liners are in the **[Wiki](https://github.com/Hyacinthe-primus/File_Converter_Pro/wiki)**.

---

## Quick Start (Developers)

```bash
git clone https://github.com/Hyacinthe-primus/File_Converter_Pro.git
cd File_Converter_Pro
pip install -r requirements.txt
pip install -r requirements-dev.txt             # Dev/Build dependencies
python main.py
```

> Full developer docs in the **[For Developers](https://github.com/Hyacinthe-primus/File_Converter_Pro/wiki/For-Developers)** wiki page.

---

## 💙 Support the Project

File Converter Pro is and will remain **completely free**. If it saves you time, a voluntary donation is always appreciated and helps fund continued development.

<div align="center">

[![Support me on Ko-fi](https://img.shields.io/badge/Support-Ko--fi-FF5E5B?style=for-the-badge&logo=ko-fi&logoColor=white)](https://ko-fi.com/hyacinthe_primus/goal?g=0)
[![Donate via PayPal](https://img.shields.io/badge/Donate-PayPal-003087?style=for-the-badge&logo=paypal&logoColor=white)](https://www.paypal.me/HyacintheATHO)

</div>

The donation dialog is also accessible anytime from **Left Tab → Support the project** inside the app itself.

---

## Contributing & Contributors

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for translations, bug reports, code fixes, and feature proposals.

[![FCP Contributors](https://contrib.rocks/image?repo=Hyacinthe-primus/File_Converter_Pro)](https://github.com/Hyacinthe-primus/File_Converter_Pro/graphs/contributors)

---

## License

Dual licensed: **GPLv3** for open-source use · **Commercial License** for proprietary products.
See [`LICENSE`](LICENSE/LICENSE.txt) and [COMMERCIAL LICENSE](COMMERCIALLICENSE.md).

© 2026 Prime Enterprises (Hyacinthe). All rights reserved.

---

<div align="center">
<sub>Built by Hyacinthe <em>because file conversion should actually feel good.</em></sub>
</div>