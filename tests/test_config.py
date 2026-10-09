import pytest
import json
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

def test_load_horses_from_individual_json_files(tmp_path):
    from config.settings import load_config
    
    horses_dir = tmp_path / "horses"
    horses_dir.mkdir()
    
    h1_data = {
        "id": 1,
        "number": 1,
        "name": "RELÂMPAGO DOURADO",
        "color_hex": "#F59E0B",
        "secondary_color_hex": "#FEF3C7",
        "mane_color_hex": "#D97706",
        "hoof_color_hex": "#1E293B",
        "jockey_silk_hex": "#3B82F6",
        "jockey_helmet_hex": "#EF4444",
        "visual_style": "fire",
        "personality": "FRONT_RUNNER",
        "base_speed": 29.0,
        "acceleration": 9.8,
        "stamina": 7.2,
        "luck": 6.5,
        "aggressiveness": 7.8,
        "description": "Edição especial com crina dourada."
    }
    
    h2_data = {
        "id": 2,
        "number": 2,
        "name": "TROVÃO NEGRO",
        "color_hex": "#1E1B4B",
        "secondary_color_hex": "#38BDF8",
        "personality": "CLOSER",
        "base_speed": 28.0,
        "acceleration": 7.2,
        "stamina": 8.6,
        "luck": 7.1,
        "aggressiveness": 8.2,
        "description": "Edição trovão da meia-noite."
    }
    
    with open(horses_dir / "1_relampago.json", "w", encoding="utf-8") as f:
        json.dump(h1_data, f)
        
    with open(horses_dir / "2_trovao.json", "w", encoding="utf-8") as f:
        json.dump(h2_data, f)
        
    config = load_config(horses_dir=horses_dir)
    assert len(config.horses) == 2
    assert config.horses[0].name == "RELÂMPAGO DOURADO"
    assert config.horses[0].mane_color_hex == "#D97706"
    assert config.horses[0].jockey_silk_hex == "#3B82F6"
    assert config.horses[0].visual_style == "fire"
    assert config.horses[1].name == "TROVÃO NEGRO"
