# Copyright (c) 2025 OPPRO.NET Network
# ───────────────────────────────────────────────────
# >> Main Cog Class
# ───────────────────────────────────────────────────
import discord
import ezcord
import wikipedia
import asyncio
from discord import slash_command
from discord.ui import Container
from datetime import datetime
from .config import WIKI_CONFIG, LANGUAGE_CHOICES
from .cache import wiki_cache
from .utils import format_page_info, clean_text
from .containers import (
    create_article_container, create_error_container,
    create_disambiguation_container, create_random_article_container
)
from .components import ArticleButtonContainer
from .autocomplete import enhanced_wiki_autocomplete


class WikipediaCog(ezcord.Cog):
    """Hauptklasse für Wikipedia-Bot Funktionen"""
    
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
        wikipedia.set_lang("de")
        wikipedia.set_rate_limiting(True)

    @ezcord.Cog.listener()
    async def on_ready(self):
        """Startet den Cache-Cleanup Task"""
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
        """Cleanup beim Entladen des Cogs"""
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
                choices=LANGUAGE_CHOICES,
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
            view = discord.ui.DesignerView(container, timeout=WIKI_CONFIG['timeout'])

            await ctx.respond(view=view)

        except wikipedia.DisambiguationError as e:
            container = create_disambiguation_container(suchbegriff, e.options[:12], sprache)
            view = discord.ui.DesignerView(container, timeout=None)
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
            view = discord.ui.DesignerView(container, timeout=None)
            await ctx.respond(view=view)

        except Exception as e:
            container = create_error_container("Unerwarteter Fehler", f"```py\n{str(e)[:800]}\n```")
            view = discord.ui.DesignerView(container, timeout=None)
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
                choices=LANGUAGE_CHOICES,
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

                container = create_random_article_container(
                    info, ctx.author, similar_articles[:4],
                    random_title, sprache, cog_instance=self
                )
                
                view = discord.ui.DesignerView(container, timeout=WIKI_CONFIG['timeout'])
                await ctx.respond(view=view)

            else:
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

                if random_articles:
                    container.add_text("📚 **Artikel öffnen:**")
                    for article in random_articles[:4]:
                        article_btn = ArticleButtonContainer(article, "similar", self)
                        container.add_item(article_btn)
                
                container.add_separator()
                container.add_text(f"Wikipedia • {anzahl} zufällige Artikel")

                view = discord.ui.DesignerView(container, timeout=WIKI_CONFIG['timeout'])
                await ctx.respond(view=view)

        except Exception as e:
            container = create_error_container("Fehler beim Laden", 
                                              f"Zufällige Artikel konnten nicht geladen werden: {str(e)[:500]}")
            view = discord.ui.DesignerView(container, timeout=None)
            await ctx.respond(view=view)
        finally:
            if sprache != original_lang:
                wikipedia.set_lang(original_lang)
                self.current_language = original_lang

    @slash_command(name="wiki_multisearch", description="🔎 Erweiterte Wikipedia-Suche mit mehreren Ergebnissen")
    async def wiki_multi_search(
            self,
            ctx: discord.ApplicationContext,
            suchbegriff: discord.Option(str, "Suchbegriff für erweiterte Suche", max_length=100),
            anzahl: discord.Option(int, "Anzahl der Ergebnisse (1-15)", min_value=1, max_value=15, default=8),
            sprache: discord.Option(str, "Sprache für die Suche", choices=LANGUAGE_CHOICES, default="de", required=False)
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
                view = discord.ui.DesignerView(container, timeout=None)
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

            container.add_text("📚 **Artikel öffnen:**")
            for result in results[:4]:
                article_btn = ArticleButtonContainer(result, "similar", self)
                container.add_item(article_btn)

            container.add_separator()
            container.add_text(f"Wikipedia • {len(results)} Ergebnisse • Sprache: {lang_info['name']}")

            view = discord.ui.DesignerView(container, timeout=WIKI_CONFIG['timeout'])
            await ctx.respond(view=view)

        except Exception as e:
            container = create_error_container("Suchfehler", f"Fehler bei der Suche: {str(e)[:500]}")
            view = discord.ui.DesignerView(container, timeout=None)
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

        view = discord.ui.DesignerView(container, timeout=None)
        await ctx.respond(view=view)

    @slash_command(name="wiki_category", description="📂 Durchsuche Wikipedia-Kategorien")
    async def wiki_category(
            self,
            ctx: discord.ApplicationContext,
            kategorie: discord.Option(str, "Name der Kategorie", max_length=100),
            sprache: discord.Option(str, "Sprache für die Kategorie-Suche", choices=LANGUAGE_CHOICES, default="de", required=False)
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
                view = discord.ui.DesignerView(container, timeout=None)
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

            container.add_text("📚 **Artikel öffnen:**")
            for result in search_results[:4]:
                article_btn = ArticleButtonContainer(result, "category", self)
                container.add_item(article_btn)

            container.add_separator()
            container.add_text(f"Wikipedia • Kategorie-Suche • {len(search_results)} Ergebnisse")

            view = discord.ui.DesignerView(container, timeout=WIKI_CONFIG['timeout'])
            await ctx.respond(view=view)

        except Exception as e:
            container = create_error_container("Kategorie-Fehler", 
                                              f"Fehler beim Laden der Kategorie: {str(e)[:500]}")
            view = discord.ui.DesignerView(container, timeout=None)
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
            view = discord.ui.DesignerView(container, timeout=None)
            await ctx.respond(view=view, ephemeral=True)
            return

        await ctx.defer(ephemeral=True)

        if aktion == "status":
            total_entries = wiki_cache.size
            expired_count = wiki_cache.get_expired_count()

            container = Container()
            container.add_text("💾 **Cache-Status**")
            container.add_separator()
            
            status_text = f"📊 **Gesamt-Einträge:** {total_entries}\n"
            status_text += f"⏰ **Abgelaufene Einträge:** {expired_count}\n"
            status_text += f"✅ **Aktive Einträge:** {total_entries - expired_count}\n"
            status_text += f"⚙️ **Cache-Dauer:** {WIKI_CONFIG['cache_duration']} Sekunden"
            container.add_text(status_text)

            view = discord.ui.DesignerView(container, timeout=None)
            await ctx.respond(view=view, ephemeral=True)

        elif aktion == "clear":
            old_count = wiki_cache.size
            wiki_cache.clear()

            container = Container()
            container.add_text("🗑️ **Cache geleert**")
            container.add_separator()
            container.add_text(f"**{old_count}** Einträge wurden entfernt.")

            view = discord.ui.DesignerView(container, timeout=None)
            await ctx.respond(view=view, ephemeral=True)

        elif aktion == "cleanup":
            old_count = wiki_cache.size
            wiki_cache.clear_expired()
            new_count = wiki_cache.size
            removed = old_count - new_count

            container = Container()
            container.add_text("⏰ **Cache bereinigt**")
            container.add_separator()
            container.add_text(f"**{removed}** abgelaufene Einträge entfernt.\n**{new_count}** Einträge verbleiben.")

            view = discord.ui.DesignerView(container, timeout=None)
            await ctx.respond(view=view, ephemeral=True)


def setup(bot):
    """Setup-Funktion für den Cog"""
    bot.add_cog(WikipediaCog(bot))