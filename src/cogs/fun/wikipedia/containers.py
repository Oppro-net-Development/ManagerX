# -*- coding: utf-8 -*-
# Copyright (c) 2025 OPPRO.NET Network
# ───────────────────────────────────────────────────
# >> Container Creation Functions (py-cord Designer)
# ───────────────────────────────────────────────────
import discord
from discord.ui import Container
from typing import Dict, Any, List


def create_article_container(
    info: Dict[str, Any], 
    user: discord.User, 
    similar_articles: List[str] = None,
    search_term: str = "", 
    language: str = 'de', 
    cog_instance=None
) -> Container:
    """Erstellt einen Container für einen Wikipedia-Artikel"""
    from .components import (
        LanguageSelectContainer, ArticleButtonContainer, 
        RandomArticleButton, ArticleInfoButton, RefreshArticleButton
    )
    
    container = Container()
    
    # Header mit Titel
    lang_info = {
        'de': {'name': 'Deutsch', 'flag': 'DE'},
        'en': {'name': 'English', 'flag': 'EN'},
        'fr': {'name': 'Français', 'flag': 'FR'},
        'es': {'name': 'Español', 'flag': 'ES'},
        'it': {'name': 'Italiano', 'flag': 'IT'},
        'ja': {'name': '日本語', 'flag': 'JP'},
        'ru': {'name': 'Русский', 'flag': 'RU'},
    }
    lang_data = lang_info.get(language, {'name': 'Deutsch', 'flag': 'DE'})
    header_text = f"📖 **{info['title']}**\n[{lang_data['flag']}] {lang_data['name']} • Wikipedia"
    container.add_text(header_text)
    
    container.add_separator()
    
    # Zusammenfassung
    summary_text = info['summary'][:800] + ("..." if len(info['summary']) > 800 else "")
    container.add_text(summary_text)
    
    # Kategorien falls vorhanden
    if info.get('categories'):
        container.add_separator()
        categories_text = "📂 **Kategorien:** " + ", ".join(info['categories'][:3])
        if len(info['categories']) > 3:
            categories_text += f" (+{len(info['categories']) - 3} weitere)"
        container.add_text(categories_text)
    
    # Koordinaten falls vorhanden
    if info.get('coordinates'):
        lat, lon = info['coordinates']
        container.add_text(f"🗺️ **Standort:** {lat:.2f}°N, {lon:.2f}°E")
    
    container.add_separator()
    
    # Link zum vollständigen Artikel
    if info.get('url'):
        container.add_text(f"🔗 [Vollständigen Artikel lesen]({info['url']})")
    
    # Sprachauswahl
    if cog_instance and search_term:
        lang_select = LanguageSelectContainer(search_term, language, cog_instance)
        container.add_item(lang_select)
    
    # Ähnliche Artikel als Buttons
    if similar_articles and cog_instance:
        container.add_separator()
        container.add_text("📚 **Ähnliche Artikel:**")
        for article in similar_articles[:4]:
            article_btn = ArticleButtonContainer(article, "similar", cog_instance)
            container.add_item(article_btn)
    
    container.add_separator()
    
    # Action Buttons
    if cog_instance:
        random_btn = RandomArticleButton(language, cog_instance)
        container.add_item(random_btn)
        
        info_btn = ArticleInfoButton(info, language)
        container.add_item(info_btn)
        
        if search_term:
            refresh_btn = RefreshArticleButton(search_term, language, cog_instance)
            container.add_item(refresh_btn)
    
    # Footer
    container.add_separator()
    footer_text = f"👤 Angefragt von {user.display_name}"
    container.add_text(footer_text)
    
    return container


def create_error_container(title: str, description: str) -> Container:
    """Erstellt einen Fehler-Container"""
    container = Container()
    container.add_text(f"❌ **{title}**")
    container.add_separator()
    container.add_text(description)
    container.add_separator()
    container.add_text("Wikipedia Bot • Fehler aufgetreten")
    return container


