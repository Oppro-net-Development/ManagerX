# -*- coding: utf-8 -*-
# Copyright (c) 2025 OPPRO.NET Network
# ───────────────────────────────────────────────────
# >> Wikipedia Bot Configuration
# ───────────────────────────────────────────────────
import discord

# Fallback für Farben
try:
    from DevTools import INFO_COLOR, ERROR_COLOR, SUCCESS_COLOR, WARNING_COLOR
except ImportError:
    INFO_COLOR = discord.Color.blue()
    ERROR_COLOR = discord.Color.red()
    SUCCESS_COLOR = discord.Color.green()
    WARNING_COLOR = discord.Color.orange()

# Wikipedia Konfiguration
WIKI_CONFIG = {
    'languages': {
        'de': {'name': 'Deutsch', 'flag': '\U0001F1E9\U0001F1EA', 'domain': 'de.wikipedia.org'},
        'en': {'name': 'English', 'flag': '\U0001F1FA\U0001F1F8', 'domain': 'en.wikipedia.org'},
        'fr': {'name': 'Français', 'flag': '\U0001F1EB\U0001F1F7', 'domain': 'fr.wikipedia.org'},
        'es': {'name': 'Español', 'flag': '\U0001F1EA\U0001F1F8', 'domain': 'es.wikipedia.org'},
        'it': {'name': 'Italiano', 'flag': '\U0001F1EE\U0001F1F9', 'domain': 'it.wikipedia.org'},
        'ja': {'name': '日本語', 'flag': '\U0001F1EF\U0001F1F5', 'domain': 'ja.wikipedia.org'},
        'ru': {'name': 'Русский', 'flag': '\U0001F1F7\U0001F1FA', 'domain': 'ru.wikipedia.org'},
    },
    'max_summary_length': 1500,
    'max_categories': 3,
    'max_similar_articles': 6,
    'timeout': 600,
    'cache_duration': 300
}

# Discord Option Choices für Sprachauswahl
LANGUAGE_CHOICES = [
    discord.OptionChoice(name="DE Deutsch", value="de"),
    discord.OptionChoice(name="US English", value="en"),
    discord.OptionChoice(name="FR Français", value="fr"),
    discord.OptionChoice(name="ES Español", value="es"),
    discord.OptionChoice(name="IT Italiano", value="it"),
    discord.OptionChoice(name="JP 日本語", value="ja"),
    discord.OptionChoice(name="RU Русский", value="ru"),
]