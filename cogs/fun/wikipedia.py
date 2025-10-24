# Copyright (c) 2025 OPPRO.NET Network
# ───────────────────────────────────────────────
# >> Imports
# ───────────────────────────────────────────────
import wikipedia
import asyncio
import re
import discord
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from discord import SlashCommandGroup, InteractionContextType, IntegrationType, slash_command
import ezcord

# Fallback für Farben falls nicht in FastCoding definiert
try:
    from DevTools import INFO_COLOR, ERROR_COLOR, SUCCESS_COLOR, WARNING_COLOR
except ImportError:
    # Eigene Farbdefinitionen als Fallback
    INFO_COLOR = discord.Color.blue()
    ERROR_COLOR = discord.Color.red()
    SUCCESS_COLOR = discord.Color.green()
    WARNING_COLOR = discord.Color.orange()
# ───────────────────────────────────────────────
# >> Settings & Configuration
# ───────────────────────────────────────────────
wikipedia.set_lang("de")
wikipedia.set_rate_limiting(True)

# Erweiterte Konfiguration
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
    'cache_duration': 300  # 5 Minuten
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
                # Cache abgelaufen
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


# Globaler Cache
wiki_cache = WikiCache()


# ───────────────────────────────────────────────
# >> Utility Functions
# ───────────────────────────────────────────────
def clean_text(text: str, max_length: int = None) -> str:
    """Erweiterte Textbereinigung"""
    if not text:
        return "Keine Beschreibung verfügbar."

    # HTML-Tags und Sonderzeichen entfernen
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\[.*?\]', '', text)  # Referenzen entfernen
    text = re.sub(r'\s+', ' ', text).strip()

    max_length = max_length or WIKI_CONFIG['max_summary_length']
    if len(text) > max_length:
        # Bei Satzende abschneiden wenn möglich
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

        # Summary sicher laden
        try:
            info['summary'] = clean_text(wikipedia.summary(page.title, sentences=4))
        except:
            info['summary'] = "Zusammenfassung nicht verfügbar."

        # Zusätzliche Informationen sicher laden
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

        # Koordinaten extrahieren falls vorhanden
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


def create_loading_embed(title: str = "Lade Wikipedia-Artikel...") -> discord.Embed:
    """Erstellt einen Lade-Embed"""
    embed = discord.Embed(
        title=f"⏳ {title}",
        description="Dies kann einen Moment dauern...",
        color=discord.Color.blue()
    )
    return embed


