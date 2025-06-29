from FastCoding.ui.emojis import emoji_no, emoji_yes, emoji_circleinfo
import discord


ERROR_TITLE = f"{emoji_no} × Fehler"
ERROR_COLOR = discord.Color.red()
ERROR_DESCRIPTION = "Es ist ein Fehler aufgetreten. Bitte versuche es später erneut oder kontaktiere den Support."


SUCCESS_TITLE = f"{emoji_yes} × Erfolg"
SUCCESS_COLOR = discord.Color.green()
SUCCESS_DESCRIPTION = "Die Aktion wurde erfolgreich abgeschlossen."

INFO_COLOR = discord.Color.blue()
INFO_TITLE = f"{emoji_circleinfo} × Info"

DEFLAUT_COLOR = 0x5c0202

AUTHOR = "ManagerX"
FLOOTER = "Powered by ManagerX"
