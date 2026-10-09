import asyncio
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config.settings import Settings
from game.director import EventDirector
from tiktok.mock_adapter import MockTikTokAdapter
from backend.database.repository import DatabaseRepository
from game.weather_events import WeatherType

logger = logging.getLogger("server")

class CommentRequest(BaseModel):
    username: str
    display_name: str = ""
    text: str

class GiftRequest(BaseModel):
    username: str
    display_name: str = ""
    gift_name: str
    count: int = 1

class LikeRequest(BaseModel):
    username: str = ""
    display_name: str = ""
    count: int = 5

class ResetViewerRequest(BaseModel):
    viewer_id: int

class BurstRequest(BaseModel):
    count: int = 20

class WeatherRequest(BaseModel):
    weather: str

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                dead_connections.append(connection)
        for dead in dead_connections:
            self.disconnect(dead)

def create_app(
    config: Settings,
    director: EventDirector,
    mock_adapter: MockTikTokAdapter,
    repository: DatabaseRepository
) -> FastAPI:
    app = FastAPI(title="TikTok LIVE Horse Racing")
    manager = ConnectionManager()
    
    # Armazena estado no app
    app.state.director = director
    app.state.mock_adapter = mock_adapter
    app.state.repository = repository
    app.state.manager = manager
    app.state.is_loop_running = False
    app.state.hud_config = {"scale": 1.0, "top": 195, "left": 28, "showTower": True, "showProgress": True}

    # Diretório estático
    static_dir = Path(__file__).resolve().parent / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def get_index():
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return HTMLResponse("<h1>TikTok LIVE Horse Racing - OBS Display</h1>")

    @app.get("/test", response_class=HTMLResponse)
    async def get_test():
        test_file = static_dir / "test.html"
        if test_file.exists():
            return FileResponse(test_file)
        return HTMLResponse("<h1>Streamer Test Mode Panel</h1>")

    @app.get("/api/state")
    async def get_state():
        return director.get_state_payload()

    @app.get("/api/leaderboard")
    async def get_leaderboard(limit: int = 10):
        return await repository.get_leaderboard(limit=limit)

    @app.get("/api/test/viewers")
    async def list_viewers(limit: int = 500):
        viewers = await repository.get_all_viewers(limit=limit)
        return {"viewers": viewers, "total": len(viewers)}

    @app.post("/api/test/reset_viewer")
    async def reset_viewer(req: ResetViewerRequest):
        ok = await repository.reset_viewer(req.viewer_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Viewer não encontrado")
        return {"status": "ok", "viewer_id": req.viewer_id}

    @app.post("/api/test/reset_all_viewers")
    async def reset_all_viewers():
        count = await repository.reset_all_viewers()
        return {"status": "ok", "reset_count": count}

    @app.post("/api/test/inject_comment")
    async def inject_comment(req: CommentRequest):
        res = await mock_adapter.inject_comment(
            username=req.username,
            display_name=req.display_name or req.username,
            text=req.text
        )
        return res

    @app.post("/api/test/inject_gift")
    async def inject_gift(req: GiftRequest):
        res = await mock_adapter.inject_gift(
            username=req.username,
            display_name=req.display_name or req.username,
            gift_name=req.gift_name,
            count=req.count
        )
        return res

    @app.post("/api/test/inject_like")
    async def inject_like(req: LikeRequest):
        res = await mock_adapter.inject_like(
            username=req.username or "Torcida",
            display_name=req.display_name or req.username or "Torcida",
            count=req.count
        )
        return res

    @app.post("/api/test/burst")
    async def burst(req: BurstRequest):
        res = await mock_adapter.simulate_crowd_burst(count=req.count)
        return res

    @app.post("/api/test/weather")
    async def set_weather(req: WeatherRequest):
        try:
            wt = WeatherType[req.weather.upper()]
            director.engine.set_weather(wt)
            return {"status": "ok", "weather": wt.value}
        except KeyError:
            raise HTTPException(status_code=400, detail="Clima inválido")

    @app.post("/api/test/skip_to_race")
    async def skip_to_race():
        await director.skip_to_countdown()
        return {"status": "ok", "state": director.state.value}

    @app.post("/api/test/force_finish")
    async def force_finish():
        await director.force_finish_race()
        return {"status": "ok", "state": director.state.value}

    @app.post("/api/test/next_race")
    async def next_race():
        await director.reset_to_new_race()
        return {"status": "ok", "race_number": director.race_number}

    @app.post("/api/test/boost_horse")
    async def boost_horse(horse_id: int = 1, power: float = 1.2, duration: float = 4.0):
        director.engine.apply_boost(horse_id, "ADMIN_BOOST", power, duration)
        return {"status": "ok", "horse_id": horse_id}

    @app.post("/api/test/hud_config")
    async def update_hud_config(config: Dict[str, Any]):
        app.state.hud_config.update(config)
        broadcast_msg = json.dumps({
            "type": "HUD_CONFIG_UPDATE",
            "config": app.state.hud_config
        })
        await manager.broadcast(broadcast_msg)
        return {"status": "ok", "config": app.state.hud_config}

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await manager.connect(websocket)
        # Envia estado inicial imediato
        initial_payload = director.get_state_payload()
        initial_payload["hud_config"] = app.state.hud_config
        await websocket.send_text(json.dumps(initial_payload))
        
        try:
            while True:
                # Ouve mensagens de clientes (ex: comandos do painel de teste via websocket)
                data_text = await websocket.receive_text()
                try:
                    msg = json.loads(data_text)
                    msg_type = msg.get("type")
                    if msg_type == "INJECT_COMMENT":
                        await mock_adapter.inject_comment(
                            msg.get("username", "anon"),
                            msg.get("display_name", "anon"),
                            msg.get("text", "")
                        )
                    elif msg_type == "INJECT_GIFT":
                        await mock_adapter.inject_gift(
                            msg.get("username", "anon"),
                            msg.get("display_name", "anon"),
                            msg.get("gift_name", "Rose"),
                            msg.get("count", 1)
                        )
                    elif msg_type == "SET_HUD_CONFIG":
                        app.state.hud_config.update(msg.get("config", {}))
                        broadcast_msg = json.dumps({
                            "type": "HUD_CONFIG_UPDATE",
                            "config": app.state.hud_config
                        })
                        await manager.broadcast(broadcast_msg)
                except Exception as e:
                    logger.debug(f"Erro processando mensagem ws: {e}")
        except WebSocketDisconnect:
            manager.disconnect(websocket)
        except Exception:
            manager.disconnect(websocket)

    return app

async def run_simulation_loop(director: EventDirector, manager: ConnectionManager, tick_rate: int = 60):
    """
    Loop principal de simulação a 60 ticks/s com broadcast contínuo aos WebSockets.
    """
    dt = 1.0 / float(tick_rate)
    while True:
        start_time = asyncio.get_event_loop().time()
        
        # Atualiza máquina de estados e simulação física
        await director.tick(dt)
        
        # Transmite snapshot se houver conexões ativas
        if manager.active_connections:
            payload = json.dumps(director.get_state_payload())
            await manager.broadcast(payload)
            
        # Manutenção de framerate constante
        elapsed = asyncio.get_event_loop().time() - start_time
        sleep_time = max(0.001, dt - elapsed)
        await asyncio.sleep(sleep_time)
