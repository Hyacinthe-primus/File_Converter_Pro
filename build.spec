# -*- mode: python ; coding: utf-8 -*-
# pyright: reportUndefinedVariable=false

block_cipher = None
import os, shutil, glob

def collect_data_files():
    datas = [
        ('icon.ico', '.'),
        ('icon.png', '.'),
        ('Assets', 'Assets'),
        ('SFX', 'SFX'),
        ('icons', 'icons'),
        ('fonts', 'fonts'),
        ('legal', 'legal'),
        ('styles', 'styles'),
    ]

    filtered_datas = []
    for src, dst in datas:
        if os.path.exists(src):
            filtered_datas.append((src, dst))
        else:
            print(f"File not found (skipped): {src}")

    lang_excludes = {'blank.lang', 'en-revisited.lang'}
    for f in glob.glob('languages/*.lang'):
        if os.path.basename(f) not in lang_excludes:
            filtered_datas.append((f, 'languages'))

    for f in glob.glob('languages/*.json'):
        filtered_datas.append((f, 'languages'))

    try:
        import docx
        docx_dir = os.path.dirname(docx.__file__)
        if os.path.exists(docx_dir):
            filtered_datas.append((docx_dir, 'docx'))
            print("python-docx data files added")
    except ImportError:
        print("python-docx not installed")

    try:
        import docxcompose
        docxcompose_dir = os.path.dirname(docxcompose.__file__)
        templates_dir = os.path.join(docxcompose_dir, 'templates')
        if os.path.exists(templates_dir):
            filtered_datas.append((templates_dir, 'docxcompose/templates'))
    except ImportError:
        print("docxcompose not installed")

    try:
        import pptx
        pptx_templates = os.path.join(os.path.dirname(pptx.__file__), 'templates')
        if os.path.exists(pptx_templates):
            filtered_datas.append((pptx_templates, 'pptx/templates'))
    except ImportError:
        print("python-pptx not installed")

    try:
        import comtypes
        gen_dir = os.path.join(os.path.dirname(comtypes.__file__), 'gen')
        if os.path.exists(gen_dir):
            filtered_datas.append((gen_dir, 'comtypes/gen'))
    except ImportError:
        print("comtypes not installed")

    try:
        from PyInstaller.utils.hooks import collect_all
        pdf2docx_datas, _, _ = collect_all("pdf2docx")
        filtered_datas.extend(pdf2docx_datas)
    except Exception as e:
        print(f"pdf2docx collect_all failed: {e}")

    try:
        from PyInstaller.utils.hooks import collect_data_files as _cdf
        cv2_datas = _cdf("cv2")
        filtered_datas.extend(cv2_datas)
    except Exception as e:
        print(f"cv2 collect failed: {e}")

    return filtered_datas


try:
    from PyInstaller.utils.hooks import collect_all as _ca
    _, _pdf2docx_bins, _pdf2docx_hidden = _ca("pdf2docx")
except Exception:
    _pdf2docx_bins, _pdf2docx_hidden = [], []

try:
    from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files as _cdf
    _cv2_bins = collect_dynamic_libs("cv2")
    _cv2_hidden = ["cv2"]
except Exception:
    _cv2_bins, _cv2_hidden = [], []

