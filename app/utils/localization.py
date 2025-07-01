"""
Localization utilities for HOT SHARK Bot
"""
import json
import os
from typing import Dict, Any

class Localization:
    def __init__(self):
        self.translations = {}
        self.load_translations()
    
    def load_translations(self):
        """Load translation files"""
        locales_dir = os.path.join(os.path.dirname(__file__), "..", "locales")
        
        for lang in ["ar", "en"]:
            file_path = os.path.join(locales_dir, f"{lang}.json")
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    self.translations[lang] = json.load(f)
            else:
                self.translations[lang] = {}
    
    def get_text(self, key: str, lang: str = "ar", **kwargs) -> str:
        """Get translated text"""
        if lang not in self.translations:
            lang = "ar"  # Fallback to Arabic
        
        text = self.translations[lang].get(key, key)
        
        # Format with kwargs if provided
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
        
        return text
    
    def get_keyboard_text(self, key: str, lang: str = "ar") -> str:
        """Get keyboard button text"""
        return self.get_text(f"keyboard.{key}", lang)

# Global localization instance
loc = Localization()

# Export functions for direct import
def get_text(key: str, lang: str = "ar", **kwargs) -> str:
    """Get translated text"""
    return loc.get_text(key, lang, **kwargs)

def get_keyboard_text(key: str, lang: str = "ar") -> str:
    """Get keyboard button text"""
    return loc.get_keyboard_text(key, lang)

