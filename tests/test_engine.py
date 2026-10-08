import pytest
from config.settings import load_config

def test_engine_initialization_and_snapshot():
    from game.engine import RaceEngine
    
    config = load_config()
    engine = RaceEngine(config)
    engine.reset()
    
    snapshot = engine.get_snapshot()
    assert snapshot["status"] == "READY"
    assert len(snapshot["horses"]) == 8
    assert snapshot["leaderboard"][0]["position"] == 1
    
    # Todos começam na linha de partida (distância 0)
    for h in snapshot["horses"]:
        assert h["distance"] == 0.0
        assert h["finished"] is False

def test_engine_race_simulation_and_boost():
    from game.engine import RaceEngine
    
    config = load_config()
    engine = RaceEngine(config)
    engine.reset()
    engine.start_race()
    
    # Aplica turbo no cavalo 1 (Relâmpago)
    engine.apply_boost(horse_id=1, boost_name="TURBO_ROSA", power=1.15, duration_seconds=3.0)
    
    # Simula 10 segundos a 60 ticks (dt = 1/60)
    dt = 1.0 / 60.0
    for _ in range(600):
        engine.update(dt)
        
    snapshot = engine.get_snapshot()
    assert snapshot["status"] == "RACING"
    h1 = next(h for h in snapshot["horses"] if h["id"] == 1)
    assert h1["distance"] > 200.0  # Percorreu distância substancial
    
    # Continua até a corrida finalizar
    ticks = 0
    while not engine.is_finished() and ticks < 3000:
        engine.update(dt)
        ticks += 1
        
    assert engine.is_finished() is True
    final_snapshot = engine.get_snapshot()
    assert final_snapshot["status"] == "FINISHED"
    assert final_snapshot["winner_horse_id"] is not None
    assert len(final_snapshot["final_results"]) == 8
    assert final_snapshot["final_results"][0]["final_position"] == 1

def test_weather_and_personalities():
    from game.engine import RaceEngine
    from game.weather_events import WeatherType
    
    config = load_config()
    engine = RaceEngine(config)
    engine.reset()
    engine.set_weather(WeatherType.RAIN)
    
    engine.start_race()
    for _ in range(300):
        engine.update(1.0 / 60.0)
        
    snap = engine.get_snapshot()
    assert snap["weather"] == "RAIN"
