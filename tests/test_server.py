import pytest
from starlette.testclient import TestClient
from config.settings import load_config
from backend.database.repository import DatabaseRepository
from game.engine import RaceEngine
from game.director import EventDirector
from tiktok.mock_adapter import MockTikTokAdapter

@pytest.fixture
def test_app(tmp_path):
    from web.server import create_app
    
    config = load_config()
    db_file = tmp_path / "test_server.db"
    repo = DatabaseRepository(str(db_file))
    
    import asyncio
    asyncio.run(repo.init_db())
    
    engine = RaceEngine(config)
    director = EventDirector(config, engine, repo)
    mock_adapter = MockTikTokAdapter(director)
    
    app = create_app(config, director, mock_adapter, repo)
    return app

def test_api_state_and_test_injection(test_app):
    client = TestClient(test_app)
    
    # Verifica endpoint /api/state
    res = client.get("/api/state")
    assert res.status_code == 200
    data = res.json()
    assert "director_state" in data
    assert "engine" in data
    assert len(data["engine"]["horses"]) == 8
    
    # Injeta comentário de teste
    comment_payload = {
        "username": "tester1",
        "display_name": "Tester Um",
        "text": "1"
    }
    res_post = client.post("/api/test/inject_comment", json=comment_payload)
    assert res_post.status_code == 200
    res_json = res_post.json()
    assert res_json["status"] == "ok"
    assert res_json["horse_id"] == 1
    
    # Injeta presente de teste
    gift_payload = {
        "username": "tester1",
        "display_name": "Tester Um",
        "gift_name": "Rose",
        "count": 1
    }
    res_gift = client.post("/api/test/inject_gift", json=gift_payload)
    assert res_gift.status_code == 200
    assert res_gift.json()["status"] == "ok"
