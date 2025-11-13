# Copyright (c) 2025 OPPRO.NET Network
# ───────────────────────────────────────────────
# >> Imports
# ───────────────────────────────────────────────
import wikipedia
import asyncio
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import discord
import ezcord
from discord import slash_command, SelectOption
from discord.ui import Container, Button, Select

# Fallback für Farben
try:
    from DevTools import INFO_COLOR, ERROR_COLOR, SUCCESS_COLOR, WARNING_COLOR
except ImportError:
    INFO_COLOR = discord.Color.blue()
    ERROR_COLOR = discord.Color.red()
    SUCCESS_COLOR = discord.Color.green()
    WARNING_COLOR = discord.Color.orange()

# ───────────────────────────────────────────────
# >> Settings & Configuration
# ───────────────────────────────────────────────
wikipedia.set_lang("de")
wikipedia.set_rate_limiting(True)

WIKI_CONFIG = {
    'languages': {
        'de': {'name': 'Deutsch', 'flag': '🇩🇪', 'domain': 'de.wikipedia.org'},
        'en': {'name': 'English', 'flag': '🇺🇸', 'domain': 'en.wikipedia.org'},
        'fr': {'name': 'Français', 'flag': '🇫🇷', 'domain': 'fr.wikipedia.org'},
        'es': {'name': 'Español', 'flag': '🇪🇸', 'domain': 'es.wikipedia.org'},
        'it': {'name': 'Italiano', 'flag': '🇮🇹', 'domain': 'it.wikipedia.org'},
        'ja': {'name': '日本語', 'flag': '🇯🇵', 'domain': 'ja.wikipedia.org'},
        'ru': {'name': 'Русский', 'flag': '🇷🇺', 'domain': 'ru.wikipedia.org'},
    },
    'max_summary_length': 1500,
    'max_categories': 3,
    'max_similar_articles': 6,
    'timeout': 600,
    'cache_duration': 300
}

# ───────────────────────────────────────────────
# >> Cache System
# ───────────────────────────────────────────────
class WikiCache:
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.timestamps: Dict[str, datetime] = {}

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        if key in self.cache:
            if datetime.now() - self.timestamps[key] < timedelta(seconds=WIKI_CONFIG['cache_duration']):
                return self.cache[key]
            else:
                del self.cache[key]
                del self.timestamps[key]
        return None

    def set(self, key: str, value: Dict[str, Any]):
        self.cache[key] = value
        self.timestamps[key] = datetime.now()

    def clear_expired(self):
        now = datetime.now()
        expired_keys = [
            key for key, timestamp in self.timestamps.items()
            if now - timestamp >= timedelta(seconds=WIKI_CONFIG['cache_duration'])
        ]
        for key in expired_keys:
            self.cache.pop(key, None)
            self.timestamps.pop(key, None)

wiki_cache = WikiCache()

# ───────────────────────────────────────────────
# >> Utility Functions
# ───────────────────────────────────────────────
def clean_text(text: str, max_length: int = None) -> str:
    """Erweiterte Textbereinigung"""
    if not text:
        return "Keine Beschreibung verfügbar."

    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()

    max_length = max_length or WIKI_CONFIG['max_summary_length']
    if len(text) > max_length:
        truncated = text[:max_length - 3]
        last_sentence = truncated.rfind('.')
        if last_sentence > max_length // 2:
            text = truncated[:last_sentence + 1]
        else:
            text = truncated + "..."

    return text

def format_page_info(page, language: str = 'de') -> Dict[str, Any]:
    """Erweiterte Seiteninformationen mit Fehlerbehandlung"""
    try:
        info = {
            'title': getattr(page, 'title', 'Unbekannt'),
            'url': getattr(page, 'url', ''),
            'summary': '',
            'categories': [],
            'links': [],
            'images': [],
            'language': language,
            'coordinates': None,
            'references': []
        }

        try:
            info['summary'] = clean_text(wikipedia.summary(page.title, sentences=4))
        except:
            info['summary'] = "Zusammenfassung nicht verfügbar."

        try:
            info['categories'] = getattr(page, 'categories', [])[:WIKI_CONFIG['max_categories']]
        except:
            pass

        try:
            info['links'] = getattr(page, 'links', [])[:15]
        except:
            pass

        try:
            info['images'] = getattr(page, 'images', [])
        except:
            pass

        try:
            content = getattr(page, 'content', '')
            coord_match = re.search(r'(\d+\.?\d*)[°]\s*N.*?(\d+\.?\d*)[°]\s*[EW]', content)
            if coord_match:
                info['coordinates'] = (float(coord_match.group(1)), float(coord_match.group(2)))
        except:
            pass

        return info
    except Exception as e:
        return {
            'title': 'Fehler beim Laden',
            'url': '',
            'summary': f'Informationen konnten nicht geladen werden: {str(e)}',
            'categories': [],
            'links': [],
            'images': [],
            'language': language,
            'coordinates': None,
            'references': []
        }

