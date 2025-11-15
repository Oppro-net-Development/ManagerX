# Copyright (c) 2025 OPPRO.NET Network
"""
DevTools Backend Initialization
Initialisiert alle Datenbank-Module mit Logging
"""

import colorama
from colorama import Fore, Style
from datetime import datetime
from typing import Callable, List
import logging

colorama.init(autoreset=True)

# Logger für Backend
logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """Verwaltet Datenbank-Initialisierungen"""
    
    def __init__(self):
        self.databases = []
        self.failed = []
    
    @staticmethod
    def timestamp() -> str:
        """Gibt formatierten Timestamp zurück"""
        return datetime.now().strftime(f"[{Fore.CYAN}%H:%M:%S{Style.RESET_ALL}]")
    
    @staticmethod
    def log_success(db_name: str):
        """Loggt erfolgreiche Initialisierung"""
        print(
            f"{DatabaseInitializer.timestamp()} "
            f"[{Style.BRIGHT}{Fore.MAGENTA}DATABASE{Style.RESET_ALL}] "
            f"{db_name} initialized ✓"
        )
    
    @staticmethod
    def log_error(db_name: str, error: Exception):
        """Loggt Fehler bei Initialisierung"""
        print(
            f"{DatabaseInitializer.timestamp()} "
            f"[{Fore.RED}DATABASE{Style.RESET_ALL}] "
            f"{db_name} initialization failed: {error}"
        )
        logger.error(f"Database init failed: {db_name}", exc_info=True)
    
    def register(self, name: str, init_func: Callable):
        """Registriert eine Datenbank für Initialisierung"""
        self.databases.append((name, init_func))
    
    def init_all(self) -> bool:
        """
        Initialisiert alle registrierten Datenbanken
        Returns: True wenn alle erfolgreich, sonst False
        """
        print(f"\n{Fore.MAGENTA}{'─' * 50}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}  Initializing Databases...{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'─' * 50}{Style.RESET_ALL}\n")
        
        success_count = 0
        
        for db_name, init_func in self.databases:
            try:
                init_func()
                self.log_success(db_name)
                success_count += 1
            except Exception as e:
                self.log_error(db_name, e)
                self.failed.append((db_name, str(e)))
        
        # Summary
        print(f"\n{Fore.MAGENTA}{'─' * 50}{Style.RESET_ALL}")
        if self.failed:
            print(
                f"{Fore.YELLOW}  ⚠ {success_count}/{len(self.databases)} databases initialized{Style.RESET_ALL}"
            )
            for db_name, error in self.failed:
                print(f"{Fore.RED}    ✗ {db_name}: {error}{Style.RESET_ALL}")
        else:
            print(
                f"{Fore.GREEN}  ✓ All {success_count} databases initialized successfully{Style.RESET_ALL}"
            )
        print(f"{Fore.MAGENTA}{'─' * 50}{Style.RESET_ALL}\n")
        
        return len(self.failed) == 0


# =============================================================================
# DATABASE INITIALIZATION FUNCTIONS
# =============================================================================

def init_spam_db():
    """Initialisiert Spam-Datenbank"""
    try:
        import DevTools.backend.database.spam_db
    except Exception as e:
        logger.debug(f"Spam DB import: {e}")
    pass


def init_warn_db():
    """Initialisiert Warn-Datenbank"""
    try:
        import DevTools.backend.database.warn_db
    except Exception as e:
        logger.debug(f"Warn DB import: {e}")
    pass


def init_notes_db():
    """Initialisiert Notes-Datenbank"""
    try:
        import DevTools.backend.database.notes_db
    except Exception as e:
        logger.debug(f"Notes DB import: {e}")
    pass


def init_tempvc_db():
    """Initialisiert TempVC-Datenbank"""
    try:
        import DevTools.backend.database.vc_db
    except Exception as e:
        logger.debug(f"TempVC DB import: {e}")
    pass


def init_stats_db():
    """Initialisiert Stats-Datenbank"""
    try:
        import DevTools.backend.database.Stats_db
    except Exception as e:
        logger.debug(f"Stats DB import: {e}")
    pass


def init_levelsystem_db():
    """Initialisiert Levelsystem-Datenbank"""
    try:
        import DevTools.backend.database.levelsystem_db
    except Exception as e:
        logger.debug(f"Levelsystem DB import: {e}")
    pass


def init_globalchat_db():
    """Initialisiert GlobalChat-Datenbank"""
    try:
        from .database.globalchat_db import GlobalChatDatabase
        # Erstelle Instanz
        db = GlobalChatDatabase()
    except Exception as e:
        logger.debug(f"GlobalChat DB import: {e}")
        raise
    pass


def init_logging_db():
    """Initialisiert Logging-Datenbank"""
    try:
        import DevTools.backend.database.logging_db
    except Exception as e:
        logger.debug(f"Logging DB import: {e}")
    pass


def init_autodelete_db():
    """Initialisiert AutoDelete-Datenbank"""
    try:
        from .database.autodelete_db import db
    except ImportError:
        pass  # Optional


def init_welcome_db():
    """Initialisiert Welcome-Datenbank"""
    try:
        from .database.welcome_db import db
    except ImportError:
        pass  # Optional


# =============================================================================
# MAIN INITIALIZATION
# =============================================================================

# Globaler Initializer
_initializer = DatabaseInitializer()

# Alle Datenbanken registrieren
_initializer.register("Spam Database", init_spam_db)
_initializer.register("Warn Database", init_warn_db)
_initializer.register("Notes Database", init_notes_db)
_initializer.register("TempVC Database", init_tempvc_db)
_initializer.register("Stats Database", init_stats_db)
_initializer.register("Levelsystem Database", init_levelsystem_db)
_initializer.register("GlobalChat Database", init_globalchat_db)
_initializer.register("Logging Database", init_logging_db)
_initializer.register("AutoDelete Database", init_autodelete_db)
_initializer.register("Welcome Database", init_welcome_db)


def init_all() -> bool:
    """
    Initialisiert alle Datenbank-Module
    
    Returns:
        bool: True wenn alle erfolgreich initialisiert wurden
    """
    return _initializer.init_all()


def get_failed_databases() -> List[tuple]:
    """
    Gibt Liste der fehlgeschlagenen Datenbanken zurück
    
    Returns:
        List[tuple]: Liste von (db_name, error_message) Tupeln
    """
    return _initializer.failed


# Backwards Compatibility - Einzelne Funktionen exportieren
__all__ = [
    'init_all',
    'init_spam_db',
    'init_warn_db',
    'init_notes_db',
    'init_tempvc_db',
    'init_stats_db',
    'init_levelsystem_db',
    'init_globalchat_db',
    'init_logging_db',
    'init_autodelete_db',
    'init_welcome_db',
    'get_failed_databases',
]