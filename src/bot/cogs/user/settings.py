import discord
from discord.ext import commands
from discord import SlashCommandGroup
import ezcord

from mx_handler import TranslationHandler


class Settings(ezcord.Cog):
    """Cog for setting user language preferences."""

    user = SlashCommandGroup("user", "User settings commands")

    language = user.create_subgroup(
        "language")

    AVAILABLE_LANGUAGES = {
        "de": "Deutsch 🇩🇪",
        "en": "English 🇬🇧"
    }

    @language.command(
        name="set",
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
            "cog_settings.language.message.language_set",
            default="Language has been set to {language}.",
            language=lang_name
        )

        await ctx.respond(response_text, ephemeral=True)


    @language.command()
    async def get(self, ctx: discord.ApplicationContext):
        """
        Get the user's current preferred language.
        
        Args:
            ctx: Discord application context
        """
        # Retrieve user's language preference
        language = self.bot.settings_db.get_user_language(ctx.author.id)

        if not language:
            response_text = await TranslationHandler.get_async(
                "en",
                "cog_settings.language.error_types.language_not_set",
                default="You have not set a preferred language yet."
            )
        else:
            lang_name = self.AVAILABLE_LANGUAGES.get(language, language)
            response_text = await TranslationHandler.get_async(
                language,
                "cog_settings.language.message.current_language",
                default="Your current preferred language is {language}.",
                language=lang_name
            )

        await ctx.respond(response_text, ephemeral=True)

    @language.command(
        name="list",
        description="List all available languages."
    )

    async def list_languages(self, ctx: discord.ApplicationContext):
        """
        List all available languages.
        
        Args:
            ctx: Discord application context
        """
        languages_list = "\n".join(
            f"{code}: {name}" for code, name in self.AVAILABLE_LANGUAGES.items()
        )
        response_text = f"**Available Languages:**\n{languages_list}"
        await ctx.respond(response_text, ephemeral=True)

def setup(bot):
    """Setup function to add the cog to the bot."""
    bot.add_cog(Settings(bot))