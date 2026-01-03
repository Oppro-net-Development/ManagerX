# Copyright (c) 2025 OPPRO.NET Network
import requests
import discord
from discord import slash_command
from discord.ui import Container
import ezcord
import os
from pathlib import Path
import yaml

WEATHER_API = os.getenv("WEATHER_API")

# --------------------------
# Hilfsfunktion für Nachrichten
# --------------------------
def load_messages(lang_code: str):
    base_path = Path("translation") / "messages"
    
    lang_file = base_path / f"{lang_code}.yaml"
    if not lang_file.exists():
        lang_file = base_path / "en.yaml"
    if not lang_file.exists():
        lang_file = base_path / "de.yaml"
    if not lang_file.exists():
        print(f"WARNUNG: Keine Sprachdatei für '{lang_code}' gefunden. Verwende leere Texte.")
        return {}
    
    with open(lang_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# --------------------------
# Weather Cog
# --------------------------
class Weather(ezcord.Cog, group="fun"):
    def __init__(self, bot: ezcord.Bot):
        self.bot = bot

    @slash_command(name="weather", description="Erhalte das Wetter für eine Stadt")
    async def weather(self, ctx: discord.ApplicationContext, city: str):
        """Get the weather for a city"""
        
        # 🌟 Benutzer-spezifische Sprache laden
        lang_code = self.bot.settings_db.get_user_language(ctx.author.id)
        messages = load_messages(lang_code)

        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API}&q={city}&lang={lang_code}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException:
            await ctx.respond(
                messages.get("cog_weather", {}).get("error_types", {}).get(
                    "api_error", "Error with the weather API."
                )
            )
            return

        if "error" in data:
            await ctx.respond(
                messages.get("cog_weather", {}).get("error_types", {}).get(
                    "city_not_found", f"⚠️ Error: {data['error']['message']}"
                )
            )
            return

        location = data['location']
        current = data['current']

        container = Container()
        
        # Übersetzbarer Header
        container.add_text(
            messages.get("cog_weather", {}).get("messages", {}).get(
                "weather_report", "Weather report for {city}, {country}\n"
            ).format(city=location['name'], country=location['country'])
        )
        container.add_separator()
        
        # Übersetzbare Details
        details = (
            messages.get("cog_weather", {}).get("messages", {}).get(
                "temperature", "Temperature: {temperature}°C\n"
            ).format(temperature=current['temp_c']) +
            messages.get("cog_weather", {}).get("messages", {}).get(
                "humidity", "Humidity: {humidity}%\n"
            ).format(humidity=current['humidity']) +
            messages.get("cog_weather", {}).get("messages", {}).get(
                "wind_speed", "Wind speed: {wind_speed} km/h ({wind_dir})\n"
            ).format(wind_speed=current['wind_kph'], wind_dir=current['wind_dir']) +
            messages.get("cog_weather", {}).get("messages", {}).get(
                "condition", "Condition: {condition}\n"
            ).format(condition=current['condition']['text']) +
            messages.get("cog_weather", {}).get("messages", {}).get(
                "visibility", "Visibility: {visibility} km\n"
            ).format(visibility=current['vis_km']) +
            messages.get("cog_weather", {}).get("messages", {}).get(
                "pressure", "Pressure: {pressure} hPa\n"
            ).format(pressure=current['pressure_mb'])
        )
        
        container.add_text(details)
        
        view = discord.ui.DesignerView(container, timeout=None)
        await ctx.respond(view=view)

def setup(bot: ezcord.Bot):
    bot.add_cog(Weather(bot))