# ───────────────────────────────────────────────
# >> Advanced UI Components
# ───────────────────────────────────────────────
class LanguageSelect(discord.ui.Select):
    def __init__(self, current_term: str, current_lang: str = 'de', cog_instance=None):
        self.current_term = current_term
        self.current_lang = current_lang
        self.cog = cog_instance

        options = []
        for code, info in WIKI_CONFIG['languages'].items():
            options.append(discord.SelectOption(
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
            await interaction.followup.send("Diese Sprache ist bereits ausgewählt.", ephemeral=True)
            return

        # Sprache wechseln und neu suchen
        original_lang = self.cog.current_language if self.cog else 'de'
        if selected_lang != original_lang:
            wikipedia.set_lang(selected_lang)
            if self.cog:
                self.cog.current_language = selected_lang

        try:
            loading_embed = create_loading_embed(
                f"Lade Artikel in {WIKI_CONFIG['languages'][selected_lang]['name']}...")
            await interaction.edit_original_response(embed=loading_embed, view=None)

            page = wikipedia.page(self.current_term)
            info = format_page_info(page, selected_lang)

            embed = create_main_embed(info, interaction.user)
            view = EnhancedWikiView(info, self.current_term, selected_lang, cog_instance=self.cog)

            await interaction.edit_original_response(embed=embed, view=view)

        except wikipedia.DisambiguationError as e:
            embed = create_disambiguation_embed(self.current_term, e.options[:10], selected_lang)
            await interaction.edit_original_response(embed=embed, view=None)
        except wikipedia.PageError:
            embed = create_error_embed(
                "Artikel nicht gefunden",
                f"'{self.current_term}' existiert nicht in {WIKI_CONFIG['languages'][selected_lang]['name']}."
            )
            await interaction.edit_original_response(embed=embed, view=None)
        except Exception as e:
            embed = create_error_embed("Unerwarteter Fehler", str(e))
            await interaction.edit_original_response(embed=embed, view=None)
        finally:
            if selected_lang != original_lang:
                wikipedia.set_lang(original_lang)
                if self.cog:
                    self.cog.current_language = original_lang


class ArticleButton(discord.ui.Button):
    def __init__(self, article_title: str, button_type: str = "similar", cog_instance=None):
        self.article_title = article_title
        self.button_type = button_type
        self.cog = cog_instance

        # Button-Styling basierend auf Typ
        if button_type == "similar":
            emoji = "📖"
            style = discord.ButtonStyle.secondary
        elif button_type == "category":
            emoji = "📂"
            style = discord.ButtonStyle.primary
        elif button_type == "link":
            emoji = "🔗"
            style = discord.ButtonStyle.success
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
            # Cache-Check
            current_lang = self.cog.current_language if self.cog else 'de'
            cache_key = f"{self.article_title}_{current_lang}"
            cached_info = wiki_cache.get(cache_key)

            if cached_info:
                info = cached_info
            else:
                page = wikipedia.page(self.article_title)
                info = format_page_info(page, current_lang)
                wiki_cache.set(cache_key, info)

            embed = create_main_embed(info, interaction.user, ephemeral=True)

            # Ähnliche Artikel für neue View
            similar_articles = wikipedia.search(self.article_title, results=8)
            similar_articles = [a for a in similar_articles if a.lower() != info['title'].lower()]

            view = EnhancedWikiView(info, self.article_title, current_lang, similar_articles[:4], cog_instance=self.cog)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        except wikipedia.DisambiguationError as e:
            embed = create_disambiguation_embed(self.article_title, e.options[:8])
            await interaction.followup.send(embed=embed, ephemeral=True)
        except wikipedia.PageError:
            embed = create_error_embed("Artikel nicht gefunden", f"'{self.article_title}' existiert nicht.")
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = create_error_embed("Fehler beim Laden", str(e)[:500])
            await interaction.followup.send(embed=embed, ephemeral=True)


class EnhancedWikiView(discord.ui.View):
    def __init__(self, info: Dict[str, Any], search_term: str, language: str = 'de',
                 similar_articles: List[str] = None, timeout: float = None, cog_instance=None):
        super().__init__(timeout=timeout or WIKI_CONFIG['timeout'])

        self.info = info
        self.search_term = search_term
        self.language = language
        self.cog = cog_instance
        self.message = None  # Will be set later

        # Hauptlink zur Wikipedia-Seite
        if info.get('url'):
            self.add_item(discord.ui.Button(
                label="🔗 Vollständigen Artikel lesen",
                url=info['url'],
                style=discord.ButtonStyle.link
            ))

        # Ähnliche Artikel
        if similar_articles:
            for article in similar_articles[:4]:
                self.add_item(ArticleButton(article, "similar", cog_instance=self.cog))

        # Sprachauswahl
        self.add_item(LanguageSelect(search_term, language, cog_instance=self.cog))

        # Kategorien als Buttons (falls Platz)
        if info.get('categories') and len(self.children) < 20:
            for category in info['categories'][:2]:
                if len(self.children) < 24:  # Platz für andere Buttons lassen
                    self.add_item(ArticleButton(category, "category", cog_instance=self.cog))

    @discord.ui.button(label="🎲 Zufälliger Artikel", style=discord.ButtonStyle.success, row=4)
    async def random_article(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            loading_embed = create_loading_embed("Lade zufälligen Artikel...")
            await interaction.edit_original_response(embed=loading_embed, view=None)

            random_title = wikipedia.random()
            page = wikipedia.page(random_title)
            info = format_page_info(page, self.language)

            embed = create_main_embed(info, interaction.user)
            embed.title = f"🎲 Zufälliger Artikel: {info['title']}"

            similar_articles = wikipedia.search(random_title, results=6)
            similar_articles = [a for a in similar_articles if a.lower() != info['title'].lower()]

            new_view = EnhancedWikiView(info, random_title, self.language, similar_articles[:4], cog_instance=self.cog)
            await interaction.edit_original_response(embed=embed, view=new_view)

        except Exception as e:
            embed = create_error_embed("Fehler beim Laden", f"Zufälliger Artikel konnte nicht geladen werden: {e}")
            await interaction.edit_original_response(embed=embed, view=None)

    @discord.ui.button(label="📊 Artikel-Info", style=discord.ButtonStyle.primary, row=4)
    async def article_info(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        embed = discord.Embed(
            title=f"📊 Informationen zu '{self.info['title']}'",
            color=INFO_COLOR
        )

        # Grundlegende Infos
        embed.add_field(name="🌐 Sprache", value=WIKI_CONFIG['languages'][self.language]['name'], inline=True)
        embed.add_field(name="📂 Kategorien", value=str(len(self.info.get('categories', []))), inline=True)
        embed.add_field(name="🔗 Verweise", value=str(len(self.info.get('links', []))), inline=True)

        # Zusätzliche Infos falls verfügbar
        if self.info.get('coordinates'):
            lat, lon = self.info['coordinates']
            embed.add_field(name="🗺️ Koordinaten", value=f"{lat:.2f}°N, {lon:.2f}°E", inline=True)

        if self.info.get('images'):
            embed.add_field(name="🖼️ Bilder", value=str(len(self.info['images'])), inline=True)

        # Kategorien auflisten falls vorhanden
        if self.info.get('categories'):
            categories_text = "\n".join([f"• {cat}" for cat in self.info['categories'][:5]])
            embed.add_field(name="📚 Hauptkategorien", value=categories_text, inline=False)

        embed.set_footer(text="Wikipedia • Artikel-Statistiken")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="🔄 Aktualisieren", style=discord.ButtonStyle.secondary, row=4)
    async def refresh_article(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            # Cache leeren für diesen Artikel
            cache_key = f"{self.search_term}_{self.language}"
            if cache_key in wiki_cache.cache:
                del wiki_cache.cache[cache_key]
                del wiki_cache.timestamps[cache_key]

            loading_embed = create_loading_embed("Aktualisiere Artikel...")
            await interaction.edit_original_response(embed=loading_embed, view=None)

            # Artikel neu laden
            page = wikipedia.page(self.search_term)
            info = format_page_info(page, self.language)

            embed = create_main_embed(info, interaction.user)
            similar_articles = wikipedia.search(self.search_term, results=6)
            similar_articles = [a for a in similar_articles if a.lower() != info['title'].lower()]

            new_view = EnhancedWikiView(info, self.search_term, self.language, similar_articles[:4],
                                        cog_instance=self.cog)
            await interaction.edit_original_response(embed=embed, view=new_view)

        except Exception as e:
            embed = create_error_embed("Aktualisierung fehlgeschlagen", str(e))
            await interaction.edit_original_response(embed=embed, view=None)

    async def on_timeout(self):
        # Nur interaktive Buttons deaktivieren, Links beibehalten
        for item in self.children:
            if hasattr(item, 'disabled') and not (hasattr(item, 'url') and item.url):
                item.disabled = True

        try:
            if self.message:
                await self.message.edit(view=self)
        except:
            pass


# ───────────────────────────────────────────────
# >> Embed Creation Functions
# ───────────────────────────────────────────────
def create_main_embed(info: Dict[str, Any], user: discord.User, ephemeral: bool = False) -> discord.Embed:
    """Erstellt das Haupt-Embed für einen Wikipedia-Artikel"""
    embed = discord.Embed(
        title=f"📖 {info['title']}",
        description=info['summary'],
        url=info.get('url', ''),
        color=INFO_COLOR,
        timestamp=datetime.now()
    )

    # Zusätzliche Informationen
    if info.get('categories'):
        categories_text = ", ".join(info['categories'][:3])
        if len(info['categories']) > 3:
            categories_text += f" (+{len(info['categories']) - 3} weitere)"
        embed.add_field(name="📂 Kategorien", value=categories_text, inline=False)

    # Koordinaten falls verfügbar
    if info.get('coordinates'):
        lat, lon = info['coordinates']
        embed.add_field(name="🗺️ Standort", value=f"{lat:.2f}°N, {lon:.2f}°E", inline=True)

    # Footer mit Benutzerinfo
    lang_info = WIKI_CONFIG['languages'].get(info.get('language', 'de'), {'name': 'Deutsch', 'flag': '🇩🇪'})
    footer_text = f"Wikipedia ({lang_info['name']}) • Angefragt von {user.display_name}"
    if ephemeral:
        footer_text += " • Nur für dich sichtbar"

    embed.set_footer(
        text=footer_text,
        icon_url=user.avatar.url if user.avatar else None
    )

    # Thumbnail
    if info.get('images'):
        try:
            embed.set_thumbnail(url=info['images'][0])
        except:
            pass

    return embed


def create_error_embed(title: str, description: str) -> discord.Embed:
    """Erstellt ein Fehler-Embed"""
    embed = discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=ERROR_COLOR
    )
    embed.set_footer(text="Wikipedia Bot • Fehler aufgetreten")
    return embed


def create_disambiguation_embed(term: str, options: List[str], language: str = 'de') -> discord.Embed:
    """Erstellt ein Mehrdeutigkeits-Embed"""
    lang_info = WIKI_CONFIG['languages'].get(language, {'name': 'Deutsch'})

    embed = discord.Embed(
        title="🔀 Mehrdeutige Suche",
        description=f"**'{term}'** kann mehrere Bedeutungen haben in {lang_info['name']}:",
        color=WARNING_COLOR
    )

    options_text = "\n".join([f"• **{opt}**" for opt in options[:10]])
    embed.add_field(name="📋 Mögliche Optionen:", value=options_text, inline=False)
    embed.set_footer(text="Versuche eine spezifischere Suche oder wähle eine der Optionen.")

    return embed


# ───────────────────────────────────────────────
# >> Autocomplete Functions
# ───────────────────────────────────────────────
async def enhanced_wiki_autocomplete(ctx: discord.AutocompleteContext):
    """Erweiterte Autocomplete mit Caching und besserer Suche"""
    suchwert = ctx.value or ""

    # Standard-Vorschläge für leere Suche
    if len(suchwert) < 2:
        return [
            "Künstliche Intelligenz", "Python (Programmiersprache)", "Discord",
            "Deutschland", "Wikipedia", "Klimawandel", "Quantenphysik", "Internet"
        ]

    try:
        # Cache-Check für Autocomplete
        cache_key = f"autocomplete_{suchwert}_de"  # Verwende 'de' als Standard
        cached_results = wiki_cache.get(cache_key)

        if cached_results:
            return cached_results.get('suggestions', [])

        # Neue Suche
        vorschlaege = wikipedia.search(suchwert, results=15)

        # Relevanz-Sortierung verbessern
        def relevance_score(suggestion):
            suggestion_lower = suggestion.lower()
            suchwert_lower = suchwert.lower()

            # Exakte Übereinstimmung = höchste Priorität
            if suchwert_lower == suggestion_lower:
                return 0
            # Beginnt mit Suchwert = hohe Priorität
            elif suggestion_lower.startswith(suchwert_lower):
                return 1
            # Enthält Suchwert = mittlere Priorität
            elif suchwert_lower in suggestion_lower:
                return 2
            # Sonstige = niedrige Priorität, sortiert nach Länge
            else:
                return 3 + len(suggestion)

        vorschlaege.sort(key=relevance_score)
        final_suggestions = vorschlaege[:25]  # Discord Limit

        # Ergebnis cachen
        wiki_cache.set(cache_key, {'suggestions': final_suggestions})

        return final_suggestions

    except Exception:
        # Fallback bei Fehlern
        return ["Fehler bei der Suche - bitte erneut versuchen"]


# ───────────────────────────────────────────────
# >> Main Cog Class
# ───────────────────────────────────────────────
class WikipediaCog(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_language = 'de'  # Aktuelle Sprache tracken
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
                await asyncio.sleep(300)  # Alle 5 Minuten
                wiki_cache.clear_expired()
            except:
                pass

    def cog_unload(self):
        if hasattr(self, 'cleanup_task') and self.cleanup_task:
            self.cleanup_task.cancel()

    wiki = SlashCommandGroup(
    "wikipedia", 
    "Wikipedia-Funktionen"
    )
    @wiki.command(
            name="search", 
            description="🔍 Durchsuche Wikipedia nach Artikeln und Informationen"
            )
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

        # Statistiken aktualisieren
        self.stats['searches'] += 1
        self.stats['languages_used'].add(sprache)

        # Sprache temporär wechseln
        original_lang = self.current_language
        if sprache != original_lang:
            wikipedia.set_lang(sprache)
            self.current_language = sprache

        try:
            # Cache-Check
            cache_key = f"{suchbegriff}_{sprache}"
            cached_info = wiki_cache.get(cache_key)

            if cached_info:
                info = cached_info
            else:
                page = wikipedia.page(suchbegriff)
                info = format_page_info(page, sprache)
                wiki_cache.set(cache_key, info)

            # Statistiken
            self.stats['articles_viewed'] += 1

            # Hauptembed erstellen
            embed = create_main_embed(info, ctx.author)

            # Ähnliche Artikel finden
            similar_articles = wikipedia.search(suchbegriff, results=8)
            similar_articles = [a for a in similar_articles if a.lower() != info['title'].lower()]

            # Enhanced View erstellen
            view = EnhancedWikiView(info, suchbegriff, sprache, similar_articles[:6], cog_instance=self)

            # FIXED: Directly use ctx.respond() return value as message
            message = await ctx.respond(embed=embed, view=view)
            view.message = message

        except wikipedia.DisambiguationError as e:
            embed = create_disambiguation_embed(suchbegriff, e.options[:12], sprache)
            await ctx.respond(embed=embed)

        except wikipedia.PageError:
            embed = create_error_embed(
                "Artikel nicht gefunden",
                f"Kein Wikipedia-Artikel für **'{suchbegriff}'** in {WIKI_CONFIG['languages'][sprache]['name']} gefunden."
            )

            # Suchvorschläge hinzufügen
            try:
                suggestions = wikipedia.search(suchbegriff, results=5)
                if suggestions:
                    suggestions_text = "\n".join([f"• **{s}**" for s in suggestions])
                    embed.add_field(name="💡 Meintest du vielleicht:", value=suggestions_text, inline=False)
            except:
                pass

            await ctx.respond(embed=embed)

        except Exception as e:
            embed = create_error_embed("Unerwarteter Fehler", f"```py\n{str(e)[:800]}\n```")
            await ctx.respond(embed=embed)

        finally:
            # Sprache zurücksetzen
            if sprache != original_lang:
                wikipedia.set_lang(original_lang)
                self.current_language = original_lang

    @wiki.command(name="multisearch", description="🔍 Erweiterte Wikipedia-Suche mit mehreren Ergebnissen")
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

        # Sprache wechseln
        original_lang = self.current_language
        if sprache != original_lang:
            wikipedia.set_lang(sprache)
            self.current_language = sprache

        try:
            results = wikipedia.search(suchbegriff, results=anzahl)

            if not results:
                embed = create_error_embed(
                    "Keine Ergebnisse",
                    f"Keine Artikel für **'{suchbegriff}'** in {WIKI_CONFIG['languages'][sprache]['name']} gefunden."
                )
                await ctx.respond(embed=embed)
                return

            lang_info = WIKI_CONFIG['languages'][sprache]
            embed = discord.Embed(
                title=f"🔍 Suchergebnisse für '{suchbegriff}'",
                description=f"**{len(results)} Ergebnisse** in {lang_info['flag']} {lang_info['name']}:",
                color=INFO_COLOR,
                timestamp=datetime.now()
            )

            # Ergebnisse mit Vorschau
            for i, result in enumerate(results, 1):
                try:
                    summary = wikipedia.summary(result, sentences=1)
                    summary = clean_text(summary, 150)
                except:
                    summary = "Keine Vorschau verfügbar."

                embed.add_field(
                    name=f"{i}. {result}",
                    value=summary,
                    inline=False
                )

            embed.set_footer(text=f"Wikipedia • {len(results)} Ergebnisse • Sprache: {lang_info['name']}")

            # View mit Buttons für die ersten Ergebnisse
            first_results = results[:4]  # Erste 4 als interaktive Buttons
            view = EnhancedWikiView({
                'title': f'Suchergebnisse für "{suchbegriff}"',
                'url': f'https://{lang_info["domain"]}/wiki/Special:Search/{suchbegriff}',
                'summary': f'{len(results)} Artikel gefunden',
                'categories': [],
                'links': results,
                'images': [],
                'language': sprache
            }, suchbegriff, sprache, first_results, cog_instance=self)

            message = await ctx.respond(embed=embed, view=view)
            view.message = message

        except Exception as e:
            embed = create_error_embed("Suchfehler", f"Fehler bei der Suche: {str(e)[:500]}")
            await ctx.respond(embed=embed)
        finally:
            if sprache != original_lang:
                wikipedia.set_lang(original_lang)
                self.current_language = original_lang

    @wiki.command(name="random", description="🎲 Zeige einen zufälligen Wikipedia-Artikel")
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
                # Einzelner zufälliger Artikel
                random_title = wikipedia.random()
                page = wikipedia.page(random_title)
                info = format_page_info(page, sprache)

                embed = create_main_embed(info, ctx.author)
                embed.title = f"🎲 Zufälliger Artikel: {info['title']}"

                similar_articles = wikipedia.search(random_title, results=6)
                similar_articles = [a for a in similar_articles if a.lower() != info['title'].lower()]

                view = EnhancedWikiView(info, random_title, sprache, similar_articles[:4], cog_instance=self)
                message = await ctx.respond(embed=embed, view=view)
                view.message = message

            else:
                # Mehrere zufällige Artikel
                lang_info = WIKI_CONFIG['languages'][sprache]
                embed = discord.Embed(
                    title=f"🎲 {anzahl} Zufällige Artikel",
                    description=f"Entdecke neue Themen in {lang_info['flag']} {lang_info['name']}:",
                    color=SUCCESS_COLOR,
                    timestamp=datetime.now()
                )

                random_articles = []
                for i in range(anzahl):
                    try:
                        random_title = wikipedia.random()
                        summary = clean_text(wikipedia.summary(random_title, sentences=1), 200)
                        random_articles.append(random_title)

                        embed.add_field(
                            name=f"{i + 1}. {random_title}",
                            value=summary,
                            inline=False
                        )
                    except:
                        embed.add_field(
                            name=f"{i + 1}. Artikel nicht verfügbar",
                            value="Dieser Artikel konnte nicht geladen werden.",
                            inline=False
                        )

                embed.set_footer(text=f"Wikipedia • {anzahl} zufällige Artikel")

                # View mit den zufälligen Artikeln als Buttons
                view = EnhancedWikiView({
                    'title': f'{anzahl} Zufällige Artikel',
                    'url': f'https://{lang_info["domain"]}/wiki/Special:Random',
                    'summary': f'{anzahl} zufällig ausgewählte Artikel',
                    'categories': [],
                    'links': random_articles,
                    'images': [],
                    'language': sprache
                }, "random", sprache, random_articles[:4], cog_instance=self)

                message = await ctx.respond(embed=embed, view=view)
                view.message = message

        except Exception as e:
            embed = create_error_embed("Fehler beim Laden", f"Zufällige Artikel konnten nicht geladen werden: {e}")
            await ctx.respond(embed=embed)
        finally:
            if sprache != original_lang:
                wikipedia.set_lang(original_lang)
                self.current_language = original_lang

    @wiki.command(name="stats", description="📊 Zeige Bot-Statistiken und Wikipedia-Informationen")
    async def wiki_statistics(self, ctx: discord.ApplicationContext):
        # Uptime berechnen
        uptime = datetime.now() - self.stats['start_time']
        uptime_str = f"{uptime.days}d {uptime.seconds // 3600}h {(uptime.seconds // 60) % 60}m"

        embed = discord.Embed(
            title="📊 Wikipedia Bot Statistiken",
            color=INFO_COLOR,
            timestamp=datetime.now()
        )

        # Grundlegende Statistiken
        embed.add_field(name="🔍 Suchanfragen", value=f"{self.stats['searches']:,}", inline=True)
        embed.add_field(name="📖 Artikel angezeigt", value=f"{self.stats['articles_viewed']:,}", inline=True)
        embed.add_field(name="⏱️ Laufzeit", value=uptime_str, inline=True)

        # Sprach-Statistiken
        lang_names = [WIKI_CONFIG['languages'][lang]['name'] for lang in self.stats['languages_used']]
        embed.add_field(
            name="🌐 Verwendete Sprachen",
            value=", ".join(lang_names) if lang_names else "Keine",
            inline=False
        )

        # Verfügbare Sprachen
        all_langs = [f"{info['flag']} {info['name']}" for info in WIKI_CONFIG['languages'].values()]
        embed.add_field(
            name="📚 Verfügbare Sprachen",
            value=", ".join(all_langs),
            inline=False
        )

        # Cache-Statistiken
        embed.add_field(name="💾 Cache-Einträge", value=f"{len(wiki_cache.cache)}", inline=True)
        embed.add_field(name="⚡ Rate Limiting", value="Aktiviert", inline=True)
        embed.add_field(name="🔧 Features", value="Suche, Zufällig, Multi-Sprache, Cache", inline=True)

        embed.set_footer(text="Wikipedia Bot • Erweiterte Funktionen verfügbar")
        embed.set_thumbnail(url=ctx.bot.user.avatar.url)

        await ctx.respond(embed=embed)

    @wiki.command(name="category", description="📂 Durchsuche Wikipedia-Kategorien")
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
            # Suche nach Artikeln, die zur Kategorie passen
            search_results = wikipedia.search(f"Kategorie:{kategorie}", results=10)
            if not search_results:
                search_results = wikipedia.search(kategorie, results=10)

            if not search_results:
                embed = create_error_embed(
                    "Kategorie nicht gefunden",
                    f"Keine Artikel in der Kategorie **'{kategorie}'** gefunden."
                )
                await ctx.respond(embed=embed)
                return

            lang_info = WIKI_CONFIG['languages'][sprache]
            embed = discord.Embed(
                title=f"📂 Kategorie: {kategorie}",
                description=f"Artikel in dieser Kategorie ({lang_info['flag']} {lang_info['name']}):",
                color=INFO_COLOR,
                timestamp=datetime.now()
            )

            # Erste 8 Ergebnisse anzeigen
            for i, result in enumerate(search_results[:8], 1):
                try:
                    summary = wikipedia.summary(result, sentences=1)
                    summary = clean_text(summary, 150)
                except:
                    summary = "Keine Beschreibung verfügbar."

                embed.add_field(
                    name=f"{i}. {result}",
                    value=summary,
                    inline=False
                )

            embed.set_footer(text=f"Wikipedia • Kategorie-Suche • {len(search_results)} Ergebnisse")

            # View mit Kategorie-Artikeln
            view = EnhancedWikiView({
                'title': f'Kategorie: {kategorie}',
                'url': f'https://{lang_info["domain"]}/wiki/Category:{kategorie}',
                'summary': f'Artikel aus der Kategorie {kategorie}',
                'categories': [kategorie],
                'links': search_results,
                'images': [],
                'language': sprache
            }, kategorie, sprache, search_results[:4], cog_instance=self)

            message = await ctx.respond(embed=embed, view=view)
            view.message = message

        except Exception as e:
            embed = create_error_embed("Kategorie-Fehler", f"Fehler beim Laden der Kategorie: {str(e)[:500]}")
            await ctx.respond(embed=embed)
        finally:
            if sprache != original_lang:
                wikipedia.set_lang(original_lang)
                self.current_language = original_lang

    @wiki.command(name="cache", description="🗑️ Cache-Management (nur für Administratoren)")
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
            embed = create_error_embed("Berechtigung verweigert", "Nur Administratoren können Cache-Befehle verwenden.")
            await ctx.respond(embed=embed, ephemeral=True)
            return

        await ctx.defer(ephemeral=True)

        if aktion == "status":
            total_entries = len(wiki_cache.cache)
            expired_count = 0
            now = datetime.now()

            for key, timestamp in wiki_cache.timestamps.items():
                if now - timestamp >= timedelta(seconds=WIKI_CONFIG['cache_duration']):
                    expired_count += 1

            embed = discord.Embed(
                title="💾 Cache-Status",
                color=INFO_COLOR
            )
            embed.add_field(name="📊 Gesamt-Einträge", value=f"{total_entries}", inline=True)
            embed.add_field(name="⏰ Abgelaufene Einträge", value=f"{expired_count}", inline=True)
            embed.add_field(name="✅ Aktive Einträge", value=f"{total_entries - expired_count}", inline=True)
            embed.add_field(name="⚙️ Cache-Dauer", value=f"{WIKI_CONFIG['cache_duration']} Sekunden", inline=True)

            await ctx.respond(embed=embed, ephemeral=True)

        elif aktion == "clear":
            old_count = len(wiki_cache.cache)
            wiki_cache.cache.clear()
            wiki_cache.timestamps.clear()

            embed = discord.Embed(
                title="🗑️ Cache geleert",
                description=f"**{old_count}** Einträge wurden entfernt.",
                color=SUCCESS_COLOR
            )
            await ctx.respond(embed=embed, ephemeral=True)

        elif aktion == "cleanup":
            old_count = len(wiki_cache.cache)
            wiki_cache.clear_expired()
            new_count = len(wiki_cache.cache)
            removed = old_count - new_count

            embed = discord.Embed(
                title="⏰ Cache bereinigt",
                description=f"**{removed}** abgelaufene Einträge entfernt.\n**{new_count}** Einträge verbleiben.",
                color=SUCCESS_COLOR
            )
            await ctx.respond(embed=embed, ephemeral=True)

    # Context Menu Commands für erweiterte Funktionen
    @discord.message_command(name="Wikipedia Suche")
    async def context_wiki_search(self, ctx: discord.ApplicationContext, message: discord.Message):
        """Kontext-Menü für Wikipedia-Suche aus Nachrichten"""
        if not message.content or len(message.content) > 100:
            await ctx.respond("❌ Nachricht ist leer oder zu lang für eine Suche.", ephemeral=True)
            return

        # Ersten Begriff aus der Nachricht extrahieren
        words = message.content.split()
        search_term = " ".join(words[:3])  # Erste 3 Wörter

        await ctx.defer(ephemeral=True)

        try:
            page = wikipedia.page(search_term)
            info = format_page_info(page, 'de')

            embed = create_main_embed(info, ctx.author, ephemeral=True)
            embed.title = f"📖 Schnellsuche: {info['title']}"

            similar_articles = wikipedia.search(search_term, results=4)
            similar_articles = [a for a in similar_articles if a.lower() != info['title'].lower()]

            view = EnhancedWikiView(info, search_term, 'de', similar_articles[:3], cog_instance=self)
            await ctx.respond(embed=embed, view=view, ephemeral=True)

        except wikipedia.DisambiguationError as e:
            embed = create_disambiguation_embed(search_term, e.options[:6])
            await ctx.respond(embed=embed, ephemeral=True)
        except wikipedia.PageError:
            embed = create_error_embed("Nicht gefunden", f"Kein Artikel für '{search_term}' gefunden.")
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            embed = create_error_embed("Fehler", f"Suche fehlgeschlagen: {str(e)[:200]}")
            await ctx.respond(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(WikipediaCog(bot))