def create_disambiguation_container(term: str, options: List[str], language: str = 'de') -> Container:
    """Erstellt einen Mehrdeutigkeits-Container"""
    lang_info = {
        'de': 'Deutsch',
        'en': 'English',
        'fr': 'Français',
        'es': 'Español',
        'it': 'Italiano',
        'ja': '日本語',
        'ru': 'Русский'
    }
    
    container = Container()
    
    lang_name = lang_info.get(language, 'Deutsch')
    container.add_text(f"🔀 **Mehrdeutige Suche**")
    container.add_separator()
    container.add_text(f"**'{term}'** kann mehrere Bedeutungen haben in {lang_name}:")
    
    container.add_separator()
    container.add_text("📋 **Mögliche Optionen:**")
    
    options_text = "\n".join([f"• {opt}" for opt in options[:10]])
    container.add_text(options_text)
    
    container.add_separator()
    container.add_text("💡 Versuche eine spezifischere Suche oder wähle eine der Optionen.")
    
    return container


def create_loading_container(title: str = "Lade Wikipedia-Artikel...") -> Container:
    """Erstellt einen Lade-Container"""
    container = Container()
    container.add_text(f"⏳ **{title}**")
    container.add_separator()
    container.add_text("Dies kann einen Moment dauern...")
    return container


def create_random_article_container(
    info: Dict[str, Any],
    user: discord.User,
    similar_articles: List[str],
    random_title: str,
    language: str,
    cog_instance=None
) -> Container:
    """Erstellt einen Container für zufällige Artikel"""
    from .components import (
        LanguageSelectContainer, ArticleButtonContainer,
        RandomArticleButton, ArticleInfoButton, RefreshArticleButton
    )
    
    container = Container()
    
    lang_info = {
        'de': {'name': 'Deutsch', 'flag': 'DE'},
        'en': {'name': 'English', 'flag': 'EN'},
        'fr': {'name': 'Français', 'flag': 'FR'},
        'es': {'name': 'Español', 'flag': 'ES'},
        'it': {'name': 'Italiano', 'flag': 'IT'},
        'ja': {'name': '日本語', 'flag': 'JP'},
        'ru': {'name': 'Русский', 'flag': 'RU'},
    }
    lang_data = lang_info.get(language, {'name': 'Deutsch', 'flag': 'DE'})
    
    container.add_text(f"🎲 **Zufälliger Artikel: {info['title']}**")
    container.add_text(f"[{lang_data['flag']}] {lang_data['name']} • Wikipedia")
    container.add_separator()
    
    summary_text = info['summary'][:800] + ("..." if len(info['summary']) > 800 else "")
    container.add_text(summary_text)
    
    if info.get('categories'):
        container.add_separator()
        categories_text = "📂 **Kategorien:** " + ", ".join(info['categories'][:3])
        if len(info['categories']) > 3:
            categories_text += f" (+{len(info['categories']) - 3} weitere)"
        container.add_text(categories_text)
    
    if info.get('coordinates'):
        lat, lon = info['coordinates']
        container.add_text(f"🗺️ **Standort:** {lat:.2f}°N, {lon:.2f}°E")
    
    container.add_separator()
    
    if info.get('url'):
        container.add_text(f"🔗 [Vollständigen Artikel lesen]({info['url']})")
    
    if cog_instance:
        lang_select = LanguageSelectContainer(random_title, language, cog_instance)
        container.add_item(lang_select)
    
    if similar_articles and cog_instance:
        container.add_separator()
        container.add_text("📚 **Ähnliche Artikel:**")
        for article in similar_articles[:4]:
            article_btn = ArticleButtonContainer(article, "similar", cog_instance)
            container.add_item(article_btn)
    
    container.add_separator()
    
    if cog_instance:
        random_btn = RandomArticleButton(language, cog_instance)
        container.add_item(random_btn)
        
        info_btn = ArticleInfoButton(info, language)
        container.add_item(info_btn)
        
        refresh_btn = RefreshArticleButton(random_title, language, cog_instance)
        container.add_item(refresh_btn)
    
    container.add_separator()
    container.add_text(f"👤 Angefragt von {user.display_name}")
    
    return container