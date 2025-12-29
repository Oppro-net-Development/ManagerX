# src/handler/translation_handler.py

import yaml
from pathlib import Path

class TranslationHandler:
    """
    Zentrale Klasse zum Laden und Abrufen von Übersetzungen.
    Unterstützt:
    - Caching
    - Fallback-Sprachen
    - get_for_user
    - Pfad als Liste oder String
    """

    TRANSLATION_PATH = Path("translation") / "messages"
    FALLBACK_LANGS = ("en", "de")
    DEFAULT_LANGUAGE = "en"
    _cache: dict[str, dict] = {}

    @classmethod
    def load_messages(cls, lang_code: str) -> dict:
        """
        Lädt Sprachdateien mit Cache und Fallback.
        """
        if lang_code in cls._cache:
            return cls._cache[lang_code]

        for code in (lang_code, *cls.FALLBACK_LANGS):
            file_path = cls.TRANSLATION_PATH / f"{code}.yaml"

            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    cls._cache[lang_code] = data
                    return data

        print(f"[TranslationHandler] WARNUNG: Keine Sprachdatei gefunden ({lang_code})")
        cls._cache[lang_code] = {}
        return {}

    @classmethod
    def get(cls, lang_code: str, path, default: str = "", **placeholders) -> str:
        """
        Holt eine Übersetzung über einen Pfad (Liste oder Punkt-String)
        und ersetzt Platzhalter.
        """
        if isinstance(path, str):
            path = path.split(".")

        messages = cls.load_messages(lang_code)
        value = messages

        for key in path:
            if not isinstance(value, dict):
                return default
            value = value.get(key)

        if not isinstance(value, str):
            return default

        try:
            return value.format(**placeholders)
        except KeyError:
            return value

    @classmethod
    async def get_for_user(cls, bot, user_id: int, path, default: str = "", **placeholders) -> str:
        """
        Holt die Übersetzung automatisch für einen User.
        Benötigt `bot.settings_db.get_user_language(user_id)`.
        """
        lang = cls.DEFAULT_LANGUAGE
        try:
            lang = bot.settings_db.get_user_language(user_id) or cls.DEFAULT_LANGUAGE
        except Exception:
            pass

        return cls.get(lang, path, default, **placeholders)

    @classmethod
    def clear_cache(cls):
        """Löscht den Cache (nützlich für Hot-Reload im DEV)."""
        cls._cache.clear()


# Optionaler Alias
MessagesHandler = TranslationHandler
