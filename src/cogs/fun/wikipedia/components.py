# Copyright (c) 2025 OPPRO.NET Network
# ───────────────────────────────────────────────────
# >> UI Button Components
# ───────────────────────────────────────────────────
import discord
import wikipedia
from discord import SelectOption
from discord.ui import Button, Select, Container
from typing import Dict, Any
from .config import WIKI_CONFIG
from .cache import wiki_cache
from .utils import format_page_info


class LanguageSelectContainer(Select):
    """Dropdown für Sprachauswahl"""
    
    def __init__(self, current_term: str, current_lang: str = 'de', cog_instance=None):
        self.current_term = current_term
        self.current_lang = current_lang
        self.cog = cog_instance

        options = []
        for code, info in WIKI_CONFIG['languages'].items():
            options.append(SelectOption(
                label=info['name'],
                value=code,
                emoji=info['flag'],
                default=(code == current_lang),
                description=f"Suche auf {info['domain']}"
            ))

        super().__init__(
            placeholder="🌐 Sprache wählen...",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        from .containers import (
            create_article_container, 
            create_disambiguation_container, 
            create_error_container, 
            create_loading_container
        )
        
        await interaction.response.defer()

        selected_lang = self.values[0]
        if selected_lang == self.current_lang:
            error_container = Container()
            error_container.add_text("Diese Sprache ist bereits ausgewählt.")
            view = discord.ui.DesignerView(error_container, timeout=60)
            await interaction.followup.send(view=view, ephemeral=True)
            return

        original_lang = self.cog.current_language if self.cog else 'de'
        if selected_lang != original_lang:
            wikipedia.set_lang(selected_lang)
            if self.cog:
                self.cog.current_language = selected_lang

        try:
            loading_container = create_loading_container(
                f"Lade Artikel in {WIKI_CONFIG['languages'][selected_lang]['name']}...")
            view = discord.ui.DesignerView(loading_container, timeout=None)
            await interaction.edit_original_response(view=view)

            page = wikipedia.page(self.current_term)
            info = format_page_info(page, selected_lang)

            similar_articles = wikipedia.search(self.current_term, results=6)
            similar_articles = [a for a in similar_articles if a.lower() != info['title'].lower()]

            container = create_article_container(info, interaction.user, similar_articles[:4], 
                                                self.current_term, selected_lang, cog_instance=self.cog)
            view = discord.ui.DesignerView(container, timeout=WIKI_CONFIG['timeout'])
            await interaction.edit_original_response(view=view)

        except wikipedia.DisambiguationError as e:
            container = create_disambiguation_container(self.current_term, e.options[:10], selected_lang)
            view = discord.ui.DesignerView(container, timeout=None)
            await interaction.edit_original_response(view=view)
        except wikipedia.PageError:
            container = create_error_container(
                "Artikel nicht gefunden",
                f"'{self.current_term}' existiert nicht in {WIKI_CONFIG['languages'][selected_lang]['name']}."
            )
            view = discord.ui.DesignerView(container, timeout=None)
            await interaction.edit_original_response(view=view)
        except Exception as e:
            container = create_error_container("Unerwarteter Fehler", str(e)[:500])
            view = discord.ui.DesignerView(container, timeout=None)
            await interaction.edit_original_response(view=view)
        finally:
            if selected_lang != original_lang:
                wikipedia.set_lang(original_lang)
                if self.cog:
                    self.cog.current_language = original_lang


class ArticleButtonContainer(Button):
    """Button zum Öffnen eines Artikels"""
    
    def __init__(self, article_title: str, button_type: str = "similar", cog_instance=None):
        self.article_title = article_title
        self.button_type = button_type
        self.cog = cog_instance

        if button_type == "similar":
            emoji = "📖"
            style = discord.ButtonStyle.secondary
        elif button_type == "category":
            emoji = "📂"
            style = discord.ButtonStyle.primary
        else:
            emoji = "📄"
            style = discord.ButtonStyle.secondary

        super().__init__(
            label=article_title[:80],
            style=style,
            emoji=emoji
        )

    async def callback(self, interaction: discord.Interaction):
        from .containers import (
            create_article_container, 
            create_disambiguation_container, 
            create_error_container
        )
        
        await interaction.response.defer(ephemeral=True)

        try:
            current_lang = self.cog.current_language if self.cog else 'de'
            cache_key = f"{self.article_title}_{current_lang}"
            cached_info = wiki_cache.get(cache_key)

            if cached_info:
                info = cached_info
            else:
                page = wikipedia.page(self.article_title)
                info = format_page_info(page, current_lang)
                wiki_cache.set(cache_key, info)

            similar_articles = wikipedia.search(self.article_title, results=6)
            similar_articles = [a for a in similar_articles if a.lower() != info['title'].lower()]

            container = create_article_container(info, interaction.user, similar_articles[:4], 
                                                self.article_title, current_lang, cog_instance=self.cog)
            view = discord.ui.DesignerView(container, timeout=WIKI_CONFIG['timeout'])
            await interaction.followup.send(view=view, ephemeral=True)

        except wikipedia.DisambiguationError as e:
            container = create_disambiguation_container(self.article_title, e.options[:8])
            view = discord.ui.DesignerView(container, timeout=None)
            await interaction.followup.send(view=view, ephemeral=True)
        except wikipedia.PageError:
            container = create_error_container("Artikel nicht gefunden", 
                                              f"'{self.article_title}' existiert nicht.")
            view = discord.ui.DesignerView(container, timeout=None)
            await interaction.followup.send(view=view, ephemeral=True)
        except Exception as e:
            container = create_error_container("Fehler beim Laden", str(e)[:500])
            view = discord.ui.DesignerView(container, timeout=None)
            await interaction.followup.send(view=view, ephemeral=True)


class RandomArticleButton(Button):
    """Button für zufällige Artikel"""
    
    def __init__(self, language: str, cog_instance=None):
        self.language = language
        self.cog = cog_instance
        super().__init__(
            label="🎲 Zufälliger Artikel",
            style=discord.ButtonStyle.success
        )

    async def callback(self, interaction: discord.Interaction):
        from .containers import (
            create_random_article_container, 
            create_loading_container, 
            create_error_container
        )
        
        await interaction.response.defer()

        try:
            loading_container = create_loading_container("Lade zufälligen Artikel...")
            view = discord.ui.DesignerView(loading_container, timeout=None)
            await interaction.edit_original_response(view=view)

            random_title = wikipedia.random()
            page = wikipedia.page(random_title)
            info = format_page_info(page, self.language)

            similar_articles = wikipedia.search(random_title, results=6)
            similar_articles = [a for a in similar_articles if a.lower() != info['title'].lower()]

            container = create_random_article_container(
                info, interaction.user, similar_articles[:4],
                random_title, self.language, cog_instance=self.cog
            )
            
            view = discord.ui.DesignerView(container, timeout=WIKI_CONFIG['timeout'])
            await interaction.edit_original_response(view=view)

        except Exception as e:
            container = create_error_container("Fehler beim Laden", 
                                              f"Zufälliger Artikel konnte nicht geladen werden: {str(e)[:300]}")
            view = discord.ui.DesignerView(container, timeout=None)
            await interaction.edit_original_response(view=view)


class ArticleInfoButton(Button):
    """Button für Artikel-Informationen"""
    
    def __init__(self, info: Dict[str, Any], language: str):
        self.info = info
        self.language = language
        super().__init__(
            label="📊 Artikel-Info",
            style=discord.ButtonStyle.primary
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        container = Container()
        container.add_text(f"📊 **Informationen zu '{self.info['title']}'**")
        container.add_separator()
        
        stats_text = f"🌐 **Sprache:** {WIKI_CONFIG['languages'][self.language]['name']}\n"
        stats_text += f"📂 **Kategorien:** {len(self.info.get('categories', []))}\n"
        stats_text += f"🔗 **Verweise:** {len(self.info.get('links', []))}"
        container.add_text(stats_text)
        
        if self.info.get('coordinates'):
            lat, lon = self.info['coordinates']
            container.add_text(f"🗺️ **Koordinaten:** {lat:.2f}°N, {lon:.2f}°E")
        
        if self.info.get('images'):
            container.add_text(f"🖼️ **Bilder:** {len(self.info['images'])}")
        
        if self.info.get('categories'):
            container.add_separator()
            container.add_text("📚 **Hauptkategorien:**")
            categories_text = "\n".join([f"• {cat}" for cat in self.info['categories'][:5]])
            container.add_text(categories_text)
        
        container.add_separator()
        container.add_text("Wikipedia • Artikel-Statistiken")

        view = discord.ui.DesignerView(container, timeout=300)
        await interaction.followup.send(view=view, ephemeral=True)


class RefreshArticleButton(Button):
    """Button zum Aktualisieren eines Artikels"""
    
    def __init__(self, search_term: str, language: str, cog_instance=None):
        self.search_term = search_term
        self.language = language
        self.cog = cog_instance
        super().__init__(
            label="🔄 Aktualisieren",
            style=discord.ButtonStyle.secondary
        )

    async def callback(self, interaction: discord.Interaction):
        from .containers import (
            create_article_container, 
            create_loading_container, 
            create_error_container
        )
        
        await interaction.response.defer()

        try:
            cache_key = f"{self.search_term}_{self.language}"
            if cache_key in wiki_cache.cache:
                del wiki_cache.cache[cache_key]
                del wiki_cache.timestamps[cache_key]

            loading_container = create_loading_container("Aktualisiere Artikel...")
            view = discord.ui.DesignerView(loading_container, timeout=None)
            await interaction.edit_original_response(view=view)

            page = wikipedia.page(self.search_term)
            info = format_page_info(page, self.language)

            similar_articles = wikipedia.search(self.search_term, results=6)
            similar_articles = [a for a in similar_articles if a.lower() != info['title'].lower()]

            container = create_article_container(info, interaction.user, similar_articles[:4], 
                                                self.search_term, self.language, cog_instance=self.cog)
            view = discord.ui.DesignerView(container, timeout=WIKI_CONFIG['timeout'])
            await interaction.edit_original_response(view=view)

        except Exception as e:
            container = create_error_container("Aktualisierung fehlgeschlagen", str(e)[:500])
            view = discord.ui.DesignerView(container, timeout=None)
            await interaction.edit_original_response(view=view)