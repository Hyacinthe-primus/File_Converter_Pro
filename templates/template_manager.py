"""
TemplateManager

Centralized manager for conversion presets.
Extracted from templates.py for better code organization.

Responsibilities:
    - CRUD operations for templates in database
    - Dynamic application of settings based on template type
    - Import/Export functionality (JSON)

"""

import json
import time
from datetime import datetime

class TemplateManager:
    """Centralized template manager"""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.current_templates = {}
        self.load_templates()

    def load_templates(self):
        """Load all templates from the database"""
        templates = self.db_manager.get_templates()
        self.current_templates = {}
        
        for template in templates:
            template_id, name, template_type, config_data, created_at, last_used = template
            self.current_templates[template_id] = {
                'name': name,
                'type': template_type,
                'config': json.loads(config_data),
                'created_at': created_at,
                'last_used': last_used
            }

    def get_template_by_id(self, template_id):
        """Retrieve a template by its ID"""
        return self.current_templates.get(template_id)

    _TYPE_NORMALIZE = {
        'PDF to Word Conversion':   'Conversion PDF→Word',
        'Word to PDF Conversion':   'Conversion Word→PDF',
        'Images to PDF Conversion': 'Conversion Images→PDF',
        'PDF Merge':                'Fusion PDF',
        'Word Merge':               'Fusion Word',
        'PDF Split':                'Division PDF',
        'PDF Protection':           'Protection PDF',
        'Quality Presets':          'Optimisation de fichiers',
        'Office Optimization':      'Optimisation de fichiers',
    }

    @classmethod
    def normalize_type(cls, t):
        """Normalize template type to French canonical form regardless of language."""
        return cls._TYPE_NORMALIZE.get(t, t)

    def get_templates_by_type(self, template_type):
        """Retrieve all templates of a specific type"""
        template_type = self.normalize_type(template_type)
        return {
            template_id: template
            for template_id, template in self.current_templates.items()
            if self.normalize_type(template['type']) == template_type
        }

    def apply_template(self, template_id, parent_app):
        """Apply a template — sets exactly the configuration fields that app.py reads."""
        template = self.get_template_by_id(template_id)
        if not template:
            return False

        try:
            self.db_manager.update_template_usage(template_id)
            cfg = template['config']
            t   = template['type']

            _type_normalize = {
                # EN
                'PDF to Word Conversion':   'Conversion PDF→Word',
                'Word to PDF Conversion':   'Conversion Word→PDF',
                'Images to PDF Conversion': 'Conversion Images→PDF',
                'PDF Merge':                'Fusion PDF',
                'Word Merge':               'Fusion Word',
                'PDF Split':                'Division PDF',
                'PDF Protection':           'Protection PDF',
                'File optimization':          'Préréglages de qualité',
                # FR (pass-through)
                'Conversion PDF→Word':      'Conversion PDF→Word',
                'Conversion Word→PDF':      'Conversion Word→PDF',
                'Conversion Images→PDF':    'Conversion Images→PDF',
                'Fusion PDF':               'Fusion PDF',
                'Fusion Word':              'Fusion Word',
                'Division PDF':             'Division PDF',
                'Protection PDF':           'Protection PDF',
                'Compression':              'Compression',
                'Optimisation de fichiers':  'Optimisation de fichiers',
            }
            t = _type_normalize.get(t, t)

            if not hasattr(parent_app, 'active_templates'):
                parent_app.active_templates = {}

            if t == "Conversion PDF→Word":
                mode_map = {
                    "Conserver les images et la mise en page":  "with_images",
                    "Texte brut uniquement":                    "text_only",
                    "Texte complet (texte + texte des images)": "text_with_image_text",
                    "Keep images and layout":                   "with_images",
                    "Plain text only":                          "text_only",
                    "Full text (text + image text)":            "text_with_image_text",
                    "with_images":          "with_images",
                    "text_only":            "text_only",
                    "text_with_image_text": "text_with_image_text",
                }
                _mode = mode_map.get(cfg.get('mode', ''), "with_images")
                parent_app.config["pdf_to_word_mode"] = _mode
                parent_app.active_templates['pdf_to_word'] = {'mode': _mode}
                parent_app.config_manager.save_config(parent_app.config)

            elif t == "Conversion Word→PDF":
                mode_map = {
                    "Conserver toute la mise en page": "preserve_all",
                    "Texte uniquement":                "text_only",
                    "Preserve all layout":             "preserve_all",
                    "Text only":                       "text_only",
                    "preserve_all":                    "preserve_all",
                    "text_only":                       "text_only",
                }
                _mode = mode_map.get(cfg.get('mode', ''), "preserve_all")
                parent_app.active_templates['word_to_pdf'] = {
                    'mode':             _mode,
                    'quality':          cfg.get('quality', 'Standard (150 DPI)'),
                    'compress_images':  cfg.get('compress_images', True),
                    'include_metadata': cfg.get('include_metadata', True),
                }
                parent_app.config["word_to_pdf_mode"] = _mode
                parent_app.config_manager.save_config(parent_app.config)

            elif t == "Conversion Images→PDF":
                separate = cfg.get('separate', False)
                parent_app.config['separate_image_pdfs'] = separate
                parent_app.config_manager.save_config(parent_app.config)
                parent_app.active_templates['images_to_pdf'] = {'separate': separate}

            elif t == "Fusion PDF":
                _order_map = {
                    "Alphabétique (A→Z)":            "alpha_az",
                    "Alphabétique (Z→A)":            "alpha_za",
                    "Numérique (1→9)":               "num_asc",
                    "Numérique (9→1)":               "num_desc",
                    "Date (ancien→nouveau)":          "date_asc",
                    "Date (nouveau→ancien)":          "date_desc",
                    "Manuel (glisser-déposer)":       "manual",
                    "Ordre actuel (liste principale)":"current",
                    "Alphabetical (A→Z)":            "alpha_az",
                    "Alphabetical (Z→A)":            "alpha_za",
                    "Numeric (1→9)":                 "num_asc",
                    "Numeric (9→1)":                 "num_desc",
                    "Date (oldest→newest)":           "date_asc",
                    "Date (newest→oldest)":           "date_desc",
                    "Manual (drag and drop)":         "manual",
                    "Current order (main list)":      "current",
                }
                parent_app.active_templates['pdf_merge'] = {
                    'merge_order_key': _order_map.get(cfg.get('merge_order', ''), 'current'),
                    'merge_order_label': cfg.get('merge_order', ''),
                }

            elif t == "Fusion Word":
                _order_map = {
                    "Alphabétique (A→Z)":            "alpha_az",
                    "Alphabétique (Z→A)":            "alpha_za",
                    "Numérique (1→9)":               "num_asc",
                    "Numérique (9→1)":               "num_desc",
                    "Date (ancien→nouveau)":          "date_asc",
                    "Date (nouveau→ancien)":          "date_desc",
                    "Manuel (glisser-déposer)":       "manual",
                    "Ordre actuel (liste principale)":"current",
                    "Alphabetical (A→Z)":            "alpha_az",
                    "Alphabetical (Z→A)":            "alpha_za",
                    "Numeric (1→9)":                 "num_asc",
                    "Numeric (9→1)":                 "num_desc",
                    "Date (oldest→newest)":           "date_asc",
                    "Date (newest→oldest)":           "date_desc",
                    "Manual (drag and drop)":         "manual",
                    "Current order (main list)":      "current",
                }
                parent_app.active_templates['word_merge'] = {
                    'merge_order_key': _order_map.get(cfg.get('merge_order', ''), 'current'),
                    'merge_order_label': cfg.get('merge_order', ''),
                }

            elif t == "Division PDF":
                _method_norm = {
                    'Par pages':        'Par pages',
                    'Toutes les pages': 'Toutes les pages',
                    'Plage de pages':   'Plage de pages',
                    'By pages':         'Par pages',
                    'All pages':        'Toutes les pages',
                    'Page range':       'Plage de pages',
                }
                _method = _method_norm.get(cfg.get('split_method', 'Par pages'),
                                           cfg.get('split_method', 'Par pages'))
                parent_app.active_templates['pdf_split'] = {
                    'split_method_label': _method,
                    'pages_per_file':     cfg.get('pages_per_file', 1),
                }

            elif t == "Protection PDF":
                _mode_norm = {
                    'Basique (restrictions uniquement)':     'basic',
                    'Avancé (mot de passe + restrictions)':  'advanced',
                    'Basique (ouvrir)':                      'basic',
                    'Avancé (ouvrir + modifications)':       'advanced',
                    'Basic (restrictions only)':             'basic',
                    'Advanced (password + restrictions)':    'advanced',
                    'basic':    'basic',
                    'advanced': 'advanced',
                }
                parent_app.active_templates['pdf_protection'] = {
                    'mode':               _mode_norm.get(cfg.get('mode', cfg.get('protection_level', 'basic')), 'basic'),
                    'allow_printing':     cfg.get('allow_printing', True),
                    'allow_copying':      cfg.get('allow_copying', True),
                    'allow_modifications': cfg.get('allow_modifications', False),
                }

            elif t == "Compression":
                _fmt = {'ZIP':'ZIP','RAR':'RAR','TAR.GZ':'TAR.GZ','TAR':'TAR'}
                _lvl = {
                    'Normal':'Normal',
                    'Haute compression':'Haute compression',
                    'Compression maximale':'Compression maximale',
                    'High compression':'Haute compression',
                    'Maximum compression':'Compression maximale',
                }
                parent_app.active_templates['compression'] = {
                    'format':           _fmt.get(cfg.get('format','ZIP'), cfg.get('format','ZIP')),
                    'compression_level':_lvl.get(cfg.get('compression_level','Normal'), cfg.get('compression_level','Normal')),
                    'encrypt':          cfg.get('encrypt', False),
                    'delete_originals': cfg.get('delete_originals', False),
                    'split_archive':    cfg.get('split_archive', False),
                    'split_size':       cfg.get('split_size', 0),
                }

            elif t == "Optimisation de fichiers":
                _mode_map = {
                    "Compression  –  réduit la taille du fichier": 0,
                    "Nettoyage  –  supprime uniquement les métadonnées": 1,
                    "Compression + Nettoyage  –  recommandé": 2,
                    "Compression  —  reduces file size": 0,
                    "Cleaning  —  removes metadata only": 1,
                    "Compression + Cleaning  —  recommended": 2,
                    "compression": 0, "nettoyage": 1, "les deux": 2,
                    0: 0, 1: 1, 2: 2,
                }
                parent_app.active_templates['office_optimization'] = {
                    'optimization_type': _mode_map.get(cfg.get('optimization_type', 2), 2),
                    'quality_level':     cfg.get('quality_level', 1),
                    'remove_metadata':   cfg.get('remove_metadata', True),
                    'compress_images':   cfg.get('compress_images', True),
                    'keep_backup':       cfg.get('keep_backup', True),
                }

            return True

        except Exception as e:
            print(f"Error applying template: {e}")
            return False

    def create_template_from_current_settings(self, name, template_type, parent_app):
        """Create a template from the current settings"""
        config = {}
        
        if template_type == "Conversion PDF→Word":
            mode_map = {
                "with_images": "Conserver les images et la mise en page",
                "text_only": "Texte brut uniquement",
                "text_with_image_text": "Texte complet (texte + texte des images)"
            }
            quality_map = {
                "high": "Haute qualité",
                "standard": "Qualité standard",
                "optimized": "Optimisé pour la taille"
            }
            
            config = {
                'mode': mode_map.get(parent_app.config.get("pdf_to_word_mode", "with_images"), "Conserver les images et la mise en page"),
                'quality': quality_map.get(parent_app.config.get("conversion_quality", "standard"), "Qualité standard"),
                'keep_bookmarks': True,
                'extract_images': False
            }
            
        elif template_type == "Conversion Word→PDF":
            config = {
                'page_format': "A4",
                'orientation': "Portrait",
                'quality': "Standard (150 DPI)",
                'include_metadata': True,
                'compress': True
            }
            
        elif template_type == "Conversion Images→PDF":
            config = {
                'orientation': "Portrait",
                'quality': "Standard (150 DPI)",
                'margin': 20,
                'compress_images': True,
                'keep_original_order': True
            }
            
        elif template_type == "Fusion PDF":
            config = {
                'merge_order': "Alphabétique",
                'merge_bookmarks': True,
                'remove_duplicates': False,
                'add_page_numbers': False,
                'name_template': 'fusion_{date}_{heure}'
            }
            
        elif template_type == "Fusion Word":
            config = {
                'merge_order': "Alphabétique",
                'keep_formatting': True,
                'add_page_breaks': True,
                'name_template': 'fusion_word_{date}_{heure}'
            }
            
        elif template_type == "Division PDF":
            config = {
                'split_method': "Par pages",
                'pages_per_file': 1,
                'keep_bookmarks': True,
                'name_template': 'page_{page}'
            }
            
        elif template_type == "Protection PDF":
            config = {
                'protection_level': "Basique (ouvrir)",
                'allow_printing': True,
                'allow_copying': True,
                'allow_modifications': False
            }
            
        elif template_type == "Préréglages de qualité":
            quality_map = {
                "high": "Haute qualité",
                "standard": "Qualité standard",
                "compressed": "Compressé"
            }
            
            compression_map = {
                "normal": "Normal",
                "high": "Haute compression",
                "maximum": "Compression maximale"
            }
            
            config = {
                'preset_type': "Qualité standard",
                'compression': 50,
                'target_format': "PDF",
                'description': "Configuration par défaut",
                'quality': quality_map.get(parent_app.config.get("conversion_quality", "standard"), "Qualité standard"),
                'compression_level': compression_map.get(parent_app.config.get("compression_level", "normal"), "Normal")
            }
        
        self.db_manager.save_template(name, template_type, config)
        self.load_templates()
        
        return config

    def apply_pdf_to_word_template(self, config, parent_app):
        """Apply a PDF to Word conversion template"""
        mode_map = {
            "Conserver les images et la mise en page": "with_images",
            "Texte brut uniquement": "text_only",
            "Texte complet (texte + texte des images)": "text_with_image_text"
        }
        
        mode = config.get('mode', 'Conserver les images et la mise en page')
        parent_app.config["pdf_to_word_mode"] = mode_map.get(mode, "with_images")
        
        quality_map = {
            "Haute qualité": "high",
            "Qualité standard": "standard",
            "Optimisé pour la taille": "optimized"
        }
        quality = config.get('quality', 'Qualité standard')
        parent_app.config["conversion_quality"] = quality_map.get(quality, "standard")
        
        parent_app.config_manager.save_config(parent_app.config)

    def apply_word_to_pdf_template(self, config, parent_app):
        """Apply a Word to PDF conversion template"""
        if not hasattr(parent_app, 'active_templates'):
            parent_app.active_templates = {}
        
        parent_app.active_templates['word_to_pdf'] = config
        
        page_format_map = {
            "A4": "a4",
            "Lettre": "letter",
            "A3": "a3",
            "Personnalisé": "custom"
        }
        
        orientation_map = {
            "Portrait": "portrait",
            "Paysage": "landscape"
        }
        
        quality_map = {
            "Haute (300 DPI)": 300,
            "Standard (150 DPI)": 150,
            "Basse (72 DPI)": 72
        }
        
        config['page_format_value'] = page_format_map.get(config.get('page_format', 'A4'), 'a4')
        config['orientation_value'] = orientation_map.get(config.get('orientation', 'Portrait'), 'portrait')
        config['quality_value'] = quality_map.get(config.get('quality', 'Standard (150 DPI)'), 150)

    def apply_pdf_merge_template(self, config, parent_app):
        """Apply a PDF merge template"""
        if not hasattr(parent_app, 'active_templates'):
            parent_app.active_templates = {}
        
        parent_app.active_templates['pdf_merge'] = config
        
        name_template = config.get('name_template', 'fusion_{date}_{heure}')
        if '{date}' in name_template:
            name_template = name_template.replace('{date}', datetime.now().strftime('%Y%m%d'))
        if '{heure}' in name_template:
            name_template = name_template.replace('{heure}', datetime.now().strftime('%H%M%S'))
        if '{timestamp}' in name_template:
            name_template = name_template.replace('{timestamp}', str(int(time.time())))
        
        config['processed_name'] = name_template

    def apply_quality_template(self, config, parent_app):
        """Apply a quality preset template"""
        quality_map = {
            "Haute qualité": "high",
            "Qualité standard": "standard",
            "Compressé": "compressed"
        }
        
        parent_app.config["conversion_quality"] = quality_map.get(config.get('preset_type', 'Qualité standard'), "standard")
        parent_app.config["compression_level"] = config.get('compression', 50)
        parent_app.config_manager.save_config(parent_app.config)

    def get_default_template(self, template_type):
        """Return the (id, template) of the default template for a given type, or (None, None)."""
        template_type = self.normalize_type(template_type)
        for tid, tpl in self.current_templates.items():
            if self.normalize_type(tpl['type']) == template_type:
                if tpl['config'].get('is_default', False):
                    return tid, tpl
        return None, None

    def set_default_template(self, template_id, template_type):
        """Mark template_id as default for its type, unset all others of the same type."""
        template_type = self.normalize_type(template_type)
        for tid, tpl in self.current_templates.items():
            if self.normalize_type(tpl['type']) == template_type:
                was_default = tpl['config'].get('is_default', False)
                should_be   = (tid == template_id)
                if was_default != should_be:
                    tpl['config']['is_default'] = should_be
                    import json
                    self.db_manager.update_template_config(tid, json.dumps(tpl['config']))

    def delete_template(self, template_id):
        """Delete a template"""
        self.db_manager.delete_template(template_id)
        self.load_templates()

    def export_templates(self, filepath):
        """Export all templates to a JSON file"""
        templates_data = []
        
        for template_id, template in self.current_templates.items():
            templates_data.append({
                'id': template_id,
                'name': template['name'],
                'type': template['type'],
                'config': template['config'],
                'created_at': template['created_at'],
                'last_used': template['last_used']
            })
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(templates_data, f, indent=2, ensure_ascii=False)
        
        return len(templates_data)

    def import_templates(self, filepath):
        """Import templates from a JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                templates_data = json.load(f)
            
            imported_count = 0
            for template_data in templates_data:
                existing_templates = self.db_manager.get_templates()
                name_exists = any(t[1] == template_data['name'] for t in existing_templates)
                
                if not name_exists:
                    self.db_manager.save_template(
                        template_data['name'],
                        template_data['type'],
                        template_data['config']
                    )
                    imported_count += 1
            
            self.load_templates()
            return imported_count
            
        except Exception as e:
            print(f"Error importing templates: {e}")
            return 0