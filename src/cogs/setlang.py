# src/cogs/informationen/setlang.py

import discord
from discord.ext import commands
import ezcord
from src.DevTools.backend.database.lang_db import SettingsDB
# Die Bot-Klasse wird später in main.py mit der SettingsDB erweitert.

class SetLangCog(ezcord.Cog, group="informationen"):
    
    # Verfügbare Sprachen (Code: Anzeigename)
    AVAILABLE_LANGUAGES = {
        "de": "Deutsch 🇩🇪",
        "en": "English 🇬🇧"
    }

    @commands.slash_command(name="set-lang", description="Stelle deine bevorzugte Sprache für Bot-Nachrichten ein.")
    @discord.option(
        "language",
        description="Wähle eine Sprache",
        choices=[
            discord.OptionChoice(name=name, value=code)
            for code, name in AVAILABLE_LANGUAGES.items()
        ],
        required=True
    )
    async def set_language(self, ctx: discord.ApplicationContext, language: str):
        
        # Setzt die Sprache in der Datenbank
        self.bot.settings_db.set_user_language(ctx.author.id, language)
        
        # Lädt die Nachrichten für die gewählte Sprache (für die Bestätigung)
        # HINWEIS: Dies setzt voraus, dass load_messages in gewinnt.py auch importiert wird oder zentral ist.
        # Für die Simplizität laden wir hier die Nachrichten direkt.
        try:
            # Wir müssen load_messages hier importieren können (für den realen Bot müssten Sie den Importpfad prüfen)
            # oder zentralisieren. Da wir es in gewinnt.py haben, kopieren wir es kurz hierher:
            from src.cogs.fun.gewinnt import load_messages
            messages = load_messages(language)
        except Exception:
            # Fallback, falls der Import/Ladevorgang fehlschlägt
            messages = {"general": {"message": {"success": "Language set to {lang}."}}} 
        
        lang_name = self.AVAILABLE_LANGUAGES.get(language, language)
        
        await ctx.respond(
            f"✅ Deine Sprache wurde erfolgreich auf **{lang_name}** eingestellt.",
            ephemeral=True
        )

def setup(bot):
    bot.add_cog(SetLangCog(bot))