SHARED_HIDDEN = [
    'cryptography.hazmat.primitives.kdf.pbkdf2',
    'cryptography.hazmat.primitives.hashes',
    'cryptography.hazmat.backends',

    *_pdf2docx_hidden,
    *_cv2_hidden,

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
    'docxcompose', 'docxcompose.composer', 'docxcompose.core',
    'docxcompose.properties', 'docxcompose.registry',
    'reportlab', 'reportlab.lib', 'reportlab.lib.pagesizes',
    'reportlab.lib.units', 'reportlab.lib.styles',
    'reportlab.lib.colors', 'reportlab.lib.enums',
    'reportlab.platypus', 'reportlab.platypus.tables',
    'reportlab.platypus.flowables', 'reportlab.pdfbase',
    'reportlab.pdfbase.pdfmetrics', 'reportlab.pdfbase.ttfonts',
    'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFont', 'PIL.ImageOps',
    'docx2pdf', 'docx2pdf.util',
    'comtypes', 'comtypes.client', 'comtypes.gen',
    'comtypes.persistence', 'comtypes.automation',
    'pythoncom', 'pywintypes',
    'pyzipper',
    'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets',
    'PySide6.QtNetwork', 'PySide6.QtCore', 'PySide6.QtGui',
    'PySide6.QtWidgets',
    'fitz', 'pypdf',
    'matplotlib', 'matplotlib.pyplot',
    'matplotlib.backends.backend_qtagg',
    'matplotlib.backends.backend_agg',
    'matplotlib.figure', 'matplotlib.patches',
    'cycler', 'kiwisolver', 'dateutil', 'dateutil.parser',
    'dateutil.relativedelta', 'pytz',
    'numpy', 'numpy.core', 'numpy.core.multiarray',
    'numpy.core._multiarray_umath',
    'fontTools', 'fontTools.ttLib', 'fontTools.misc',
    'fontTools.misc.encodingTools', 'fontTools.misc.textTools',
    'openpyxl', 'openpyxl.styles', 'openpyxl.utils',
    'pptx', 'pptx.util', 'pptx.enum.shapes', 'pptx.enum.chart',
    'cv2',
    'lxml', 'lxml.etree', 'lxml._elementpath', 'lxml.html', 'ebooklib',
    'pillow_heif', 'weasyprint',
    'rawpy',
    'config', 'database', 'translations', 'widgets',
    'utils', 'utils.translation_mixin',
    'dialogs', 'dialogs.terms_dialog', 'dialogs.word_to_pdf_dialog',
    'dialogs.pdf_to_word_dialog', 'dialogs.splash_screen', 'dialogs.preview_dialog',
    'dialogs.password_dialog', 'dialogs.split_dialog', 'dialogs.compression_dialog',
    'dialogs.batch_convert_dialog', 'dialogs.batch_rename_dialog',
    'dialogs.settings_dialog', 'dialogs.conversion_options_dialog',
    'dialogs.pdf_protection_dialog', 'dialogs.merge_order_dialog',
    'dashboard', 'history',
    'templates', 'templates.templates', 'templates.template_manager',
    'templates.create_template_dialog', 'templates.template_editor_dialog',
    'app', 'app.logic', 'app.ui',
    'app.mixins', 'app.mixins.optimization', 'app.mixins.image_to_pdf',
    'app.mixins.batch', 'app.mixins.pdf_operations',
    'app.mixins.pdf_to_word', 'app.mixins.word_to_pdf',
    'app.mixins.compression', 'app.mixins.archive_engines', 'app.mixins.file_management',
    'app.mixins.panels', 'app.mixins.project_management',
    'app.mixins.theme_language',
    'converter', 'converter.converters', 'converter.advanced_db',
    'converter.html_inline',
    'converter.mixins', 'converter.mixins.document_converters',
    'converter.mixins.image_converters', 'converter.mixins.media_converters',
    'advanced_conversions', 'donate',
    'achievements', 'achievements.achievements_system',
    'achievements.achievements_ui', 'achievements.achievements_popup',
    'achievements.rank_popup', 'achievements.achievements_manager',
    'special_events_manager', 'system_notifier',
    'context_menu', 'context_menu.window', 'context_menu.formats',
    'tasks', 'tasks.watcher', 'tasks.scheduler',
    'theme_manager',
    'watchdog', 'watchdog.observers', 'watchdog.events',
    'apscheduler', 'apscheduler.schedulers.background',
    'apscheduler.triggers.cron', 'apscheduler.triggers.interval',
    'tomli',
    'daemon',
    'qss_helpers'
]

