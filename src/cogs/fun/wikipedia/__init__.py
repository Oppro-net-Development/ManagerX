# Copyright (c) 2025 OPPRO.NET Network
# ───────────────────────────────────────────────────
# >> Wikipedia Bot Package
# ───────────────────────────────────────────────────
"""
Wikipedia Bot für Discord

Ein umfassender Wikipedia-Bot mit Unterstützung für mehrere Sprachen,
Caching, interaktive UI-Komponenten und erweiterte Suchfunktionen.
"""

__version__ = "2.0.0"
__author__ = "OPPRO.NET Network"

from .cog import WikipediaCog, setup
from .config import WIKI_CONFIG, LANGUAGE_CHOICES
from .cache import WikiCache, wiki_cache
from .utils import clean_text, format_page_info
from .containers import (
    create_article_container,
    create_error_container,
    create_disambiguation_container,
    create_loading_container,
    create_random_article_container
)
from .components import (
    LanguageSelectContainer,
    ArticleButtonContainer,
    RandomArticleButton,
    ArticleInfoButton,
    RefreshArticleButton
)
from .autocomplete import enhanced_wiki_autocomplete

__all__ = [
    # Main
    'WikipediaCog',
    'setup',
    
    # Config
    'WIKI_CONFIG',
    'LANGUAGE_CHOICES',
    
    # Cache
    'WikiCache',
    'wiki_cache',
    
    # Utils
    'clean_text',
    'format_page_info',
    
    # Containers
    'create_article_container',
    'create_error_container',
    'create_disambiguation_container',
    'create_loading_container',
    'create_random_article_container',
    
    # Components
    'LanguageSelectContainer',
    'ArticleButtonContainer',
    'RandomArticleButton',
    'ArticleInfoButton',
    'RefreshArticleButton',
    
    # Autocomplete
    'enhanced_wiki_autocomplete',
]