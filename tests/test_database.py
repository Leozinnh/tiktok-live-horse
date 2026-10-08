import pytest
import asyncio
from pathlib import Path

@pytest.mark.asyncio
async def test_database_lifecycle_and_xp(tmp_path):
    from backend.database.repository import DatabaseRepository
    from backend.progression import calculate_level, xp_for_level
    
    db_file = tmp_path / "test_race.db"
    repo = DatabaseRepository(db_path=str(db_file))
    await repo.init_db()
    
    # 1. Teste de viewer
    viewer = await repo.get_or_create_viewer("user_123", "Leonardo")
    assert viewer["tiktok_username"] == "user_123"
    assert viewer["display_name"] == "Leonardo"
    assert viewer["xp"] == 0
    assert viewer["level"] == 1
    
    # 2. Criar uma corrida e registrar escolha
    race_id = await repo.create_race(race_number=1)
    assert race_id > 0
    
    choice_ok = await repo.record_choice(race_id=race_id, viewer_id=viewer["id"], horse_id=1)
    assert choice_ok is True
    
    # 3. Finalizar corrida com resultados
    results = [
        {"horse_id": 1, "final_position": 1, "finish_time_ms": 34120},
        {"horse_id": 2, "final_position": 2, "finish_time_ms": 34500},
        {"horse_id": 3, "final_position": 3, "finish_time_ms": 34800},
    ]
    await repo.finish_race(race_id=race_id, winner_horse_id=1, results=results)
    
    # 4. Distribuir XP e verificar subida de nível
    updated_viewers = await repo.distribute_race_xp(
        race_id=race_id,
        winner_horse_id=1,
        top_3_horse_ids=[1, 2, 3],
        xp_participation=20,
        xp_win=150,
        xp_top3=50
    )
    assert len(updated_viewers) == 1
    v_updated = updated_viewers[0]
    assert v_updated["xp"] == 170  # 20 participação + 150 vitória
    assert v_updated["wins_count"] == 1
    
    # 5. Obter Leaderboard
    leaderboard = await repo.get_leaderboard(limit=5)
    assert len(leaderboard) == 1
    assert leaderboard[0]["tiktok_username"] == "user_123"
    assert leaderboard[0]["xp"] == 170

def test_progression_math():
    from backend.progression import calculate_level, xp_for_level, get_title_for_level
    
    assert calculate_level(0) == 1
    assert calculate_level(50) == 1
    assert calculate_level(200) >= 2
    assert calculate_level(5000) > 5
    
    assert xp_for_level(1) == 0
    assert xp_for_level(2) > 0
    assert xp_for_level(3) > xp_for_level(2)
    
    title = get_title_for_level(1)
    assert isinstance(title, str)
    assert len(title) > 0