SHARED_EXCLUDES = [
    'PyQt5', 'PyQt6', 'PySide2', 'tkinter',
    'pytest', 'unittest', 'nose', 'sphinx', 'docutils',
    'torch', 'torchvision', 'torchaudio',
    'scipy', 'skimage', 'sklearn', 'numba', 'llvmlite',
    'IPython', 'jedi', 'parso', 'prompt_toolkit',
    'zmq', 'tornado', 'ipykernel', 'ipython_genutils',
    'pandas', 'babel',
    'PySide6.QtBluetooth', 'PySide6.QtDBus',
    'PySide6.QtLocation', 'PySide6.QtNfc',
    'PySide6.QtPositioning', 'PySide6.QtRemoteObjects',
    'PySide6.QtScxml', 'PySide6.QtSensors',
    'PySide6.QtSerialBus', 'PySide6.QtSerialPort',
    'PySide6.QtSql', 'PySide6.QtTest',
    'PySide6.QtWebChannel', 'PySide6.QtWebEngine',
    'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebSockets',
    'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuickWidgets',
]

UPX_EXCLUDE = [
    'Qt6Multimedia.dll', 'Qt6MultimediaWidgets.dll',
    'Qt6PrintSupport.dll', 'Qt6Qml.dll', 'Qt6Quick.dll', 'Qt6DBus.dll',
    'libopenblas*.dll', 'libblas*.dll',
    '_multiarray_umath*.pyd', '_numpy_core*.pyd', 'multiarray*.pyd',
    'numpy.core*.dll',
    'python3*.dll', 'python*.dll',
    'vcruntime*.dll', 'msvcp*.dll', 'msvcr*.dll',
    'api-ms-win*.dll', 'ucrtbase.dll',
    '_mupdf*.pyd', 'mupdf*.dll', '_fitz*.pyd',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[] + _pdf2docx_bins + _cv2_bins,
    datas=collect_data_files(),
    hiddenimports=SHARED_HIDDEN,
    hookspath=[],
    hooksconfig={'matplotlib': {'backends': ['qtagg', 'agg']}},
    runtime_hooks=[],
    excludes=SHARED_EXCLUDES,
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
    upx_exclude=UPX_EXCLUDE,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon='icon.ico',
    version='version_info.txt',
    manifest='manifest.xml',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=UPX_EXCLUDE,
    name='File Converter Pro',
)

dist_dir = os.path.join(DISTPATH, 'File Converter Pro', '_internal')

for d in glob.glob(os.path.join(dist_dir, '*.dist-info')):
    shutil.rmtree(d)

for py in glob.glob(os.path.join(dist_dir, '**', '*.py'), recursive=True):
    os.remove(py)

for pyc in glob.glob(os.path.join(dist_dir, '**', '*.pyc'), recursive=True):
    os.remove(pyc)

for cache in glob.glob(os.path.join(dist_dir, '**', '__pycache__'), recursive=True):
    shutil.rmtree(cache, ignore_errors=True)

comtypes_cache = os.path.join(DISTPATH, 'File Converter Pro', '_internal', 'comtypes', 'gen')
if os.path.exists(comtypes_cache):
    shutil.rmtree(comtypes_cache)
    os.makedirs(comtypes_cache)

mpl_sample = os.path.join(dist_dir, 'matplotlib', 'mpl-data', 'sample_data')
if os.path.exists(mpl_sample):
    shutil.rmtree(mpl_sample)

mpl_fonts = os.path.join(dist_dir, 'matplotlib', 'mpl-data', 'fonts')
if os.path.exists(mpl_fonts):
    for f in glob.glob(os.path.join(mpl_fonts, '**', '*.ttf'), recursive=True):
        if 'DejaVu' not in os.path.basename(f):
            os.remove(f)
    for f in glob.glob(os.path.join(mpl_fonts, '**', '*.afm'), recursive=True):
        os.remove(f)

old_ffmpeg = os.path.join(dist_dir, 'cv2', 'opencv_videoio_ffmpeg4100_64.dll')
if os.path.exists(old_ffmpeg):
    os.remove(old_ffmpeg)

automation_dir = os.path.join(DISTPATH, 'File Converter Pro', 'automation')
os.makedirs(automation_dir, exist_ok=True)