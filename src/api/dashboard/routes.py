from fastapi import APIRouter, Request, HTTPException
from typing import List, Optional
from datetime import datetime
import time
# Falls du Schemas nutzt: from .schemas import ServerStatus, UserInfo

# Wir erstellen einen Router, den wir später in die Haupt-App einbinden
router = APIRouter(
    prefix="/api/v1/managerx",
    tags=["dashboard"]
)

# Global Bot-Referenz (wird später in main.py gesetzt)
bot_instance = None

def set_bot_instance(bot):
    """
    Setzt die globale Bot-Instanz für die API.
    Diese Funktion wird aus main.py aufgerufen.
    
    Args:
        bot: Die discord.py Bot-Instanz
    """
    global bot_instance
    bot_instance = bot


@router.get("/stats", response_model=dict)
async def get_stats(request: Request):
    """
    Endpoint to get the current server status with real bot data.
    
    Returns:
        dict: Server status mit echten Bot-Daten
    """
    if bot_instance is None:
        raise HTTPException(status_code=503, detail="Bot-Verbindung nicht verfügbar")
    
    try:
        # Berechne Uptime (in Sekunden seit dem letzten Ready-Event)
        uptime_seconds = (datetime.utcnow() - bot_instance.start_time).total_seconds() if hasattr(bot_instance, 'start_time') else 0
        uptime_minutes, remainder = divmod(int(uptime_seconds), 60)
        uptime_hours, uptime_minutes = divmod(uptime_minutes, 60)
        uptime_days, uptime_hours = divmod(uptime_hours, 24)
        
        uptime_str = f"{int(uptime_days)}d {int(uptime_hours)}h {int(uptime_minutes)}m"
        
        # Sammle echte Daten vom Bot
        server_status = {
            "uptime": uptime_str,
            "latency": f"{round(bot_instance.latency * 1000)}ms",
            "guilds": len(bot_instance.guilds),
            "users": len(bot_instance.users),
            "bot_name": bot_instance.user.name if bot_instance.user else "Unknown",
            "bot_id": bot_instance.user.id if bot_instance.user else None,
            "status": "online" if bot_instance.latency != float('inf') else "offline",
            "database": "connected" if hasattr(bot_instance, 'settings_db') and bot_instance.settings_db else "disconnected"
        }
        return server_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    