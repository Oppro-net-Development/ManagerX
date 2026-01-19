"""
ManagerX - Configuration Loader
================================

Lädt und verwaltet die Bot-Konfiguration aus config.yaml
"""

import os
import sys
import yaml
from pathlib import Path
from colorama import Fore, Style
from dotenv import load_dotenv
base_path = Path(__file__).resolve().parent.parent.parent.parent
env_path = base_path / "config" / ".env"

# Lade die .env Datei
load_dotenv(dotenv_path=env_path)

class BotConfig:
    """Zentrale Konfigurationsklasse"""
    TOKEN = os.getenv("TOKEN")
    VERSION = "2.0.0"

class ConfigLoader:
    """Lädt die Bot-Konfiguration aus config.yaml"""
    
    def __init__(self, basedir: Path):
        self.basedir = basedir
        self.config_path = basedir / 'config' / 'config.yaml'
    
    def load(self) -> dict:
        """
        Lädt die Konfigurationsdatei und gibt alle Einstellungen zurück.
        
        Returns:
            dict: Vollständige Konfiguration
            
        Raises:
            SystemExit: Bei kritischen Fehlern
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Bot deaktiviert?
            if not config.get('enabled', True):
                print(f"[{Fore.YELLOW}INFO{Style.RESET_ALL}] Bot ist in config.yaml deaktiviert. Beende...")
                sys.exit(0)
            
            # Version übernehmen
            BotConfig.VERSION = config.get('version', '2.0.0')
            
            # Strukturierte Rückgabe
            return {
                'enabled': config.get('enabled', True),
                'version': BotConfig.VERSION,
                'features': config.get('features', {}),
                'bot_behavior': config.get('bot_behavior', {}),
                'ui': config.get('ui', {}),
                'security': config.get('security', {}),
                'performance': config.get('performance', {}),
                'cogs': config.get('features', {}).get('cogs', {})
            }
            
        except FileNotFoundError:
            print(f"[{Fore.RED}ERROR{Style.RESET_ALL}] config.yaml nicht gefunden: {self.config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"[{Fore.RED}ERROR{Style.RESET_ALL}] YAML-Parsing-Fehler: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"[{Fore.RED}ERROR{Style.RESET_ALL}] Fehler beim Laden der config.yaml: {e}")
            sys.exit(1)