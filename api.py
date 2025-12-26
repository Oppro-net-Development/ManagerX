from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI()

# CORS-Einstellungen (Später durch .env ALLOWED_ORIGINS ersetzen)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/managerx/stats")
async def get_stats():
    try:
        # Pfad zur bot_stats.json (muss im selben Ordner liegen)
        if os.path.exists("bot_stats.json"):
            with open("bot_stats.json", "r") as f:
                data = json.load(f)
            return data
        else:
            return {"error": "Datei nicht gefunden"}, 404
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=3002)