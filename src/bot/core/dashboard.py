"""
ManagerX - Dashboard Task
==========================

Verwaltet das Dashboard-Update-System
Pfad: src/bot/core/dashboard.py
"""

import json
from datetime import datetime
from pathlib import Path
from discord.ext import tasks
from logger import logger, Category

class DashboardTask:
    """Verwaltet periodische Dashboard-Updates"""
    
    def __init__(self, bot, basedir: Path):
        self.bot = bot
        self.basedir = basedir
        self.stats_file = basedir / 'bot_stats.json'
        self._task = None
        
        # Task definieren
        @tasks.loop(minutes=1)
        async def update_dashboard():
            await self._update_stats()
        
        self._task = update_dashboard
    
    async def _update_stats(self):
        """Aktualisiert die Dashboard-Statistiken"""
        try:
            # Basis-Statistiken sammeln
            stats = {
                "bot_info": {
                    "name": str(self.bot.user.name) if self.bot.user else "Unknown",
                    "id": str(self.bot.user.id) if self.bot.user else "0",
                    "status": "online",
                    "latency": round(self.bot.latency * 1000, 1)
                },
                "stats": {
                    "server_count": len(self.bot.guilds),
                    "user_count": sum(g.member_count for g in self.bot.guilds if g.member_count),
                    "shards": self.bot.shard_count or 1,
                    "commands": len(self.bot.tree.get_commands()) if hasattr(self.bot, 'tree') else 0
                },
                "system": {
                    "uptime": self._get_uptime(),
                    "python_version": self._get_python_version()
                },
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # In Datei schreiben
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            logger.error(Category.BOT, f"Dashboard-Update fehlgeschlagen: {e}")
    
    def _get_uptime(self) -> str:
        """Berechnet die Bot-Uptime"""
        if hasattr(self.bot, 'start_time'):
            delta = datetime.now() - self.bot.start_time
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours}h {minutes}m {seconds}s"
        return "Unknown"
    
    def _get_python_version(self) -> str:
        """Gibt die Python-Version zurück"""
        import sys
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    def register(self):
        """Registriert den Task (startet ihn noch nicht)"""
        # Startzeit speichern
        self.bot.start_time = datetime.now()
        logger.info(Category.DISCORD_BOT, "Dashboard-Task registriert")
    
    def start(self):
        """Startet den Dashboard-Update-Task"""
        if self._task and not self._task.is_running():
            self._task.start()
            logger.success(Category.DISCORD_BOT, "Dashboard-Task gestartet")
    
    def stop(self):
        """Stoppt den Dashboard-Update-Task"""
        if self._task and self._task.is_running():
            self._task.cancel()
            logger.info(Category.DISCORD_BOT, "Dashboard-Task gestoppt")
    
    def is_running(self) -> bool:
        """
        Prüft ob der Task läuft.
        
        Returns:
            bool: True wenn Task läuft
        """
        return self._task.is_running() if self._task else False