# -*- mode: python ; coding: utf-8 -*-
# pyright: reportUndefinedVariable=false

block_cipher = None
import os

def collect_data_files():
    """Collects all necessary files for PyInstaller"""
    datas = [
        ('icon.ico', '.'),
        ('icon.png', '.'),

        ('Assets', 'Assets'),
        ('SFX', 'SFX'),
        ('icons', 'icons'),
        ('fonts', 'fonts'),
        ('legal', 'legal'),
    ]

    filtered_datas = []
    for src, dst in datas:
        if os.path.exists(src):
            filtered_datas.append((src, dst))
        else:
            print(f"File not found (skipped): {src}")

    try:
        import docx
        docx_dir = os.path.dirname(docx.__file__)
        if os.path.exists(docx_dir):
            filtered_datas.append((docx_dir, 'docx'))
            print("python-docx data files added")
    except ImportError:
        print("python-docx not installed")

    try:
        import pptx
        pptx_templates = os.path.join(os.path.dirname(pptx.__file__), 'templates')
        if os.path.exists(pptx_templates):
            filtered_datas.append((pptx_templates, 'pptx/templates'))
            print("python-pptx templates added")
    except ImportError:
        print("python-pptx not installed")

    try:
        import comtypes
        gen_dir = os.path.join(os.path.dirname(comtypes.__file__), 'gen')
        if os.path.exists(gen_dir):
            filtered_datas.append((gen_dir, 'comtypes/gen'))
            print("comtypes gen cache added")
    except ImportError:
        print("comtypes not installed")

    try:
        from PyInstaller.utils.hooks import collect_all
        pdf2docx_datas, pdf2docx_bins, pdf2docx_hidden = collect_all("pdf2docx")
        filtered_datas.extend(pdf2docx_datas)
        print("pdf2docx data files added")
    except Exception as e:
        print(f"pdf2docx collect_all failed: {e}")

    try:
        from PyInstaller.utils.hooks import collect_all
        np_datas, _, _ = collect_all("numpy")
        filtered_datas.extend(np_datas)
        print("numpy data files added")
    except Exception as e:
        print(f"numpy collect_all failed: {e}")

    try:
        from PyInstaller.utils.hooks import collect_data_files as _cdf
        cv2_datas = _cdf("cv2")
        filtered_datas.extend(cv2_datas)
        print("cv2 data files added")
    except Exception as e:
        print(f"cv2 collect failed: {e}")

    try:
        from PyInstaller.utils.hooks import collect_all
        ft_datas, _, _ = collect_all("fontTools")
        filtered_datas.extend(ft_datas)
        print("fontTools data files added")
    except Exception as e:
        print(f"fontTools collect_all failed: {e}")

    return filtered_datas


try:
    from PyInstaller.utils.hooks import collect_all as _ca
    _, _pdf2docx_bins, _pdf2docx_hidden = _ca("pdf2docx")
except Exception:
    _pdf2docx_bins, _pdf2docx_hidden = [], []

try:
    from PyInstaller.utils.hooks import collect_all as _ca
    _, _np_bins, _np_hidden = _ca("numpy")
except Exception:
    _, _np_bins, _np_hidden = [], [], []

try:
    from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files as _cdf
    _cv2_bins = collect_dynamic_libs("cv2")
    _cv2_datas = _cdf("cv2")
    _cv2_hidden = ["cv2"]
except Exception:
    _, _cv2_bins, _cv2_hidden = [], [], []

try:
    from PyInstaller.utils.hooks import collect_all as _ca
    _, _ft_bins, _ft_hidden = _ca("fontTools")
