import requests
from FastCoding.backend import discord, slash_command, ezcord
from FastCoding.backend import WEATHER_API
from FastCoding import DEFLAUT_COLOR
class Weather(ezcord.Cog, group="fun"):
    def __init__(self, bot: ezcord.Bot):
        self.bot = bot

    @slash_command(name="weather", description="Get the weather for a city")
    async def weather(self, ctx: discord.ApplicationContext, city: str):
        """Get the weather for a city"""
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API}&q={city}&lang=de"
        response = requests.get(url)
        data = response.json()

        if "error" in data:
            await ctx.respond(f"Error: {data['error']['message']}")
            return

        data = response.json()
        ort = data['location']['name']
        land = data['location']['country']
        temp = data['current']['temp_c']
        zustand = data['current']['condition']['text']
        icon = data['current']['condition']['icon']
        wind = data['current']['wind_kph']

        embed = discord.Embed(title=f"Wetter in {ort}, {land}", color=DEFLAUT_COLOR)
        embed.add_field(name="🌡️ Temperatur", value=f"{temp}°C", inline=True)
        embed.add_field(name="🌬️ Wind", value=f"{wind} km/h", inline=True)
        embed.add_field(name="☁️ Zustand", value=zustand, inline=False)
        embed.set_footer(text="Weather data provided by WeatherAPI")
        embed.set_thumbnail(url="http:" + icon)

        await ctx.respond(embed=embed)

def setup(bot: ezcord.Bot):
    bot.add_cog(Weather(bot))