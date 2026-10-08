import pytest
import asyncio
from config.settings import load_config
from backend.database.repository import DatabaseRepository
from game.engine import RaceEngine
from game.director import EventDirector, DirectorState
from tiktok.mock_adapter import MockTikTokAdapter

@pytest.mark.asyncio
async def test_full_e2e_race_cycle(tmp_path):
    config = load_config()
    # Durações curtas para validação rápida no teste
    config.track_length_meters = 120.0
    config.voting_duration_seconds = 0.2
    config.countdown_duration_seconds = 0.1
    config.race_duration_seconds = 4.0
    config.podium_duration_seconds = 0.1
    config.xp_duration_seconds = 0.1
    config.leaderboard_duration_seconds = 0.1

    db_path = tmp_path / "e2e_test.db"
    repo = DatabaseRepository(str(db_path))
    await repo.init_db()

    engine = RaceEngine(config)
    director = EventDirector(config, engine, repo)
    adapter = MockTikTokAdapter(director)

    # 1. Fase VOTING: Espectadores escolhem cavalos
    assert director.state == DirectorState.VOTING
    res1 = await adapter.inject_comment("viewer_ana", "Ana", "1")
    assert res1["status"] == "ok"
    assert res1["horse_id"] == 1

    res2 = await adapter.inject_comment("viewer_bob", "Bob", "2")
    assert res2["status"] == "ok"
    assert res2["horse_id"] == 2

    # Injeta presente durante a votação
    await adapter.inject_gift("viewer_ana", "Ana", "Rose", 1)

    # 2. Transição VOTING -> COUNTDOWN
    await director.tick(0.25)
    assert director.state == DirectorState.COUNTDOWN

    # 3. Transição COUNTDOWN -> RACING
    await director.tick(0.15)
    assert director.state == DirectorState.RACING

    # Injeta boost durante a corrida
    await adapter.inject_gift("viewer_bob", "Bob", "Galaxy", 1)

    # 4. Simula avanço da corrida até a linha de chegada
    dt = 1.0 / 60.0
    for _ in range(400):
        await director.tick(dt)
        if director.state != DirectorState.RACING:
            break

    # Deve ter transicionado para PODIUM
    assert director.state == DirectorState.PODIUM
    assert len(director.podium_data) > 0
    winner_id = director.engine.winner_horse_id
    assert winner_id is not None

    # 5. Transição PODIUM -> XP_REWARDS
    await director.tick(0.15)
    assert director.state == DirectorState.XP_REWARDS
    assert len(director.last_race_rewards) == 2  # Ana e Bob receberam XP

    # 6. Transição XP_REWARDS -> LEADERBOARD
    await director.tick(0.15)
    assert director.state == DirectorState.LEADERBOARD
    assert len(director.leaderboard_data) >= 2

    # 7. Transição LEADERBOARD -> Novo ciclo VOTING (Corrida #2)
    await director.tick(0.15)
    assert director.state == DirectorState.VOTING
    assert director.race_number == 2