except Exception:
    _, _ft_bins, _ft_hidden = [], [], []

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[] + _pdf2docx_bins + _cv2_bins + _ft_bins + _np_bins,
    datas=collect_data_files(),
    hiddenimports=[
        'cryptography.hazmat.primitives.kdf.pbkdf2',
        'cryptography.hazmat.primitives.hashes',
        'cryptography.hazmat.backends',

        *_pdf2docx_hidden,
        *_cv2_hidden,
        *_ft_hidden,
        *_np_hidden,
        'pdf2docx', 'pdf2docx.main', 'pdf2docx.converter',
        'pdf2docx.common', 'pdf2docx.common.share', 'pdf2docx.common.algorithm',
        'pdf2docx.common.constants', 'pdf2docx.common.Collection',
        'pdf2docx.common.docx', 'pdf2docx.common.Element', 'pdf2docx.common.Block',
        'pdf2docx.text', 'pdf2docx.text.TextSpan', 'pdf2docx.text.TextBlock',
        'pdf2docx.text.Lines', 'pdf2docx.text.Line', 'pdf2docx.text.Char',
        'pdf2docx.text.Spans',
        'pdf2docx.image', 'pdf2docx.image.ImagesExtractor', 'pdf2docx.image.ImageBlock',
        'pdf2docx.image.ImageSpan', 'pdf2docx.image.Image',
        'pdf2docx.table', 'pdf2docx.table.Row', 'pdf2docx.table.TableStructure',
        'pdf2docx.table.Rows', 'pdf2docx.table.TablesConstructor',
        'pdf2docx.table.Cells', 'pdf2docx.table.Cell', 'pdf2docx.table.TableBlock',
        'pdf2docx.table.Border',
        'pdf2docx.shape', 'pdf2docx.shape.Paths', 'pdf2docx.shape.Shapes',
        'pdf2docx.shape.Path', 'pdf2docx.shape.Shape',
        'pdf2docx.font', 'pdf2docx.font.Fonts',
        'pdf2docx.page', 'pdf2docx.page.RawPageFitz', 'pdf2docx.page.RawPage',
        'pdf2docx.page.Page', 'pdf2docx.page.RawPageFactory',
        'pdf2docx.page.BasePage', 'pdf2docx.page.Pages',
        'pdf2docx.layout', 'pdf2docx.layout.Blocks', 'pdf2docx.layout.Section',
        'pdf2docx.layout.Sections', 'pdf2docx.layout.Layout',
        'pdf2docx.layout.Column',
        'PyPDF2', 'PyPDF2.generic', 'PyPDF2._reader', 'PyPDF2._writer',
        'PyPDF2._merger', 'PyPDF2._page', 'PyPDF2.filters', 'PyPDF2.utils',
        'docx', 'docx.document', 'docx.opc', 'docx.opc.constants',
        'docx.opc.part', 'docx.opc.pkgreader', 'docx.opc.api',
        'docx.shared', 'docx.enum', 'docx.enum.style',
        'docx.enum.section', 'docx.enum.text', 'docx.enum.dml',
        'docx.oxml', 'docx.oxml.ns', 'docx.oxml.shared',
        'docx.oxml.document', 'docx.oxml.text', 'docx.oxml.table',
        'docx.parts', 'docx.parts.document', 'docx.parts.image',
        'docx.styles', 'docx.styles.style', 'docx.styles.latent',
        'docx.table', 'docx.text', 'docx.text.paragraph',
        'docx.text.run', 'docx.text.parfmt', 'docx.image',
        'docx.image.png', 'docx.image.jpeg',
        'reportlab', 'reportlab.lib', 'reportlab.lib.pagesizes',
        'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFont', 'PIL.ImageOps',
        'docx2pdf', 'docx2pdf.util',
        'comtypes', 'comtypes.client', 'comtypes.gen',
        'comtypes.persistence', 'comtypes.automation',
        'pythoncom', 'pywintypes',

        'pyzipper',

        'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets',
        'PySide6.QtNetwork', 'PySide6.QtCore', 'PySide6.QtGui',
        'PySide6.QtWidgets',

        'fitz', 'pymupdf', 'pypdf',

        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.figure',
        'matplotlib.patches',
        'cycler', 'kiwisolver', 'dateutil', 'dateutil.parser',
        'dateutil.relativedelta', 'pytz', 'six', 'pyparsing',

        'numpy', 'numpy.core', 'numpy.core.multiarray',
        'numpy.core._multiarray_umath', 'numpy.core._multiarray_tests',
        'numpy.core.numeric', 'numpy.core.fromnumeric',
        'numpy.core.arrayprint', 'numpy.core.defchararray',
        'numpy.core.records', 'numpy.core.memmap',
        'numpy.core.function_base', 'numpy.core.machar',
        'numpy.core.getlimits', 'numpy.core.shape_base',
        'numpy.core.einsumfunc', 'numpy.core._dtype',
        'numpy.core._type_aliases', 'numpy.core._ufunc_config',
        'numpy.lib', 'numpy.lib.stride_tricks', 'numpy.lib.mixins',
        'numpy.lib.index_tricks', 'numpy.lib.nanfunctions',

        'openpyxl', 'openpyxl.styles', 'openpyxl.utils',
        'pptx', 'pptx.util', 'pptx.enum.shapes', 'pptx.enum.chart',
        'reportlab.lib', 'reportlab.lib.pagesizes',
        'reportlab.lib.units', 'reportlab.lib.styles',
        'reportlab.lib.colors', 'reportlab.lib.enums',
        'reportlab.platypus', 'reportlab.platypus.tables',
        'reportlab.platypus.flowables', 'reportlab.pdfbase',
        'reportlab.pdfbase.pdfmetrics', 'reportlab.pdfbase.ttfonts',
        'fontTools', 'fontTools.ttLib', 'fontTools.ttLib.ttFont',
        'fontTools.ttLib.tables', 'fontTools.ttLib.tables._n_a_m_e',
        'fontTools.ttLib.tables.otTables', 'fontTools.ttLib.tables.DefaultTable',
        'fontTools.pens', 'fontTools.pens.basePen', 'fontTools.pens.pointPen',
        'fontTools.misc', 'fontTools.misc.encodingTools', 'fontTools.misc.textTools',
        'fontTools.misc.roundTools', 'fontTools.misc.fixedTools',
        'fontTools.misc.arrayTools', 'fontTools.misc.psCharStrings',
        'fontTools.cffLib', 'fontTools.varLib', 'fontTools.feaLib',
        'fontTools.designspaceLib', 'fontTools.colorLib',

        'cv2',

        'lxml', 'lxml.etree', 'lxml._elementpath', 'lxml.html', 'ebooklib',
        'pillow_heif',
        'weasyprint',

        'config', 'database', 'translations', 'widgets',
        'dialogs', 'dialogs.dialogs', 'dialogs.terms_dialog', 'dialogs.word_to_pdf_dialog',
        'dashboard', 'history',
        'templates', 'templates.templates', 'templates.template_manager',
        'app', 'app.logic', 'app.ui',
        'converter',
        'converter.converters',
        'converter.advanced_db',
        'advanced_conversions',
        'donate',

        'achievements',
        'achievements.achievements_system',
        'achievements.achievements_ui',
        'achievements.achievements_popup',
        'achievements.rank_popup',
        'achievements.achievements_manager',
        'special_events_manager', 'system_notifier',
        'context_menu', 'context_menu.window',
    ],
    hookspath=[],
    hooksconfig={
        'matplotlib': {'backends': 'qt5agg'},
    },
    runtime_hooks=[],
    excludes=[
        'PyQt5', 'PyQt6', 'PySide2', 'tkinter',
        'pytest', 'unittest', 'nose', 'sphinx', 'docutils',
        'torch', 'torchvision', 'torchaudio',
        'scipy',
        'skimage', 'sklearn', 'numba', 'llvmlite',
        'IPython', 'jedi', 'parso', 'prompt_toolkit',
        'zmq', 'tornado', 'ipykernel', 'ipython_genutils',
        'pandas',
        'PySide6.QtBluetooth', 'PySide6.QtDBus',
        'PySide6.QtLocation', 'PySide6.QtNfc',
        'PySide6.QtPositioning', 'PySide6.QtRemoteObjects',
        'PySide6.QtScxml', 'PySide6.QtSensors',
        'PySide6.QtSerialBus', 'PySide6.QtSerialPort',
        'PySide6.QtSql', 'PySide6.QtTest',
        'PySide6.QtWebChannel', 'PySide6.QtWebEngine',
        'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebSockets',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    target_arch='x86_64',
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='File Converter Pro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[
        'Qt6Multimedia.dll', 'Qt6MultimediaWidgets.dll',
        'Qt6Qml.dll', 'Qt6Quick.dll', 'Qt6DBus.dll',

        'libopenblas*.dll', 'libblas*.dll',
        '_multiarray_umath*.pyd', '_numpy_core*.pyd', 'multiarray*.pyd',
        'numpy.core*.dll',

        'python3*.dll', 'python*.dll',
        'vcruntime*.dll', 'msvcp*.dll', 'msvcr*.dll',
        'api-ms-win*.dll', 'ucrtbase.dll',

        '_mupdf*.pyd', 'mupdf*.dll', '_fitz*.pyd',

    ],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon='icon.ico',
    version='version_info.txt',
    manifest='manifest.xml'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[
        'Qt6Multimedia.dll', 'Qt6MultimediaWidgets.dll',
        'Qt6PrintSupport.dll',
        'Qt6Qml.dll', 'Qt6Quick.dll', 'Qt6DBus.dll',
        'libopenblas*.dll', 'libblas*.dll',
        '_multiarray_umath*.pyd', '_numpy_core*.pyd', 'multiarray*.pyd',
        'numpy.core*.dll',
        'python3*.dll', 'python*.dll',
        'vcruntime*.dll', 'msvcp*.dll', 'msvcr*.dll',
        'api-ms-win*.dll', 'ucrtbase.dll',

        '_mupdf*.pyd', 'mupdf*.dll', '_fitz*.pyd',
    ],
    name='File Converter Pro',
)

import shutil, glob, os
dist_dir = os.path.join(DISTPATH, 'File Converter Pro', '_internal')
for d in glob.glob(os.path.join(dist_dir, '*.dist-info')):
    shutil.rmtree(d)
py_files = glob.glob(os.path.join(dist_dir, '**', '*.py'), recursive=True)
for py in py_files:
    os.remove(py)
old_ffmpeg = os.path.join(dist_dir, 'cv2', 'opencv_videoio_ffmpeg4100_64.dll')
if os.path.exists(old_ffmpeg):
    os.remove(old_ffmpeg)