# ───────────────────────────────────────────────
# >> Container Creation Functions
# ───────────────────────────────────────────────
def create_article_container(info: Dict[str, Any], user: discord.User, similar_articles: List[str] = None, 
                            search_term: str = "", language: str = 'de', cog_instance=None) -> Container:
    """Erstellt einen Container für einen Wikipedia-Artikel"""
    container = Container()
    
    # Header mit Titel
    lang_info = WIKI_CONFIG['languages'].get(language, {'name': 'Deutsch', 'flag': '🇩🇪'})
    header_text = f"📖 **{info['title']}**\n{lang_info['flag']} {lang_info['name']} • Wikipedia"
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
        link_button = Button(
            label="🔗 Vollständigen Artikel lesen",
            url=info['url'],
            style=discord.ButtonStyle.link
        )
        container.add_item(link_button)
    
    # Sprachauswahl
    if cog_instance:
        lang_select = LanguageSelectContainer(search_term, language, cog_instance)
        container.add_item(lang_select)
    
    # Ähnliche Artikel als Buttons
    if similar_articles:
        container.add_separator()
        container.add_text("📚 **Ähnliche Artikel:**")
        for article in similar_articles[:4]:
            article_btn = ArticleButtonContainer(article, "similar", cog_instance)
            container.add_item(article_btn)
    
    container.add_separator()
    
    # Action Buttons
    random_btn = RandomArticleButton(language, cog_instance)
    container.add_item(random_btn)
    
    info_btn = ArticleInfoButton(info, language)
    container.add_item(info_btn)
    
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
    container = Container()
    
    lang_info = WIKI_CONFIG['languages'].get(language, {'name': 'Deutsch'})
    container.add_text(f"🔀 **Mehrdeutige Suche**")
    container.add_separator()
    container.add_text(f"**'{term}'** kann mehrere Bedeutungen haben in {lang_info['name']}:")
    
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

# ───────────────────────────────────────────────
# >> Button Components
# ───────────────────────────────────────────────
class LanguageSelectContainer(Select):
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
        await interaction.response.defer()

        selected_lang = self.values[0]
        if selected_lang == self.current_lang:
            error_container = Container()
            error_container.add_text("Diese Sprache ist bereits ausgewählt.")
            view = discord.ui.View(error_container, timeout=60)
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
            view = discord.ui.View(loading_container, timeout=None)
            await interaction.edit_original_response(view=view)

            page = wikipedia.page(self.current_term)
            info = format_page_info(page, selected_lang)

            similar_articles = wikipedia.search(self.current_term, results=6)
            similar_articles = [a for a in similar_articles if a.lower() != info['title'].lower()]

            container = create_article_container(info, interaction.user, similar_articles[:4], 
                                                self.current_term, selected_lang, cog_instance=self.cog)
            view = discord.ui.View(container, timeout=WIKI_CONFIG['timeout'])
            await interaction.edit_original_response(view=view)

        except wikipedia.DisambiguationError as e:
            container = create_disambiguation_container(self.current_term, e.options[:10], selected_lang)
            view = discord.ui.View(container, timeout=None)
            await interaction.edit_original_response(view=view)
        except wikipedia.PageError:
            container = create_error_container(
                "Artikel nicht gefunden",
                f"'{self.current_term}' existiert nicht in {WIKI_CONFIG['languages'][selected_lang]['name']}."
            )
            view = discord.ui.View(container, timeout=None)
            await interaction.edit_original_response(view=view)
        except Exception as e:
            container = create_error_container("Unerwarteter Fehler", str(e)[:500])
            view = discord.ui.View(container, timeout=None)
            await interaction.edit_original_response(view=view)
        finally:
            if selected_lang != original_lang:
                wikipedia.set_lang(original_lang)
                if self.cog:
                    self.cog.current_language = original_lang

