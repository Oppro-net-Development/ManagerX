# -*- coding: utf-8 -*-
# Copyright (c) 2025 OPPRO.NET Network
# ───────────────────────────────────────────────────
# >> Utility Functions
# ───────────────────────────────────────────────────
import re
import wikipedia
from typing import Dict, Any


def clean_text(text: str, max_length: int = None) -> str:
    """
    Erweiterte Textbereinigung
    
    Args:
        text: Der zu bereinigende Text
        max_length: Maximale Länge des Textes
        
    Returns:
        Bereinigter Text
    """
    if not text:
        return "Keine Beschreibung verfügbar."

    # HTML-Tags entfernen
    text = re.sub(r'<[^>]+>', '', text)
    # Referenzen in eckigen Klammern entfernen
    text = re.sub(r'\[.*?\]', '', text)
    # Mehrfache Leerzeichen normalisieren
    text = re.sub(r'\s+', ' ', text).strip()

    max_length = max_length or 1500
    if len(text) > max_length:
        truncated = text[:max_length - 3]
        last_sentence = truncated.rfind('.')
        if last_sentence > max_length // 2:
            text = truncated[:last_sentence + 1]
        else:
            text = truncated + "..."

    return text


def format_page_info(page, language: str = 'de') -> Dict[str, Any]:
    """
    Erweiterte Seiteninformationen mit Fehlerbehandlung
    
    Args:
        page: Wikipedia-Seitenobjekt
        language: Sprachcode
        
    Returns:
        Dictionary mit formatierten Seiteninformationen
    """
    try:
        info = {
            'title': getattr(page, 'title', 'Unbekannt'),
            'url': getattr(page, 'url', ''),
            'summary': '',
            'categories': [],
            'links': [],
            'images': [],
            'language': language,
            'coordinates': None,
            'references': []
        }

        # Zusammenfassung laden
        try:
            info['summary'] = clean_text(wikipedia.summary(page.title, sentences=4))
        except:
            info['summary'] = "Zusammenfassung nicht verfügbar."

        # Kategorien laden
        try:
            info['categories'] = getattr(page, 'categories', [])[:3]
        except:
            pass

        # Links laden
        try:
            info['links'] = getattr(page, 'links', [])[:15]
        except:
            pass

        # Bilder laden
        try:
            info['images'] = getattr(page, 'images', [])
        except:
            pass

        # Koordinaten extrahieren
        try:
            content = getattr(page, 'content', '')
            coord_match = re.search(r'(\d+\.?\d*)°\s*N.*?(\d+\.?\d*)°\s*[EW]', content)
            if coord_match:
                info['coordinates'] = (float(coord_match.group(1)), float(coord_match.group(2)))
        except:
            pass

        return info
        
    except Exception as e:
        return {
            'title': 'Fehler beim Laden',
            'url': '',
            'summary': f'Informationen konnten nicht geladen werden: {str(e)}',
            'categories': [],
            'links': [],
            'images': [],
            'language': language,
            'coordinates': None,
            'references': []
        }