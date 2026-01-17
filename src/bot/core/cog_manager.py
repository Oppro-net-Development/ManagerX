"""
ManagerX - Cog Manager
======================

Verwaltet das Laden und Deaktivieren von Cogs
Pfad: src/bot/core/cog_manager.py
"""

from logger import logger, Category

class CogManager:
    """Verwaltet Cog-Loading und Ignore-Liste"""
    
    # Hilfs-/Utility-Dateien, die keine Cogs sind
    UTILITY_FILES = [
        "autocomplete",
        "cache",
        "components",
        "config",
        "containers",
        "utils",
        "backend",
        "emojis"
    ]
    
    # Mapping: Config-Key -> Dateiname
    COG_MAPPING = {
        'fun': {
            'gewinnt': 'gewinnt',
            'tictactoe': 'tictactoe',
            'weather': 'weather',
            'wikipedia': 'cog'
        },
        'information': {
            'botstatus': 'botstatus',
            'serverinfo': 'serverinfo',
            'usermanagemt': 'usermanagemt'
        },
        'moderation': {
            'antispam': 'antispam',
            'moderation': 'moderation',
            'notes': 'notes',
            'warningsystem': 'warningsystem'
        },
        'server_management': {
            'autodelete': 'autodelete',
            'globalchat': 'globalchat',
            'levelsystem': 'levelsystem',
            'logging': 'logging',
            'stats': 'stats',
            'tempvc': 'tempvc',
            'welcome': 'welcome'
        },
        'other': {
            'setlang': 'setlang'
        }
    }
    
    def __init__(self, cogs_config: dict):
        self.cogs_config = cogs_config
    
    def get_ignored_cogs(self) -> list:
        """
        Erstellt Liste von zu ignorierenden Cogs basierend auf config.yaml.
        
        Returns:
            list: Dateinamen (ohne .py) der zu ignorierenden Cogs
        """
        ignored = self.UTILITY_FILES.copy()
        
        # Deaktivierte Cogs hinzufügen
        for category, cogs in self.COG_MAPPING.items():
            category_config = self.cogs_config.get(category, {})
            
            for cog_key, file_name in cogs.items():
                if not category_config.get(cog_key, True):
                    ignored.append(file_name)
                    logger.info(Category.BOT, f"Cog '{file_name}' deaktiviert (config.yaml)")
        
        return ignored
    
    def is_cog_enabled(self, category: str, cog_name: str) -> bool:
        """
        Prüft ob ein bestimmter Cog aktiviert ist.
        
        Args:
            category: Kategorie des Cogs (z.B. 'fun', 'moderation')
            cog_name: Name des Cogs
            
        Returns:
            bool: True wenn aktiviert, sonst False
        """
        category_config = self.cogs_config.get(category, {})
        return category_config.get(cog_name, True)
    
    def get_enabled_cogs(self) -> dict:
        """
        Gibt alle aktivierten Cogs nach Kategorie zurück.
        
        Returns:
            dict: Dictionary mit Kategorien und aktivierten Cogs
        """
        enabled = {}
        
        for category, cogs in self.COG_MAPPING.items():
            category_config = self.cogs_config.get(category, {})
            enabled_in_category = []
            
            for cog_key, file_name in cogs.items():
                if category_config.get(cog_key, True):
                    enabled_in_category.append(file_name)
            
            if enabled_in_category:
                enabled[category] = enabled_in_category
        
        return enabled