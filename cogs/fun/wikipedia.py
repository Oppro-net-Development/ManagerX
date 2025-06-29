# ───────────────────────────────────────────────
# >> Imports
# ───────────────────────────────────────────────
import wikipedia
from FastCoding import discord, ezcord
from FastCoding import INFO_COLOR
# ───────────────────────────────────────────────
# >> Settings
# ───────────────────────────────────────────────
wikipedia.set_lang("de")
# ───────────────────────────────────────────────
# >> Cogs
# ───────────────────────────────────────────────
class SimilarButton(discord.ui.Button):
    def __init__(self, label: str):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            seite = wikipedia.page(self.label)
            zusammenfassung = wikipedia.summary(self.label, sentences=3)

            embed = discord.Embed(
                title=seite.title,
                description=zusammenfassung[:4000],
                url=seite.url,
                color=INFO_COLOR
            )
            embed.set_footer(text="Quelle: Wikipedia")

            if seite.images:
                embed.set_thumbnail(url=seite.images[0])
            else:
                embed.set_thumbnail(url=interaction.client.user.avatar.url)

            view = WikiView(seite.url)  # Nur "Ganzen Artikel lesen" Button
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        except wikipedia.DisambiguationError as e:
            await interaction.followup.send(
                f"⚠️ Mehrdeutiger Begriff:\n{', '.join(e.options[:5])}...",
                ephemeral=True
            )
        except wikipedia.PageError:
            await interaction.followup.send("❌ Seite nicht gefunden.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Fehler: {e}", ephemeral=True)


class WikiView(discord.ui.View):
    def __init__(self, url: str, ähnliche: list[str] = None, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.add_item(discord.ui.Button(label="🔗 Ganzen Artikel lesen", url=url))

        if ähnliche:
            for begriff in ähnliche[:5]:
                self.add_item(SimilarButton(begriff))

    async def on_timeout(self):
        # Buttons deaktivieren bei Timeout
        for item in self.children:
            item.disabled = True
        # Nachricht updaten, falls möglich (keine Fehler werfen)
        try:
            message = self.message
            if message:
                await message.edit(view=self)
        except:
            pass


# Autocomplete-Funktion für den Slash-Command
async def wiki_autocomplete(ctx: discord.AutocompleteContext):
    suchwert = ctx.value or ""
    vorschlaege = wikipedia.search(suchwert, results=5)
    return vorschlaege


class WikiCog(ezcord.Cog, group="fun"):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="wiki", description="🔍 Suche auf Wikipedia")
    async def wiki(
        self,
        ctx: discord.ApplicationContext,
        suchbegriff: discord.Option(str, "Was soll ich suchen?", autocomplete=wiki_autocomplete)
    ):
        await ctx.defer()
        try:
            seite = wikipedia.page(suchbegriff)
            zusammenfassung = wikipedia.summary(suchbegriff, sentences=3)

            embed = discord.Embed(
                title=seite.title,
                description=zusammenfassung[:4000],
                url=seite.url,
                color=discord.Color.blurple()
            )
            embed.set_footer(text="Quelle: Wikipedia")

            if seite.images:
                embed.set_thumbnail(url=seite.images[0])
            else:
                embed.set_thumbnail(url=ctx.bot.user.avatar.url)

            ähnliche = wikipedia.search(suchbegriff)
            ähnliche = [b for b in ähnliche if b.lower() != seite.title.lower()]

            view = WikiView(seite.url, ähnliche)
            response = await ctx.respond(embed=embed, view=view)

            # View Message referenz speichern für Timeout Handling
            if not hasattr(view, 'message'):
                view.message = await response.original_message()

        except wikipedia.DisambiguationError as e:
            await ctx.respond(
                f"🚫 Mehrdeutiger Begriff. Versuch es genauer:\n{', '.join(e.options[:5])}...",
                ephemeral=True
            )
        except wikipedia.PageError:
            await ctx.respond("❌ Keine passende Seite gefunden.", ephemeral=True)
        except Exception as e:
            await ctx.respond(f"⚠️ Fehler: {e}", ephemeral=True)


def setup(bot):
    bot.add_cog(WikiCog(bot))
