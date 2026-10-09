import pytest
import asyncio
from config.settings import load_config
from backend.database.repository import DatabaseRepository

@pytest.mark.asyncio
async def test_event_bus():
    from backend.event_bus import EventBus
    
    bus = EventBus()
    received = []
    
    async def listener(event):
        received.append(event)
        
    bus.subscribe("PLAYER_CHOICE", listener)
    await bus.publish({"type": "PLAYER_CHOICE", "user": "Leo", "horse_id": 1})
    
    assert len(received) == 1
    assert received[0]["user"] == "Leo"
    assert received[0]["horse_id"] == 1

@pytest.mark.asyncio
async def test_director_state_transitions(tmp_path):
    from game.director import EventDirector, DirectorState
    from game.engine import RaceEngine
    
    config = load_config()
    # Durações curtas para teste unitário ágil
    config.voting_duration_seconds = 0.1
    config.countdown_duration_seconds = 0.05
    config.podium_duration_seconds = 0.05
    config.xp_duration_seconds = 0.05
    config.leaderboard_duration_seconds = 0.05
    
    db_file = tmp_path / "test_director.db"
    repo = DatabaseRepository(db_path=str(db_file))
    await repo.init_db()
    
    engine = RaceEngine(config)
    director = EventDirector(config=config, engine=engine, repository=repo)
    
    # Estado inicial deve ser VOTING
    assert director.state == DirectorState.VOTING
    assert director.race_number == 1
    
    # Registra escolha de cavalo de um viewer
    await director.handle_viewer_choice("leo", "Leonardo", 1)
    choices = director.get_current_choices_summary()
    assert choices[1]["supporters_count"] == 1
    
    # Executa step de tempo que transiciona VOTING -> COUNTDOWN
    await director.tick(0.15)
    assert director.state == DirectorState.COUNTDOWN

    # Transiciona COUNTDOWN -> RACING
    await director.tick(0.06)
    assert director.state == DirectorState.RACING


@pytest.mark.asyncio
async def test_narracao_da_corrida_no_console(tmp_path, caplog):
    """O console conta a história da live: votação, largada, presente, prêmios."""
    import logging
    from game.director import EventDirector
    from game.engine import RaceEngine

    config = load_config()
    config.voting_duration_seconds = 0.1
    config.countdown_duration_seconds = 0.05

    repo = DatabaseRepository(db_path=str(tmp_path / "test_narracao.db"))
    await repo.init_db()
    engine = RaceEngine(config)

    with caplog.at_level(logging.INFO, logger="game.director"):
        director = EventDirector(config=config, engine=engine, repository=repo)
        assert "votação aberta" in caplog.text

        await director.handle_viewer_choice("leo", "Leonardo", 1)
        await director.tick(0.15)
        assert "Votação encerrada" in caplog.text
        assert "favorito #1" in caplog.text

        await director.tick(0.06)
        assert "COMEÇOU" in caplog.text

        await director.handle_viewer_gift("leo", "Leonardo", "Lion", 1)
        assert "enviou Lion x1" in caplog.text

        await director.handle_viewer_like("leo", "Leonardo", 10)
        assert "10 curtidas" in caplog.text
