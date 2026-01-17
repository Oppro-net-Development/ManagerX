"""
ManagerX - Database Manager
============================

Verwaltet Datenbankverbindungen und Initialisierung
Pfad: src/bot/core/database.py
"""

from logger import logger, Category

try:
    from DevTools import SettingsDB
except ImportError as e:
    logger.critical(Category.DATABASE, f"SettingsDB Import fehlgeschlagen: {e}")
    SettingsDB = None

class DatabaseManager:
    """Verwaltet die Datenbank-Initialisierung"""
    
    def __init__(self):
        self.db = None
    
    def initialize(self, bot) -> bool:
        """
        Initialisiert die Datenbank und hängt sie an den Bot an.
        
        Args:
            bot: Bot-Instanz
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        if SettingsDB is None:
            logger.critical(Category.DATABASE, "SettingsDB nicht verfügbar!")
            return False
        
        try:
            self.db = SettingsDB()
            bot.settings_db = self.db
            logger.success(Category.DATABASE, "Settings Database initialized ✓")
            return True
            
        except Exception as e:
            logger.critical(Category.DATABASE, f"Datenbankfehler: {e}")
            return False
    
    def get_database(self):
        """
        Gibt die Datenbankinstanz zurück.
        
        Returns:
            SettingsDB: Datenbankinstanz oder None
        """
        return self.db
    
    def close(self):
        """Schließt die Datenbankverbindung"""
        if self.db:
            try:
                # Falls SettingsDB eine close()-Methode hat
                if hasattr(self.db, 'close'):
                    self.db.close()
                logger.info(Category.DATABASE, "Datenbankverbindung geschlossen")
            except Exception as e:
                logger.error(Category.DATABASE, f"Fehler beim Schließen der DB: {e}")
    
    def is_connected(self) -> bool:
        """
        Prüft ob die Datenbank verbunden ist.
        
        Returns:
            bool: True wenn verbunden, sonst False
        """
        return self.db is not None