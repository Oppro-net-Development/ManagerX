# ________  ________  ___     
#|\   __  \|\   __  \|\  \    
#\ \  \|\  \ \  \|\  \ \  \   
# \ \   __  \ \   ____\ \  \  
#  \ \  \ \  \ \  \___|\ \  \ 
#   \ \__\ \__\ \__\    \ \__\
#    \|__|\|__|\|__|     \|__|
                             
# --- STANDARD LIBRARIES ---
import json
import logging
import os
from typing import Optional, List, Dict, Any

# --- THIRD PARTY LIBRARIES ---
import httpx
import uvicorn
import yaml
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# --- LOCAL IMPORTS ---
try:
    from src.DevTools import TempVCDatabase
    from src.DevTools.backend.database.welcome_db import WelcomeDatabase
    from src.DevTools.backend.database.levelsystem_db import LevelDatabase
except ImportError:
    TempVCDatabase = None
    WelcomeDatabase = None
    LevelDatabase = None
    logging.warning("Database modules not found - some features may be unavailable")

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("ManagerX-API")
logger.setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

# --- KONFIGURATION ---
load_dotenv(os.path.join("config", ".env"))

# Bot-Config laden
config_path = os.path.join("config", "config.yaml")
bot_config = {}
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        bot_config = yaml.safe_load(f)
    logger.info("Bot-Config für API-Prüfungen geladen")
except FileNotFoundError:
    logger.warning("Config-Datei nicht gefunden")
except Exception as e:
    logger.error(f"Fehler beim Laden der Config: {e}")

