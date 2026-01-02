# Copyright (c) 2025 OPPRO.NET Network
# ───────────────────────────────────────────────────
# >> Autocomplete Functions
# ───────────────────────────────────────────────────
import discord
import wikipedia
from .cache import wiki_cache


async def enhanced_wiki_autocomplete(ctx: discord.AutocompleteContext):
    """
    Erweiterte Autocomplete mit Caching
    
    Args:
        ctx: Autocomplete Context
        
    Returns:
        Liste von Vorschlägen
    """
    suchwert = ctx.value or ""

    # Standard-Vorschläge für kurze Eingaben
    if len(suchwert) < 2:
        return [
            "Künstliche Intelligenz", "Python (Programmiersprache)", "Discord",
            "Deutschland", "Wikipedia", "Klimawandel", "Quantenphysik", "Internet"
        ]

    try:
        cache_key = f"autocomplete_{suchwert}_de"
        cached_results = wiki_cache.get(cache_key)

        if cached_results:
            return cached_results.get('suggestions', [])

        # Wikipedia-Suche
        vorschlaege = wikipedia.search(suchwert, results=15)

        def relevance_score(suggestion):
            """Berechnet die Relevanz eines Vorschlags"""
            suggestion_lower = suggestion.lower()
            suchwert_lower = suchwert.lower()

            if suchwert_lower == suggestion_lower:
                return 0
            elif suggestion_lower.startswith(suchwert_lower):
                return 1
            elif suchwert_lower in suggestion_lower:
                return 2
            else:
                return 3 + len(suggestion)

        # Nach Relevanz sortieren
        vorschlaege.sort(key=relevance_score)
        final_suggestions = vorschlaege[:25]

        # Im Cache speichern
        wiki_cache.set(cache_key, {'suggestions': final_suggestions})

        return final_suggestions

    except Exception:
        return ["Fehler bei der Suche - bitte erneut versuchen"]