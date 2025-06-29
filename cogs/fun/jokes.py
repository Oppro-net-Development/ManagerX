import discord
from discord.ext import commands
from discord.commands import slash_command
import aiohttp

class JokeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="joke", description="Get a random joke")
    async def joke(self, ctx):
        try:
            async with aiohttp.ClientSession() as session, session.get("https://witzapi.de/api/joke/") as response:
                response.raise_for_status()
                joke_data = await response.json()

                if joke_data and isinstance(joke_data, list):
                    joke_text = joke_data[0].get('text', 'Kein Witz gefunden.')
                    embed = discord.Embed(
                        title=":joy: Hier ist dein Witz!",
                        description=joke_text,
                        color=discord.Color.blue()
                    ).set_footer(text="Provided by witzapi.de")
                    await ctx.respond(embed=embed)
                else:
                    await ctx.respond("Es wurde kein Witz gefunden")
        except aiohttp.ClientError as e:
            await ctx.respond(f"Fehler bei der Anfrage: {e}")

def setup(bot):
    bot.add_cog(JokeCog(bot))