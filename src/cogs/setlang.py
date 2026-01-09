import discord
from discord.ext import commands
import ezcord

from handler import TranslationHandler


class SetLangCog(ezcord.Cog):
    """Cog for setting user language preferences."""

    AVAILABLE_LANGUAGES = {
        "de": "Deutsch 🇩🇪",
        "en": "English 🇬🇧"
    }

    @commands.slash_command(
        name="set-lang",
        description="Set your preferred language for bot messages."
    )
    @discord.option(
        "language",
        description="Choose a language",
        choices=[
            discord.OptionChoice(name=name, value=code)
            for code, name in AVAILABLE_LANGUAGES.items()
        ],
        required=True
    )
    async def set_language(self, ctx: discord.ApplicationContext, language: str):
        """
        Set the user's preferred language.
        
        Args:
            ctx: Discord application context
            language: Selected language code
        """
        # Save language preference
        self.bot.settings_db.set_user_language(ctx.author.id, language)

        # Get display name for the selected language
        lang_name = self.AVAILABLE_LANGUAGES.get(language, language)

        # Load response message using TranslationHandler
        response_text = await TranslationHandler.get_async(
            language,
            "cog_setlang.message.language_set",
            default="Language has been set to {language}.",
            language=lang_name
        )

        await ctx.respond(response_text, ephemeral=True)


def setup(bot):
    """Setup function to add the cog to the bot."""
    bot.add_cog(SetLangCog(bot))