# --- FASTAPI APP ---
app = FastAPI(title="ManagerX Ultimate API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- STATISCHE DATEIEN ---
if os.path.exists("site"):
    app.mount("/site", StaticFiles(directory="site", html=True), name="site")

# --- DATENBANKEN INITIALISIEREN ---
DB_PATH = os.path.join("data", "tempvc.db")
db = TempVCDatabase(DB_PATH) if TempVCDatabase else None
welcome_db = WelcomeDatabase() if WelcomeDatabase else None
level_db = LevelDatabase() if LevelDatabase else None

# --- SECURITY ---
security = HTTPBearer()

def get_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return credentials.credentials

# --- DATEN-MODELLE ---
class TempVCUpdate(BaseModel):
    token: str
    creator_channel_id: str
    category_id: str
    auto_delete_time: int
    ui_enabled: bool
    ui_prefix: str

class WelcomeUpdate(BaseModel):
    token: str
    channel_id: str
    welcome_message: str = ""
    enabled: bool = True
    embed_enabled: bool = False
    embed_color: str = "#00ff00"
    embed_title: str = ""
    embed_description: str = ""
    embed_thumbnail: bool = False
    embed_footer: str = ""
    ping_user: bool = False
    delete_after: int = 0

class LevelUpdate(BaseModel):
    token: str
    levelsystem_enabled: bool = True
    min_xp: int = 10
    max_xp: int = 20
    xp_cooldown: int = 30
    level_up_channel: str = ""
    prestige_enabled: bool = True
    prestige_min_level: int = 50

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# --- HILFSFUNKTIONEN ---
def is_feature_enabled(feature_path: str) -> bool:
    """Prüft, ob ein Feature in der Config aktiviert ist."""
    keys = feature_path.split('.')
    current = bot_config
    try:
        for key in keys:
            current = current.get(key, {})
        return current if isinstance(current, bool) else True
    except:
        return True

async def check_admin_permissions(guild_id: int, token: str):
    """Prüft bei Discord, ob der User Admin-Rechte hat."""
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(
                "https://discord.com/api/users/@me/guilds",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0
            )
            if res.status_code == 401:
                raise HTTPException(status_code=401, detail="Token abgelaufen")
            if res.status_code != 200:
                raise HTTPException(status_code=401, detail="Sitzung abgelaufen oder Token ungültig")
            
            guilds = res.json()
            guild = next((g for g in guilds if int(g['id']) == guild_id), None)
            
            if not guild:
                raise HTTPException(status_code=404, detail="Server nicht gefunden")
            
            # Bitwise check für ADMINISTRATOR (0x8)
            if not (int(guild.get('permissions', 0)) & 0x8) == 0x8:
                raise HTTPException(status_code=403, detail="Du hast keine Admin-Rechte")
            
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Fehler bei Discord-Validierung: {e}")
            raise HTTPException(status_code=500, detail="Discord API Kommunikationsfehler")

# --- ENDPOINTS ---

@app.get("/")
async def root():
    """Redirect zur Landing Page"""
    return RedirectResponse(url="/site/index.html")

@app.get("/api/managerx/stats")
@app.get("/api/v2/stats")
async def get_bot_stats():
    """Bot-Statistiken laden"""
    stats_file = "bot_stats.json"
    if os.path.exists(stats_file):
        try:
            with open(stats_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Fehler beim Laden der Stats: {e}")
    
    return {
        "stats": {"server_count": 50, "user_count": 15000},
        "bot_info": {"latency": 35, "status": "Online"}
    }

@app.get("/api/auth/callback")
async def auth_callback(code: str):
    """OAuth2 Callback für Discord-Login"""
    async with httpx.AsyncClient() as client:
        payload = {
            'client_id': os.getenv("DISCORD_CLIENT_ID"),
            'client_secret': os.getenv("DISCORD_CLIENT_SECRET"),
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': os.getenv("DISCORD_REDIRECT_URI")
        }
        r = await client.post('https://discord.com/api/oauth2/token', data=payload)
        
        if r.status_code != 200:
            logger.error(f"Login Fehler: {r.text}")
            raise HTTPException(status_code=400, detail="Discord Token Austausch fehlgeschlagen")
        
        tokens = r.json()
        u = await client.get(
            'https://discord.com/api/users/@me',
            headers={'Authorization': f"Bearer {tokens['access_token']}"}
        )
        
        return {
            "access_token": tokens['access_token'],
            "refresh_token": tokens.get('refresh_token'),
            "user": u.json()
        }

@app.post("/api/auth/refresh")
async def refresh_access_token(data: RefreshTokenRequest):
    """Token erneuern"""
    async with httpx.AsyncClient() as client:
        payload = {
            'client_id': os.getenv("DISCORD_CLIENT_ID"),
            'client_secret': os.getenv("DISCORD_CLIENT_SECRET"),
            'grant_type': 'refresh_token',
            'refresh_token': data.refresh_token
        }
        r = await client.post('https://discord.com/api/oauth2/token', data=payload)
        
        if r.status_code != 200:
            raise HTTPException(status_code=400, detail="Token-Refresh fehlgeschlagen")
        
        tokens = r.json()
        return {
            "access_token": tokens['access_token'],
            "refresh_token": tokens.get('refresh_token')
        }

@app.get("/api/user/guilds")
async def get_user_guilds(token: str = Depends(get_token)):
    """Alle Server mit Admin-Rechten"""
    async with httpx.AsyncClient() as client:
        res = await client.get(
            "https://discord.com/api/users/@me/guilds",
            headers={"Authorization": f"Bearer {token}"}
        )
        if res.status_code != 200:
            return []
        
        # Filtert nur Server mit Admin-Rechten
        return [g for g in res.json() if (int(g.get('permissions', 0)) & 0x8) == 0x8]

@app.get("/api/guild/{guild_id}/channels")
async def get_guild_channels(guild_id: int, token: str = Depends(get_token)):
    """Kanäle eines Servers laden"""
    await check_admin_permissions(guild_id, token)
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        res = await client.get(
            f"https://discord.com/api/guilds/{guild_id}/channels",
            headers=headers
        )
        
        if res.status_code == 401:
            raise HTTPException(status_code=401, detail="Token abgelaufen")
        if res.status_code != 200:
            logger.error(f"Discord API Fehler: {res.status_code} - {res.text}")
            raise HTTPException(status_code=500, detail=f"Discord API Fehler: {res.status_code}")
        
        channels = res.json()
        # Filtere Text-, Voice-Kanäle und Kategorien
        filtered = [
            {"id": str(ch["id"]), "name": ch["name"], "type": ch["type"]}
            for ch in channels if ch["type"] in [0, 2, 4]  # 0=Text, 2=Voice, 4=Category
        ]
        return {"channels": filtered}

@app.get("/api/guild/{guild_id}/tempvc")
async def get_tempvc(guild_id: int, token: str = Depends(get_token)):
    """TempVC Einstellungen laden"""
    await check_admin_permissions(guild_id, token)
    
    if not is_feature_enabled('features.cogs.server_management.tempvc'):
        raise HTTPException(status_code=403, detail="TempVC Feature ist deaktiviert")
    
    if not db:
        raise HTTPException(status_code=500, detail="TempVC Database nicht verfügbar")
    
    settings = db.get_tempvc_settings(guild_id)
    ui = db.get_ui_settings(guild_id)
    
    return {
        "creator_channel_id": str(settings[0]) if settings else "",
        "category_id": str(settings[1]) if settings else "",
        "auto_delete_time": settings[2] if settings and len(settings) > 2 else 0,
        "ui_enabled": bool(ui[0]) if ui else False,
        "ui_prefix": ui[1] if ui else "🔧"
    }

@app.post("/api/guild/{guild_id}/tempvc")
async def save_tempvc(guild_id: int, data: TempVCUpdate):
    """TempVC Einstellungen speichern"""
    await check_admin_permissions(guild_id, data.token)
    
    if not is_feature_enabled('features.cogs.server_management.tempvc'):
        raise HTTPException(status_code=403, detail="TempVC Feature ist deaktiviert")
    
    if not db:
        raise HTTPException(status_code=500, detail="TempVC Database nicht verfügbar")
    
    try:
        c_id = int(data.creator_channel_id)
        cat_id = int(data.category_id)
        logger.info(f"💾 SPEICHERN: Guild {guild_id} | IDs: {c_id}, {cat_id}")
        
        db.set_tempvc_settings(guild_id, c_id, cat_id, data.auto_delete_time)
        db.set_ui_settings(guild_id, data.ui_enabled, data.ui_prefix)
        
        return {"status": "success", "message": "Daten wurden permanent gespeichert"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Kanal- und Kategorie-IDs müssen Zahlen sein")
    except Exception as e:
        logger.error(f"Datenbank-Fehler: {e}")
        raise HTTPException(status_code=500, detail="Interner Datenbank-Fehler")

@app.get("/api/guild/{guild_id}/welcome")
async def get_welcome(guild_id: int, token: str = Depends(get_token)):
    """Welcome Einstellungen laden"""
    await check_admin_permissions(guild_id, token)
    
    if not is_feature_enabled('features.cogs.server_management.welcome'):
        raise HTTPException(status_code=403, detail="Welcome Feature ist deaktiviert")
    
    if not welcome_db:
        raise HTTPException(status_code=500, detail="Welcome Database nicht verfügbar")
    
    settings = welcome_db.get_welcome_settings(guild_id)
    
    if not settings:
        return {
            "channel_id": "",
            "welcome_message": "Willkommen {user} auf {server}!",
            "enabled": True,
            "embed_enabled": False,
            "embed_color": "#00ff00",
            "embed_title": "Willkommen!",
            "embed_description": "",
            "embed_thumbnail": False,
            "embed_footer": "",
            "ping_user": False,
            "delete_after": 0
        }
    
    return {
        "channel_id": str(settings.get('channel_id', '')),
        "welcome_message": settings.get('welcome_message', ''),
        "enabled": bool(settings.get('enabled', True)),
        "embed_enabled": bool(settings.get('embed_enabled', False)),
        "embed_color": settings.get('embed_color', '#00ff00'),
        "embed_title": settings.get('embed_title', ''),
        "embed_description": settings.get('embed_description', ''),
        "embed_thumbnail": bool(settings.get('embed_thumbnail', False)),
        "embed_footer": settings.get('embed_footer', ''),
        "ping_user": bool(settings.get('ping_user', False)),
        "delete_after": settings.get('delete_after', 0)
    }

@app.post("/api/guild/{guild_id}/welcome")
async def save_welcome(guild_id: int, data: WelcomeUpdate):
    """Welcome Einstellungen speichern"""
    await check_admin_permissions(guild_id, data.token)
    
    if not is_feature_enabled('features.cogs.server_management.welcome'):
        raise HTTPException(status_code=403, detail="Welcome Feature ist deaktiviert")
    
    if not welcome_db:
        raise HTTPException(status_code=500, detail="Welcome Database nicht verfügbar")
    
    try:
        ch_id = int(data.channel_id) if data.channel_id else None
        logger.info(f"💾 SPEICHERN WELCOME: Guild {guild_id} | Channel: {ch_id}")
        
        success = welcome_db.update_welcome_settings(
            guild_id,
            channel_id=ch_id,
            welcome_message=data.welcome_message,
            enabled=data.enabled,
            embed_enabled=data.embed_enabled,
            embed_color=data.embed_color,
            embed_title=data.embed_title,
            embed_description=data.embed_description,
            embed_thumbnail=data.embed_thumbnail,
            embed_footer=data.embed_footer,
            ping_user=data.ping_user,
            delete_after=data.delete_after
        )
        
        if success:
            return {"status": "success", "message": "Welcome-Einstellungen gespeichert"}
        else:
            raise HTTPException(status_code=500, detail="Fehler beim Speichern")
    except ValueError:
        raise HTTPException(status_code=400, detail="Ungültige Channel-ID")
    except Exception as e:
        logger.error(f"Fehler beim Speichern: {e}")
        raise HTTPException(status_code=500, detail="Interner Fehler")

@app.get("/api/guild/{guild_id}/levelsystem")
async def get_levelsystem(guild_id: int, token: str = Query(...)):
    """Levelsystem Einstellungen laden"""
    await check_admin_permissions(guild_id, token)
    
    if not is_feature_enabled('features.cogs.server_management.levelsystem'):
        raise HTTPException(status_code=403, detail="Levelsystem Feature ist deaktiviert")
    
    if not level_db:
        raise HTTPException(status_code=500, detail="Levelsystem Database nicht verfügbar")
    
    settings = level_db.get_guild_config(guild_id)
    
    if not settings:
        return {
            "levelsystem_enabled": True,
            "min_xp": 10,
            "max_xp": 20,
            "xp_cooldown": 30,
            "level_up_channel": "",
            "prestige_enabled": True,
            "prestige_min_level": 50
        }
    
    return {
        "levelsystem_enabled": settings.get('levelsystem_enabled', True),
        "min_xp": settings.get('min_xp', 10),
        "max_xp": settings.get('max_xp', 20),
        "xp_cooldown": settings.get('xp_cooldown', 30),
        "level_up_channel": str(settings.get('level_up_channel', '')),
        "prestige_enabled": settings.get('prestige_enabled', True),
        "prestige_min_level": settings.get('prestige_min_level', 50)
    }

@app.post("/api/guild/{guild_id}/levelsystem")
async def save_levelsystem(guild_id: int, data: LevelUpdate):
    """Levelsystem Einstellungen speichern"""
    await check_admin_permissions(guild_id, data.token)
    
    if not is_feature_enabled('features.cogs.server_management.levelsystem'):
        raise HTTPException(status_code=403, detail="Levelsystem Feature ist deaktiviert")
    
    if not level_db:
        raise HTTPException(status_code=500, detail="Levelsystem Database nicht verfügbar")
    
    try:
        ch_id = int(data.level_up_channel) if data.level_up_channel else None
        logger.info(f"💾 SPEICHERN LEVELSYSTEM: Guild {guild_id} | Channel: {ch_id}")
        
        config = {
            'levelsystem_enabled': data.levelsystem_enabled,
            'min_xp': data.min_xp,
            'max_xp': data.max_xp,
            'xp_cooldown': data.xp_cooldown,
            'level_up_channel': ch_id,
            'prestige_enabled': data.prestige_enabled,
            'prestige_min_level': data.prestige_min_level
        }
        level_db.update_guild_config(guild_id, config)
        
        return {"status": "success", "message": "Levelsystem-Einstellungen gespeichert"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Ungültige Channel-ID")
    except Exception as e:
        logger.error(f"Fehler beim Speichern: {e}")
        raise HTTPException(status_code=500, detail="Interner Fehler")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3002, log_level="warning")