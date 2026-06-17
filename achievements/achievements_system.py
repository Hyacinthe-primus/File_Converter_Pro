"""
Achievements System
- Central logic for unlocking, tracking, and persisting achievements
- SQLite database integration for permanent storage
- Signal-based architecture for real-time notifications
- Support for secret achievements and progression statistics

"""

import json
import os
import sqlite3
from datetime import datetime, timedelta
from PySide6.QtCore import QObject, Signal, QTimer
import sys
import traceback

_PKG_DIR  = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_PKG_DIR)

if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from translations import TranslationManager

class AchievementSystem(QObject):
    """Achievement management system"""
    achievement_unlocked = Signal(dict)
    rank_unlocked = Signal(dict)

    def __init__(self, config_manager=None):
        super().__init__()
        self.config_manager = config_manager
        self.current_language = "fr"
        self.translation_manager = TranslationManager()
        self.achievements_data = None
        self.stats = {}
        
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.db_path = os.path.join(app_dir, "achievements.db")
        if not os.path.exists(self.db_path):
            print("[INFO] Creating achievements database...")
        
        self.load_achievements_data()
        self.init_database()
        self.initialize_achievements()
        self.load_stats()
        self.load_achievements_from_db()
        self.ranks = [
            ("Rookie", "Débutant"),
            ("Initiate", "Initié"),
            ("Adept", "Adepte"),
            ("Veteran", "Vétéran"),
            ("Elite", "Élite"),
            ("Champion", "Champion"),
            ("Master", "Maître"),
            ("Grand Master", "Grand Maître"),
            ("Legendary", "Légendaire"),
            ("Mythic", "Mythique")
        ]
        self.rank_colors = [
            "#B0BEC5",  # Rookie
            "#4FC3F7",  # Initiate
            "#4CAF50",  # Adept
            "#FF9800",  # Veteran
            "#E91E63",  # Elite
            "#9C27B0",  # Champion 
            "#FF5722",  # Master
            "#795548",  # Grand Master
            "#FFD600",  # Legendary
            "#FF1744"   # Mythic
        ]
        self.current_rank_index = 0
        self.last_rank_index = -1
        self.update_all_progress()

        _startup_rank_index, _, _ = self.get_current_rank()
        self.last_rank_index = _startup_rank_index

        unlocked_count = self.get_unlocked_count()
        print(f"[DEBUG] {unlocked_count} achievements unlocked at startup")
        print(f"[DEBUG] Rank at startup: {_startup_rank_index} ({self.ranks[_startup_rank_index][0]})")
        
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.save_stats)
        self.save_timer.start(30000)

    def get_resource_path(self, relative_path):
        """Get resource path compatible dev + PyInstaller.

        Frozen mode: PyInstaller extracts data into sys._MEIPASS
                     (e.g. File Converter Pro_internal/)
        Dev mode:    assets are at the project root (_ROOT_DIR)
        """
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            path = os.path.join(meipass, relative_path)
            if os.path.exists(path):
                return path

        path = os.path.join(_ROOT_DIR, relative_path)
        if os.path.exists(path):
            return path

        path = os.path.join(os.getcwd(), relative_path)
        if os.path.exists(path):
            return path

        if meipass:
            return os.path.join(meipass, relative_path)
        return os.path.join(_ROOT_DIR, relative_path)

    def load_achievements_data(self):
        try:
            self.achievements_data = {
                "sound_groups": {
                    "trophy_progression": {
                        "sfx": "trophy_progression.wav",
                        "achievements": [
                            "apprentice",
                            "steel_warrior",
                            "format_expert",
                            "platinum_master",
                            "tpl_architecte",
                            "tpl_maitre_presets",
                            "tpl_le_rituel",
                        ]
                    },
                    "ultimate_tier": {
                        "sfx": "ultimate_epic.wav",
                        "achievements": [
                            "file_industrial",
                            "file_god",
                            "eternal_loyalty",
                            "absolute_perfection"
                        ]
                    },
                    "security_sounds": {
                        "sfx": "security_lock.wav",
                        "achievements": [
                            "data_guardian",
                            "impenetrable_fortress",
                            "master_key"
                        ]
                    },
                    "compression_sounds": {
                        "sfx": "compress_zip.wav",
                        "achievements": [
                            "titanic_compressor",
                            "royal_archivist"
                        ]
                    },
                    "pdf_tools_sounds": {
                        "sfx": "pdf_action.wav",
                        "achievements": [
                            "division_blade",
                            "eternal_librarian"
                        ]
                    },
                    "legendary_sounds": {
                        "sfx": "legendary_unlock.wav",
                        "achievements": [
                            "dragon_breath",
                            "division_blade",
                            "absolute_perfection",
                            "adv_la_machine",
                            "adv_collectionneur",
                        ]
                    },
                    "conversion_sounds": {
                        "sfx": "conversion_done.wav",
                        "achievements": [
                            "visual_alchemist",
                            "processing_king",
                            "adv_data_architect",
                            "adv_csv_sorcier",
                            "adv_web_harvester",
                            "adv_bibliotheque",
                            "adv_icon_forge",
                            "adv_pixel_perfect",
                            "adv_extracteur_pro",
                            "adv_studio_underground",
                            "tpl_automatiste",
                            "tpl_archiviste",
                            "tpl_importateur",
                        ]
                    },
                    "technical_sounds": {
                        "sfx": "tech_achievement.wav",
                        "achievements": [
                            "all_seeing_eye",
                            "visionary",
                            "universal_traveler",
                            "adv_office_slayer",
                            "adv_format_nomade",
                            "adv_codec_master",
                            "adv_all_rounder",
                            "tpl_polyvalent",
                            "tpl_perfectionniste",
                            "tpl_reference_absolue",
                            "tpl_collectionneur_workflows",
                        ]
                    },
                    "fun_sounds": {
                        "sfx": "fun_unlock.wav",
                        "achievements": [
                            "night_owl",
                            "flash_gordon",
                            "adv_heic_hunter"
                        ]
                    },
                    "unique_sounds": {
                        "first_adventure": "first_step.wav",
                        "night_knight": "dark_mode.wav",
                        "cosmic_orb": "cosmic_unlock.wav"
                    }
                },
                "achievements": {},
                "categories": {},
                "tiers": {}
            }
            
            achievements = {
                "first_adventure": {
                    "id": "first_adventure",
                    "name": "Le Début de l'Aventure",
                    "description": "Réaliser la toute première conversion avec succès",
                    "icon": "smiling_smile.png",
                    "category": "progression",
                    "tier": "starter",
                    "requirement": {
                        "type": "conversions_total",
                        "value": 1
                    },
                    "reward_xp": 10,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "apprentice": {
                    "id": "apprentice",
                    "name": "L'Apprenti Convertisseur",
                    "description": "Convertir un total de 100 fichiers",
                    "icon": "bronze_trophy.png",
                    "category": "progression",
                    "tier": "bronze",
                    "requirement": {
                        "type": "conversions_total",
                        "value": 100
                    },
                    "reward_xp": 100,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "steel_warrior": {
                    "id": "steel_warrior",
                    "name": "Le Guerrier d'Acier",
                    "description": "Convertir un total de 500 fichiers",
                    "icon": "steel_trophy.png",
                    "category": "progression",
                    "tier": "steel",
                    "requirement": {
                        "type": "conversions_total",
                        "value": 500
                    },
                    "reward_xp": 300,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "format_expert": {
                    "id": "format_expert",
                    "name": "L'Expert du Format",
                    "description": "Convertir un total de 1 000 fichiers",
                    "icon": "silver_trophy.png",
                    "category": "progression",
                    "tier": "silver",
                    "requirement": {
                        "type": "conversions_total",
                        "value": 1000
                    },
                    "reward_xp": 500,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "platinum_master": {
                    "id": "platinum_master",
                    "name": "Le Maître Electrum",
                    "description": "Convertir un total de 5 000 fichiers",
                    "icon": "Electrum_trophy.png",
                    "category": "progression",
                    "tier": "platinum_tier",
                    "requirement": {
                        "type": "conversions_total",
                        "value": 5000
                    },
                    "reward_xp": 1500,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "file_industrial": {
                    "id": "file_industrial",
                    "name": "L'Industriel du Fichier",
                    "description": "Convertir un total de 10 000 fichiers",
                    "icon": "gold_trophy.png",
                    "category": "progression",
                    "tier": "gold",
                    "requirement": {
                        "type": "conversions_total",
                        "value": 10000
                    },
                    "reward_xp": 2000,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "file_god": {
                    "id": "file_god",
                    "name": "Le Dieu des Fichiers",
                    "description": "Débloquer absolument tous les autres succès",
                    "icon": "100%_platinium.png",
                    "category": "ultimate",
                    "tier": "platinum",
                    "requirement": {
                        "type": "all_achievements",
                        "value": True
                    },
                    "reward_xp": 10000,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "titanic_compressor": {
                    "id": "titanic_compressor",
                    "name": "Le Compresseur Titanique",
                    "description": "Compresser un total de 100 Go de données cumulées",
                    "icon": "Titan's_hammer.png",
                    "category": "compression",
                    "tier": "epic",
                    "requirement": {
                        "type": "compressed_data_gb",
                        "value": 100
                    },
                    "reward_xp": 800,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "division_blade": {
                    "id": "division_blade",
                    "name": "La Lame de Division",
                    "description": "Diviser un PDF contenant plus de 1 000 pages en une seule opération",
                    "icon": "Legendary_sword.png",
                    "category": "pdf_tools",
                    "tier": "legendary",
                    "requirement": {
                        "type": "pdf_split_max_pages",
                        "value": 1000
                    },
                    "reward_xp": 1000,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "visual_alchemist": {
                    "id": "visual_alchemist",
                    "name": "L'Alchimiste Visuel",
                    "description": "Convertir 5 000 images (JPG/PNG) en PDF",
                    "icon": "magic_potion.png",
                    "category": "conversion",
                    "tier": "epic",
                    "requirement": {
                        "type": "images_to_pdf_total",
                        "value": 5000
                    },
                    "reward_xp": 1200,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "eternal_librarian": {
                    "id": "eternal_librarian",
                    "name": "Le Bibliothécaire Éternel",
                    "description": "Fusionner des PDF pour créer un document unique de plus de 500 pages",
                    "icon": "Ancient_scroll(papyrus).png",
                    "category": "pdf_tools",
                    "tier": "epic",
                    "requirement": {
                        "type": "pdf_merge_max_pages",
                        "value": 500
                    },
                    "reward_xp": 800,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "royal_archivist": {
                    "id": "royal_archivist",
                    "name": "L'Archiviste Royal",
                    "description": "Créer 500 archives (ZIP, RAR, TAR) différentes",
                    "icon": "treasure_chest.png",
                    "category": "compression",
                    "tier": "epic",
                    "requirement": {
                        "type": "archives_created",
                        "value": 500
                    },
                    "reward_xp": 900,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "processing_king": {
                    "id": "processing_king",
                    "name": "Le Roi du Traitement",
                    "description": "Convertir 2 000 fichiers Word vers PDF (ou inversement)",
                    "icon": "royal_crown.png",
                    "category": "conversion",
                    "tier": "epic",
                    "requirement": {
                        "type": "word_pdf_conversions",
                        "value": 2000
                    },
                    "reward_xp": 1000,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "data_guardian": {
                    "id": "data_guardian",
                    "name": "Gardien des Données",
                    "description": "Protéger 50 fichiers PDF avec un mot de passe",
                    "icon": "Protector's_shield.png",
                    "category": "security",
                    "tier": "rare",
                    "requirement": {
                        "type": "pdf_protected",
                        "value": 50
                    },
                    "reward_xp": 400,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "impenetrable_fortress": {
                    "id": "impenetrable_fortress",
                    "name": "La Forteresse Impénétrable",
                    "description": "Protéger 100 archives avec un mot de passe complexe (12+ caractères)",
                    "icon": "Sacred_lock.png",
                    "category": "security",
                    "tier": "epic",
                    "requirement": {
                        "type": "batch_protect_complex",
                        "value": 100,
                        "extra": {
                            "min_password_length": 12
                        }
                    },
                    "reward_xp": 800,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "master_key": {
                    "id": "master_key",
                    "name": "Le Passe-Partout",
                    "description": "Réussir une conversion sur un fichier protégé (avec bon mot de passe) 50 fois",
                    "icon": "golden_key.png",
                    "category": "security",
                    "tier": "rare",
                    "requirement": {
                        "type": "protected_files_converted",
                        "value": 50
                    },
                    "reward_xp": 500,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "night_knight": {
                    "id": "night_knight",
                    "name": "Chevalier de la Nuit",
                    "description": "Utiliser l'application en Mode Sombre pendant un total de 100 heures",
                    "icon": "silver_shield.png",
                    "category": "usage",
                    "tier": "rare",
                    "requirement": {
                        "type": "dark_mode_hours",
                        "value": 100
                    },
                    "reward_xp": 600,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "dragon_breath": {
                    "id": "dragon_breath",
                    "name": "Le Souffle du Dragon",
                    "description": "Lancer une conversion par lot (Batch) contenant plus de 500 fichiers d'un coup",
                    "icon": "red_dragon.png",
                    "category": "technical",
                    "tier": "legendary",
                    "requirement": {
                        "type": "batch_max_files",
                        "value": 500
                    },
                    "reward_xp": 1500,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "all_seeing_eye": {
                    "id": "all_seeing_eye",
                    "name": "L'Œil Qui Voit Tout",
                    "description": "Utiliser la fonction OCR sur 1 000 pages au total",
                    "icon": "cyclop.png",
                    "category": "technical",
                    "tier": "epic",
                    "requirement": {
                        "type": "ocr_pages_total",
                        "value": 1000
                    },
                    "reward_xp": 1000,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "visionary": {
                    "id": "visionary",
                    "name": "Le Visionnaire",
                    "description": "Utiliser la fonction Aperçu (Preview) sur 2 000 fichiers différents",
                    "icon": "clairvoyance_crystal.png",
                    "category": "usage",
                    "tier": "epic",
                    "requirement": {
                        "type": "previews_used",
                        "value": 2000
                    },
                    "reward_xp": 900,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "universal_traveler": {
                    "id": "universal_traveler",
                    "name": "Le Voyageur Universel",
                    "description": "Avoir effectué au moins une conversion vers CHAQUE format de base supporté",
                    "icon": "cosmic_orb.png",
                    "category": "completion",
                    "tier": "epic",
                    "requirement": {
                        "type": "all_formats_used",
                        "value": True,
                        "formats": [
                            "pdf",
                            "docx",
                            "jpg",
                            "png",
                            "zip",
                            "rar",
                            "tar",
                            "gz"
                        ]
                    },
                    "reward_xp": 1000,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "eternal_loyalty": {
                    "id": "eternal_loyalty",
                    "name": "Fidélité Éternelle",
                    "description": "Lancer l'application 365 jours différents (cumulés)",
                    "icon": "eternal_diamond.png",
                    "category": "ultimate",
                    "tier": "diamond",
                    "requirement": {
                        "type": "unique_days_used",
                        "value": 365
                    },
                    "reward_xp": 3000,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "absolute_perfection": {
                    "id": "absolute_perfection",
                    "name": "La Perfection Absolue",
                    "description": "Réaliser une série de 500 conversions consécutives sans aucune erreur ni annulation",
                    "icon": "medal_of_excellence.png",
                    "category": "ultimate",
                    "tier": "legendary",
                    "requirement": {
                        "type": "consecutive_success",
                        "value": 500
                    },
                    "reward_xp": 5000,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "night_owl": {
                    "id": "night_owl",
                    "name": "Le Noctambule",
                    "description": "Convertir 100 fichiers entre 00h et 06h",
                    "icon": "Night_owl.png",
                    "category": "fun",
                    "tier": "rare",
                    "requirement": {
                        "type": "night_conversions",
                        "value": 100,
                        "extra": {
                            "time_start": "00:00",
                            "time_end": "06:00"
                        }
                    },
                    "reward_xp": 500,
                    "secret": True,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "flash_gordon": {
                    "id": "flash_gordon",
                    "name": "Flash Gordon",
                    "description": "Convertir 50 fichiers en moins de 5 minutes",
                    "icon": "Fast_as_lightning.png",
                    "category": "fun",
                    "tier": "rare",
                    "requirement": {
                        "type": "speed_conversion",
                        "value": 50,
                        "extra": {
                            "max_time_seconds": 300
                        }
                    },
                    "reward_xp": 600,
                    "secret": True,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                # Advanced Conversions
                "adv_data_architect": {
                    "id": "adv_data_architect",
                    "name": "⚡ Data Architect",
                    "description": "Réaliser 50 conversions de documents via les Conversions Avancées",
                    "icon": "blueprint.png",
                    "category": "advanced_conversions",
                    "tier": "advanced",
                    "requirement": {
                        "type": "adv_doc_conversions",
                        "value": 50
                    },
                    "reward_xp": 300,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "adv_csv_sorcier": {
                    "id": "adv_csv_sorcier",
                    "name": "⚡ CSV Sorcier",
                    "description": "Convertir 25 fichiers CSV↔JSON via les Conversions Avancées",
                    "icon": "spellbook.png",
                    "category": "advanced_conversions",
                    "tier": "advanced",
                    "requirement": {
                        "type": "adv_csv_json_conversions",
                        "value": 25
                    },
                    "reward_xp": 350,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "adv_office_slayer": {
                    "id": "adv_office_slayer",
                    "name": "⚡ Office Slayer",
                    "description": "Convertir 10 XLSX→PDF ET 10 PPTX→PDF via les Conversions Avancées",
                    "icon": "bow_and_arrow.png",
                    "category": "advanced_conversions",
                    "tier": "advanced",
                    "requirement": {
                        "type": "adv_office_slayer",
                        "value": 20
                    },
                    "reward_xp": 450,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "adv_web_harvester": {
                    "id": "adv_web_harvester",
                    "name": "⚡ Web Harvester",
                    "description": "Convertir 20 fichiers HTML→PDF via les Conversions Avancées",
                    "icon": "spider.png",
                    "category": "advanced_conversions",
                    "tier": "advanced",
                    "requirement": {
                        "type": "adv_html_to_pdf",
                        "value": 20
                    },
                    "reward_xp": 350,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "adv_bibliotheque": {
                    "id": "adv_bibliotheque",
                    "name": "⚡ Bibliothèque Numérique",
                    "description": "Convertir 15 fichiers EPUB→PDF via les Conversions Avancées",
                    "icon": "scroll.png",
                    "category": "advanced_conversions",
                    "tier": "advanced",
                    "requirement": {
                        "type": "adv_epub_to_pdf",
                        "value": 15
                    },
                    "reward_xp": 400,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "adv_icon_forge": {
                    "id": "adv_icon_forge",
                    "name": "⚡ Icon Forge",
                    "description": "Créer 25 fichiers ICO via les Conversions Avancées",
                    "icon": "anvil.png",
                    "category": "advanced_conversions",
                    "tier": "advanced",
                    "requirement": {
                        "type": "adv_image_to_ico",
                        "value": 25
                    },
                    "reward_xp": 350,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "adv_format_nomade": {
                    "id": "adv_format_nomade",
                    "name": "⚡ Format Nomade",
                    "description": "Avoir utilisé les 13 types de conversion image des Conversions Avancées",
                    "icon": "compass.png",
                    "category": "advanced_conversions",
                    "tier": "advanced",
                    "requirement": {
                        "type": "adv_image_types_used",
                        "value": 13
                    },
                    "reward_xp": 500,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "adv_heic_hunter": {
                    "id": "adv_heic_hunter",
                    "name": "⚡ HEIC Hunter",
                    "description": "Convertir 20 fichiers HEIC→PNG via les Conversions Avancées",
                    "icon": "telescope.png",
                    "category": "fun",
                    "tier": "advanced",
                    "requirement": {
                        "type": "adv_heic_conversions",
                        "value": 20
                    },
                    "reward_xp": 400,
                    "secret": True,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "adv_pixel_perfect": {
                    "id": "adv_pixel_perfect",
                    "name": "⚡ Pixel Perfect",
                    "description": "Convertir 100 images au total via les Conversions Avancées",
                    "icon": "potions.png",
                    "category": "advanced_conversions",
                    "tier": "epic",
                    "requirement": {
                        "type": "adv_image_conversions",
                        "value": 100
                    },
                    "reward_xp": 600,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "adv_extracteur_pro": {
                    "id": "adv_extracteur_pro",
                    "name": "⚡ Extracteur Pro",
                    "description": "Extraire l'audio de 30 vidéos (VIDEO→MP3) via les Conversions Avancées",
                    "icon": "eagle_shield.png",
                    "category": "advanced_conversions",
                    "tier": "advanced",
                    "requirement": {
                        "type": "adv_video_to_audio",
                        "value": 30
                    },
                    "reward_xp": 450,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "adv_codec_master": {
                    "id": "adv_codec_master",
                    "name": "⚡ Codec Master",
                    "description": "Avoir utilisé les 9 types de conversion vidéo des Conversions Avancées",
                    "icon": "mechanical_raven.png",
                    "category": "advanced_conversions",
                    "tier": "advanced",
                    "requirement": {
                        "type": "adv_video_types_used",
                        "value": 9
                    },
                    "reward_xp": 500,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "adv_studio_underground": {
                    "id": "adv_studio_underground",
                    "name": "⚡ Studio Underground",
                    "description": "Convertir 75 fichiers audio au total via les Conversions Avancées",
                    "icon": "lyre.png",
                    "category": "advanced_conversions",
                    "tier": "epic",
                    "requirement": {
                        "type": "adv_audio_conversions",
                        "value": 75
                    },
                    "reward_xp": 600,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "adv_all_rounder": {
                    "id": "adv_all_rounder",
                    "name": "⚡ All-Rounder",
                    "description": "Avoir ≥20 conversions réussies dans chacune des 3 catégories (document, image, audio/vidéo) des Conversions Avancées",
                    "icon": "scarab.png",
                    "category": "advanced_conversions",
                    "tier": "epic",
                    "requirement": {
                        "type": "adv_all_rounder",
                        "value": 20
                    },
                    "reward_xp": 800,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "adv_la_machine": {
                    "id": "adv_la_machine",
                    "name": "⚡ La Machine",
                    "description": "Réaliser 250 conversions avancées au total",
                    "icon": "gauntlet.png",
                    "category": "advanced_conversions",
                    "tier": "legendary",
                    "requirement": {
                        "type": "adv_total_conversions",
                        "value": 250
                    },
                    "reward_xp": 1500,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                "adv_collectionneur": {
                    "id": "adv_collectionneur",
                    "name": "⚡ Collectionneur Ultime",
                    "description": "Avoir utilisé CHAQUE type de conversion disponible dans les Conversions Avancées",
                    "icon": "treasure.png",
                    "category": "advanced_conversions",
                    "tier": "legendary",
                    "requirement": {
                        "type": "adv_all_types_used",
                        "value": 41
                    },
                    "reward_xp": 2000,
                    "secret": False,
                    "unlocked": False,
                    "unlock_date": None,
                    "progress": 0
                },
                # Templates achievements
                "tpl_architecte": {
                    "id": "tpl_architecte",
                    "name": "📋 Architecte de Flux",
                    "description": "Créer 10 templates au total",
                    "icon": "spinning_wheel.png",
                    "category": "templates",
                    "tier": "rare",
                    "requirement": {"type": "tpl_created_total", "value": 10},
                    "reward_xp": 300,
                    "secret": False, "unlocked": False, "unlock_date": None, "progress": 0
                },
                "tpl_maitre_presets": {
                    "id": "tpl_maitre_presets",
                    "name": "📋 Maître des Préréglages",
                    "description": "Créer 25 templates au total",
                    "icon": "assassin_kit.png",
                    "category": "templates",
                    "tier": "epic",
                    "requirement": {"type": "tpl_created_total", "value": 25},
                    "reward_xp": 600,
                    "secret": False, "unlocked": False, "unlock_date": None, "progress": 0
                },
                "tpl_reference_absolue": {
                    "id": "tpl_reference_absolue",
                    "name": "📋 Référence Absolue",
                    "description": "Avoir 5 templates différents marqués comme défaut simultanément (un par type d'opération)",
                    "icon": "tarot_cards.png",
                    "category": "templates",
                    "tier": "epic",
                    "requirement": {"type": "tpl_defaults_count", "value": 5},
                    "reward_xp": 700,
                    "secret": False, "unlocked": False, "unlock_date": None, "progress": 0
                },
                "tpl_automatiste": {
                    "id": "tpl_automatiste",
                    "name": "📋 Automatiste",
                    "description": "Appliquer des templates 50 fois au total",
                    "icon": "hourglass.png",
                    "category": "templates",
                    "tier": "rare",
                    "requirement": {"type": "tpl_applied_total", "value": 50},
                    "reward_xp": 400,
                    "secret": False, "unlocked": False, "unlock_date": None, "progress": 0
                },
                "tpl_le_rituel": {
                    "id": "tpl_le_rituel",
                    "name": "📋 Le Rituel",
                    "description": "Appliquer le même template 25 fois",
                    "icon": "skull.png",
                    "category": "templates",
                    "tier": "rare",
                    "requirement": {"type": "tpl_single_max_applied", "value": 25},
                    "reward_xp": 500,
                    "secret": False, "unlocked": False, "unlock_date": None, "progress": 0
                },
                "tpl_collectionneur_workflows": {
                    "id": "tpl_collectionneur_workflows",
                    "name": "📋 Collectionneur de Workflows",
                    "description": "Avoir au moins un template pour chacune des 9 catégories disponibles",
                    "icon": "treasure_map.png",
                    "category": "templates",
                    "tier": "epic",
                    "requirement": {"type": "tpl_all_categories", "value": 9},
                    "reward_xp": 800,
                    "secret": False, "unlocked": False, "unlock_date": None, "progress": 0
                },
                "tpl_polyvalent": {
                    "id": "tpl_polyvalent",
                    "name": "📋 Polyvalent",
                    "description": "Utiliser 5 types de templates différents en une seule session",
                    "icon": "mushrooms.png",
                    "category": "templates",
                    "tier": "rare",
                    "requirement": {"type": "tpl_types_session", "value": 5},
                    "reward_xp": 350,
                    "secret": False, "unlocked": False, "unlock_date": None, "progress": 0
                },
                "tpl_archiviste": {
                    "id": "tpl_archiviste",
                    "name": "📋 Archiviste de Templates",
                    "description": "Exporter ses templates au moins une fois",
                    "icon": "bear_totem.png",
                    "category": "templates",
                    "tier": "advanced",
                    "requirement": {"type": "tpl_exported", "value": 1},
                    "reward_xp": 200,
                    "secret": False, "unlocked": False, "unlock_date": None, "progress": 0
                },
                "tpl_importateur": {
                    "id": "tpl_importateur",
                    "name": "📋 Importateur",
                    "description": "Importer un fichier de templates au moins une fois",
                    "icon": "ship_wheel.png",
                    "category": "templates",
                    "tier": "advanced",
                    "requirement": {"type": "tpl_imported", "value": 1},
                    "reward_xp": 200,
                    "secret": False, "unlocked": False, "unlock_date": None, "progress": 0
                },
                "tpl_perfectionniste": {
                    "id": "tpl_perfectionniste",
                    "name": "📋 Perfectionniste",
                    "description": "Modifier 10 templates existants via Edit",
                    "icon": "magic_staff.png",
                    "category": "templates",
                    "tier": "rare",
                    "requirement": {"type": "tpl_edited_total", "value": 10},
                    "reward_xp": 400,
                    "secret": False, "unlocked": False, "unlock_date": None, "progress": 0
                }
            }
            
            self.achievements_data["achievements"] = achievements
            
            categories = {
                "progression": {
                    "name": "Progression Globale",
                    "icon": "trophy_icon.png",
                    "color": "#FFD700"
                },
                "conversion": {
                    "name": "Conversion",
                    "icon": "convert_icon.png",
                    "color": "#4dabf7"
                },
                "pdf_tools": {
                    "name": "Outils PDF",
                    "icon": "pdf_icon.png",
                    "color": "#FF6B6B"
                },
                "compression": {
                    "name": "Compression",
                    "icon": "compress_icon.png",
                    "color": "#51CF66"
                },
                "security": {
                    "name": "Sécurité",
                    "icon": "security_icon.png",
                    "color": "#FFA94D"
                },
                "technical": {
                    "name": "Exploits Techniques",
                    "icon": "tech_icon.png",
                    "color": "#CC5DE8"
                },
                "usage": {
                    "name": "Utilisation",
                    "icon": "usage_icon.png",
                    "color": "#339AF0"
                },
                "completion": {
                    "name": "Complétude",
                    "icon": "completion_icon.png",
                    "color": "#20C997"
                },
                "ultimate": {
                    "name": "Ultime",
                    "icon": "ultimate_icon.png",
                    "color": "#9775FA"
                },
                "fun": {
                    "name": "Fun & Easter Eggs",
                    "icon": "fun_icon.png",
                    "color": "#FF8787"
                },
                "advanced_conversions": {
                    "name": "Conversions Avancées",
                    "icon": "tech_icon.png",
                    "color": "#22d3ee"
                },
                "templates": {
                    "name": "Templates",
                    "icon": "tech_icon.png",
                    "color": "#a78bfa"
                }
            }
            
            self.achievements_data["categories"] = categories
            
            tiers = {
                "starter": {
                    "name": "Débutant",
                    "color": "#A8DADC",
                    "order": 1
                },
                "bronze": {
                    "name": "Bronze",
                    "color": "#CD7F32",
                    "order": 2
                },
                "steel": {
                    "name": "Acier",
                    "color": "#71797E",
                    "order": 3
                },
                "silver": {
                    "name": "Argent",
                    "color": "#C0C0C0",
                    "order": 4
                },
                "platinum_tier": {
                    "name": "Electrum",
                    "color": "#C18D30",
                    "order": 5
                },
                "gold": {
                    "name": "Or",
                    "color": "#FFD700",
                    "order": 6
                },
                "rare": {
                    "name": "Rare",
                    "color": "#4169E1",
                    "order": 7
                },
                "epic": {
                    "name": "Épique",
                    "color": "#9370DB",
                    "order": 8
                },
                "legendary": {
                    "name": "Légendaire",
                    "color": "#FF8C00",
                    "order": 9
                },
                "diamond": {
                    "name": "Diamant",
                    "color": "#B9F2FF",
                    "order": 10
                },
                "platinum": {
                    "name": "Platine Ultime",
                    "color": "#E5E4E2",
                    "order": 11
                },
                "advanced": {
                    "name": "Avancé",
                    "color": "#22d3ee",
                    "order": 7
                }
            }
            
            self.achievements_data["tiers"] = tiers
            
            self.initialize_achievements()
        
        except Exception as e:
            print(f"Error loading achievements data: {e}")

    def init_database(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                icon TEXT,
                category TEXT,
                tier TEXT,
                requirement_type TEXT,
                requirement_value REAL,
                requirement_extra TEXT,
                reward_xp INTEGER,
                secret BOOLEAN,
                unlocked BOOLEAN,
                unlock_date TEXT,
                progress REAL,
                max_progress REAL
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                key TEXT PRIMARY KEY,
                value REAL,
                last_updated TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                date TEXT PRIMARY KEY,
                conversions INTEGER DEFAULT 0,
                previews INTEGER DEFAULT 0,
                dark_mode_minutes INTEGER DEFAULT 0
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS used_formats (
                format TEXT PRIMARY KEY,
                used BOOLEAN DEFAULT FALSE
            )
            ''')
            
            conn.commit()
            conn.close()
            print(f"[DB OK] Database created/updated: {self.db_path}")
        
        except Exception as e:
            print(f"[DB ERROR] Cannot access {self.db_path}: {e}")
            traceback.print_exc()

    def initialize_achievements(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for achievement_id, achievement in self.achievements_data["achievements"].items():
                cursor.execute('''
                INSERT OR IGNORE INTO achievements 
                (id, name, description, icon, category, tier, requirement_type, 
                 requirement_value, requirement_extra, reward_xp, secret, 
                 unlocked, unlock_date, progress, max_progress)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    achievement["id"],
                    json.dumps(achievement["name"]),
                    json.dumps(achievement["description"]),
                    achievement["icon"],
                    achievement["category"],
                    achievement["tier"],
                    achievement["requirement"]["type"],
                    achievement["requirement"]["value"],
                    json.dumps(achievement["requirement"].get("extra", {})),
                    achievement["reward_xp"],
                    achievement["secret"],
                    achievement["unlocked"],
                    achievement["unlock_date"],
                    achievement["progress"],
                    achievement["requirement"]["value"]
                ))

                cursor.execute('''
                UPDATE achievements
                SET requirement_value = ?,
                    max_progress      = ?
                WHERE id       = ?
                  AND unlocked = FALSE
                ''', (
                    achievement["requirement"]["value"],
                    achievement["requirement"]["value"],
                    achievement["id"],
                ))
            formats = ["pdf", "docx", "jpg", "png", "zip", "rar", "tar", "gz"]
            for fmt in formats:
                cursor.execute('INSERT OR IGNORE INTO used_formats (format, used) VALUES (?, ?)', (fmt, False))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            print(f"Error initializing achievements: {e}")

    def load_stats(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT key, value FROM stats')
            rows = cursor.fetchall()
            
            for key, value in rows:
                self.stats[key] = value
            
            default_stats = {
                "total_conversions": 0,
                "images_to_pdf": 0,
                "word_pdf_conversions": 0,
                "pdf_protected": 0,
                "archives_created": 0,
                "previews_used": 0,
                "dark_mode_minutes": 0,
                "ocr_pages": 0,
                "compressed_gb": 0.0,
                "consecutive_success": 0,
                "conversions_today": 0,
                "previews_today": 0,
                "dark_mode_today": 0,
                "start_time": datetime.now().isoformat(),
                "unique_days": 1,
                "last_launch_date": datetime.now().date().isoformat(),
                "night_conversions": 0,
                # Advanced conversions stats
                "adv_total_conversions": 0,
                "adv_doc_conversions": 0,
                "adv_image_conversions": 0,
                "adv_audio_conversions": 0,
                "adv_video_conversions": 0,
                "adv_csv_json_conversions": 0,
                "adv_html_to_pdf": 0,
                "adv_epub_to_pdf": 0,
                "adv_image_to_ico": 0,
                "adv_heic_conversions": 0,
                "adv_video_to_audio": 0,
                "adv_xlsx_to_pdf": 0,
                "adv_pptx_to_pdf": 0,
                "adv_image_types_used": 0,
                "adv_video_types_used": 0,
                # Per-type image flags (image_to_*)
                "adv_image_to_png": 0,
                "adv_image_to_jpeg": 0,
                "adv_image_to_jpg": 0,
                "adv_image_to_bmp": 0,
                "adv_image_to_heic": 0,
                "adv_image_to_webp": 0,
                "adv_image_to_tiff": 0,
                "adv_image_to_psd": 0,
                "adv_image_to_svg": 0,
                "adv_image_to_avif": 0,
                "adv_image_to_j2k": 0,
                "adv_image_to_dng": 0,
                "adv_image_to_ico_flag": 0,
                # Per-type video flags (video_to_*)
                "adv_video_to_mp4": 0,
                "adv_video_to_webm": 0,
                "adv_video_to_mkv": 0,
                "adv_video_to_mov": 0,
                "adv_video_to_avi": 0,
                "adv_video_to_mp3": 0,
                "adv_video_to_wav": 0,
                "adv_video_to_aac": 0,
                "adv_video_to_flac": 0,
                # Templates stats
                "tpl_created_total": 0,
                "tpl_applied_total": 0,
                "tpl_edited_total": 0,
                "tpl_exported": 0,
                "tpl_imported": 0,
                "tpl_single_max_applied": 0,
                "tpl_types_session": 0,
            }
            
            for key, default_value in default_stats.items():
                if key not in self.stats:
                    self.stats[key] = default_value
                    cursor.execute('INSERT OR REPLACE INTO stats (key, value, last_updated) VALUES (?, ?, ?)',
                                  (key, default_value, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            print(f"Error loading stats: {e}")

    def save_stats(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for key, value in self.stats.items():
                cursor.execute('INSERT OR REPLACE INTO stats (key, value, last_updated) VALUES (?, ?, ?)',
                              (key, value, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            print(f"Error saving stats: {e}")

    def update_all_progress(self):
        if not self.achievements_data or "achievements" not in self.achievements_data:
            return
        
        for ach_id, achievement in self.achievements_data["achievements"].items():
            if achievement["unlocked"]:
                achievement["progress"] = achievement["requirement"]["value"]
                continue
            
            req_type = achievement["requirement"]["type"]
            progress = 0
            
            if req_type == "conversions_total":
                progress = self.stats.get("total_conversions", 0)
            elif req_type == "images_to_pdf_total":
                progress = self.stats.get("images_to_pdf", 0)
            elif req_type == "word_pdf_conversions":
                progress = self.stats.get("word_pdf_conversions", 0)
            elif req_type == "pdf_protected":
                progress = self.stats.get("pdf_protected", 0)
            elif req_type == "archives_created":
                progress = self.stats.get("archives_created", 0)
            elif req_type == "previews_used":
                progress = self.stats.get("previews_used", 0)
            elif req_type == "dark_mode_hours":
                progress = self.stats.get("dark_mode_minutes", 0) / 60
            elif req_type == "ocr_pages_total":
                progress = self.stats.get("ocr_pages", 0)
            elif req_type == "compressed_data_gb":
                progress = self.stats.get("compressed_gb", 0)
            elif req_type == "consecutive_success":
                progress = self.stats.get("consecutive_success", 0)
            elif req_type == "night_conversions":
                progress = self.stats.get("night_conversions", 0)
            elif req_type == "protected_files_converted":
                progress = self.stats.get("protected_files_converted", 0)
            elif req_type == "unique_days_used":
                progress = self.stats.get("unique_days", 0)
            elif req_type == "all_formats_used":
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    
                    cursor.execute('SELECT COUNT(*) FROM used_formats WHERE used = TRUE')
                    used_count = cursor.fetchone()[0]
                    
                    cursor.execute('SELECT COUNT(*) FROM used_formats')
                    total_count = cursor.fetchone()[0]
                    
                    conn.close()
                    
                    if total_count > 0:
                        achievement["progress"] = used_count
                    else:
                        achievement["progress"] = 0
                        
                except Exception:
                    achievement["progress"] = 0
            elif req_type == "batch_max_files":
                progress = self.stats.get("max_batch_files", 0)
            elif req_type == "batch_protect_complex":
                progress = self.stats.get("batch_protect_complex_count", 0)
            # Advanced conversions
            elif req_type == "adv_total_conversions":
                progress = self.stats.get("adv_total_conversions", 0)
            elif req_type == "adv_doc_conversions":
                progress = self.stats.get("adv_doc_conversions", 0)
            elif req_type == "adv_image_conversions":
                progress = self.stats.get("adv_image_conversions", 0)
            elif req_type == "adv_audio_conversions":
                progress = self.stats.get("adv_audio_conversions", 0)
            elif req_type == "adv_video_to_audio":
                progress = self.stats.get("adv_video_to_audio", 0)
            elif req_type == "adv_csv_json_conversions":
                progress = self.stats.get("adv_csv_json_conversions", 0)
            elif req_type == "adv_html_to_pdf":
                progress = self.stats.get("adv_html_to_pdf", 0)
            elif req_type == "adv_epub_to_pdf":
                progress = self.stats.get("adv_epub_to_pdf", 0)
            elif req_type == "adv_image_to_ico":
                progress = self.stats.get("adv_image_to_ico", 0)
            elif req_type == "adv_heic_conversions":
                progress = self.stats.get("adv_heic_conversions", 0)
            elif req_type == "adv_image_types_used":
                progress = self.stats.get("adv_image_types_used", 0)
            elif req_type == "adv_video_types_used":
                progress = self.stats.get("adv_video_types_used", 0)
            elif req_type in ("adv_office_slayer", "adv_all_rounder", "adv_all_types_used"):
                # computed dynamically in check_achievement — derive progress here
                if req_type == "adv_all_types_used":
                    all_flags = [v[2] for v in self._ADV_TYPE_MAP.values() if v[2]]
                    progress = sum(1 for f in all_flags if self.stats.get(f, 0) > 0)
                    achievement["progress"] = progress
                    continue
                elif req_type == "adv_office_slayer":
                    progress = min(
                        self.stats.get("adv_xlsx_to_pdf", 0),
                        self.stats.get("adv_pptx_to_pdf", 0)
                    )
                elif req_type == "adv_all_rounder":
                    progress = min(
                        self.stats.get("adv_doc_conversions", 0),
                        self.stats.get("adv_image_conversions", 0),
                        self.stats.get("adv_audio_conversions", 0) +
                        self.stats.get("adv_video_conversions", 0)
                    )
            # Templates
            elif req_type == "tpl_created_total":
                progress = self.stats.get("tpl_created_total", 0)
            elif req_type == "tpl_applied_total":
                progress = self.stats.get("tpl_applied_total", 0)
            elif req_type == "tpl_edited_total":
                progress = self.stats.get("tpl_edited_total", 0)
            elif req_type == "tpl_exported":
                progress = self.stats.get("tpl_exported", 0)
            elif req_type == "tpl_imported":
                progress = self.stats.get("tpl_imported", 0)
            elif req_type == "tpl_single_max_applied":
                progress = self.stats.get("tpl_single_max_applied", 0)
            elif req_type == "tpl_types_session":
                progress = self.stats.get("tpl_types_session", 0)
            elif req_type == "tpl_defaults_count":
                # computed dynamically
                progress = achievement.get("progress", 0)
            elif req_type == "tpl_all_categories":
                progress = achievement.get("progress", 0)
            
            achievement["progress"] = progress

    def mark_format_as_used(self, file_format):
        if not file_format:
            return
        
        file_format = file_format.lower().strip().replace('.', '')
        
        valid_formats = ["pdf", "docx", "jpg", "jpeg", "png", "zip", "rar", "tar", "gz"]
        
        if file_format not in valid_formats:
            print(f"[ACHIEVEMENTS] Format ignored (invalid): {file_format}")
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT used FROM used_formats WHERE format = ?', (file_format,))
            result = cursor.fetchone()
            was_used = result[0] if result else False
            
            if was_used:
                print(f"[ACHIEVEMENTS] Format {file_format} already counted.")
                conn.close()
                return
            
            cursor.execute('UPDATE used_formats SET used = TRUE WHERE format = ?', (file_format,))
            
            cursor.execute('SELECT used FROM used_formats WHERE format = ?', (file_format,))
            result_after = cursor.fetchone()
            is_now_used = result_after[0] if result_after else False
            
            conn.commit()
            conn.close()
            
            print(f"[ACHIEVEMENTS] Format {file_format} marked as used (Before: {was_used}, After: {is_now_used})")
            
            self.update_all_progress()
            self.check_all_formats_used() 
        
        except Exception as e:
            print(f"[ACHIEVEMENTS] Error marking format {file_format}: {e}")

    def update_stat(self, key, value):
        self.stats[key] = value
        self.update_all_progress()
        self.check_achievements_for_stat(key, value)

    def increment_stat(self, key, amount=1):
        current = self.stats.get(key, 0)
        self.stats[key] = current + amount
        self.update_all_progress()
        self.check_achievements_for_stat(key, self.stats[key])

    def add_dark_mode_time(self, minutes):
        if minutes > 0:
            self.increment_stat("dark_mode_minutes", minutes)
            self.increment_stat("dark_mode_today", minutes)
            self.check_achievement("night_knight")

    def check_achievements_for_stat(self, stat_key, stat_value):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, requirement_type, requirement_value, unlocked 
            FROM achievements 
            WHERE requirement_type = ?
            ''', (stat_key,))
            
            achievements = cursor.fetchall()
            
            for ach_id, req_type, req_value, unlocked in achievements:
                if not unlocked:
                    check_value = stat_value
                    if req_type == "dark_mode_hours" and stat_key == "dark_mode_minutes":
                        check_value = stat_value / 60
                        
                    if check_value >= req_value:
                        self.unlock_achievement(ach_id)
            
            conn.close()
        
        except Exception as e:
            print(f"Error checking achievements: {e}")

    def check_achievement(self, achievement_id):
        try:
            achievement = self.achievements_data["achievements"][achievement_id]
            
            if achievement["unlocked"]:
                return
            
            req_type = achievement["requirement"]["type"]
            req_value = achievement["requirement"]["value"]
            
            unlocked = False
            
            if req_type == "conversions_total":
                unlocked = self.stats.get("total_conversions", 0) >= req_value
            elif req_type == "images_to_pdf_total":
                unlocked = self.stats.get("images_to_pdf", 0) >= req_value
            elif req_type == "word_pdf_conversions":
                unlocked = self.stats.get("word_pdf_conversions", 0) >= req_value
            elif req_type == "pdf_protected":
                unlocked = self.stats.get("pdf_protected", 0) >= req_value
            elif req_type == "archives_created":
                unlocked = self.stats.get("archives_created", 0) >= req_value
            elif req_type == "previews_used":
                unlocked = self.stats.get("previews_used", 0) >= req_value
            elif req_type == "dark_mode_hours":
                unlocked = (self.stats.get("dark_mode_minutes", 0) / 60) >= req_value
            elif req_type == "ocr_pages_total":
                unlocked = self.stats.get("ocr_pages", 0) >= req_value
            elif req_type == "compressed_data_gb":
                unlocked = self.stats.get("compressed_gb", 0) >= req_value
            elif req_type == "consecutive_success":
                unlocked = self.stats.get("consecutive_success", 0) >= req_value
            elif req_type == "night_conversions":
                unlocked = self.stats.get("night_conversions", 0) >= req_value
            
            elif req_type == "unique_days_used":
                unlocked = self.stats.get("unique_days", 0) >= req_value
            elif req_type == "all_formats_used":
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    
                    cursor.execute('SELECT COUNT(*) FROM used_formats WHERE used = TRUE')
                    used_count = cursor.fetchone()[0]
                    
                    cursor.execute('SELECT COUNT(*) FROM used_formats')
                    total_count = cursor.fetchone()[0]
                    
                    conn.close()
                    
                    if total_count > 0:
                        achievement["progress"] = used_count
                    else:
                        achievement["progress"] = 0
                    if used_count == total_count:
                        unlocked = True
                
                except Exception as e:
                    print(f"Error check_all_formats_used: {e}")
            elif req_type == "batch_max_files":
                unlocked = self.stats.get("max_batch_files", 0) >= req_value
            elif req_type == "batch_protect_complex":
                unlocked = False
            elif req_type == "protected_files_converted":
                unlocked = False
            elif req_type == "speed_conversion":
                files_done = self.stats.get("recent_batch_files", 0)
                time_taken = self.stats.get("recent_batch_time", float('inf'))
                max_allowed = achievement["requirement"]["extra"].get("max_time_seconds", 300)
                required_files = achievement["requirement"]["value"]
                unlocked = (files_done >= required_files) and (time_taken <= max_allowed)
            elif req_type == "pdf_split_max_pages":
                unlocked = self.stats.get("max_pdf_split_pages", 0) >= req_value
            elif req_type == "pdf_merge_max_pages":
                unlocked = self.stats.get("max_pdf_merge_pages", 0) >= req_value
            # Advanced conversions
            elif req_type == "adv_total_conversions":
                unlocked = self.stats.get("adv_total_conversions", 0) >= req_value
            elif req_type == "adv_doc_conversions":
                unlocked = self.stats.get("adv_doc_conversions", 0) >= req_value
            elif req_type == "adv_image_conversions":
                unlocked = self.stats.get("adv_image_conversions", 0) >= req_value
            elif req_type == "adv_audio_conversions":
                unlocked = self.stats.get("adv_audio_conversions", 0) >= req_value
            elif req_type == "adv_video_to_audio":
                unlocked = self.stats.get("adv_video_to_audio", 0) >= req_value
            elif req_type == "adv_csv_json_conversions":
                unlocked = self.stats.get("adv_csv_json_conversions", 0) >= req_value
            elif req_type == "adv_html_to_pdf":
                unlocked = self.stats.get("adv_html_to_pdf", 0) >= req_value
            elif req_type == "adv_epub_to_pdf":
                unlocked = self.stats.get("adv_epub_to_pdf", 0) >= req_value
            elif req_type == "adv_image_to_ico":
                unlocked = self.stats.get("adv_image_to_ico", 0) >= req_value
            elif req_type == "adv_heic_conversions":
                unlocked = self.stats.get("adv_heic_conversions", 0) >= req_value
            elif req_type == "adv_image_types_used":
                unlocked = self.stats.get("adv_image_types_used", 0) >= req_value
            elif req_type == "adv_video_types_used":
                unlocked = self.stats.get("adv_video_types_used", 0) >= req_value
            elif req_type == "adv_office_slayer":
                unlocked = (self.stats.get("adv_xlsx_to_pdf", 0) >= 10 and
                            self.stats.get("adv_pptx_to_pdf", 0) >= 10)
            elif req_type == "adv_all_rounder":
                unlocked = (self.stats.get("adv_doc_conversions", 0) >= req_value and
                            self.stats.get("adv_image_conversions", 0) >= req_value and
                            (self.stats.get("adv_audio_conversions", 0) +
                             self.stats.get("adv_video_conversions", 0)) >= req_value)
            elif req_type == "adv_all_types_used":
                all_flags = [v[2] for v in self._ADV_TYPE_MAP.values() if v[2]]
                used_count = sum(1 for f in all_flags if self.stats.get(f, 0) > 0)
                achievement["progress"] = used_count
                unlocked = used_count >= len(all_flags)
            # Templates
            elif req_type == "tpl_created_total":
                unlocked = self.stats.get("tpl_created_total", 0) >= req_value
            elif req_type == "tpl_applied_total":
                unlocked = self.stats.get("tpl_applied_total", 0) >= req_value
            elif req_type == "tpl_edited_total":
                unlocked = self.stats.get("tpl_edited_total", 0) >= req_value
            elif req_type == "tpl_exported":
                unlocked = self.stats.get("tpl_exported", 0) >= req_value
            elif req_type == "tpl_imported":
                unlocked = self.stats.get("tpl_imported", 0) >= req_value
            elif req_type == "tpl_single_max_applied":
                unlocked = self.stats.get("tpl_single_max_applied", 0) >= req_value
            elif req_type == "tpl_types_session":
                unlocked = self.stats.get("tpl_types_session", 0) >= req_value
            elif req_type == "tpl_defaults_count":
                unlocked = achievement.get("progress", 0) >= req_value
            elif req_type == "tpl_all_categories":
                unlocked = achievement.get("progress", 0) >= req_value
            
            if unlocked:
                self.unlock_achievement(achievement_id)
        
        except Exception as e:
            print(f"Error checking achievement {achievement_id}: {e}")

    def load_achievements_from_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, unlocked, unlock_date, progress
            FROM achievements
            ''')
            
            rows = cursor.fetchall()
            
            for row in rows:
                achievement_id, unlocked, unlock_date, progress = row
                
                if achievement_id in self.achievements_data["achievements"]:
                    self.achievements_data["achievements"][achievement_id]["unlocked"] = bool(unlocked)
                    self.achievements_data["achievements"][achievement_id]["unlock_date"] = unlock_date
            
            conn.close()
        
        except Exception as e:
            print(f"[ERROR] Cannot load achievements from DB: {e}")

    def check_flash_gordon(self, files_count, time_seconds):
        """Checks and triggers Flash Gordon if ≥50 files in ≤300s."""
        if files_count >= 50 and time_seconds <= 300:
            print(f"[DEBUG FLASH GORDON] Condition met: {files_count} files in {time_seconds:.2f}s")
            self.check_achievement("flash_gordon")
        else:
            print(f"[DEBUG FLASH GORDON] Failed: {files_count} files in {time_seconds:.2f}s (threshold: ≥50 / ≤300s)")

    def unlock_achievement(self, achievement_id):
        try:
            achievement = self.achievements_data["achievements"][achievement_id]
            
            if achievement["unlocked"]:
                return
            
            achievement["unlocked"] = True
            achievement["unlock_date"] = datetime.now().isoformat()
            achievement["progress"] = achievement["requirement"]["value"]
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            UPDATE achievements 
            SET unlocked = ?, unlock_date = ?, progress = ?
            WHERE id = ?
            ''', (True, achievement["unlock_date"], achievement["progress"], achievement_id))
            
            conn.commit()
            conn.close()
            
            self.achievement_unlocked.emit(achievement)
            if achievement_id == "flash_gordon":
                self.update_stat("recent_batch_files", 0)
                self.update_stat("recent_batch_time", float('inf'))
            print(f"[ACHIEVEMENT] {achievement_id} unlocked!")
            
            self.check_all_achievements_unlocked()
            self.check_rank_up()
        
        except Exception as e:
            print(f"[ERROR] Unlocking achievement {achievement_id}: {e}")

    def check_rank_up(self):
        """Checks if the rank has changed and emits a signal if so"""
        current_index, _, _ = self.get_current_rank()
        if current_index != self.last_rank_index:
            self.last_rank_index = current_index
            if hasattr(self, 'rank_unlocked'):
                self.rank_unlocked.emit(self.get_rank_data_for_popup())

    def get_rank_data_for_popup(self):
        """Prepares data for the rank popup"""
        idx, fr_name, color = self.get_current_rank()
        rank_key = self.ranks[idx][0].lower().replace(" ", "_")
        return {
            "id": rank_key,
            "name": fr_name,  # FR key = translation key
            "icon": f"{rank_key}.png",
            "color": color,
            "sound": f"{rank_key}.wav"
        }

    def check_all_achievements_unlocked(self):
        try:
            all_unlocked = True
            
            for achievement_id, achievement in self.achievements_data["achievements"].items():
                if achievement_id == "file_god":
                    continue
                    
                if not achievement["unlocked"]:
                    all_unlocked = False
                    break
            
            if all_unlocked:
                self.unlock_achievement("file_god")
        
        except Exception as e:
            print(f"Error checking all achievements: {e}")

    def get_achievement_sound(self, achievement_id):
        try:
            for group_name, group_data in self.achievements_data["sound_groups"].items():
                if group_name == "unique_sounds":
                    if achievement_id in group_data:
                        return group_data[achievement_id]
                else:
                    if achievement_id in group_data.get("achievements", []):
                        return group_data["sfx"]
            
            return "trophy_progression.wav"
            
        except Exception as e:
            print(f"Error retrieving achievement sound: {e}")
            return "trophy_progression.wav"

    def get_achievement_icon_path(self, icon_name):
        try:
            possible_paths = []
            meipass = getattr(sys, '_MEIPASS', None)
            if meipass:
                possible_paths.append(os.path.join(meipass, "Assets", icon_name))
            # Dev
            possible_paths += [
                os.path.join(_ROOT_DIR, "Assets", icon_name),
                os.path.join(os.getcwd(), "Assets", icon_name),
                os.path.join("Assets", icon_name),
                icon_name,
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    return path

            return self.get_resource_path("Assets/smiling_smile.png")

        except Exception as e:
            print(f"Error getting icon path {icon_name}: {e}")
            return ""

    def get_sound_path(self, sound_name):
        try:
            possible_paths = []
            # PyInstaller: _MEIPASS first
            meipass = getattr(sys, '_MEIPASS', None)
            if meipass:
                possible_paths.append(os.path.join(meipass, "SFX", sound_name))
            # Dev
            possible_paths += [
                os.path.join(_ROOT_DIR, "SFX", sound_name),
                os.path.join(os.getcwd(), "SFX", sound_name),
                os.path.join("SFX", sound_name),
                sound_name,
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    return path

            return ""

        except Exception as e:
            print(f"Error getting sound path {sound_name}: {e}")
            return ""

    def get_all_achievements(self):
        self.update_all_progress()
        return self.achievements_data["achievements"]

    def get_achievement(self, achievement_id):
        return self.achievements_data["achievements"].get(achievement_id)

    def get_category(self, category_id):
        return self.achievements_data["categories"].get(category_id)

    def get_tier(self, tier_id):
        return self.achievements_data["tiers"].get(tier_id)

    def get_unlocked_count(self):
        count = 0
        for achievement in self.achievements_data["achievements"].values():
            if achievement.get("unlocked"):
                count += 1
        return count

    def get_total_xp(self):
        total_xp = 0
        for achievement in self.achievements_data["achievements"].values():
            if achievement.get("unlocked"):
                total_xp += achievement.get("reward_xp", 0)
        return total_xp

    def get_current_rank(self):
        """Returns (index, fr_name, color) of the current rank.
        fr_name is the FR string used as translation key via translate_text()."""
        unlocked = self.get_unlocked_count()
        thresholds = [0, 1, 4, 9, 15, 21, 28, 35, 41, 49]
        rank_index = 0
        for i, thresh in enumerate(thresholds):
            if unlocked >= thresh:
                rank_index = i
            else:
                break
        fr_name = self.ranks[rank_index][1]
        color = self.rank_colors[rank_index]
        return rank_index, fr_name, color

    def get_progress_percentage(self):
        total = len(self.achievements_data["achievements"])
        if total == 0:
            return 0
        return (self.get_unlocked_count() / total) * 100

    def get_category_stats(self):
        category_stats = {}
        
        for category_id in self.achievements_data["categories"]:
            category_stats[category_id] = {
                "total": 0,
                "unlocked": 0,
                "percentage": 0
            }
        
        for achievement in self.achievements_data["achievements"].values():
            category = achievement["category"]
            if category in category_stats:
                category_stats[category]["total"] += 1
                if achievement["unlocked"]:
                    category_stats[category]["unlocked"] += 1
        
        for category_id, stats in category_stats.items():
            if stats["total"] > 0:
                stats["percentage"] = (stats["unlocked"] / stats["total"]) * 100
        
        return category_stats

    def record_conversion(self, conversion_type, file_size=0, success=True, night_time=False):
        try:
            type_str = str(conversion_type).lower()
            
            self.increment_stat("total_conversions")
            self.increment_stat("conversions_today")
            
            if night_time:
                self.increment_stat("night_conversions")
            
            formats_to_mark = []
            
            if "pdf_to_word" in type_str or "pdf_to_docx" in type_str:
                self.increment_stat("word_pdf_conversions")
                formats_to_mark.append("docx")
            elif "word_to_pdf" in type_str or "docx_to_pdf" in type_str:
                self.increment_stat("word_pdf_conversions")
                formats_to_mark.append("pdf")
            elif "image_to_pdf" in type_str or "jpg_to_pdf" in type_str or "png_to_pdf" in type_str:
                self.increment_stat("images_to_pdf")
                formats_to_mark.append("pdf")
            elif "compress" in type_str or "archive" in type_str:
                self.increment_stat("archives_created")
                if "zip" in type_str:
                    formats_to_mark.append("zip")
                elif "rar" in type_str:
                    formats_to_mark.append("rar")
                elif "tar" in type_str:
                    formats_to_mark.append("tar")
                    if "gz" in type_str or "gzip" in type_str or "tgz" in type_str:
                        formats_to_mark.append("gz")
                elif "gz" in type_str:
                    formats_to_mark.append("gz")
            
            if "image" in type_str:
                formats_to_mark.append("jpg")
                formats_to_mark.append("png")
            elif "jpg" in type_str or "jpeg" in type_str:
                formats_to_mark.append("jpg")
            elif "png" in type_str or "bmp" in type_str or "tiff" in type_str:
                formats_to_mark.append("png")
            elif "word" in type_str or "doc" in type_str:
                formats_to_mark.append("docx")
            elif "pdf" in type_str:
                formats_to_mark.append("pdf")
            
            unique_formats = set(formats_to_mark)
            for fmt in unique_formats:
                if fmt:
                    self.record_format_usage(fmt)
            
            if success:
                self.increment_stat("consecutive_success")
            else:
                self.update_stat("consecutive_success", 0)
            
            self.check_progression_achievements()
            
        except Exception as e:
            print(f"[ERROR] record_conversion: {e}")

    def check_progression_achievements(self):
        total = self.stats.get("total_conversions", 0)
        
        thresholds = [
            (1, "first_adventure"),
            (100, "apprentice"),
            (500, "steel_warrior"),
            (1000, "format_expert"),
            (5000, "platinum_master"),
            (10000, "file_industrial")
        ]
        
        for threshold, achievement_id in thresholds:
            if total >= threshold:
                self.check_achievement(achievement_id)

    def record_preview(self):
        self.increment_stat("previews_used")
        self.increment_stat("previews_today")
        self.check_achievement("visionary")

    def record_ocr_usage(self, pages):
        if pages > 0:
            self.increment_stat("ocr_pages", pages)
            self.check_achievement("all_seeing_eye")

    def record_compression(self, size_gb):
        if size_gb > 0:
            self.increment_stat("compressed_gb", size_gb)
            self.increment_stat("archives_created")
            self.check_achievement("titanic_compressor")
            self.check_achievement("royal_archivist")

    def record_protected_file_conversion(self, count=1, file_type="pdf"):
        """
        Records conversion of a file that REQUIRED a password (Master Key achievement).
        Must be called ONLY when the user provides the correct password.
        """
        print(f"[ACHIEVEMENTS] Recording protected file converted: {count} ({file_type})")
        self.increment_stat("protected_files_converted", count)
        
        if self.stats.get("protected_files_converted", 0) >= 50:
            self.unlock_achievement("master_key")

    def record_archive_protection(self, count=1, password_length=0, archive_format="zip"):
        """
        Records archive protection (Impenetrable Fortress achievement).
        Only works on ZIP/RAR with a complex password.
        """
        print(f"[ACHIEVEMENTS] Recording archive protection: {count}, Pwd len: {password_length}, Format: {archive_format}")
        
        # Only process ZIP and RAR for "Impenetrable Fortress"
        if archive_format.lower() in ["zip", "rar"]:
            if password_length >= 12:
                self.increment_stat("batch_protect_complex_count", count)
                
                if self.stats.get("batch_protect_complex_count", 0) >= 100:
                    self.unlock_achievement("impenetrable_fortress")

    def record_pdf_protection(self, files_count, password_length=0):
        """
        Records PDF protection (Data Guardian achievement).
        Removed: Master Key achievement (handled by record_protected_file_conversion).
        """
        print(f"[ACHIEVEMENTS] Recording PDF protection: {files_count} files")
        
        self.increment_stat("pdf_protected", files_count)
        
        if self.stats.get("pdf_protected", 0) >= 50:
            self.unlock_achievement("data_guardian")

    def record_batch_conversion(self, files_count):
        if files_count > self.stats.get("max_batch_files", 0):
            self.update_stat("max_batch_files", files_count)
        if files_count >= 500:
            self.check_achievement("dragon_breath")

    def record_pdf_split(self, pages_count):
        if pages_count > self.stats.get("max_pdf_split_pages", 0):
            self.update_stat("max_pdf_split_pages", pages_count)
        
        if pages_count >= 1000:
            self.check_achievement("division_blade")

    def record_pdf_merge(self, pages_count):
        if pages_count > self.stats.get("max_pdf_merge_pages", 0):
            self.update_stat("max_pdf_merge_pages", pages_count)
        
        if pages_count >= 500:
            self.check_achievement("eternal_librarian")

    # Advanced conversions tracking
    _ADV_TYPE_MAP = {
        # Documents (13 types)
        "txt_to_pdf":    ("adv_doc_conversions",   None,                    "adv_txt_to_pdf"),
        "rtf_to_pdf":    ("adv_doc_conversions",   None,                    "adv_rtf_to_pdf"),
        "txt_to_docx":   ("adv_doc_conversions",   None,                    "adv_txt_to_docx"),
        "rtf_to_docx":   ("adv_doc_conversions",   None,                    "adv_rtf_to_docx"),
        "csv_to_json":   ("adv_doc_conversions",   "adv_csv_json_conversions", "adv_csv_to_json"),
        "json_to_csv":   ("adv_doc_conversions",   "adv_csv_json_conversions", "adv_json_to_csv"),
        "xlsx_to_pdf":   ("adv_doc_conversions",   "adv_xlsx_to_pdf",       "adv_xlsx_to_pdf_flag"),
        "xlsx_to_json":  ("adv_doc_conversions",   None,                    "adv_xlsx_to_json"),
        "xlsx_to_csv":   ("adv_doc_conversions",   None,                    "adv_xlsx_to_csv"),
        "pptx_to_pdf":   ("adv_doc_conversions",   "adv_pptx_to_pdf",       "adv_pptx_to_pdf_flag"),
        "html_to_pdf":   ("adv_doc_conversions",   "adv_html_to_pdf",       "adv_html_to_pdf_flag"),
        "pdf_to_html":   ("adv_doc_conversions",   None,                    "adv_pdf_to_html"),
        "epub_to_pdf":   ("adv_doc_conversions",   "adv_epub_to_pdf",       "adv_epub_to_pdf_flag"),
        # Images (13 types unified image_to_* keys matching CATEGORY_MAP)
        "image_to_png":  ("adv_image_conversions", None,                    "adv_image_to_png"),
        "image_to_jpeg": ("adv_image_conversions", None,                    "adv_image_to_jpeg"),
        "image_to_jpg":  ("adv_image_conversions", None,                    "adv_image_to_jpg"),
        "image_to_bmp":  ("adv_image_conversions", None,                    "adv_image_to_bmp"),
        "image_to_heic": ("adv_image_conversions", "adv_heic_conversions",  "adv_image_to_heic"),
        "image_to_webp": ("adv_image_conversions", None,                    "adv_image_to_webp"),
        "image_to_tiff": ("adv_image_conversions", None,                    "adv_image_to_tiff"),
        "image_to_psd":  ("adv_image_conversions", None,                    "adv_image_to_psd"),
        "image_to_svg":  ("adv_image_conversions", None,                    "adv_image_to_svg"),
        "image_to_avif": ("adv_image_conversions", None,                    "adv_image_to_avif"),
        "image_to_j2k":  ("adv_image_conversions", None,                    "adv_image_to_j2k"),
        "image_to_dng":  ("adv_image_conversions", None,                    "adv_image_to_dng"),
        "image_to_ico":  ("adv_image_conversions", "adv_image_to_ico",      "adv_image_to_ico_flag"),
        # Video (9 types video_to_* keys matching CATEGORY_MAP)
        "video_to_mp4":  ("adv_video_conversions", None,                    "adv_video_to_mp4"),
        "video_to_webm": ("adv_video_conversions", None,                    "adv_video_to_webm"),
        "video_to_mkv":  ("adv_video_conversions", None,                    "adv_video_to_mkv"),
        "video_to_mov":  ("adv_video_conversions", None,                    "adv_video_to_mov"),
        "video_to_avi":  ("adv_video_conversions", None,                    "adv_video_to_avi"),
        "video_to_mp3":  ("adv_audio_conversions", "adv_video_to_audio",    "adv_video_to_mp3"),
        "video_to_wav":  ("adv_audio_conversions", "adv_video_to_audio",    "adv_video_to_wav"),
        "video_to_aac":  ("adv_audio_conversions", "adv_video_to_audio",    "adv_video_to_aac"),
        "video_to_flac": ("adv_audio_conversions", "adv_video_to_audio",    "adv_video_to_flac"),
        # Audio (6 types)
        "wav_to_mp3":    ("adv_audio_conversions", None,                    "adv_wav_to_mp3"),
        "mp3_to_wav":    ("adv_audio_conversions", None,                    "adv_mp3_to_wav"),
        "acc_to_mp3":    ("adv_audio_conversions", None,                    "adv_aac_to_mp3"),
        "mp3_to_acc":    ("adv_audio_conversions", None,                    "adv_mp3_to_aac"),
        "flac_to_mp3":   ("adv_audio_conversions", None,                    "adv_flac_to_mp3"),
        "ogg_to_mp3":    ("adv_audio_conversions", None,                    "adv_ogg_to_mp3"),
    }

    # 13 image type flags — one per image_to_* conversion type
    _ADV_IMG_TYPE_FLAGS = [
        "adv_image_to_png",  "adv_image_to_jpeg", "adv_image_to_jpg",
        "adv_image_to_bmp",  "adv_image_to_heic", "adv_image_to_webp",
        "adv_image_to_tiff", "adv_image_to_psd",  "adv_image_to_svg",
        "adv_image_to_avif", "adv_image_to_j2k",  "adv_image_to_dng",
        "adv_image_to_ico_flag",
    ]
    # 9 video type flags — video_to_mp4/webm/mkv/mov/avi + video_to_mp3/wav/aac/flac
    _ADV_VID_TYPE_FLAGS = [
        "adv_video_to_mp4",  "adv_video_to_webm", "adv_video_to_mkv",
        "adv_video_to_mov",  "adv_video_to_avi",
        "adv_video_to_mp3",  "adv_video_to_wav",  "adv_video_to_aac",
        "adv_video_to_flac",
    ]

    _TPL_CATEGORIES = {
        "Conversion PDF→Word", "Conversion Word→PDF", "Conversion Images→PDF",
        "Fusion PDF", "Fusion Word", "Division PDF",
        "Protection PDF", "Compression", "Préréglages de qualité",
    }

    def record_template_created(self, template_type: str = ""):
        """Call when a template is successfully created."""
        self.increment_stat("tpl_created_total")
        self.check_achievement("tpl_architecte")
        self.check_achievement("tpl_maitre_presets")
        self._recompute_tpl_categories(new_type=template_type)
        self.check_achievement("tpl_collectionneur_workflows")

    def record_template_applied(self, template_id: str = "", template_type: str = ""):
        """Call when a template is applied."""
        self.increment_stat("tpl_applied_total")
        self.check_achievement("tpl_automatiste")

        key = f"tpl_usage_{template_id}"
        self.increment_stat(key)
        current_max = self.stats.get("tpl_single_max_applied", 0)
        this_count  = self.stats.get(key, 0)
        if this_count > current_max:
            self.update_stat("tpl_single_max_applied", this_count)
        self.check_achievement("tpl_le_rituel")

        session_key = f"tpl_session_{template_type}"
        if self.stats.get(session_key, 0) == 0:
            self.update_stat(session_key, 1)
            used = sum(1 for cat in self._TPL_CATEGORIES
                       if self.stats.get(f"tpl_session_{cat}", 0) > 0)
            self.update_stat("tpl_types_session", used)
        self.check_achievement("tpl_polyvalent")

    def record_template_edited(self):
        """Call when a template is edited via TemplateEditorDialog."""
        self.increment_stat("tpl_edited_total")
        self.check_achievement("tpl_perfectionniste")

    def record_template_exported(self):
        """Call when templates are exported (single or all)."""
        self.increment_stat("tpl_exported")
        self.check_achievement("tpl_archiviste")

    def record_template_imported(self, count: int = 1):
        """Call when templates are imported."""
        if count > 0:
            self.increment_stat("tpl_imported")
            self.check_achievement("tpl_importateur")

    def record_template_default_set(self, template_manager=None):
        """Call when a template is marked as default. Recomputes the defaults count."""
        if template_manager is None:
            return
        try:
            defaults = sum(
                1 for tpl in template_manager.current_templates.values()
                if tpl['config'].get('is_default', False)
            )
            ach = self.achievements_data["achievements"].get("tpl_reference_absolue")
            if ach:
                ach["progress"] = defaults
            self.check_achievement("tpl_reference_absolue")
        except Exception as e:
            print(f"[TPL ACH] record_template_default_set error: {e}")

    def _recompute_tpl_categories(self, new_type: str = ""):
        """
        Recompute how many template categories are covered.
        We track covered categories in stats (one flag per category) so we
        never need to query the templates table in a different DB file.
        """
        try:
            from templates import TemplateManager
            if new_type:
                normalized = TemplateManager.normalize_type(new_type)
                if normalized in self._TPL_CATEGORIES:
                    stat_key = "tpl_cat_" + normalized.replace(' ', '_').replace('→', '_').replace('é', 'e').replace('è', 'e').replace('ê', 'e').replace('â', 'a')
                    self.update_stat(stat_key, 1)

            covered = 0
            for cat in self._TPL_CATEGORIES:
                stat_key = "tpl_cat_" + cat.replace(' ', '_').replace('→', '_').replace('é', 'e').replace('è', 'e').replace('ê', 'e').replace('â', 'a')
                if self.stats.get(stat_key, 0) >= 1:
                    covered += 1

            ach = self.achievements_data["achievements"].get("tpl_collectionneur_workflows")
            if ach:
                ach["progress"] = covered
            print(f"[TPL ACH] tpl_collectionneur_workflows progress: {covered}/9")
        except Exception as e:
            print(f"[TPL ACH] _recompute_tpl_categories error: {e}")

    def record_advanced_conversion(self, conversion_type: str, success: bool = True):
        """
        Called from _ConversionWorker for every advanced conversion attempt.
        Updates all relevant stats and checks concerned achievements.
        Thread-safe: stats update + DB writes happen here (worker thread),
        signal emission is deferred to the main thread via QMetaObject.
        """
        if not success:
            self.update_stat("consecutive_success", 0)
            self.save_stats()
            return

        mapping = self._ADV_TYPE_MAP.get(conversion_type)
        if not mapping:
            print(f"[ADV ACH] Unknown conversion type: {conversion_type}")
            return

        cat_stat, specific_stat, flag_stat = mapping

        self.increment_stat("adv_total_conversions")
        # Category counter
        self.increment_stat(cat_stat)
        if specific_stat:
            self.increment_stat(specific_stat)
        if flag_stat and self.stats.get(flag_stat, 0) == 0:
            self.update_stat(flag_stat, 1)

        img_types_used = sum(1 for f in self._ADV_IMG_TYPE_FLAGS if self.stats.get(f, 0) > 0)
        self.update_stat("adv_image_types_used", img_types_used)
        vid_types_used = sum(1 for f in self._ADV_VID_TYPE_FLAGS if self.stats.get(f, 0) > 0)
        self.update_stat("adv_video_types_used", vid_types_used)

        from datetime import datetime as _dt
        _hour = _dt.now().hour
        _night = 0 <= _hour < 6

        self.increment_stat("total_conversions")
        self.increment_stat("conversions_today")
        self.increment_stat("consecutive_success")

        if _night:
            self.increment_stat("night_conversions")

        # Mark the output format as used for universal_traveler
        _ext = conversion_type.split("_to_", 1)[-1].lower() if "_to_" in conversion_type else ""
        _ext_norm = {
            "jpeg": "jpg", "doc": "docx", "tiff": "png", "bmp": "png",
            "tgz": "gz",   "gzip": "gz",  "webp": "png", "gif": "png",
            "heic": "png", "psd": "png",  "svg": "png",  "avif": "png",
            "j2k": "png",  "dng": "png",  "ico": "png",
            "webm": "mp4", "mkv": "mp4",  "mov": "mp4",  "avi": "mp4",
            "mp3": "mp3",  "wav": "mp3",  "aac": "mp3",  "flac": "mp3",
        }.get(_ext, _ext)
        if _ext_norm in ("pdf", "docx", "jpg", "png", "zip", "rar", "tar", "gz"):
            self.record_format_usage(_ext_norm)

        _batch = self.stats.get("recent_batch_files", 0) + 1
        self.update_stat("recent_batch_files", _batch)

        self.save_stats()

        # Achievement checks
        self.check_progression_achievements()

        if _night:
            self.check_achievement("night_owl")

        self.check_achievement("absolute_perfection")

        adv_ids = [
            "adv_data_architect", "adv_csv_sorcier", "adv_office_slayer",
            "adv_web_harvester", "adv_bibliotheque", "adv_icon_forge",
            "adv_format_nomade", "adv_heic_hunter", "adv_pixel_perfect",
            "adv_extracteur_pro", "adv_codec_master", "adv_studio_underground",
            "adv_all_rounder", "adv_la_machine", "adv_collectionneur",
        ]
        for ach_id in adv_ids:
            self.check_achievement(ach_id)

    def record_format_usage(self, format_type):
        try:
            norm = {
                'jpeg': 'jpg',
                'doc': 'docx',
                'tiff': 'png',
                'bmp': 'png',
                'tar.gz': 'gz',
                'tgz': 'gz',
                'gzip': 'gz',
                'zip': 'zip',
                'rar': 'rar',
                'tar': 'tar',
                'png': 'png',
                'jpg': 'jpg',
                'pdf': 'pdf',
                'docx': 'docx'
            }
            fmt = norm.get(format_type.lower(), format_type.lower())
            
            if fmt == 'gz' and format_type.lower() in ['tar.gz', 'tgz']:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('UPDATE used_formats SET used = TRUE WHERE format = ?', ('tar',))
                conn.commit()
                conn.close()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO used_formats (format, used) VALUES (?, TRUE)', (fmt,))
            conn.commit()
            conn.close()
            
            self.update_all_progress()
            self.check_all_formats_used()
        except Exception as e:
            print(f"Error recording format {format_type}: {e}")

    def check_all_formats_used(self):
        try:
            required_formats = ["pdf", "docx", "jpg", "png", "zip", "rar", "tar", "gz"]
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            all_ok = True
            missing = []
            
            for fmt in required_formats:
                cursor.execute('SELECT used FROM used_formats WHERE format = ?', (fmt,))
                result = cursor.fetchone()
                
                if not result or result[0] == 0:
                    all_ok = False
                    missing.append(fmt)
                else:
                    pass
            
            conn.close()
            
            if all_ok:
                print(f"✅ SUCCESS: All formats validated ({len(required_formats)}/{len(required_formats)}). Unlocking Universal Traveller!")
                self.check_achievement("universal_traveler")
            else:
                print(f"⏳ Waiting... Missing formats: {missing}")
        
        except Exception as e:
            print(f"Critical error check_all_formats_used: {e}")

    def record_app_launch(self):
        try:
            today = datetime.now().date().isoformat()
            last_launch = self.stats.get("last_launch_date")
            
            if last_launch != today:
                self.stats["last_launch_date"] = today
                
                self.save_daily_stats()
                
                self.stats["conversions_today"] = 0
                self.stats["previews_today"] = 0
                self.stats["dark_mode_today"] = 0
                
                self.increment_stat("unique_days")
                
                self.check_achievement("eternal_loyalty")
        
        except Exception as e:
            print(f"Error recording app launch: {e}")

    def save_daily_stats(self):
        try:
            yesterday = (datetime.now().date()).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT OR REPLACE INTO daily_stats 
            (date, conversions, previews, dark_mode_minutes)
            VALUES (?, ?, ?, ?)
            ''', (
                yesterday,
                self.stats.get("conversions_today", 0),
                self.stats.get("previews_today", 0),
                self.stats.get("dark_mode_today", 0)
            ))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            print(f"Error saving daily stats: {e}")

    def get_daily_stats(self, days=30):
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days-1)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT date, conversions, previews, dark_mode_minutes
            FROM daily_stats
            WHERE date BETWEEN ? AND ?
            ORDER BY date
            ''', (start_date.isoformat(), end_date.isoformat()))
            
            stats = cursor.fetchall()
            conn.close()
            
            return stats
        
        except Exception as e:
            print(f"Error retrieving daily stats: {e}")
            return []

    def set_language(self, language: str) -> None:
        """Sync language with the app-wide TranslationManager."""
        self.current_language = language
        self.translation_manager.set_language(language)

    def translate_text(self, text, language=None):
        if language is not None:
            self.translation_manager.set_language(language)
        return self.translation_manager.translate_text(text)

    def check_speed_conversion(self, files_count, time_seconds):
        if files_count >= 50 and time_seconds <= 300:
            self.check_achievement("flash_gordon")
