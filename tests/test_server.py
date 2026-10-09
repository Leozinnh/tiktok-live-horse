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


def _boosts_of_horse(client, horse_id: int):
    data = client.get("/api/state").json()
    horse = next(h for h in data["engine"]["horses"] if h["id"] == horse_id)
    return horse["boosts"]


def test_gift_power_scales_with_value_and_count(test_app):
    client = TestClient(test_app)

    def last_boost(horse_id=1):
        return _boosts_of_horse(client, horse_id)[-1]

    # Rosa x1 -> 1.20 | Rosa x10: +10% do delta por unidade extra (teto de 5) -> 1.30
    client.post("/api/test/inject_gift", json={
        "username": "doador", "display_name": "Doador", "gift_name": "Rose", "count": 1})
    assert last_boost()["power"] == 1.2

    client.post("/api/test/inject_gift", json={
        "username": "doador", "display_name": "Doador", "gift_name": "Rose", "count": 10})
    assert last_boost()["power"] == 1.3

    # Leão x1 -> 1.70 | Leão x100 estoura o teto -> 1.80
    client.post("/api/test/inject_gift", json={
        "username": "doador", "display_name": "Doador", "gift_name": "Lion", "count": 1})
    assert last_boost()["power"] == 1.7
    assert last_boost()["legendary"] is True

    client.post("/api/test/inject_gift", json={
        "username": "doador", "display_name": "Doador", "gift_name": "Lion", "count": 100})
    assert last_boost()["power"] == 1.8


def test_like_burst_gives_light_boost(test_app):
    client = TestClient(test_app)

    # Rajada de 5+ curtidas: empurrão bem leve no cavalo do apoiador (líder/1 se não escolheu)
    res = client.post("/api/test/inject_like", json={
        "username": "torcedor", "display_name": "Torcedor", "count": 5})
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    like_boosts = [b for b in _boosts_of_horse(client, 1) if b["name"] == "GALERA CURTIU"]
    assert len(like_boosts) == 1
    assert like_boosts[0]["power"] == 1.02
    assert like_boosts[0]["emoji"] == "❤️"

    # Rajada maior empurra um pouco mais, mas nunca passa do teto (1.05)
    client.post("/api/test/inject_like", json={
        "username": "torcedor", "display_name": "Torcedor", "count": 30})
    like_boosts = [b for b in _boosts_of_horse(client, 1) if b["name"] == "GALERA CURTIU"]
    assert like_boosts[-1]["power"] == 1.04
    assert like_boosts[-1]["power"] <= 1.05

    # Menos de 5 de uma vez: nenhum boost
    before = len(_boosts_of_horse(client, 1))
    client.post("/api/test/inject_like", json={
        "username": "torcedor", "display_name": "Torcedor", "count": 4})
    assert len(_boosts_of_horse(client, 1)) == before

    # Curtida não cria usuário nem rende XP/estatística
    names = [v["tiktok_username"] for v in client.get("/api/test/viewers").json()["viewers"]]
    assert "torcedor" not in names


def test_like_burst_goes_to_supporters_horse(test_app):
    client = TestClient(test_app)

    # Espectador escolhe o cavalo 3 e depois manda curtidas: boost vai para o cavalo dele
    client.post("/api/test/inject_comment", json={
        "username": "fa", "display_name": "Fã", "text": "3"})
    client.post("/api/test/inject_like", json={
        "username": "fa", "display_name": "Fã", "count": 10})

    boosts = _boosts_of_horse(client, 3)
    assert any(b["name"] == "GALERA CURTIU" for b in boosts)
    assert not any(b["name"] == "GALERA CURTIU" for b in _boosts_of_horse(client, 1))


def test_viewers_list_and_reset(test_app):
    client = TestClient(test_app)

    # Cria um usuário com XP via presente
    client.post("/api/test/inject_gift", json={
        "username": "vitima", "display_name": "Vítima", "gift_name": "Rose", "count": 2})

    data = client.get("/api/test/viewers").json()
    assert data["total"] >= 1
    viewer = next(v for v in data["viewers"] if v["tiktok_username"] == "vitima")
    assert viewer["xp"] > 0

    # Zera só esse usuário
    res = client.post("/api/test/reset_viewer", json={"viewer_id": viewer["id"]})
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    viewer = next(v for v in client.get("/api/test/viewers").json()["viewers"] if v["id"] == viewer["id"])
    assert (viewer["xp"], viewer["level"], viewer["races_count"], viewer["wins_count"]) == (0, 1, 0, 0)

    # ID inexistente -> 404
    res = client.post("/api/test/reset_viewer", json={"viewer_id": 999999})
    assert res.status_code == 404

    # Zerar todos
    client.post("/api/test/inject_gift", json={
        "username": "outro", "display_name": "Outro", "gift_name": "Lion", "count": 1})
    res = client.post("/api/test/reset_all_viewers")
    assert res.status_code == 200
    assert res.json()["reset_count"] >= 2

    for v in client.get("/api/test/viewers").json()["viewers"]:
        assert (v["xp"], v["level"], v["races_count"], v["wins_count"]) == (0, 1, 0, 0)
