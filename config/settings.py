import json
from pathlib import Path
from typing import List, Literal
from pydantic import BaseModel, Field

PersonalityType = Literal[
    "FRONT_RUNNER",
    "CLOSER",
    "PACER",
    "DRAFTER",
    "CORNER_SPECIALIST",
    "JUGGERNAUT",
    "COLD_TACTICIAN",
    "WILDCARD"
]

class HorseConfig(BaseModel):
    id: int
    number: int
    name: str
    color_hex: str
    secondary_color_hex: str = "#FFFFFF"
    personality: PersonalityType
    base_speed: float = Field(ge=10.0, le=50.0)
    acceleration: float = Field(ge=1.0, le=20.0)
    stamina: float = Field(ge=1.0, le=20.0)
    luck: float = Field(ge=1.0, le=20.0)
    aggressiveness: float = Field(ge=1.0, le=20.0)
    description: str = ""

class XpConfig(BaseModel):
    participation: int = 20
    cheer: int = 5
    top_3: int = 50
    win: int = 150
    gift_small: int = 100
    gift_medium: int = 250
    gift_large: int = 500

class Settings(BaseModel):
    race_duration_seconds: float = 35.0
    voting_duration_seconds: float = 30.0
    countdown_duration_seconds: float = 5.0
    podium_duration_seconds: float = 8.0
    xp_duration_seconds: float = 6.0
    leaderboard_duration_seconds: float = 10.0
    track_length_meters: float = 1000.0
    tick_rate: int = 60
    xp: XpConfig = Field(default_factory=XpConfig)
    horses: List[HorseConfig] = Field(default_factory=list)

def load_config(config_path: Path | None = None) -> Settings:
    if config_path is None:
        config_path = Path(__file__).resolve().parent / "config.json"
    
    if not config_path.exists():
        # Retorna configuração padrão caso não exista
        return Settings()
    
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Settings.model_validate(data)
