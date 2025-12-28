# -*- coding: utf-8 -*-
# Copyright (c) 2025 OPPRO.NET Network
# ───────────────────────────────────────────────────
# >> Cache System
# ───────────────────────────────────────────────────
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class WikiCache:
    """Cache-System für Wikipedia-Anfragen"""
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.timestamps: Dict[str, datetime] = {}

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Ruft einen Wert aus dem Cache ab"""
        if key in self.cache:
            cache_duration = 300  # 5 Minuten
            if datetime.now() - self.timestamps[key] < timedelta(seconds=cache_duration):
                return self.cache[key]
            else:
                del self.cache[key]
                del self.timestamps[key]
        return None

    def set(self, key: str, value: Dict[str, Any]):
        """Speichert einen Wert im Cache"""
        self.cache[key] = value
        self.timestamps[key] = datetime.now()

    def clear_expired(self):
        """Entfernt abgelaufene Cache-Einträge"""
        now = datetime.now()
        cache_duration = 300  # 5 Minuten
        expired_keys = [
            key for key, timestamp in self.timestamps.items()
            if now - timestamp >= timedelta(seconds=cache_duration)
        ]
        for key in expired_keys:
            self.cache.pop(key, None)
            self.timestamps.pop(key, None)

    def clear(self):
        """Leert den gesamten Cache"""
        self.cache.clear()
        self.timestamps.clear()

    @property
    def size(self) -> int:
        """Gibt die Anzahl der Cache-Einträge zurück"""
        return len(self.cache)

    def get_expired_count(self) -> int:
        """Zählt die abgelaufenen Einträge"""
        now = datetime.now()
        cache_duration = 300  # 5 Minuten
        return sum(
            1 for timestamp in self.timestamps.values()
            if now - timestamp >= timedelta(seconds=cache_duration)
        )


# Globale Cache-Instanz
wiki_cache = WikiCache()