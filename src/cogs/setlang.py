import discord
from discord.ext import commands
import ezcord

from handler import TranslationHandler

class SetLangCog(ezcord.Cog, group="informationen"):

    AVAILABLE_LANGUAGES = {
        "de": "Deutsch 🇩🇪",
        "en": "English 🇬🇧"
    }

    @commands.slash_command(
        name="set-lang",
        description="Stelle deine bevorzugte Sprache für Bot-Nachrichten ein."
    )
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
        # Sprache speichern
        self.bot.settings_db.set_user_language(ctx.author.id, language)

        # Name für Anzeige
        lang_name = self.AVAILABLE_LANGUAGES.get(language, language)

        # Nachricht laden über TranslationHandler
        response_text = TranslationHandler.get(
            language,
            "cog_setlang.message.language_set",
            default="Language has been set to {language}.",
            language=lang_name
        )

        await ctx.respond(response_text, ephemeral=True)


def setup(bot):
    bot.add_cog(SetLangCog(bot))
