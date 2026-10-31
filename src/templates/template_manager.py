"""
TemplateManager

Centralized manager for conversion presets.
Extracted from templates.py for better code organization.

Responsibilities:
    - CRUD operations for templates in database
    - Dynamic application of settings based on template type
    - Import/Export functionality

"""

import json

from . import semantic_keys as sk
from .frequent_configs import FrequentConfigTracker


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
                "name": name,
                "type": template_type,
                "config": json.loads(config_data),
                "created_at": created_at,
                "last_used": last_used,
            }

    def get_template_by_id(self, template_id):
        """Retrieve a template by its ID"""
        return self.current_templates.get(template_id)

    @classmethod
    def normalize_type(cls, t):
        """Return the legacy storage type for any semantic/legacy type value."""
        return sk.legacy_type(t)

    def get_templates_by_type(self, template_type):
        """Retrieve all templates of a specific type"""
        template_type = self.normalize_type(template_type)
        return {
            template_id: template
            for template_id, template in self.current_templates.items()
            if self.normalize_type(template["type"]) == template_type
        }

    def apply_template(self, template_id, parent_app):
        """Apply a template - sets exactly the configuration fields that app.py reads."""
        template = self.get_template_by_id(template_id)
        if not template:
            return False

        try:
            self.db_manager.update_template_usage(template_id)
            template_type = sk.normalize_type(template["type"])
            cfg = sk.normalize_config(template_type, template["config"])

            if not hasattr(parent_app, "active_templates"):
                parent_app.active_templates = {}

            if template_type == sk.PDF_TO_WORD:
                parent_app.config["pdf_to_word_mode"] = cfg["mode"]
                parent_app.active_templates["pdf_to_word"] = {"mode": cfg["mode"]}
                parent_app.config_manager.save_config(parent_app.config)

            elif template_type == sk.WORD_TO_PDF:
                parent_app.active_templates["word_to_pdf"] = {
                    "mode": cfg["mode"],
                    "quality": sk.quality_legacy_label(cfg["quality"]),
                    "compress_images": cfg["compress_images"],
                    "include_metadata": cfg["include_metadata"],
                }
                parent_app.config["word_to_pdf_mode"] = cfg["mode"]
                parent_app.config_manager.save_config(parent_app.config)

            elif template_type == sk.IMAGES_TO_PDF:
                parent_app.config["separate_image_pdfs"] = cfg["separate"]
                parent_app.config_manager.save_config(parent_app.config)
                parent_app.active_templates["images_to_pdf"] = {"separate": cfg["separate"]}

            elif template_type in (sk.PDF_MERGE, sk.WORD_MERGE):
                key = "pdf_merge" if template_type == sk.PDF_MERGE else "word_merge"
                parent_app.active_templates[key] = {
                    "merge_order_key": cfg["merge_order"],
                    "merge_order_label": sk.merge_order_legacy_label(cfg["merge_order"]),
                }

            elif template_type == sk.PDF_SPLIT:
                parent_app.active_templates["pdf_split"] = {
                    "split_method_key": cfg["split_method"],
                    "split_method_label": sk.split_method_legacy_label(cfg["split_method"]),
                    "pages_per_file": cfg["pages_per_file"],
                }

            elif template_type == sk.PDF_PROTECTION:
                parent_app.active_templates["pdf_protection"] = {
                    "mode": cfg["protection_level"],
                    "allow_printing": cfg["allow_printing"],
                    "allow_copying": cfg["allow_copying"],
                    "allow_modifications": cfg["allow_modifications"],
                }

            elif template_type == sk.COMPRESSION:
                parent_app.active_templates["compression"] = {
                    "format": sk.archive_format_legacy(cfg["format"]),
                    "compression_level": sk.compression_level_legacy_label(cfg["compression_level"]),
                    "encrypt": cfg["encrypt"],
                    "delete_originals": cfg["delete_originals"],
                    "split_archive": cfg["split_archive"],
                    "split_size": cfg["split_size"],
                }

            elif template_type == sk.FILE_OPTIMIZATION:
                parent_app.active_templates["office_optimization"] = {
                    "optimization_type": sk.optimization_type_value(cfg["optimization_type"]),
                    "quality_level": cfg["quality_level"],
                    "remove_metadata": cfg["remove_metadata"],
                    "compress_images": cfg["compress_images"],
                    "keep_backup": cfg["keep_backup"],
                }

            return True

        except Exception as e:
            print(f"Error applying template: {e}")
            return False

    def create_template_from_current_settings(self, name, template_type, parent_app):
        """Create a semantic template from the current application settings."""
        template_type = sk.normalize_type(template_type)
        app_config = getattr(parent_app, "config", {})

        if template_type == sk.PDF_TO_WORD:
            config = sk.normalize_config(
                template_type,
                {
                    "mode": app_config.get("pdf_to_word_mode", sk.MODE_WITH_IMAGES),
                    "quality": app_config.get("conversion_quality", "standard"),
                },
            )
        elif template_type == sk.WORD_TO_PDF:
            config = sk.normalize_config(
                template_type,
                {
                    "mode": app_config.get("word_to_pdf_mode", sk.MODE_PRESERVE_ALL),
                    "quality": app_config.get("conversion_quality", "standard"),
                },
            )
        elif template_type == sk.IMAGES_TO_PDF:
            config = sk.normalize_config(
                template_type,
                {"separate": app_config.get("separate_image_pdfs", False)},
            )
        elif template_type == sk.PDF_MERGE:
            config = sk.normalize_config(
                template_type,
                {"merge_order": sk.ORDER_CURRENT, "name_template": "fusion_{date}_{hour}"},
            )
        elif template_type == sk.WORD_MERGE:
            config = sk.normalize_config(
                template_type,
                {"merge_order": sk.ORDER_CURRENT, "name_template": "fusion_word_{date}_{hour}"},
            )
        elif template_type == sk.PDF_SPLIT:
            config = sk.normalize_config(
                template_type,
                {"split_method": sk.SPLIT_BY_PAGES, "name_template": "page_{page}"},
            )
        elif template_type == sk.PDF_PROTECTION:
            config = sk.normalize_config(
                template_type,
                {"protection_level": sk.PROTECTION_BASIC},
            )
        elif template_type == sk.COMPRESSION:
            config = sk.normalize_config(
                template_type,
                {"format": sk.FORMAT_ZIP, "compression_level": sk.LEVEL_NORMAL},
            )
        elif template_type == sk.FILE_OPTIMIZATION:
            config = sk.normalize_config(
                template_type,
                {"optimization_type": sk.OPTIMIZATION_BOTH, "quality_level": 1},
            )
        else:
            config = {}

        self.db_manager.save_template(name, self.normalize_type(template_type), config)
        self.load_templates()
        return config

    def get_default_template(self, template_type):
        """Return the (id, template) of the default template for a given type, or (None, None)."""
        template_type = self.normalize_type(template_type)
        for tid, tpl in self.current_templates.items():
            if self.normalize_type(tpl["type"]) == template_type:
                if tpl["config"].get("is_default", False):
                    return tid, tpl
        return None, None

    def set_default_template(self, template_id, template_type):
        """Mark template_id as default for its type, unset all others of the same type."""
        template_type = self.normalize_type(template_type)
        for tid, tpl in self.current_templates.items():
            if self.normalize_type(tpl["type"]) == template_type:
                was_default = tpl["config"].get("is_default", False)
                should_be = tid == template_id
                if was_default != should_be:
                    tpl["config"]["is_default"] = should_be
                    import json

                    self.db_manager.update_template_config(tid, json.dumps(tpl["config"]))

    def delete_template(self, template_id):
        """Delete a template. Deleting an auto-created one also stops it from being auto-created again."""
        template = self.get_template_by_id(template_id)
        if template and FrequentConfigTracker.is_auto_template(template):
            FrequentConfigTracker(self).dismiss(template["type"], template["config"])
        self.db_manager.delete_template(template_id)
        self.load_templates()

    def record_config_usage(self, template_type, config, label=None):
        """Register one successful use of a configuration (may auto-create a template).

        See templates.frequent_configs for the rules. Returns a RecordResult.
        """
        return FrequentConfigTracker(self).record(template_type, config, label)

    def export_templates(self, filepath):
        """Export all templates to a JSON file"""
        templates_data = []

        for template_id, template in self.current_templates.items():
            templates_data.append(
                {
                    "id": template_id,
                    "name": template["name"],
                    "type": self.normalize_type(template["type"]),
                    "config": sk.normalize_config(template["type"], template["config"]),
                    "created_at": template["created_at"],
                    "last_used": template["last_used"],
                }
            )

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(templates_data, f, indent=2, ensure_ascii=False)

        return len(templates_data)

    def import_templates(self, filepath):
        """Import templates from a JSON file"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                templates_data = json.load(f)

            imported_count = 0
            for template_data in templates_data:
                existing_templates = self.db_manager.get_templates()
                name_exists = any(t[1] == template_data["name"] for t in existing_templates)

                if not name_exists:
                    template_type = self.normalize_type(template_data["type"])
                    config = sk.normalize_config(template_type, template_data.get("config", {}))
                    self.db_manager.save_template(template_data["name"], template_type, config)
                    imported_count += 1

            self.load_templates()
            return imported_count

        except Exception as e:
            print(f"Error importing templates: {e}")
            return 0


