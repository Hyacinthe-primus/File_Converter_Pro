"""
Achievements Admin Manager
- Internal tool for testing and database maintenance
- Real-time achievement status modification (Lock/Unlock)
- Direct SQLite database manipulation via GUI
- Debugging features for achievement triggers and stats reset

"""

import sys
import sqlite3
from datetime import datetime
import os

_PKG_DIR  = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_PKG_DIR)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QComboBox, QLineEdit, QMessageBox, QCheckBox,
                               QGroupBox, QFormLayout, QSpinBox, QTextEdit,
                               QWidget, QDialogButtonBox, QMenu)
from PySide6.QtCore import Qt, QUrl
from shiboken6 import isValid as shiboken6_isValid
from PySide6.QtGui import QColor, QShortcut, QKeySequence, QAction, QIcon
try:
    from config import ConfigManager
except ImportError as e:
    print(f"[ERROR] Unable to import ConfigManager from config.py: {e}")
    sys.exit(1)

def get_app_dir():
    """
    Returns the project root directory.
    - PyInstaller : directory of the .exe  (NOT _MEIPASS)
    - Development : parent of this package (achievements/)
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return _ROOT_DIR

def get_assets_dir():
    """
    Returns the directory containing bundled assets (SFX, Assets...).
    - PyInstaller : sys._MEIPASS  (where datas are extracted by PyInstaller)
    - Development : project root (_ROOT_DIR)
    """
    from utils import resource_path
    # resource_path("") resolves to _MEIPASS in frozen mode, project root otherwise
    base = resource_path("")
    return base if os.path.isdir(base) else _ROOT_DIR

def _load_dark_mode() -> bool:
    """Reads dark_mode from config, returns False on any error."""
    try:
        config_manager = ConfigManager()
        config = config_manager.load_config()
        return bool(config.get("dark_mode", False))
    except Exception:
        return False

_LIGHT_STYLE = """
QDialog, QWidget {
    background-color: #f8f9fa;
    color: #212529;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}
QGroupBox {
    background-color: #ffffff;
    border: 2px solid #ced4da;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: bold;
    color: #495057;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: #495057;
}
QLineEdit, QSpinBox, QComboBox {
    background-color: #ffffff;
    color: #212529;
    border: 1px solid #ced4da;
    border-radius: 6px;
    padding: 5px;
}
QCheckBox {
    color: #212529;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #adb5bd;
    background-color: #ffffff;
    border-radius: 3px;
}
QCheckBox::indicator:checked {
    background-color: #4dabf7;
    border: 2px solid #4dabf7;
}
QPushButton {
    background-color: #007bff;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: bold;
    min-height: 16px;
}
QPushButton:hover  { background-color: #0069d9; }
QPushButton:pressed { background-color: #0056b3; }
QTextEdit, QTableWidget {
    background-color: #ffffff;
    color: #212529;
    border: 1px solid #ced4da;
    selection-background-color: #a5d8ff;
    selection-color: #212529;
}
QHeaderView::section {
    background-color: #e9ecef;
    color: #212529;
    padding: 5px;
    border: 1px solid #ced4da;
}
QLabel {
    color: #212529;
}
QScrollBar:vertical {
    background: #f1f3f5;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #adb5bd;
    border-radius: 5px;
    min-height: 20px;
}
"""

_DARK_STYLE = """
/* ── Base ── */
QDialog, QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

/* ── GroupBox ── */
QGroupBox {
    font-weight: 700;
    font-size: 13px;
    border: 1px solid #30363d;
    border-radius: 10px;
    margin-top: 14px;
    padding-top: 10px;
    background-color: #161b22;
    color: #8b949e;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    color: #8b949e;
}

/* ── Buttons ── */
QPushButton {
    background-color: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 7px;
    font-weight: 700;
    font-size: 12px;
    padding: 8px 16px;
    min-height: 16px;
}
QPushButton:hover {
    background-color: #30363d;
    border-color: #8b949e;
    color: #e6edf3;
}
QPushButton:pressed {
    background-color: #161b22;
    border-color: #6e7681;
}
QPushButton:disabled {
    background-color: #161b22;
    color: #484f58;
    border-color: #21262d;
}

/* ── Inputs ── */
QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit {
    background-color: #0d1117;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 7px 10px;
    font-size: 13px;
    selection-background-color: #388bfd33;
}
QLineEdit:focus, QSpinBox:focus, QTextEdit:focus { border: 1px solid #388bfd; }
QLineEdit:hover, QSpinBox:hover { border: 1px solid #484f58; }

/* ── ComboBox ── */
QComboBox {
    background-color: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 7px 10px;
    font-size: 13px;
    min-width: 120px;
}
QComboBox:hover { border: 1px solid #484f58; }
QComboBox:focus { border: 1px solid #388bfd; }
QComboBox::drop-down { border: none; width: 28px; }
QComboBox::down-arrow {
    image: none;
    width: 0; height: 0;
    border-left:  5px solid transparent;
    border-right: 5px solid transparent;
    border-top:   6px solid #8b949e;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #161b22;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    selection-background-color: #388bfd22;
    selection-color: #79c0ff;
    outline: none;
}

/* ── Table ── */
QTableWidget {
    background-color: #161b22;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 8px;
    gridline-color: #21262d;
    selection-background-color: #388bfd22;
    selection-color: #e6edf3;
    alternate-background-color: #0d1117;
    outline: none;
}
QTableWidget::item       { padding: 7px 10px; border: none; }
QTableWidget::item:hover { background-color: #1f2937; }
QTableWidget::item:selected {
    background-color: #388bfd22;
    color: #79c0ff;
}
QHeaderView::section {
    background-color: #1e2330;
    color: #8b949e;
    border: none;
    border-right:  1px solid #30363d;
    border-bottom: 1px solid #30363d;
    padding: 8px 10px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.4px;
}

/* ── CheckBox ── */
QCheckBox {
    color: #e6edf3;
    spacing: 8px;
    font-size: 13px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #484f58;
    background-color: #0d1117;
    border-radius: 4px;
}
QCheckBox::indicator:hover   { border-color: #388bfd; }
QCheckBox::indicator:checked {
    background-color: #388bfd;
    border-color: #388bfd;
}

/* ── Scrollbars ── */
QScrollBar:vertical {
    background: #0d1117;
    width: 8px; margin: 0; border: none;
}
QScrollBar::handle:vertical {
    background: #30363d;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #484f58; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #0d1117;
    height: 8px; margin: 0; border: none;
}
QScrollBar::handle:horizontal {
    background: #30363d;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #484f58; }
QScrollBar::add-page:vertical,  QScrollBar::sub-page:vertical,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
}

/* ── Tooltip ── */
QToolTip {
    background-color: #1e2330;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 7px 10px;
    font-size: 12px;
}

/* ── Label ── */
QLabel { color: #e6edf3; background: transparent; }

/* ── MessageBox Buttons ── */
QMessageBox QPushButton {
    padding: 8px 12px;
    min-width: 10px;
    min-height: 14px;
}
"""

def _parse_ach_name(name_json: str, fallback: str = "", language: str = "fr") -> str:
    """Parse achievement name from DB — handles both old dict JSON and new plain string."""
    import json as _json
    try:
        data = _json.loads(name_json)
        if isinstance(data, dict):
            return data.get(language, data.get("fr", fallback))
        return str(data)  # plain string (new format)
    except Exception:
        return name_json if name_json else fallback

class TranslationManager:
    def __init__(self, language="en"):
        self.current_language = language
        self.translations = {
    "fr": {
        # Titles & warnings
        "🔧 Gestionnaire de Succès - Mode Admin": "🔧 Gestionnaire de Succès - Mode Admin",
        "⚠️ ATTENTION : Cet outil est réservé à l'administrateur. Les modifications sont permanentes !": "⚠️ ATTENTION : Cet outil est réservé à l'administrateur. Les modifications sont permanentes !",
        "⚡ Réinitialisation Rapide des Succès":"⚡ Réinitialisation Rapide des Succès",
        "⚡ RÉINITIALISATION RAPIDE DES SUCCÈS":"⚡ RÉINITIALISATION RAPIDE DES SUCCÈS",
        "🔧 Admin Succès":"🔧 Admin Succès",
        
        # Statistics
        "📊 Statistiques": "📊 Statistiques",
        "Total:": "Total :",
        "Débloqué":"Débloqué",
        "débloqué":"débloqué",
        "verrouillé":"verrouillé",
        "Débloqués:": "Débloqués :",
        "Verrouillés:": "Verrouillés :",
        "Secrets:": "Secrets :",
        "Total: 0": "Total : 0",
        "Débloqués: 0": "Débloqués : 0",
        "Verrouillés: 0": "Verrouillés : 0",
        "Secrets: 0": "Secrets : 0",
        
        # Filters
        "🔍 Filtres": "🔍 Filtres",
        "Statut:": "Statut :",
        "Catégorie:": "Catégorie :",
        "Recherche:": "Recherche :",
        "Tous": "Tous",
        "Débloqués": "Débloqués",
        "Verrouillés": "Verrouillés",
        "Secrets": "Secrets",
        "Toutes catégories": "Toutes catégories",
        
        # Table headers
        "ID": "ID",
        "Nom": "Nom",
        "Catégorie": "Catégorie",
        "Tier": "Niveau",
        "Statut": "Statut",
        "Progression": "Progression",
        "Date déblocage": "Date de déblocage",
        "Actions": "Actions",
        
        # Status labels
        "✅ DÉBLOQUÉ": "✅ DÉBLOQUÉ",
        "🔒 VERROUILLÉ": "🔒 VERROUILLÉ",
        "🔒 SECRET": "🔒 SECRET",
        "✅ Succès actuellement débloqués":"✅ Succès actuellement débloqués",
        
        # Quick actions
        "🎯 Actions Rapides":"🎯 Actions Rapides",
        "🔄 Charger les succès débloqués":"🔄 Charger les succès débloqués",
        "🔁 Réinitialiser un succès spécifique":"🔁 Réinitialiser un succès spécifique",
        "🗑️ Réinitialiser TOUS les succès":"🗑️ Réinitialiser TOUS les succès",
        "📊 Réinitialiser les statistiques seulement":"📊 Réinitialiser les statistiques seulement",
        "🔧 Ouvrir le gestionnaire complet":"🔧 Ouvrir le gestionnaire complet",
        "Réinitialiser un succès":"Réinitialiser un succès",

        # Bulk actions
        "🎯 Actions en masse": "🎯 Actions en masse",
        "✅ Débloquer tous les succès": "✅ Débloquer tous les succès",
        "🔒 Verrouiller tous les succès": "🔒 Verrouiller tous les succès",
        "🔄 Réinitialiser toutes les statistiques": "🔄 Réinitialiser toutes les statistiques",
        "📤 Exporter la base de données": "📤 Exporter la base de données",
        
        # Editor
        "✏️ Éditeur de succès": "✏️ Éditeur de succès",
        "Rechercher par nom ou ID...":"Rechercher par nom ou ID...",
        "ID du succès:": "ID du succès :",
        "ID du succès": "ID du succès ",
        "Progression:": "Progression :",
        "Date de déblocage:": "Date de déblocage :",
        "💾 Appliquer les modifications": "💾 Appliquer les modifications",
        "❌ Fermer": "❌ Fermer",
        "🔄 Rafraîchir": "🔄 Rafraîchir",
        "ID du succès à réinitialiser :":"ID du succès à réinitialiser :",
        
        # Dynamic messages
        "{0} succès au total": "{0} succès au total",
        "{0} débloqués": "{0} débloqués",
        "{0} verrouillés": "{0} verrouillés",
        "{0} secrets": "{0} secrets",
        "total_ {0}":"total: {0}",
        "débloqués {0}": "débloqués: {0}",
        "verrouillés {0}": "verrouillés: {0}",
        "secrets {0}": "secrets: {0}",
        "Succès '{achievement_id}' {action} !": "Succès '{achievement_id}' {action} !",
        "Voulez-vous vraiment réinitialiser le succès '{0}' ?": "Voulez-vous vraiment réinitialiser le succès «\xa0{0}\xa0»\xa0?",
        "Succès '{0}' réinitialisé !": "Succès « {0} » réinitialisé !",
        "Succès '{achievement_id}' introuvable":"Succès '{achievement_id}' introuvable",
        "Succès '{achievement_id}' modifié !":"Succès '{achievement_id}' modifié !",
        "Base de données exportée vers :\n{0}":"Base de données exportée vers :\n{0}",
        "✅ {achievements} succès débloqués :\n\n":"✅ {achievements} succès débloqués :\n\n",
        "  Débloqué le : {date_str}\n\n":"  Débloqué le : {date_str}\n\n",
        "Voulez-vous vraiment réinitialiser le succès :\n\n{name}\n({achievement_id}) ?":"Voulez-vous vraiment réinitialiser le succès :\n\n{name}\n({achievement_id}) ?",
        "Succès '{name}' réinitialisé !":"Succès '{name}' réinitialisé !",

        # Critical errors
        "Erreur":"Erreur",
        "Impossible de charger la base de données:\n{0}": "Impossible de charger la base de données :\n{0}",
        "Impossible de modifier le succès:\n{error}":"Impossible de modifier le succès:\n{error}",
        "Impossible de réinitialiser le succès:\n{error}":"Impossible de réinitialiser le succès:\n{error}",
        "ATTENTION : Voulez-vous vraiment SUPPRIMER DÉFINITIVEMENT le succès '{0}' ?\n\nCette action est irréversible !": 
        "ATTENTION : Voulez-vous vraiment SUPPRIMER DÉFINITIVEMENT le succès « {0} » ?\n\nCette action est irréversible !",
        "Succès '{achievement_id}' supprimé !":"Succès '{achievement_id}' supprimé !",
        "Son non trouvé : {sound_path}":"Son non trouvé : {sound_path}",
        "Impossible de débloquer tous les succès:\n{error}":"Impossible de débloquer tous les succès:\n{error}",
        "Impossible de verrouiller tous les succès:\n{error}":"Impossible de verrouiller tous les succès:\n{error}",
        "Impossible de réinitialiser les statistiques:\n{error}":"Impossible de réinitialiser les statistiques:\n{error}",
        "Impossible d'exporter la base de données:\n{error}":"Impossible d'exporter la base de données:\n{error}",
        "Impossible de charger les succès:\n{error}":"Impossible de charger les succès:\n{error}",

        # Information
        "Succès":"Succès",
        "Confirmation":"Confirmation",
        "Information": "Information",
        "DANGER !": "DANGER !",
        "Supprimé":"Supprimé",
        "Fichier manquant":"Fichier manquant",
        "Voulez-vous vraiment débloquer TOUS les succès ?":"Voulez-vous vraiment débloquer TOUS les succès ?",
        "Tous les succès ont été débloqués !":"Tous les succès ont été débloqués !",
        "Voulez-vous vraiment verrouiller TOUS les succès ?\n\nCela verrouillera toute votre progression !": (
        "Voulez-vous vraiment verrouiller TOUS les succès ?\n\n"
        "Cela verrouillera toute votre progression !"),
        "Tous les succès ont été verrouillés !":"Tous les succès ont été verrouillés !",
        "RESET_STATS_CONFIRM_MESSAGE": (
        "ATTENTION : Voulez-vous vraiment réinitialiser TOUTES les statistiques ?\n\n"
        "Cela supprimera :\n"
        "- Toutes les conversions\n"
        "- Tous les temps en mode sombre\n"
        "- Tous les aperçus utilisés\n"
        "- Tous les formats utilisés\n\n"
        "Cette action est irréversible !"),
        "Toutes les statistiques ont été réinitialisées !":"Toutes les statistiques ont été réinitialisées !",
        "Attention":"Attention",
        "Veuillez entrer un ID de succès":"Veuillez entrer un ID de succès",
        "Export réussi":"Export réussi",
        "Aucun succès débloqué.":"Aucun succès débloqué.",
        "RESET_ACH_CONFIRM_MESSAGE":("ATTENTION : Voulez-vous vraiment réinitialiser TOUS les succès ?\n\n"
        "Cela verrouillera tous vos succès et réinitialisera toute votre progression !\n\n"
        "Cette action est irréversible !"),
        "Tous les succès ont été réinitialisés !":"Tous les succès ont été réinitialisés !",
        "RESET_STAT_MESSAGE":("Voulez-vous réinitialiser seulement les statistiques ?\n\n"
        "Cela réinitialisera :\n"
        "- Le nombre de conversions\n"
        "- Les temps en mode sombre\n"
        "- Les aperçus utilisés\n"
        "- Les formats utilisés\n\n"
        "Mais gardera vos succès débloqués."),
        "Statistiques réinitialisées !":"Statistiques réinitialisées !",

        # Tooltips
        "Jouer le son du succès": "Jouer le son du succès",
        "Débloquer/Verrouiller": "Débloquer/Verrouiller",
        "Réinitialiser la progression": "Réinitialiser la progression",
        "Supprimer le succès":"Supprimer le succès",
    },
    "en": {
        # Titles & warnings
        "🔧 Gestionnaire de Succès - Mode Admin": "🔧 Achievements Manager - Admin Mode",
        "⚠️ ATTENTION : Cet outil est réservé à l'administrateur. Les modifications sont permanentes !": "⚠️ WARNING: This tool is for administrators only. Changes are permanent!",
        "⚡ Réinitialisation Rapide des Succès": "⚡ Quick Achievement Reset",
        "⚡ RÉINITIALISATION RAPIDE DES SUCCÈS": "⚡ QUICK ACHIEVEMENT RESET",
        "🔧 Admin Succès":"🔧 Admin Achievements",

        # Statistics
        "📊 Statistiques": "📊 Statistics",
        "Total:": "Total:",
        "Débloqués:": "Unlocked:",
        "Débloqué": "Unlocked",
        "débloqué":"unlocked",
        "verrouillé":"locked",
        "Verrouillés:": "Locked:",
        "Secrets:": "Secrets:",
        "Total: 0": "Total: 0",
        "Débloqués: 0": "Unlocked: 0",
        "Verrouillés: 0": "Locked: 0",
        "Secrets: 0": "Secrets: 0",
        "Verrouiller":"Verrouiller",
        
        # Filters
        "🔍 Filtres": "🔍 Filters",
        "Statut:": "Status:",
        "Catégorie:": "Category:",
        "Recherche:": "Search:",
        "Tous": "All",
        "Débloqués": "Unlocked",
        "Verrouillés": "Locked",
        "Secrets": "Secrets",
        "Toutes catégories": "All categories",
        
        # Table headers
        "ID": "ID",
        "Nom": "Name",
        "Catégorie": "Category",
        "Tier": "Tier",
        "Statut": "Status",
        "Progression": "Progress",
        "Date déblocage": "Unlock Date",
        "Actions": "Actions",
        
        # Status labels
        "✅ DÉBLOQUÉ": "✅ UNLOCKED",
        "🔒 VERROUILLÉ": "🔒 LOCKED",
        "🔒 SECRET": "🔒 SECRET",
        "✅ Succès actuellement débloqués": "✅ Currently unlocked achievements",

        # Quick actions
        "🎯 Actions Rapides": "🎯 Quick Actions",
        "🔄 Charger les succès débloqués": "🔄 Load unlocked achievements",
        "🔁 Réinitialiser un succès spécifique": "🔁 Reset a specific achievement",
        "🗑️ Réinitialiser TOUS les succès": "🗑️ Reset ALL achievements",
        "📊 Réinitialiser les statistiques seulement": "📊 Reset statistics only",
        "🔧 Ouvrir le gestionnaire complet": "🔧 Open full manager",
        "Réinitialiser un succès": "Reset an achievement",
        
        # Bulk actions
        "🎯 Actions en masse": "🎯 Bulk Actions",
        "✅ Débloquer tous les succès": "✅ Unlock All Achievements",
        "🔒 Verrouiller tous les succès": "🔒 Lock All Achievements",
        "🔄 Réinitialiser toutes les statistiques": "🔄 Reset All Stats",
        "📤 Exporter la base de données": "📤 Export Database",
        
        # Editor
        "✏️ Éditeur de succès": "✏️ Achievement Editor",
        "Rechercher par nom ou ID...":"Search by name or ID...",
        "ID du succès:": "Achievement ID:",
        "ID du succès": "Achievement ID ",
        "Progression:": "Progress:",
        "Date de déblocage:": "Unlock Date:",
        "💾 Appliquer les modifications": "💾 Apply Changes",
        "❌ Fermer": "❌ Close",
        "🔄 Rafraîchir": "🔄 Refresh",
        "ID du succès à réinitialiser :": "Achievement ID to reset:",
        
        # Dynamic messages
        "{0} succès au total": "{0} total achievements",
        "{0} débloqués": "{0} unlocked",
        "{0} verrouillés": "{0} locked",
        "{0} secrets": "{0} secrets",
        "total_ {0}":"total: {0}",
        "débloqués {0}": "unlocked: {0}",
        "verrouillés {0}": "locked: {0}",
        "secrets {0}": "secrets: {0}",
        "Succès '{achievement_id}' {action} !": "Achievement '{achievement_id}' {action} !",
        "Voulez-vous vraiment réinitialiser le succès '{0}' ?": "Are you sure you want to reset achievement '{0}'?",
        "Succès '{0}' réinitialisé !": "Achievement '{0}' reset!",
        "ATTENTION : Voulez-vous vraiment SUPPRIMER DÉFINITIVEMENT le succès '{0}' ?\n\nCette action est irréversible !": 
        "WARNING: Are you sure you want to PERMANENTLY DELETE achievement '{0}'?\n\nThis action cannot be undone!",
        "Succès '{achievement_id}' supprimé !":"Success '{achievement_id}' deleted !",
        "Succès '{achievement_id}' introuvable": "Achievement '{achievement_id}' not found",
        "Succès '{achievement_id}' modifié !": "Achievement '{achievement_id}' updated!",
        "Base de données exportée vers :\n{0}": "Database exported to:\n{0}",
        "✅ {achievements} succès débloqués :\n\n": "✅ {achievements} achievements unlocked:\n\n",
        "  Débloqué le : {date_str}\n\n": "  Unlocked on: {date_str}\n\n",
        "Voulez-vous vraiment réinitialiser le succès :\n\n{name}\n({achievement_id}) ?": "Do you really want to reset the achievement:\n\n{name}\n({achievement_id})?",
        "Succès '{name}' réinitialisé !": "Achievement '{name}' reset!",

        # Critical errors
        "Erreur":"Error",
        "Impossible de charger la base de données:\n{0}": "Unable to load the database:\n{0}",
        "Impossible de modifier le succès:\n{error}":"Impossible de modifier le succès:\n{error}",
        "Impossible de réinitialiser le succès:\n{error}":"Unable to rest the achievement:\n{error}",
        "Impossible de supprimer le succès:\n{error}":"Unable to delete the achievement:\n{error}",
        "Son non trouvé : {sound_path}":"Song not found : {sound_path}",
        "Impossible de débloquer tous les succès:\n{error}":"Unable to unlock all achievements:\n{error}",
        "Impossible de verrouiller tous les succès:\n{error}":"Unable to lock all achievements:\n{error}",
        "Impossible de réinitialiser les statistiques:\n{error}":"Unable to reset statistics:\n{error}",
        "Impossible d'exporter la base de données:\n{error}":"Unable to export database:\n{error}",
        "Impossible de charger les succès:\n{error}": "Unable to load achievements:\n{error}",

        # Information
        "Succès":"Success",
        "Confirmation":"Confirmation",
        "Information": "Information",
        "DANGER !": "DANGER !",
        "Supprimé":"Deleted",
        "Fichier manquant":"File missing",
        "Voulez-vous vraiment débloquer TOUS les succès ?": "Do you really want to unlock ALL achievements?",
        "Tous les succès ont été débloqués !": "All achievements have been unlocked!",
        "Voulez-vous vraiment verrouiller TOUS les succès ?\n\nCela verrouillera toute votre progression !": (
        "Are you sure you want to lock ALL achievements?\n\n"
        "This will lock all your progress!"),
        "Tous les succès ont été verrouillés !":"All achievements have been locked !",
        "RESET_STATS_CONFIRM_MESSAGE": (
        "WARNING: Are you sure you want to reset ALL statistics?\n\n"
        "This will delete:\n"
        "- All conversions\n"
        "- All dark mode usage time\n"
        "- All previews used\n"
        "- All formats used\n\n"
        "This action is irreversible!"),
        "Toutes les statistiques ont été réinitialisées !":"All achievements have been reset !",
        "Attention": "Warning",
        "Veuillez entrer un ID de succès": "Please enter an achievement ID",
        "Export réussi": "Export successful",
        "Aucun succès débloqué.":"No achievements unlocked.",
        "RESET_ACH_CONFIRM_MESSAGE": (
        "WARNING: Do you really want to reset ALL achievements?\n\n"
        "This will lock all your achievements and reset all your progress!\n\n"
        "This action is irreversible!"),
        "Tous les succès ont été réinitialisés !": "All achievements have been reset!",
        "RESET_STAT_MESSAGE": (
        "Do you want to reset only the statistics?\n\n"
        "This will reset:\n"
        "- Number of conversions\n"
        "- Dark mode usage time\n"
        "- Previews used\n"
        "- Formats used\n\n"
        "But your unlocked achievements will be kept."),
        "Statistiques réinitialisées !": "Statistics reset!",

        # Tooltips
        "Jouer le son du succès": "Play success sound",
        "Débloquer/Verrouiller": "Unlock/Lock",
        "Réinitialiser la progression": "Reset progress",
        "Supprimer le succès": "Delete achievement",
    }
}

    def translate(self, text, *args, **kwargs):
        """
        Translates text with format support.
        - If a single positional argument is given: replaces {0}
        - If kwargs are given: standard .format(**kwargs) usage
        - If both args and kwargs: combined (uncommon)
        """
        # For unknown language codes (e.g. external .lang), fall back to "en"
        lang = self.current_language if self.current_language in self.translations else "en"
        translated = self.translations.get(lang, {}).get(text, text)
        
        if len(args) == 1 and not kwargs:
            try:
                return translated.format(args[0])
            except (KeyError, IndexError, ValueError):
                return translated
        
        try:
            if kwargs:
                return translated.format(*args, **kwargs)
            elif args:
                return translated.format(*args)
            else:
                return translated
        except (KeyError, IndexError, ValueError):
            return translated

def detect_language():
    """Determines the language: CLI arguments take priority, otherwise reads from config."""
    if "--en" in sys.argv:
        return "en"
    if "--fr" in sys.argv:
        return "fr"
    try:
        config_manager = ConfigManager()
        config = config_manager.load_config()
        return config.get("language", "en")
    except Exception as e:
        print(f"[WARN] Unable to load language: {e}. Defaulting to English.")
        return "en"

class AchievementsManager(QDialog):
    """Achievement management interface"""

    def __init__(self, db_path="achievements.db", parent=None, language=None):
        super().__init__(parent)
        
        if db_path == "achievements.db":
            script_dir = get_app_dir()
            self.db_path = os.path.join(script_dir, "achievements.db")
        else:
            self.db_path = db_path
        
        self.language = language if language is not None else detect_language()
        self.dark_mode = _load_dark_mode()

        self.setStyleSheet(_DARK_STYLE if self.dark_mode else _LIGHT_STYLE)

        self.translator = TranslationManager(self.language)
        self.setWindowTitle(self.translator.translate("🔧 Gestionnaire de Succès - Mode Admin"))
        self.setMinimumSize(1000, 700)
        self.resize(1050, 750)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setup_ui()
        self.load_achievements()

    def _is_alive(self) -> bool:
        """Check that the underlying C++ PySide6 object is still valid before any UI operation."""
        try:
            return shiboken6_isValid(self)
        except Exception:
            return False

    def apply_light_theme(self):
        self.setStyleSheet(_LIGHT_STYLE)

    def apply_dark_theme(self):
        self.setStyleSheet(_DARK_STYLE)

    def setup_ui(self):
        """Configure the interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(self.translator.translate("🔧 Gestionnaire de Succès - Mode Admin").upper())
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #dc3545; padding: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        warning_label = QLabel(self.translator.translate(
            "⚠️ ATTENTION : Cet outil est réservé à l'administrateur. Les modifications sont permanentes !"
        ))
        warning_label.setStyleSheet("color: #ffc107; font-weight: bold; background-color: #343a40; padding: 8px; border-radius: 5px;")
        warning_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(warning_label)
        
        stats_group = QGroupBox(self.translator.translate("📊 Statistiques"))
        stats_layout = QVBoxLayout(stats_group)

        counters_layout = QHBoxLayout()
        self.total_label    = QLabel(self.translator.translate("Total: 0"))
        self.unlocked_label = QLabel(self.translator.translate("Débloqués: 0"))
        self.locked_label   = QLabel(self.translator.translate("Verrouillés: 0"))
        self.secret_label   = QLabel(self.translator.translate("Secrets: 0"))
        self.xp_label       = QLabel("XP : 0")

        for label in [self.total_label, self.unlocked_label, self.locked_label,
                      self.secret_label, self.xp_label]:
            label.setStyleSheet("font-weight: bold; padding: 4px 10px;")
            counters_layout.addWidget(label)

        counters_layout.addStretch()
        stats_layout.addLayout(counters_layout)

        from PySide6.QtWidgets import QProgressBar as _QPB
        self.global_progress = _QPB()
        self.global_progress.setRange(0, 100)
        self.global_progress.setValue(0)
        self.global_progress.setFormat("0 / 0 succès débloqués")
        self.global_progress.setFixedHeight(16)
        self.global_progress.setStyleSheet("""
            QProgressBar {
                background: #21262d; border-radius: 6px; border: none;
                color: #e6edf3; font-size: 10px; text-align: center;
            }
            QProgressBar::chunk { background: #3fb950; border-radius: 6px; }
        """)
        stats_layout.addWidget(self.global_progress)
        layout.addWidget(stats_group)
        
        # Filters
        filters_group = QGroupBox(self.translator.translate("🔍 Filtres"))
        filters_layout = QHBoxLayout(filters_group)
        
        self.status_filter = QComboBox()
        self.status_filter.addItems([self.translator.translate("Tous"), self.translator.translate("Débloqués"), self.translator.translate("Verrouillés"), self.translator.translate("Secrets")])
        self.status_filter.currentTextChanged.connect(self.filter_achievements)
        
        self.category_filter = QComboBox()
        self.category_filter.addItems([self.translator.translate("Toutes catégories")])
        self.category_filter.currentTextChanged.connect(self.filter_achievements)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.translator.translate("Rechercher par nom ou ID..."))
        self.search_input.textChanged.connect(self.filter_achievements)
        
        filters_layout.addWidget(QLabel(self.translator.translate("Statut:")))
        filters_layout.addWidget(self.status_filter)
        filters_layout.addWidget(QLabel(self.translator.translate("Catégorie:")))
        filters_layout.addWidget(self.category_filter)
        filters_layout.addWidget(QLabel(self.translator.translate("Recherche:")))
        filters_layout.addWidget(self.search_input)
        
        layout.addWidget(filters_group)
        
        self.achievements_table = QTableWidget()
        self.achievements_table.setColumnCount(8)
        self.achievements_table.setHorizontalHeaderLabels([
            self.translator.translate(text)
            for text in (
                "ID", "Nom", "Catégorie", "Tier", "Statut",
                "Progression", "Date déblocage", "Actions"
            )
        ])
        self.achievements_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.achievements_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.achievements_table.horizontalHeader().setStretchLastSection(True)
        self.achievements_table.horizontalHeader().setFixedHeight(28)
        self.achievements_table.verticalHeader().setDefaultSectionSize(32)
        self.achievements_table.setSizePolicy(
            self.achievements_table.sizePolicy().horizontalPolicy(),
            __import__('PySide6.QtWidgets', fromlist=['QSizePolicy']).QSizePolicy.Expanding
        )
        
        layout.addWidget(self.achievements_table, stretch=10)
        
        bulk_group = QGroupBox(self.translator.translate("🎯 Actions en masse"))
        bulk_layout = QHBoxLayout(bulk_group)
        
        unlock_all_btn = QPushButton(self.translator.translate("✅ Débloquer tous les succès"))
        unlock_all_btn.clicked.connect(self.unlock_all)
        unlock_all_btn.setStyleSheet("background-color: #28a745; color: white;")
        
        lock_all_btn = QPushButton(self.translator.translate("🔒 Verrouiller tous les succès"))
        lock_all_btn.clicked.connect(self.lock_all)
        lock_all_btn.setStyleSheet("background-color: #dc3545; color: white;")
        
        reset_stats_btn = QPushButton(self.translator.translate("🔄 Réinitialiser toutes les statistiques"))
        reset_stats_btn.clicked.connect(self.reset_all_stats)
        reset_stats_btn.setStyleSheet("background-color: #ffc107; color: black;")
        
        export_btn = QPushButton(self.translator.translate("📤 Exporter la base de données"))
        export_btn.clicked.connect(self.export_database)
        
        bulk_layout.addWidget(unlock_all_btn)
        bulk_layout.addWidget(lock_all_btn)
        bulk_layout.addWidget(reset_stats_btn)
        bulk_layout.addWidget(export_btn)
        
        layout.addWidget(bulk_group)
        
        # Achievement editor
        editor_group = QGroupBox(self.translator.translate("✏️ Éditeur de succès"))
        editor_layout = QFormLayout(editor_group)
        
        self.edit_id_input = QLineEdit()
        self.edit_id_input.setPlaceholderText(self.translator.translate("ID du succès"))
        
        self.edit_progress_spin = QSpinBox()
        self.edit_progress_spin.setRange(0, 1000000)
        
        self.edit_unlocked_check = QCheckBox(self.translator.translate("Débloqué"))
        
        self.edit_date_input = QLineEdit()
        self.edit_date_input.setPlaceholderText("YYYY-MM-DD HH:MM:SS")
        self.edit_date_input.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        edit_btn = QPushButton(self.translator.translate("💾 Appliquer les modifications"))
        edit_btn.clicked.connect(self.apply_edits)
        edit_btn.setStyleSheet("background-color: #007bff; color: white;")
        
        editor_layout.addRow(self.translator.translate("ID du succès:"), self.edit_id_input)
        editor_layout.addRow(self.translator.translate("Progression:"), self.edit_progress_spin)
        editor_layout.addRow(self.edit_unlocked_check)
        editor_layout.addRow(self.translator.translate("Date de déblocage:"), self.edit_date_input)
        editor_layout.addRow(edit_btn)
        
        layout.addWidget(editor_group)
        
        close_btn = QPushButton(self.translator.translate("❌ Fermer"))
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("background-color: #6c757d; color: white;")
        
        refresh_btn = QPushButton(self.translator.translate("🔄 Rafraîchir"))
        refresh_btn.clicked.connect(self.load_achievements)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(refresh_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)

    def load_achievements(self):
        """Load achievements from the database"""
        if not self._is_alive():
            return
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, name, description, icon, category, tier, 
                   requirement_type, requirement_value, requirement_extra,
                   reward_xp, secret, unlocked, unlock_date, progress, max_progress
            FROM achievements
            ORDER BY category, tier, id
            ''')
            
            achievements = cursor.fetchall()
            
            cursor.execute('SELECT key, value FROM stats')
            {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            
            total    = len(achievements)
            unlocked = sum(1 for a in achievements if a[11])
            secret   = sum(1 for a in achievements if a[10])
            total_xp = sum(a[9] for a in achievements if a[11])

            self.total_label.setText(self.translator.translate("total_ {0}", total))
            self.unlocked_label.setText(self.translator.translate("débloqués {0}", unlocked))
            self.locked_label.setText(self.translator.translate("verrouillés {0}", total - unlocked))
            self.secret_label.setText(self.translator.translate("secrets {0}", secret))
            self.xp_label.setText(f"XP : {total_xp:,}".replace(",", " "))

            pct = int((unlocked / total * 100)) if total else 0
            self.global_progress.setRange(0, total)
            self.global_progress.setValue(unlocked)
            self.global_progress.setFormat(f"{unlocked} / {total} succès débloqués  ({pct}%)")
            
            categories = set()
            for ach in achievements:
                categories.add(ach[4])
            
            self.category_filter.clear()
            self.category_filter.addItem(self.translator.translate("Toutes catégories"))
            for category in sorted(categories):
                self.category_filter.addItem(category)
            
            self.all_achievements = achievements
            self.filter_achievements()
        
        except Exception as e:
            msg = self.translator.translate("Impossible de charger la base de données:\n{0}", str(e))
            QMessageBox.critical(self, self.translator.translate("Erreur"), msg)

    def filter_achievements(self):
        """Filter achievements"""
        if not hasattr(self, 'all_achievements'):
            return
        
        status_filter   = self.status_filter.currentText()
        category_filter = self.category_filter.currentText()
        search_text     = self.search_input.text().lower()
        
        filtered = []
        for ach in self.all_achievements:
            if status_filter == self.translator.translate("Débloqués") and not ach[11]:
                continue
            if status_filter == self.translator.translate("Verrouillés") and ach[11]:
                continue
            if status_filter == self.translator.translate("Secrets") and not ach[10]:
                continue
            if category_filter != self.translator.translate("Toutes catégories") and ach[4] != category_filter:
                continue
            if search_text:
                name = _parse_ach_name(ach[1], "", "fr").lower()
                desc = _parse_ach_name(ach[2], "", "fr").lower()
                if (search_text not in ach[0].lower() and
                        search_text not in name and
                        search_text not in desc):
                    continue
            filtered.append(ach)
        
        self.display_achievements(filtered)

    def display_achievements(self, achievements):
        """Display achievements in the table"""
        from PySide6.QtWidgets import QProgressBar

        self.achievements_table.setRowCount(0)

        TIER_COLORS = {
            "starter":      "#a8dadc",
            "bronze":       "#cd7f32",
            "steel":        "#71797e",
            "silver":       "#c0c0c0",
            "platinum_tier":"#c18d30",
            "gold":         "#ffd700",
            "rare":         "#4169e1",
            "epic":         "#9370db",
            "legendary":    "#ff8c00",
            "diamond":      "#b9f2ff",
            "platinum":     "#e5e4e2",
            "advanced":     "#22d3ee",
            "templates":    "#a78bfa",
        }

        emoji_button_style = """
            QPushButton {
                border: none; background: transparent;
                font-size: 15px; padding: 0; margin: 0;
            }
            QPushButton:hover { background: rgba(255,255,255,0.08); border-radius: 4px; }
        """

        for i, ach in enumerate(achievements):
            self.achievements_table.insertRow(i)
            self.achievements_table.setRowHeight(i, 34)

            unlocked = bool(ach[11])
            secret   = bool(ach[10])

            row_bg = QColor("#0d2818" if unlocked else "#1a0a0a") if self.dark_mode else \
                     QColor("#e6f4ea" if unlocked else "#fdf0f0")

            def _item(text, bg=row_bg, align=Qt.AlignVCenter | Qt.AlignLeft):
                it = QTableWidgetItem(text)
                it.setBackground(bg)
                it.setTextAlignment(align)
                return it

            self.achievements_table.setItem(i, 0, _item(ach[0]))

            name = _parse_ach_name(ach[1], ach[0], "fr")
            self.achievements_table.setItem(i, 1, _item(name))

            self.achievements_table.setItem(i, 2, _item(ach[4]))

            tier_item = _item(ach[5])
            tier_color = TIER_COLORS.get(ach[5], "#8b949e")
            tier_item.setForeground(QColor(tier_color))
            self.achievements_table.setItem(i, 3, tier_item)

            if unlocked:
                status_text  = self.translator.translate("✅ DÉBLOQUÉ")
                status_color = QColor("#3fb950")
            elif secret:
                status_text  = self.translator.translate("🔒 SECRET")
                status_color = QColor("#d29922")
            else:
                status_text  = self.translator.translate("🔒 VERROUILLÉ")
                status_color = QColor("#f85149")
            status_item = _item(status_text)
            status_item.setForeground(status_color)
            self.achievements_table.setItem(i, 4, status_item)

            max_p = int(ach[14]) if ach[14] else 1
            cur_p = min(int(ach[13]) if ach[13] is not None else 0, max_p)
            pbar = QProgressBar()
            pbar.setRange(0, max_p)
            pbar.setValue(cur_p)
            pbar.setFormat(f"{cur_p}/{max_p}")
            pbar.setTextVisible(True)
            pbar.setFixedHeight(18)
            fill_color = "#3fb950" if unlocked else (TIER_COLORS.get(ach[5], "#388bfd"))
            pbar.setStyleSheet(f"""
                QProgressBar {{
                    background: {'#21262d' if self.dark_mode else '#e9ecef'};
                    border-radius: 5px; border: none;
                    color: {'#e6edf3' if self.dark_mode else '#212529'};
                    font-size: 10px;
                }}
                QProgressBar::chunk {{
                    background: {fill_color};
                    border-radius: 5px;
                }}
            """)
            pbar_container = QWidget()
            pbar_container.setStyleSheet("background: transparent;")
            pbar_layout = QHBoxLayout(pbar_container)
            pbar_layout.setContentsMargins(4, 7, 4, 7)
            pbar_layout.addWidget(pbar)
            self.achievements_table.setCellWidget(i, 5, pbar_container)

            date_str = ach[12][:10] if ach[12] else "—"
            self.achievements_table.setItem(i, 6, _item(date_str, align=Qt.AlignCenter | Qt.AlignVCenter))

            action_widget = QWidget()
            action_widget.setStyleSheet("background: transparent;")
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 2, 4, 2)
            action_layout.setSpacing(2)

            for emoji, tip, slot in [
                ("🔊", self.translator.translate("Jouer le son du succès"),
                 lambda checked, idx=i: self.play_sound(achievements[idx][0])),
                ("✅" if not unlocked else "🔒",
                 self.translator.translate("Débloquer/Verrouiller") if not unlocked else self.translator.translate("Verrouiller"),
                 lambda checked, idx=i: self.toggle_achievement(achievements[idx][0])),
                ("🔄", self.translator.translate("Réinitialiser la progression"),
                 lambda checked, idx=i: self.reset_achievement(achievements[idx][0])),
                ("🗑️", self.translator.translate("Supprimer le succès"),
                 lambda checked, idx=i: self.delete_achievement(achievements[idx][0])),
            ]:
                btn = QPushButton(emoji)
                btn.setFixedSize(26, 26)
                btn.setToolTip(tip)
                btn.setStyleSheet(emoji_button_style)
                btn.clicked.connect(slot)
                action_layout.addWidget(btn)
            action_layout.addStretch()
            self.achievements_table.setCellWidget(i, 7, action_widget)

        self.achievements_table.resizeColumnsToContents()
        if self.achievements_table.receivers("cellClicked(int,int)") > 0:
            self.achievements_table.cellClicked.disconnect()
        self.achievements_table.cellClicked.connect(
            lambda row, _col: self._autofill_editor(achievements[row]) if row < len(achievements) else None
        )

    def _autofill_editor(self, ach):
        """Pre-fill the editor fields from a clicked achievement row."""
        self.edit_id_input.setText(ach[0])
        self.edit_progress_spin.setValue(int(ach[13]) if ach[13] is not None else 0)
        self.edit_unlocked_check.setChecked(bool(ach[11]))
        if ach[12]:
            self.edit_date_input.setText(ach[12])
        else:
            self.edit_date_input.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def toggle_achievement(self, achievement_id):
        """Toggle achievement state silently and refresh the table."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT unlocked FROM achievements WHERE id = ?', (achievement_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return
            new_state   = not row[0]
            unlock_date = datetime.now().isoformat() if new_state else None
            cursor.execute(
                'UPDATE achievements SET unlocked = ?, unlock_date = ? WHERE id = ?',
                (new_state, unlock_date, achievement_id)
            )
            conn.commit()
            conn.close()
            if self._is_alive():
                self.load_achievements()
        except Exception as e:
            if self._is_alive():
                QMessageBox.critical(self, self.translator.translate("Erreur"),
                                     self.translator.translate("Impossible de modifier le succès:\n{error}", error=str(e)))

    def reset_achievement(self, achievement_id):
        """Reset an achievement"""
        reply = QMessageBox.question(
            self,
            self.translator.translate("Confirmation"),
            self.translator.translate("Voulez-vous vraiment réinitialiser le succès '{0}' ?", achievement_id),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                UPDATE achievements 
                SET unlocked = FALSE, unlock_date = NULL, progress = 0
                WHERE id = ?
                ''', (achievement_id,))
                
                conn.commit()
                conn.close()
                
                if self._is_alive():
                    QMessageBox.information(self, self.translator.translate("Information"),
                                            self.translator.translate("Succès '{0}' réinitialisé !", achievement_id))
                if self._is_alive():
                    self.load_achievements()
            
            except Exception as e:
                if self._is_alive():
                    QMessageBox.critical(self, self.translator.translate("Erreur"),
                                         self.translator.translate("Impossible de réinitialiser le succès:\n{error}", error=str(e)))

    def delete_achievement(self, achievement_id):
        """Delete an achievement (danger!)"""
        reply = QMessageBox.warning(
            self,
            self.translator.translate("DANGER !"),
            self.translator.translate(
                "ATTENTION : Voulez-vous vraiment SUPPRIMER DÉFINITIVEMENT le succès '{0}' ?\n\nCette action est irréversible !",
                achievement_id
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM achievements WHERE id = ?', (achievement_id,))
                conn.commit()
                conn.close()
                
                if self._is_alive():
                    QMessageBox.warning(self, self.translator.translate("Supprimé"),
                                        self.translator.translate("Succès '{achievement_id}' supprimé !", achievement_id=achievement_id))
                if self._is_alive():
                    self.load_achievements()
            
            except Exception as e:
                if self._is_alive():
                    QMessageBox.critical(self, self.translator.translate("Erreur"),
                                         self.translator.translate("Impossible de supprimer le succès:\n{error}", error=str(e)))

    def play_sound(self, achievement_id):
        """Play the sound associated with an achievement, thread-safe"""
        try:
            sound_file = "trophy_progression.wav"
            sound_groups = {
                "trophy_progression": {
                    "sfx": "trophy_progression.wav",
                    "achievements": [
                        "apprentice", "steel_warrior", "format_expert", "platinum_master",
                        "tpl_architecte", "tpl_maitre_presets", "tpl_le_rituel",
                    ]
                },
                "ultimate_tier": {
                    "sfx": "ultimate_epic.wav",
                    "achievements": ["file_industrial", "file_god", "eternal_loyalty", "absolute_perfection"]
                },
                "security_sounds":    {"sfx": "security_lock.wav",   "achievements": ["data_guardian", "impenetrable_fortress", "master_key"]},
                "compression_sounds": {"sfx": "compress_zip.wav",    "achievements": ["titanic_compressor", "royal_archivist"]},
                "pdf_tools_sounds":   {"sfx": "pdf_action.wav",      "achievements": ["division_blade", "eternal_librarian"]},
                "legendary_sounds":   {
                    "sfx": "legendary_unlock.wav",
                    "achievements": [
                        "dragon_breath", "division_blade", "absolute_perfection",
                        "adv_la_machine", "adv_collectionneur",
                    ]
                },
                "conversion_sounds":  {
                    "sfx": "conversion_done.wav",
                    "achievements": [
                        "visual_alchemist", "processing_king",
                        "adv_data_architect", "adv_csv_sorcier", "adv_web_harvester",
                        "adv_bibliotheque", "adv_icon_forge", "adv_pixel_perfect",
                        "adv_extracteur_pro", "adv_studio_underground",
                        "tpl_automatiste", "tpl_archiviste", "tpl_importateur",
                    ]
                },
                "technical_sounds":   {
                    "sfx": "tech_achievement.wav",
                    "achievements": [
                        "all_seeing_eye", "visionary", "universal_traveler",
                        "adv_office_slayer", "adv_format_nomade",
                        "adv_codec_master", "adv_all_rounder",
                        "tpl_polyvalent", "tpl_perfectionniste",
                        "tpl_reference_absolue", "tpl_collectionneur_workflows",
                    ]
                },
                "fun_sounds":         {"sfx": "fun_unlock.wav",      "achievements": ["night_owl", "flash_gordon", "adv_heic_hunter",]},
                "unique_sounds": {
                    "first_adventure": "first_step.wav",
                    "night_knight":    "dark_mode.wav",
                    "cosmic_orb":      "cosmic_unlock.wav"
                }
            }
            
            if achievement_id in sound_groups["unique_sounds"]:
                sound_file = sound_groups["unique_sounds"][achievement_id]
            else:
                for group in sound_groups.values():
                    if "achievements" in group and achievement_id in group["achievements"]:
                        sound_file = group["sfx"]
                        break
            
            get_app_dir()
            sound_path = os.path.join(get_assets_dir(), "SFX", sound_file)
            
            if not os.path.exists(sound_path):
                QMessageBox.warning(self, self.translator.translate("Fichier manquant"),
                                    self.translator.translate("Son non trouvé : {sound_path}", sound_path=sound_path))
                print(f"[DEBUG] Missing sound: {sound_path}")
                return
            
            if hasattr(self, '_global_media_player') and self._global_media_player:
                try:
                    if self._global_media_player.playbackState() != self._global_media_player.StoppedState:
                        self._global_media_player.stop()
                    self._global_media_player.deleteLater()
                except Exception as e:
                    print(f"[WARNING] Error cleaning up old player: {e}")
                finally:
                    self._global_media_player = None
                    self._global_audio_output = None
            
            from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
            self._global_audio_output = QAudioOutput()
            self._global_media_player = QMediaPlayer()
            
            self._global_audio_output.setVolume(0.7)
            self._global_media_player.setAudioOutput(self._global_audio_output)
            self._global_media_player.setSource(QUrl.fromLocalFile(sound_path))
            
            def on_error(error):
                print(f"[ERROR MediaPlayer] {error} — {self._global_media_player.errorString()}")
                self._global_media_player.deleteLater()
                self._global_audio_output.deleteLater()
                self._global_media_player = None
                self._global_audio_output  = None
            
            def on_playback_state_changed(state):
                state_names = {0: "Stopped", 1: "Playing", 2: "Paused"}
                print(f"[DEBUG] Playback state: {state_names.get(state, state)}")
            
            def on_media_status_changed(status):
                status_names = {
                    0: "NoMedia", 1: "Loading", 2: "Loaded", 3: "Stalled",
                    4: "Buffering", 5: "Buffered", 6: "EndOfMedia", 7: "InvalidMedia"
                }
                print(f"[DEBUG] Media status: {status_names.get(status, status)}")
            
            self._global_media_player.errorOccurred.connect(on_error)
            self._global_media_player.playbackStateChanged.connect(on_playback_state_changed)
            self._global_media_player.mediaStatusChanged.connect(on_media_status_changed)
            self._global_media_player.play()
            print(f"[DEBUG] ✅ Playback started: {sound_path}")
            
            def cleanup_on_end():
                try:
                    if self._global_media_player:
                        self._global_media_player.deleteLater()
                    if self._global_audio_output:
                        self._global_audio_output.deleteLater()
                except Exception:
                    pass
                finally:
                    self._global_media_player = None
                    self._global_audio_output  = None
                    print("[DEBUG] 🔊 Player cleaned up after playback ended")
            
            self._global_media_player.mediaStatusChanged.connect(
                lambda status: cleanup_on_end() if status == QMediaPlayer.MediaStatus.EndOfMedia else None
            )
        
        except Exception as e:
            import traceback
            print(f"[CRITICAL] Sound playback error: {e}")
            traceback.print_exc()

    def unlock_all(self):
        """Unlock all achievements"""
        reply = QMessageBox.question(
            self, self.translator.translate("Confirmation"),
            self.translator.translate("Voulez-vous vraiment débloquer TOUS les succès ?"),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                UPDATE achievements 
                SET unlocked = TRUE, unlock_date = ?, progress = max_progress
                ''', (datetime.now().isoformat(),))
                conn.commit()
                conn.close()
                
                if self._is_alive():
                    QMessageBox.information(self, self.translator.translate("Succès"),
                                            self.translator.translate("Tous les succès ont été débloqués !"))
                if self._is_alive():
                    self.load_achievements()
            
            except Exception as e:
                if self._is_alive():
                    QMessageBox.critical(self, self.translator.translate("Erreur"),
                                         self.translator.translate("Impossible de débloquer tous les succès:\n{error}", error=str(e)))

    def lock_all(self):
        """Lock all achievements"""
        reply = QMessageBox.question(
            self, self.translator.translate("Confirmation"),
            self.translator.translate(
                "Voulez-vous vraiment verrouiller TOUS les succès ?\n\nCela verrouillera toute votre progression !"
            ),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                UPDATE achievements 
                SET unlocked = FALSE, unlock_date = NULL, progress = 0
                ''')
                conn.commit()
                conn.close()
                
                if self._is_alive():
                    QMessageBox.information(self, self.translator.translate("Succès"),
                                            self.translator.translate("Tous les succès ont été verrouillés !"))
                if self._is_alive():
                    self.load_achievements()
            
            except Exception as e:
                if self._is_alive():
                    QMessageBox.critical(self, self.translator.translate("Erreur"),
                                         self.translator.translate("Impossible de verrouiller tous les succès:\n{error}", error=str(e)))

    def reset_all_stats(self):
        """Reset all statistics"""
        reply = QMessageBox.warning(
            self,
            self.translator.translate("DANGER !"),
            self.translator.translate("RESET_STATS_CONFIRM_MESSAGE"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM stats')
                cursor.execute('DELETE FROM daily_stats')
                cursor.execute('UPDATE used_formats SET used = FALSE')
                
                default_stats = [
                    ('total_conversions', 0),
                    ('images_to_pdf', 0),
                    ('word_pdf_conversions', 0),
                    ('pdf_protected', 0),
                    ('archives_created', 0),
                    ('previews_used', 0),
                    ('dark_mode_minutes', 0),
                    ('ocr_pages', 0),
                    ('compressed_gb', 0.0),
                    ('consecutive_success', 0),
                    ('conversions_today', 0),
                    ('previews_today', 0),
                    ('dark_mode_today', 0),
                    ('start_time', datetime.now().isoformat()),
                    ('unique_days', 1),
                    ('last_launch_date', datetime.now().date().isoformat()),
                    ('night_conversions', 0),
                    ('adv_total_conversions', 0),
                    ('adv_doc_conversions', 0),
                    ('adv_image_conversions', 0),
                    ('adv_audio_conversions', 0),
                    ('adv_video_conversions', 0),
                    ('adv_csv_json_conversions', 0),
                    ('adv_html_to_pdf', 0),
                    ('adv_epub_to_pdf', 0),
                    ('adv_image_to_ico', 0),
                    ('adv_heic_conversions', 0),
                    ('adv_video_to_audio', 0),
                    ('adv_xlsx_to_pdf', 0),
                    ('adv_pptx_to_pdf', 0),
                    ('adv_image_types_used', 0),
                    ('adv_video_types_used', 0),
                    ('adv_txt_to_pdf', 0), ('adv_rtf_to_pdf', 0),
                    ('adv_txt_to_docx', 0), ('adv_rtf_to_docx', 0),
                    ('adv_csv_to_json', 0), ('adv_json_to_csv', 0),
                    ('adv_xlsx_to_json', 0), ('adv_xlsx_to_csv', 0),
                    ('adv_html_to_pdf_flag', 0), ('adv_pdf_to_html', 0),
                    ('adv_epub_to_pdf_flag', 0),
                    ('adv_jpeg_to_png', 0), ('adv_png_to_jpg', 0),
                    ('adv_jpg_to_png', 0), ('adv_webp_to_png', 0),
                    ('adv_bmp_to_png', 0), ('adv_tiff_to_png', 0),
                    ('adv_heic_to_png', 0), ('adv_gif_to_png', 0),
                    ('adv_image_to_ico_flag', 0),
                    ('adv_avi_to_mp4', 0), ('adv_webm_to_mp4', 0),
                    ('adv_mkv_to_mp4', 0), ('adv_mp4_to_mp3', 0),
                    ('adv_avi_to_mp3', 0), ('adv_webm_to_mp3', 0),
                    ('adv_wav_to_mp3', 0), ('adv_mp3_to_wav', 0),
                    ('adv_aac_to_mp3', 0), ('adv_mp3_to_aac', 0),
                    ('adv_flac_to_mp3', 0), ('adv_ogg_to_mp3', 0),
                    # Templates stats
                    ('tpl_created_total', 0),
                    ('tpl_applied_total', 0),
                    ('tpl_edited_total', 0),
                    ('tpl_exported', 0),
                    ('tpl_imported', 0),
                    ('tpl_single_max_applied', 0),
                    ('tpl_types_session', 0),
                ]
                
                for key, value in default_stats:
                    cursor.execute('INSERT INTO stats (key, value, last_updated) VALUES (?, ?, ?)',
                                   (key, value, datetime.now().isoformat()))

                conn.commit()
                conn.close()

                if self._is_alive():
                    QMessageBox.information(self, self.translator.translate("Succès"),
                                            self.translator.translate("Toutes les statistiques ont été réinitialisées !"))
                if self._is_alive():
                    self.load_achievements()
            
            except Exception as e:
                if self._is_alive():
                    QMessageBox.critical(self, self.translator.translate("Erreur"),
                                         self.translator.translate("Impossible de réinitialiser les statistiques:\n{error}", error=str(e)))

    def apply_edits(self):
        """Apply manual edits"""
        achievement_id = self.edit_id_input.text().strip()
        if not achievement_id:
            QMessageBox.warning(self, self.translator.translate("Attention"),
                                self.translator.translate("Veuillez entrer un ID de succès"))
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM achievements WHERE id = ?', (achievement_id,))
            if cursor.fetchone()[0] == 0:
                QMessageBox.warning(self, self.translator.translate("Erreur"),
                                    self.translator.translate("Succès '{achievement_id}' introuvable", achievement_id=achievement_id))
                return
            
            progress    = self.edit_progress_spin.value()
            unlocked    = self.edit_unlocked_check.isChecked()
            unlock_date = self.edit_date_input.text().strip() if unlocked else None
            
            cursor.execute('''
            UPDATE achievements 
            SET progress = ?, unlocked = ?, unlock_date = ?
            WHERE id = ?
            ''', (progress, unlocked, unlock_date, achievement_id))
            
            conn.commit()
            conn.close()
            
            if self._is_alive():
                QMessageBox.information(self, self.translator.translate("Succès"),
                                        self.translator.translate("Succès '{achievement_id}' modifié !", achievement_id=achievement_id))
            if self._is_alive():
                self.load_achievements()
                self.edit_id_input.clear()
                self.edit_progress_spin.setValue(0)
                self.edit_unlocked_check.setChecked(False)
                self.edit_date_input.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        except Exception as e:
            if self._is_alive():
                QMessageBox.critical(self, self.translator.translate("Erreur"),
                                     self.translator.translate("Impossible de modifier le succès:\n{error}", error=str(e)))

    def export_database(self):
        """Export the database"""
        try:
            export_filename = f"achievements_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            import shutil
            shutil.copy2(self.db_path, export_filename)
            QMessageBox.information(self, self.translator.translate("Export réussi"),
                                    self.translator.translate("Base de données exportée vers :\n{0}", export_filename))
        
        except Exception as e:
            QMessageBox.critical(self, self.translator.translate("Erreur"),
                                 self.translator.translate("Impossible d'exporter la base de données:\n{error}", error=str(e)))

class QuickAchievementsReset(QDialog):
    """Quick reset interface"""

    def __init__(self, db_path="achievements.db", parent=None, language=None):
        super().__init__(parent)
        
        if db_path == "achievements.db":
            script_dir = get_app_dir()
            self.db_path = os.path.join(script_dir, "achievements.db")
        else:
            self.db_path = db_path
        
        self.language   = language if language is not None else detect_language()
        self.translator = TranslationManager(self.language)
        self.dark_mode  = _load_dark_mode()
        self.setStyleSheet(_DARK_STYLE if self.dark_mode else _LIGHT_STYLE)

        self.setWindowTitle(self.translator.translate("⚡ Réinitialisation Rapide des Succès"))
        self.setMinimumSize(500, 400)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setup_ui()

    def _is_alive(self) -> bool:
        """Check that the underlying C++ PySide6 object is still valid before any UI operation."""
        try:
            return shiboken6_isValid(self)
        except Exception:
            return False

    def apply_light_theme(self):
        self.setStyleSheet(_LIGHT_STYLE)

    def apply_dark_theme(self):
        self.setStyleSheet(_DARK_STYLE)

    def setup_ui(self):
        """Configure the interface"""
        layout = QVBoxLayout(self)
        
        title_label = QLabel(self.translator.translate("⚡ RÉINITIALISATION RAPIDE DES SUCCÈS"))
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #dc3545; padding: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        unlocked_group = QGroupBox(self.translator.translate("✅ Succès actuellement débloqués"))
        unlocked_layout = QVBoxLayout(unlocked_group)
        
        self.unlocked_list = QTextEdit()
        self.unlocked_list.setReadOnly(True)
        unlocked_layout.addWidget(self.unlocked_list)
        
        layout.addWidget(unlocked_group)
        
        actions_group = QGroupBox(self.translator.translate("🎯 Actions Rapides"))
        actions_layout = QVBoxLayout(actions_group)
        
        load_btn = QPushButton(self.translator.translate("🔄 Charger les succès débloqués"))
        load_btn.clicked.connect(self.load_unlocked_achievements)
        
        reset_specific_btn = QPushButton(self.translator.translate("🔁 Réinitialiser un succès spécifique"))
        reset_specific_btn.clicked.connect(self.reset_specific_achievement)
        
        reset_all_btn = QPushButton(self.translator.translate("🗑️ Réinitialiser TOUS les succès"))
        reset_all_btn.setStyleSheet("background-color: #dc3545; color: white;")
        reset_all_btn.clicked.connect(self.reset_all_achievements)
        
        reset_stats_btn = QPushButton(self.translator.translate("📊 Réinitialiser les statistiques seulement"))
        reset_stats_btn.setStyleSheet("background-color: #ffc107; color: black;")
        reset_stats_btn.clicked.connect(self.reset_statistics_only)

        reset_adv_btn = QPushButton(self.translator.translate("⚡ Réinitialiser les succès Conversions Avancées"))
        reset_adv_btn.setStyleSheet("background-color: #22d3ee; color: #0a0a0a; font-weight: bold;")
        reset_adv_btn.clicked.connect(self.reset_advanced_achievements)

        actions_layout.addWidget(load_btn)
        actions_layout.addWidget(reset_specific_btn)
        actions_layout.addWidget(reset_all_btn)
        actions_layout.addWidget(reset_stats_btn)
        actions_layout.addWidget(reset_adv_btn)
        
        layout.addWidget(actions_group)
        
        close_btn = QPushButton(self.translator.translate("❌ Fermer"))
        close_btn.clicked.connect(self.close)
        
        manager_btn = QPushButton(self.translator.translate("🔧 Ouvrir le gestionnaire complet"))
        manager_btn.clicked.connect(self.open_full_manager)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(manager_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)

    def load_unlocked_achievements(self):
        """Load and display unlocked achievements with rich info."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, category, tier, progress, max_progress, unlock_date
                FROM achievements
                WHERE unlocked = TRUE
                ORDER BY unlock_date DESC
            ''')
            achievements = cursor.fetchall()

            cursor.execute('SELECT COUNT(*) FROM achievements')
            total_all = cursor.fetchone()[0]
            conn.close()

            if not achievements:
                self.unlocked_list.setText(self.translator.translate("Aucun succès débloqué."))
                return

            count = len(achievements)
            pct   = int(count / total_all * 100) if total_all else 0
            lines = [f"✅  {count} / {total_all} succès débloqués ({pct}%)\n"]

            for ach_id, name_json, category, tier, progress, max_progress, unlock_date in achievements:
                name     = _parse_ach_name(name_json, ach_id, "fr")
                date_str = unlock_date[:10] if unlock_date else "?"
                prog_str = f"{int(progress)}/{int(max_progress)}" if max_progress else "—"
                lines.append(f"  {name}")
                lines.append(f"    ├ ID : {ach_id}")
                lines.append(f"    ├ Catégorie : {category}  •  Tier : {tier}")
                lines.append(f"    ├ Progression : {prog_str}")
                lines.append(f"    └ Débloqué le : {date_str}\n")

            self.unlocked_list.setText("\n".join(lines))

        except Exception as e:
            QMessageBox.critical(self, self.translator.translate("Erreur"),
                                 self.translator.translate("Impossible de charger les succès:\n{error}", error=str(e)))

    def reset_specific_achievement(self):
        """Reset a specific achievement"""
        dialog = QDialog(self)
        dialog.setWindowTitle(self.translator.translate("Réinitialiser un succès"))
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel(self.translator.translate("ID du succès à réinitialiser :")))
        
        id_input = QLineEdit()
        id_input.setPlaceholderText("Ex: first_adventure, apprentice, etc.")
        layout.addWidget(id_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.Accepted:
            achievement_id = id_input.text().strip()
            if achievement_id:
                self.do_reset_achievement(achievement_id)

    def do_reset_achievement(self, achievement_id):
        """Reset an achievement"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT name FROM achievements WHERE id = ?', (achievement_id,))
            result = cursor.fetchone()
            
            if not result:
                QMessageBox.warning(self, self.translator.translate("Erreur"),
                                    self.translator.translate("Succès '{achievement_id}' introuvable", achievement_id=achievement_id))
                return
            
            name  = _parse_ach_name(result[0], achievement_id, "fr")
            rmsg  = self.translator.translate(
                "Voulez-vous vraiment réinitialiser le succès :\n\n{name}\n({achievement_id}) ?",
                name=name, achievement_id=achievement_id
            )
            
            reply = QMessageBox.question(
                self, self.translator.translate("Confirmation"),
                rmsg,
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                cursor.execute('''
                UPDATE achievements 
                SET unlocked = FALSE, unlock_date = NULL, progress = 0
                WHERE id = ?
                ''', (achievement_id,))
                conn.commit()
                conn.close()
                
                if self._is_alive():
                    QMessageBox.information(self, self.translator.translate("Succès"),
                                            self.translator.translate("Succès '{name}' réinitialisé !", name=name))
                if self._is_alive():
                    self.load_unlocked_achievements()
        
        except Exception as e:
            if self._is_alive():
                QMessageBox.critical(self, self.translator.translate("Erreur"),
                                     self.translator.translate("Impossible de réinitialiser le succès:\n{error}", error=str(e)))

    def reset_all_achievements(self):
        """Reset all achievements"""
        reply = QMessageBox.warning(
            self, self.translator.translate("DANGER !"),
            self.translator.translate("RESET_ACH_CONFIRM_MESSAGE"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                UPDATE achievements 
                SET unlocked = FALSE, unlock_date = NULL, progress = 0
                ''')
                conn.commit()
                conn.close()
                
                if self._is_alive():
                    QMessageBox.information(self, self.translator.translate("Succès"),
                                            self.translator.translate("Tous les succès ont été réinitialisés !"))
                if self._is_alive():
                    self.load_unlocked_achievements()
            
            except Exception as e:
                if self._is_alive():
                    QMessageBox.critical(self, self.translator.translate("Erreur"),
                                         self.translator.translate("Impossible de réinitialiser le succès:\n{error}", error=str(e)))

    def reset_statistics_only(self):
        """Reset statistics only"""
        reply = QMessageBox.question(
            self, self.translator.translate("Confirmation"),
            self.translator.translate("RESET_STAT_MESSAGE"),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM stats')
                cursor.execute('DELETE FROM daily_stats')
                cursor.execute('UPDATE used_formats SET used = FALSE')
                
                default_stats = [
                    ('total_conversions', 0),
                    ('images_to_pdf', 0),
                    ('word_pdf_conversions', 0),
                    ('pdf_protected', 0),
                    ('archives_created', 0),
                    ('previews_used', 0),
                    ('dark_mode_minutes', 0),
                    ('ocr_pages', 0),
                    ('compressed_gb', 0.0),
                    ('consecutive_success', 0),
                    ('conversions_today', 0),
                    ('previews_today', 0),
                    ('dark_mode_today', 0),
                    ('start_time', datetime.now().isoformat()),
                    ('unique_days', 1),
                    ('last_launch_date', datetime.now().date().isoformat()),
                    ('night_conversions', 0),
                    ('adv_total_conversions', 0),
                    ('adv_doc_conversions', 0),
                    ('adv_image_conversions', 0),
                    ('adv_audio_conversions', 0),
                    ('adv_video_conversions', 0),
                    ('adv_csv_json_conversions', 0),
                    ('adv_html_to_pdf', 0),
                    ('adv_epub_to_pdf', 0),
                    ('adv_image_to_ico', 0),
                    ('adv_heic_conversions', 0),
                    ('adv_video_to_audio', 0),
                    ('adv_xlsx_to_pdf', 0),
                    ('adv_pptx_to_pdf', 0),
                    ('adv_image_types_used', 0),
                    ('adv_video_types_used', 0),
                    ('adv_txt_to_pdf', 0), ('adv_rtf_to_pdf', 0),
                    ('adv_txt_to_docx', 0), ('adv_rtf_to_docx', 0),
                    ('adv_csv_to_json', 0), ('adv_json_to_csv', 0),
                    ('adv_xlsx_to_json', 0), ('adv_xlsx_to_csv', 0),
                    ('adv_html_to_pdf_flag', 0), ('adv_pdf_to_html', 0),
                    ('adv_epub_to_pdf_flag', 0),
                    ('adv_jpeg_to_png', 0), ('adv_png_to_jpg', 0),
                    ('adv_jpg_to_png', 0), ('adv_webp_to_png', 0),
                    ('adv_bmp_to_png', 0), ('adv_tiff_to_png', 0),
                    ('adv_heic_to_png', 0), ('adv_gif_to_png', 0),
                    ('adv_image_to_ico_flag', 0),
                    ('adv_avi_to_mp4', 0), ('adv_webm_to_mp4', 0),
                    ('adv_mkv_to_mp4', 0), ('adv_mp4_to_mp3', 0),
                    ('adv_avi_to_mp3', 0), ('adv_webm_to_mp3', 0),
                    ('adv_wav_to_mp3', 0), ('adv_mp3_to_wav', 0),
                    ('adv_aac_to_mp3', 0), ('adv_mp3_to_aac', 0),
                    ('adv_flac_to_mp3', 0), ('adv_ogg_to_mp3', 0),
                    # Templates stats
                    ('tpl_created_total', 0),
                    ('tpl_applied_total', 0),
                    ('tpl_edited_total', 0),
                    ('tpl_exported', 0),
                    ('tpl_imported', 0),
                    ('tpl_single_max_applied', 0),
                    ('tpl_types_session', 0),
                ]
                
                for key, value in default_stats:
                    cursor.execute('INSERT INTO stats (key, value, last_updated) VALUES (?, ?, ?)',
                                   (key, value, datetime.now().isoformat()))
                
                conn.commit()
                conn.close()
                
                if self._is_alive():
                    QMessageBox.information(self, self.translator.translate("Succès"),
                                            self.translator.translate("Statistiques réinitialisées !"))
            
            except Exception as e:
                if self._is_alive():
                    QMessageBox.critical(self, self.translator.translate("Erreur"),
                                         self.translator.translate("Impossible de réinitialiser les statistiques:\n{error}", error=str(e)))

    def reset_advanced_achievements(self):
        """Reset all advanced conversion achievements AND their stats — for real."""
        reply = QMessageBox.warning(
            self,
            self.translator.translate("Confirmation"),
            self.translator.translate(
                "Ceci va réinitialiser les 15 succès ⚡ Conversions Avancées\n"
                "ET toutes leurs statistiques associées.\n\n"
                "Cette action est irréversible. Continuer ?"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        adv_ids = [
            "adv_data_architect", "adv_csv_sorcier", "adv_office_slayer",
            "adv_web_harvester", "adv_bibliotheque", "adv_icon_forge",
            "adv_format_nomade", "adv_heic_hunter", "adv_pixel_perfect",
            "adv_extracteur_pro", "adv_codec_master", "adv_studio_underground",
            "adv_all_rounder", "adv_la_machine", "adv_collectionneur",
        ]

        adv_stat_keys = [
            'adv_total_conversions', 'adv_doc_conversions',
            'adv_image_conversions', 'adv_audio_conversions',
            'adv_video_conversions', 'adv_csv_json_conversions',
            'adv_html_to_pdf', 'adv_epub_to_pdf', 'adv_image_to_ico',
            'adv_heic_conversions', 'adv_video_to_audio',
            'adv_xlsx_to_pdf', 'adv_pptx_to_pdf',
            'adv_image_types_used', 'adv_video_types_used',
            'adv_txt_to_pdf', 'adv_rtf_to_pdf',
            'adv_txt_to_docx', 'adv_rtf_to_docx',
            'adv_csv_to_json', 'adv_json_to_csv',
            'adv_xlsx_to_json', 'adv_xlsx_to_csv',
            'adv_html_to_pdf_flag', 'adv_pdf_to_html',
            'adv_epub_to_pdf_flag',
            'adv_jpeg_to_png', 'adv_png_to_jpg',
            'adv_jpg_to_png', 'adv_webp_to_png',
            'adv_bmp_to_png', 'adv_tiff_to_png',
            'adv_heic_to_png', 'adv_gif_to_png',
            'adv_image_to_ico_flag',
            'adv_avi_to_mp4', 'adv_webm_to_mp4',
            'adv_mkv_to_mp4', 'adv_mov_to_mp4',   # was missing — entry 34 in _ADV_TYPE_MAP
            'adv_mp4_to_mp3', 'adv_avi_to_mp3', 'adv_webm_to_mp3',
            'adv_mkv_to_mp3',                       # was missing — entry 36 in _ADV_TYPE_MAP
            'adv_wav_to_mp3', 'adv_mp3_to_wav',
            'adv_aac_to_mp3', 'adv_mp3_to_aac',
            'adv_flac_to_mp3', 'adv_ogg_to_mp3',
        ]

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for ach_id in adv_ids:
                cursor.execute(
                    'UPDATE achievements SET unlocked = FALSE, unlock_date = NULL, progress = 0 WHERE id = ?',
                    (ach_id,)
                )

            for key in adv_stat_keys:
                cursor.execute(
                    'INSERT OR REPLACE INTO stats (key, value, last_updated) VALUES (?, 0, ?)',
                    (key, datetime.now().isoformat())
                )

            conn.commit()
            conn.close()

            if self._is_alive():
                QMessageBox.information(
                    self,
                    self.translator.translate("Succès"),
                    self.translator.translate(
                        "✅ 15 succès Conversions Avancées réinitialisés\n"
                        "et toutes leurs statistiques remises à zéro."
                    )
                )
            if self._is_alive():
                self.load_unlocked_achievements()

        except Exception as e:
            if self._is_alive():
                QMessageBox.critical(
                    self,
                    self.translator.translate("Erreur"),
                    self.translator.translate(
                        "Impossible de réinitialiser:\n{error}", error=str(e)
                    )
                )

    def open_full_manager(self):
        """Open the full manager"""
        self.full_manager = AchievementsManager(self.db_path, self)
        self.full_manager.show()

def reset_specific_achievement_cli(achievement_id):
    """Reset a specific achievement (CLI)"""
    try:
        script_dir = get_app_dir()
        db_path    = os.path.join(script_dir, "achievements.db")
        conn       = sqlite3.connect(db_path)
        cursor     = conn.cursor()
        cursor.execute('''
        UPDATE achievements 
        SET unlocked = FALSE, unlock_date = NULL, progress = 0
        WHERE id = ?
        ''', (achievement_id,))
        conn.commit()
        conn.close()
        print(f"✅ Achievement '{achievement_id}' reset!")
    except Exception as e:
        print(f"❌ Error: {e}")

def unlock_specific_achievement_cli(achievement_id):
    """Unlock a specific achievement (CLI)"""
    try:
        script_dir = get_app_dir()
        db_path    = os.path.join(script_dir, "achievements.db")
        conn       = sqlite3.connect(db_path)
        cursor     = conn.cursor()
        cursor.execute('SELECT max_progress FROM achievements WHERE id = ?', (achievement_id,))
        max_progress = cursor.fetchone()[0]
        cursor.execute('''
        UPDATE achievements 
        SET unlocked = TRUE, unlock_date = ?, progress = ?
        WHERE id = ?
        ''', (datetime.now().isoformat(), max_progress, achievement_id))
        conn.commit()
        conn.close()
        print(f"✅ Achievement '{achievement_id}' unlocked!")
    except Exception as e:
        print(f"❌ Error: {e}")

def reset_all_achievements_cli():
    """Reset all achievements (CLI)"""
    try:
        script_dir = get_app_dir()
        db_path    = os.path.join(script_dir, "achievements.db")
        conn       = sqlite3.connect(db_path)
        cursor     = conn.cursor()
        cursor.execute('''
        UPDATE achievements 
        SET unlocked = FALSE, unlock_date = NULL, progress = 0
        ''')
        conn.commit()
        conn.close()
        print("✅ All achievements have been reset!")
    except Exception as e:
        print(f"❌ Error: {e}")

def show_achievements_status_cli():
    """Display achievement status (CLI)"""
    try:
        script_dir = get_app_dir()
        db_path    = os.path.join(script_dir, "achievements.db")
        conn       = sqlite3.connect(db_path)
        cursor     = conn.cursor()
        cursor.execute('SELECT id, name, unlocked, progress, max_progress FROM achievements')
        achievements  = cursor.fetchall()
        conn.close()
        unlocked_count = sum(1 for a in achievements if a[2])
        print("📊 Achievement status:")
        print(f"   Total:    {len(achievements)}")
        print(f"   Unlocked: {unlocked_count}")
        print(f"   Locked:   {len(achievements) - unlocked_count}")
        print()
        for ach_id, name_json, unlocked, progress, max_progress in achievements:
            name   = _parse_ach_name(name_json, ach_id, "fr")
            status = "✅" if unlocked else "🔒"
            print(f"{status} {name} ({ach_id})")
            print(f"   Progress: {progress}/{max_progress}")
            print()
    except Exception as e:
        print(f"❌ Error: {e}")

def add_achievements_admin_to_app(main_app):
    """Add an admin menu for achievements in the main application"""
    admin_action = QAction("🔧 Admin Succès", main_app)
    admin_action.triggered.connect(lambda: open_achievements_admin(main_app))
    
    if hasattr(main_app, 'toolbar'):
        main_app.toolbar.addAction(admin_action)
    
    main_app.admin_menu = QMenu("&Admin", main_app)
    main_app.admin_menu.addAction(admin_action)
    main_app.menuBar().addMenu(main_app.admin_menu)
    main_app.admin_menu.setVisible(False)
    
    admin_shortcut = QShortcut(QKeySequence("Ctrl+Shift+A"), main_app)
    admin_shortcut.activated.connect(lambda: main_app.admin_menu.setVisible(True))

def open_achievements_admin(parent, base_path=None):
    """Open the achievements admin interface"""
    script_dir = get_app_dir()
    db_path    = os.path.join(script_dir, "achievements.db")
    
    manager = QuickAchievementsReset(db_path, parent)
    
    if parent is not None:
        parent._achievements_manager_ref = manager
    
    icon_path = "manager_icon.ico"
    if base_path:
        icon_path = os.path.join(base_path, "manager_icon.ico")
    
    try:
        manager.setWindowIcon(QIcon(icon_path))
    except Exception as e:
        print(f"Error applying icon: {e} (Path tried: {icon_path})")
    
    manager.exec()

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    cli_commands = {"status", "reset", "unlock", "reset-all"}

    if len(sys.argv) > 1 and sys.argv[1] in cli_commands:
        command = sys.argv[1]
        if command == "status":
            show_achievements_status_cli()
        elif command == "reset" and len(sys.argv) > 2:
            reset_specific_achievement_cli(sys.argv[2])
        elif command == "unlock" and len(sys.argv) > 2:
            unlock_specific_achievement_cli(sys.argv[2])
        elif command == "reset-all":
            reset_all_achievements_cli()
        else:
            print("Usage:")
            print("  python achievements_manager.py status")
            print("  python achievements_manager.py reset <achievement_id>")
            print("  python achievements_manager.py unlock <achievement_id>")
            print("  python achievements_manager.py reset-all")
    else:
        app        = QApplication(sys.argv)
        manager    = QuickAchievementsReset()
        script_dir = get_app_dir()
        icon_path  = os.path.join(script_dir, "manager_icon.ico")
        if os.path.exists(icon_path):
            manager.setWindowIcon(QIcon(icon_path))
        else:
            icon_path_png = os.path.join(script_dir, "manager_icon.png")
            if os.path.exists(icon_path_png):
                manager.setWindowIcon(QIcon(icon_path_png))
            else:
                print(f"Icon not found. Searched at: {icon_path}")
        manager.show()
        sys.exit(app.exec())