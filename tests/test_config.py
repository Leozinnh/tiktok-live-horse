import pytest
from pathlib import Path

def test_load_config_values():
    from config.settings import load_config, Settings
    
    config = load_config()
    assert isinstance(config, Settings)
    assert config.race_duration_seconds > 0
    assert config.voting_duration_seconds > 0
    assert len(config.horses) == 8
    
    # Validação do cavalo 1 - Relâmpago
    h1 = config.horses[0]
    assert h1.id == 1
    assert h1.name.upper() == "RELÂMPAGO"
    assert h1.number == 1
    assert h1.color_hex.startswith("#")
    assert h1.base_speed > 0
    assert h1.personality in [
        "FRONT_RUNNER", "CLOSER", "PACER", "DRAFTER",
        "CORNER_SPECIALIST", "JUGGERNAUT", "COLD_TACTICIAN", "WILDCARD"
    ]
    
    # Validação de compliance (100% virtual)
    assert config.xp.participation > 0
    assert config.xp.win > 0