class ArticleButtonContainer(Button):
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
            view = discord.ui.View(container, timeout=WIKI_CONFIG['timeout'])
            await interaction.followup.send(view=view, ephemeral=True)

        except wikipedia.DisambiguationError as e:
            container = create_disambiguation_container(self.article_title, e.options[:8])
            view = discord.ui.View(container, timeout=None)
            await interaction.followup.send(view=view, ephemeral=True)
        except wikipedia.PageError:
            container = create_error_container("Artikel nicht gefunden", 
                                              f"'{self.article_title}' existiert nicht.")
            view = discord.ui.View(container, timeout=None)
            await interaction.followup.send(view=view, ephemeral=True)
        except Exception as e:
            container = create_error_container("Fehler beim Laden", str(e)[:500])
            view = discord.ui.View(container, timeout=None)
            await interaction.followup.send(view=view, ephemeral=True)

class RandomArticleButton(Button):
    def __init__(self, language: str, cog_instance=None):
        self.language = language
        self.cog = cog_instance
        super().__init__(
            label="🎲 Zufälliger Artikel",
            style=discord.ButtonStyle.success
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            loading_container = create_loading_container("Lade zufälligen Artikel...")
            view = discord.ui.View(loading_container, timeout=None)
            await interaction.edit_original_response(view=view)

            random_title = wikipedia.random()
            page = wikipedia.page(random_title)
            info = format_page_info(page, self.language)

            similar_articles = wikipedia.search(random_title, results=6)
            similar_articles = [a for a in similar_articles if a.lower() != info['title'].lower()]

            container = create_article_container(info, interaction.user, similar_articles[:4], 
                                                random_title, self.language, cog_instance=self.cog)
            
            # Header anpassen für zufälligen Artikel
            container_new = Container()
            container_new.add_text(f"🎲 **Zufälliger Artikel: {info['title']}**")
            # Restlichen Inhalt kopieren (vereinfachte Version - in Produktion würde man den Container besser strukturieren)
            
            view = discord.ui.View(container, timeout=WIKI_CONFIG['timeout'])
            await interaction.edit_original_response(view=view)

        except Exception as e:
            container = create_error_container("Fehler beim Laden", 
                                              f"Zufälliger Artikel konnte nicht geladen werden: {str(e)[:300]}")
            view = discord.ui.View(container, timeout=None)
            await interaction.edit_original_response(view=view)

class ArticleInfoButton(Button):
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
        
        # Statistiken
        stats_text = f"🌐 **Sprache:** {WIKI_CONFIG['languages'][self.language]['name']}\n"
        stats_text += f"📂 **Kategorien:** {len(self.info.get('categories', []))}\n"
        stats_text += f"🔗 **Verweise:** {len(self.info.get('links', []))}"
        container.add_text(stats_text)
        
        if self.info.get('coordinates'):
            lat, lon = self.info['coordinates']
            container.add_text(f"🗺️ **Koordinaten:** {lat:.2f}°N, {lon:.2f}°E")
        
        if self.info.get('images'):
            container.add_text(f"🖼️ **Bilder:** {len(self.info['images'])}")
        
        # Kategorien auflisten
        if self.info.get('categories'):
            container.add_separator()
            container.add_text("📚 **Hauptkategorien:**")
            categories_text = "\n".join([f"• {cat}" for cat in self.info['categories'][:5]])
            container.add_text(categories_text)
        
        container.add_separator()
        container.add_text("Wikipedia • Artikel-Statistiken")
        
        view = discord.ui.View(container, timeout=300)
        await interaction.followup.send(view=view, ephemeral=True)

class RefreshArticleButton(Button):
    def __init__(self, search_term: str, language: str, cog_instance=None):
        self.search_term = search_term
        self.language = language
        self.cog = cog_instance
        super().__init__(
            label="🔄 Aktualisieren",
            style=discord.ButtonStyle.secondary
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            # Cache leeren
            cache_key = f"{self.search_term}_{self.language}"
            if cache_key in wiki_cache.cache:
                del wiki_cache.cache[cache_key]
                del wiki_cache.timestamps[cache_key]

            loading_container = create_loading_container("Aktualisiere Artikel...")
            view = discord.ui.View(loading_container, timeout=None)
            await interaction.edit_original_response(view=view)

            page = wikipedia.page(self.search_term)
            info = format_page_info(page, self.language)

            similar_articles = wikipedia.search(self.search_term, results=6)
            similar_articles = [a for a in similar_articles if a.lower() != info['title'].lower()]

            container = create_article_container(info, interaction.user, similar_articles[:4], 
                                                self.search_term, self.language, cog_instance=self.cog)
            view = discord.ui.View(container, timeout=WIKI_CONFIG['timeout'])
            await interaction.edit_original_response(view=view)

        except Exception as e:
            container = create_error_container("Aktualisierung fehlgeschlagen", str(e)[:500])
            view = discord.ui.View(container, timeout=None)
            await interaction.edit_original_response(view=view)

# ───────────────────────────────────────────────
# >> Autocomplete Functions
# ───────────────────────────────────────────────
async def enhanced_wiki_autocomplete(ctx: discord.AutocompleteContext):
    """Erweiterte Autocomplete mit Caching"""
    suchwert = ctx.value or ""

    if len(suchwert) < 2:
        return [
            "Künstliche Intelligenz", "Python (Programmiersprache)", "Discord",
            "Deutschland", "Wikipedia", "Klimawandel", "Quantenphysik", "Internet"
        ]

    try:
        cache_key = f"autocomplete_{suchwert}_de"
        cached_results = wiki_cache.get(cache_key)

        if cached_results:
            return cached_results.get('suggestions', [])

        vorschlaege = wikipedia.search(suchwert, results=15)

        def relevance_score(suggestion):
            suggestion_lower = suggestion.lower()
            suchwert_lower = suchwert.lower()

            if suchwert_lower == suggestion_lower:
                return 0
            elif suggestion_lower.startswith(suchwert_lower):
                return 1
            elif suchwert_lower in suggestion_lower:
                return 2
            else:
                return 3 + len(suggestion)

        vorschlaege.sort(key=relevance_score)
        final_suggestions = vorschlaege[:25]

        wiki_cache.set(cache_key, {'suggestions': final_suggestions})

        return final_suggestions

    except Exception:
        return ["Fehler bei der Suche - bitte erneut versuchen"]

# ───────────────────────────────────────────────
# >> Main Cog Class
# ───────────────────────────────────────────────
class WikipediaCog(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_language = 'de'
        self.cleanup_task = None
        self.stats = {
            'searches': 0,
            'articles_viewed': 0,
            'languages_used': set(),
            'start_time': datetime.now()
        }

    @ezcord.Cog.listener()
    async def on_ready(self):
        if self.cleanup_task is None:
            self.cleanup_task = self.bot.loop.create_task(self._cleanup_cache())

    async def _cleanup_cache(self):
        """Regelmäßige Cache-Bereinigung"""
        while True:
            try:
                await asyncio.sleep(300)
                wiki_cache.clear_expired()
            except:
                pass

    def cog_unload(self):
        if hasattr(self, 'cleanup_task') and self.cleanup_task:
            self.cleanup_task.cancel()

    @slash_command(name="wiki_search", description="🔍 Durchsuche Wikipedia nach Artikeln und Informationen")
    async def wikipedia_search(
            self,
            ctx: discord.ApplicationContext,
            suchbegriff: discord.Option(
                str,
                "Was möchtest du auf Wikipedia nachschlagen?",
                autocomplete=enhanced_wiki_autocomplete,
                max_length=100
            ),
            sprache: discord.Option(
                str,
                "Sprache für die Suche",
                choices=[
                    discord.OptionChoice(name="🇩🇪 Deutsch", value="de"),
                    discord.OptionChoice(name="🇺🇸 English", value="en"),
                    discord.OptionChoice(name="🇫🇷 Français", value="fr"),
                    discord.OptionChoice(name="🇪🇸 Español", value="es"),
                    discord.OptionChoice(name="🇮🇹 Italiano", value="it"),
                    discord.OptionChoice(name="🇯🇵 日本語", value="ja"),
                    discord.OptionChoice(name="🇷🇺 Русский", value="ru"),
                ],
                default="de",
                required=False
            )
    ):
        await ctx.defer()

        self.stats['searches'] += 1
        self.stats['languages_used'].add(sprache)

        original_lang = self.current_language
        if sprache != original_lang:
            wikipedia.set_lang(sprache)
            self.current_language = sprache

        try:
            cache_key = f"{suchbegriff}_{sprache}"
            cached_info = wiki_cache.get(cache_key)

            if cached_info:
                info = cached_info
            else:
                page = wikipedia.page(suchbegriff)
                info = format_page_info(page, sprache)
                wiki_cache.set(cache_key, info)

            self.stats['articles_viewed'] += 1

            similar_articles = wikipedia.search(suchbegriff, results=8)
            similar_articles = [a for a in similar_articles if a.lower() != info['title'].lower()]

            container = create_article_container(info, ctx.author, similar_articles[:6], 
                                                suchbegriff, sprache, cog_instance=self)
            view = discord.ui.View(container, timeout=WIKI_CONFIG['timeout'])

            await ctx.respond(view=view)

        except wikipedia.DisambiguationError as e:
            container = create_disambiguation_container(suchbegriff, e.options[:12], sprache)
            view = discord.ui.View(container, timeout=None)
            await ctx.respond(view=view)

        except wikipedia.PageError:
            error_text = f"Kein Wikipedia-Artikel für **'{suchbegriff}'** in {WIKI_CONFIG['languages'][sprache]['name']} gefunden."
            
            try:
                suggestions = wikipedia.search(suchbegriff, results=5)
                if suggestions:
                    error_text += "\n\n💡 **Meintest du vielleicht:**\n"
                    error_text += "\n".join([f"• {s}" for s in suggestions])
            except:
                pass

            container = create_error_container("Artikel nicht gefunden", error_text)
            view = discord.ui.View(container, timeout=None)
            await ctx.respond(view=view)

        except Exception as e:
            container = create_error_container("Unerwarteter Fehler", f"```py\n{str(e)[:800]}\n```")
            view = discord.ui.View(container, timeout=None)
            await ctx.respond(view=view)

        finally:
            if sprache != original_lang:
                wikipedia.set_lang(original_lang)
                self.current_language = original_lang

    @slash_command(name="wiki_random", description="🎲 Zeige einen zufälligen Wikipedia-Artikel")
    async def wiki_random(
            self,
            ctx: discord.ApplicationContext,
            sprache: discord.Option(
                str,
                "Sprache für den zufälligen Artikel",
                choices=[
                    discord.OptionChoice(name="🇩🇪 Deutsch", value="de"),
                    discord.OptionChoice(name="🇺🇸 English", value="en"),
                    discord.OptionChoice(name="🇫🇷 Français", value="fr"),
                    discord.OptionChoice(name="🇪🇸 Español", value="es"),
                    discord.OptionChoice(name="🇮🇹 Italiano", value="it"),
                    discord.OptionChoice(name="🇯🇵 日本語", value="ja"),
                    discord.OptionChoice(name="🇷🇺 Русский", value="ru"),
                ],
                default="de",
                required=False
            ),
            anzahl: discord.Option(int, "Anzahl zufälliger Artikel (1-5)", min_value=1, max_value=5, default=1)
    ):
        await ctx.defer()

        original_lang = self.current_language
        if sprache != original_lang:
            wikipedia.set_lang(sprache)
            self.current_language = sprache

        try:
            if anzahl == 1:
                random_title = wikipedia.random()
                page = wikipedia.page(random_title)
                info = format_page_info(page, sprache)

                similar_articles = wikipedia.search(random_title, results=6)
                similar_articles = [a for a in similar_articles if a.lower() != info['title'].lower()]

                container = create_article_container(info, ctx.author, similar_articles[:4], 
                                                    random_title, sprache, cog_instance=self)
                
                # Titel für zufälligen Artikel anpassen
                container_random = Container()
                container_random.add_text(f"🎲 **Zufälliger Artikel: {info['title']}**")
                lang_info = WIKI_CONFIG['languages'].get(sprache, {'name': 'Deutsch', 'flag': '🇩🇪'})
                container_random.add_text(f"{lang_info['flag']} {lang_info['name']} • Wikipedia")
                container_random.add_separator()
                
                # Zusammenfassung und Rest vom Original-Container
                summary_text = info['summary'][:800] + ("..." if len(info['summary']) > 800 else "")
                container_random.add_text(summary_text)
                
                if info.get('categories'):
                    container_random.add_separator()
                    categories_text = "📂 **Kategorien:** " + ", ".join(info['categories'][:3])
                    if len(info['categories']) > 3:
                        categories_text += f" (+{len(info['categories']) - 3} weitere)"
                    container_random.add_text(categories_text)
                
                if info.get('coordinates'):
                    lat, lon = info['coordinates']
                    container_random.add_text(f"🗺️ **Standort:** {lat:.2f}°N, {lon:.2f}°E")
                
                container_random.add_separator()
                
                if info.get('url'):
                    link_button = Button(label="🔗 Vollständigen Artikel lesen", url=info['url'], 
                                       style=discord.ButtonStyle.link)
                    container_random.add_item(link_button)
                
                lang_select = LanguageSelectContainer(random_title, sprache, self)
                container_random.add_item(lang_select)
                
                if similar_articles:
                    container_random.add_separator()
                    container_random.add_text("📚 **Ähnliche Artikel:**")
                    for article in similar_articles[:4]:
                        article_btn = ArticleButtonContainer(article, "similar", self)
                        container_random.add_item(article_btn)
                
                container_random.add_separator()
                
                random_btn = RandomArticleButton(sprache, self)
                container_random.add_item(random_btn)
                
                info_btn = ArticleInfoButton(info, sprache)
                container_random.add_item(info_btn)
                
                refresh_btn = RefreshArticleButton(random_title, sprache, self)
                container_random.add_item(refresh_btn)
                
                container_random.add_separator()
                container_random.add_text(f"👤 Angefragt von {ctx.author.display_name}")
                
                view = discord.ui.View(container_random, timeout=WIKI_CONFIG['timeout'])
                await ctx.respond(view=view)

            else:
                # Mehrere zufällige Artikel
                lang_info = WIKI_CONFIG['languages'][sprache]
                container = Container()
                container.add_text(f"🎲 **{anzahl} Zufällige Artikel**")
                container.add_text(f"Entdecke neue Themen in {lang_info['flag']} {lang_info['name']}:")
                container.add_separator()

                random_articles = []
                for i in range(anzahl):
                    try:
                        random_title = wikipedia.random()
                        summary = clean_text(wikipedia.summary(random_title, sentences=1), 200)
                        random_articles.append(random_title)

                        container.add_text(f"**{i + 1}. {random_title}**")
                        container.add_text(summary)
                        container.add_separator()
                    except:
                        container.add_text(f"**{i + 1}. Artikel nicht verfügbar**")
                        container.add_text("Dieser Artikel konnte nicht geladen werden.")
                        container.add_separator()

                # Buttons für die ersten Artikel
                if random_articles:
                    container.add_text("📚 **Artikel öffnen:**")
                    for article in random_articles[:4]:
                        article_btn = ArticleButtonContainer(article, "similar", self)
                        container.add_item(article_btn)
                
                container.add_separator()
                container.add_text(f"Wikipedia • {anzahl} zufällige Artikel")

                view = discord.ui.View(container, timeout=WIKI_CONFIG['timeout'])
                await ctx.respond(view=view)

        except Exception as e:
            container = create_error_container("Fehler beim Laden", 
                                              f"Zufällige Artikel konnten nicht geladen werden: {str(e)[:500]}")
            view = discord.ui.View(container, timeout=None)
            await ctx.respond(view=view)
        finally:
            if sprache != original_lang:
                wikipedia.set_lang(original_lang)
                self.current_language = original_lang

    @slash_command(name="wiki_multisearch", description="🔍 Erweiterte Wikipedia-Suche mit mehreren Ergebnissen")
    async def wiki_multi_search(
            self,
            ctx: discord.ApplicationContext,
            suchbegriff: discord.Option(str, "Suchbegriff für erweiterte Suche", max_length=100),
            anzahl: discord.Option(int, "Anzahl der Ergebnisse (1-15)", min_value=1, max_value=15, default=8),
            sprache: discord.Option(
                str,
                "Sprache für die Suche",
                choices=[
                    discord.OptionChoice(name="Deutsch", value="de"),
                    discord.OptionChoice(name="English", value="en"),
                    discord.OptionChoice(name="Français", value="fr"),
                    discord.OptionChoice(name="Español", value="es"),
                    discord.OptionChoice(name="Italiano", value="it"),
                    discord.OptionChoice(name="日本語", value="ja"),
                    discord.OptionChoice(name="Русский", value="ru"),
                ],
                default="de",
                required=False
            )
    ):
        await ctx.defer()

        original_lang = self.current_language
        if sprache != original_lang:
            wikipedia.set_lang(sprache)
            self.current_language = sprache

        try:
            results = wikipedia.search(suchbegriff, results=anzahl)

            if not results:
                container = create_error_container(
                    "Keine Ergebnisse",
                    f"Keine Artikel für **'{suchbegriff}'** in {WIKI_CONFIG['languages'][sprache]['name']} gefunden."
                )
                view = discord.ui.View(container, timeout=None)
                await ctx.respond(view=view)
                return

            lang_info = WIKI_CONFIG['languages'][sprache]
            container = Container()
            container.add_text(f"🔍 **Suchergebnisse für '{suchbegriff}'**")
            container.add_text(f"**{len(results)} Ergebnisse** in {lang_info['flag']} {lang_info['name']}:")
            container.add_separator()

            for i, result in enumerate(results, 1):
                try:
                    summary = wikipedia.summary(result, sentences=1)
                    summary = clean_text(summary, 150)
                except:
                    summary = "Keine Vorschau verfügbar."

                container.add_text(f"**{i}. {result}**")
                container.add_text(summary)
                container.add_separator()

            # Erste Ergebnisse als Buttons
            container.add_text("📚 **Artikel öffnen:**")
            for result in results[:4]:
                article_btn = ArticleButtonContainer(result, "similar", self)
                container.add_item(article_btn)

            container.add_separator()
            container.add_text(f"Wikipedia • {len(results)} Ergebnisse • Sprache: {lang_info['name']}")

            view = discord.ui.View(container, timeout=WIKI_CONFIG['timeout'])
            await ctx.respond(view=view)

        except Exception as e:
            container = create_error_container("Suchfehler", f"Fehler bei der Suche: {str(e)[:500]}")
            view = discord.ui.View(container, timeout=None)
            await ctx.respond(view=view)
        finally:
            if sprache != original_lang:
                wikipedia.set_lang(original_lang)
                self.current_language = original_lang

    @slash_command(name="wiki_stats", description="📊 Zeige Bot-Statistiken und Wikipedia-Informationen")
    async def wiki_statistics(self, ctx: discord.ApplicationContext):
        uptime = datetime.now() - self.stats['start_time']
        uptime_str = f"{uptime.days}d {uptime.seconds // 3600}h {(uptime.seconds // 60) % 60}m"

        container = Container()
        container.add_text("📊 **Wikipedia Bot Statistiken**")
        container.add_separator()
        
        stats_text = f"🔍 **Suchanfragen:** {self.stats['searches']:,}\n"
        stats_text += f"📖 **Artikel angezeigt:** {self.stats['articles_viewed']:,}\n"
        stats_text += f"⏱️ **Laufzeit:** {uptime_str}"
        container.add_text(stats_text)
        
        container.add_separator()
        
        lang_names = [WIKI_CONFIG['languages'][lang]['name'] for lang in self.stats['languages_used']]
        if lang_names:
            container.add_text(f"🌐 **Verwendete Sprachen:** {', '.join(lang_names)}")
        else:
            container.add_text("🌐 **Verwendete Sprachen:** Keine")
        
        container.add_separator()
        
        all_langs = [f"{info['flag']} {info['name']}" for info in WIKI_CONFIG['languages'].values()]
        container.add_text("📚 **Verfügbare Sprachen:**")
        container.add_text(", ".join(all_langs))
        
        container.add_separator()
        
        tech_text = f"💾 **Cache-Einträge:** {len(wiki_cache.cache)}\n"
        tech_text += f"⚡ **Rate Limiting:** Aktiviert\n"
        tech_text += f"🔧 **Features:** Suche, Zufällig, Multi-Sprache, Cache"
        container.add_text(tech_text)
        
        container.add_separator()
        container.add_text("Wikipedia Bot • Erweiterte Funktionen verfügbar")

        view = discord.ui.View(container, timeout=None)
        await ctx.respond(view=view)

    @slash_command(name="wiki_category", description="📂 Durchsuche Wikipedia-Kategorien")
    async def wiki_category(
            self,
            ctx: discord.ApplicationContext,
            kategorie: discord.Option(str, "Name der Kategorie", max_length=100),
            sprache: discord.Option(
                str,
                "Sprache für die Kategorie-Suche",
                choices=[
                    discord.OptionChoice(name="🇩🇪 Deutsch", value="de"),
                    discord.OptionChoice(name="🇺🇸 English", value="en"),
                    discord.OptionChoice(name="🇫🇷 Français", value="fr"),
                    discord.OptionChoice(name="🇪🇸 Español", value="es"),
                    discord.OptionChoice(name="🇮🇹 Italiano", value="it"),
                    discord.OptionChoice(name="🇯🇵 日本語", value="ja"),
                    discord.OptionChoice(name="🇷🇺 Русский", value="ru"),
                ],
                default="de",
                required=False
            )
    ):
        await ctx.defer()

        original_lang = self.current_language
        if sprache != original_lang:
            wikipedia.set_lang(sprache)
            self.current_language = sprache

        try:
            search_results = wikipedia.search(f"Kategorie:{kategorie}", results=10)
            if not search_results:
                search_results = wikipedia.search(kategorie, results=10)

            if not search_results:
                container = create_error_container(
                    "Kategorie nicht gefunden",
                    f"Keine Artikel in der Kategorie **'{kategorie}'** gefunden."
                )
                view = discord.ui.View(container, timeout=None)
                await ctx.respond(view=view)
                return

            lang_info = WIKI_CONFIG['languages'][sprache]
            container = Container()
            container.add_text(f"📂 **Kategorie: {kategorie}**")
            container.add_text(f"Artikel in dieser Kategorie ({lang_info['flag']} {lang_info['name']}):")
            container.add_separator()

            for i, result in enumerate(search_results[:8], 1):
                try:
                    summary = wikipedia.summary(result, sentences=1)
                    summary = clean_text(summary, 150)
                except:
                    summary = "Keine Beschreibung verfügbar."

                container.add_text(f"**{i}. {result}**")
                container.add_text(summary)
                container.add_separator()

            # Artikel als Buttons
            container.add_text("📚 **Artikel öffnen:**")
            for result in search_results[:4]:
                article_btn = ArticleButtonContainer(result, "category", self)
                container.add_item(article_btn)

            container.add_separator()
            container.add_text(f"Wikipedia • Kategorie-Suche • {len(search_results)} Ergebnisse")

            view = discord.ui.View(container, timeout=WIKI_CONFIG['timeout'])
            await ctx.respond(view=view)

        except Exception as e:
            container = create_error_container("Kategorie-Fehler", 
                                              f"Fehler beim Laden der Kategorie: {str(e)[:500]}")
            view = discord.ui.View(container, timeout=None)
            await ctx.respond(view=view)
        finally:
            if sprache != original_lang:
                wikipedia.set_lang(original_lang)
                self.current_language = original_lang

    @slash_command(name="wiki_cache", description="🗑️ Cache-Management (nur für Administratoren)")
    @discord.default_permissions(administrator=True)
    async def wiki_cache_management(
            self,
            ctx: discord.ApplicationContext,
            aktion: discord.Option(
                str,
                "Cache-Aktion",
                choices=[
                    discord.OptionChoice(name="📊 Status anzeigen", value="status"),
                    discord.OptionChoice(name="🗑️ Cache leeren", value="clear"),
                    discord.OptionChoice(name="⏰ Abgelaufene entfernen", value="cleanup")
                ]
            )
    ):
        if not ctx.author.guild_permissions.administrator:
            container = create_error_container("Berechtigung verweigert", 
                                              "Nur Administratoren können Cache-Befehle verwenden.")
            view = discord.ui.View(container, timeout=None)
            await ctx.respond(view=view, ephemeral=True)
            return

        await ctx.defer(ephemeral=True)

        if aktion == "status":
            total_entries = len(wiki_cache.cache)
            expired_count = 0
            now = datetime.now()

            for key, timestamp in wiki_cache.timestamps.items():
                if now - timestamp >= timedelta(seconds=WIKI_CONFIG['cache_duration']):
                    expired_count += 1

            container = Container()
            container.add_text("💾 **Cache-Status**")
            container.add_separator()
            
            status_text = f"📊 **Gesamt-Einträge:** {total_entries}\n"
            status_text += f"⏰ **Abgelaufene Einträge:** {expired_count}\n"
            status_text += f"✅ **Aktive Einträge:** {total_entries - expired_count}\n"
            status_text += f"⚙️ **Cache-Dauer:** {WIKI_CONFIG['cache_duration']} Sekunden"
            container.add_text(status_text)

            view = discord.ui.View(container, timeout=None)
            await ctx.respond(view=view, ephemeral=True)

        elif aktion == "clear":
            old_count = len(wiki_cache.cache)
            wiki_cache.cache.clear()
            wiki_cache.timestamps.clear()

            container = Container()
            container.add_text("🗑️ **Cache geleert**")
            container.add_separator()
            container.add_text(f"**{old_count}** Einträge wurden entfernt.")

            view = discord.ui.View(container, timeout=None)
            await ctx.respond(view=view, ephemeral=True)

        elif aktion == "cleanup":
            old_count = len(wiki_cache.cache)
            wiki_cache.clear_expired()
            new_count = len(wiki_cache.cache)
            removed = old_count - new_count

            container = Container()
            container.add_text("⏰ **Cache bereinigt**")
            container.add_separator()
            container.add_text(f"**{removed}** abgelaufene Einträge entfernt.\n**{new_count}** Einträge verbleiben.")

            view = discord.ui.View(container, timeout=None)
            await ctx.respond(view=view, ephemeral=True)


def setup(bot):
    bot.add_cog(WikipediaCog(bot))