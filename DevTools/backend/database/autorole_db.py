import aiosqlite
import random
import string
import os

class AutoRoleDatabase:
    def __init__(self, db_path="data/autorole.db"):
        self.db_path = db_path
        # Erstellt den Ordner 'data', falls er fehlt
        directory = os.path.dirname(self.db_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    
    async def init_db(self):
        """Erstellt die Tabelle, falls sie noch nicht existiert"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS autoroles (
                    autorole_id TEXT PRIMARY KEY,
                    guild_id INTEGER NOT NULL,
                    role_id INTEGER NOT NULL,
                    enabled INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.commit()
    
    def generate_autorole_id(self, guild_id: int, role_id: int):
        guild_part = str(guild_id)[-2:].zfill(2)
        role_part = str(role_id)[-2:].zfill(2)
        random_part = ''.join(random.choices(string.digits, k=3))
        return f"{guild_part}-{role_part}-{random_part}"
    
    async def add_autorole(self, guild_id: int, role_id: int):
        # WICHTIG: Erst sicherstellen, dass die Tabelle da ist!
        await self.init_db()
        
        autorole_id = self.generate_autorole_id(guild_id, role_id)
        
        async with aiosqlite.connect(self.db_path) as db:
            # Check ob ID existiert
            while True:
                async with db.execute(
                    "SELECT autorole_id FROM autoroles WHERE autorole_id = ?",
                    (autorole_id,)
                ) as cursor:
                    if not await cursor.fetchone():
                        break
                    autorole_id = self.generate_autorole_id(guild_id, role_id)
            
            await db.execute("""
                INSERT INTO autoroles (autorole_id, guild_id, role_id, enabled)
                VALUES (?, ?, ?, 1)
            """, (autorole_id, guild_id, role_id))
            await db.commit()
        
        return autorole_id

    async def get_all_autoroles(self, guild_id: int):
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT autorole_id, role_id, enabled FROM autoroles WHERE guild_id = ?", 
                (guild_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [{"autorole_id": r[0], "role_id": r[1], "enabled": bool(r[2])} for r in rows]

    async def get_autorole(self, autorole_id: str):
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT autorole_id, guild_id, role_id, enabled FROM autoroles WHERE autorole_id = ?", 
                (autorole_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return {"autorole_id": row[0], "guild_id": row[1], "role_id": row[2], "enabled": bool(row[3])} if row else None

    async def get_enabled_autoroles(self, guild_id: int):
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT role_id FROM autoroles WHERE guild_id = ? AND enabled = 1", 
                (guild_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [r[0] for r in rows]

    async def remove_autorole(self, autorole_id: str):
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM autoroles WHERE autorole_id = ?", (autorole_id,))
            await db.commit()

    async def toggle_autorole(self, autorole_id: str, enabled: bool):
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE autoroles SET enabled = ? WHERE autorole_id = ?", 
                (1 if enabled else 0, autorole_id)
            )
            await db.commit()