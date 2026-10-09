import json
import logging
from pathlib import Path
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("config")

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
    mane_color_hex: str = "#1E293B"
    hoof_color_hex: str = "#0F172A"
    jockey_silk_hex: str = ""
    jockey_helmet_hex: str = ""
    body_model: str = "classic"
    visual_style: str = "classic"
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

class TtsConfig(BaseModel):
    active: bool = True
    voz: str = ""
    vozes: List[str] = Field(default_factory=list)
    rate: str = ""
    pitch: str = ""
    anunciar_entrada: bool = True
    falas: Optional[List[str]] = None
    boas_vindas: Optional[List[str]] = None
    votacao: Optional[List[str]] = None
    largada: Optional[List[str]] = None
    vencedor: Optional[List[str]] = None
    corrida_abertura: Optional[List[str]] = None
    corrida_disputa: Optional[List[str]] = None
    corrida_placar: Optional[List[str]] = None
    reta_final: Optional[List[str]] = None
    foto_finish: Optional[List[str]] = None
    clima: Optional[List[str]] = None
    clima_virada: Optional[List[str]] = None

class Settings(BaseModel):
    race_duration_seconds: float = 35.0
    voting_duration_seconds: float = 30.0
    countdown_duration_seconds: float = 5.0
    podium_duration_seconds: float = 8.0
    xp_duration_seconds: float = 6.0
    leaderboard_duration_seconds: float = 10.0
    track_length_meters: float = 1000.0
    tick_rate: int = 60
    tts: TtsConfig = Field(default_factory=TtsConfig)
    xp: XpConfig = Field(default_factory=XpConfig)
    horses: List[HorseConfig] = Field(default_factory=list)

def _find_horses_directory(config_path: Path, explicit_dir: Path | None = None) -> Optional[Path]:
    if explicit_dir is not None:
        p = Path(explicit_dir)
        return p if p.exists() and p.is_dir() else None

    # Candidatos padrão para a pasta 'horses'
    candidates = [
        config_path.parent.parent / "horses",
        Path("horses").resolve(),
        config_path.parent / "horses"
    ]
    for c in candidates:
        if c.exists() and c.is_dir():
            return c
    return None

def load_horses_from_dir(horses_dir: Path) -> List[HorseConfig]:
    loaded = []
    json_files = sorted(list(horses_dir.glob("*.json")))
    for jf in json_files:
        try:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)
                horse = HorseConfig.model_validate(data)
                loaded.append(horse)
        except Exception as e:
            logger.warning(f"Erro ao carregar cavalo do arquivo {jf.name}: {e}")
            
    # Ordena por número e depois ID
    loaded.sort(key=lambda h: (h.number, h.id))
    return loaded

def load_config(config_path: Path | None = None, horses_dir: Path | None = None) -> Settings:
    if config_path is None:
        config_path = Path(__file__).resolve().parent / "config.json"
    
    if not config_path.exists():
        settings = Settings()
    else:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        settings = Settings.model_validate(data)
    
    # Busca e carrega cavalos individuais da pasta 'horses' se existir
    h_dir = _find_horses_directory(config_path, explicit_dir=horses_dir)
    if h_dir is not None:
        horses_from_files = load_horses_from_dir(h_dir)
        if horses_from_files:
            settings.horses = horses_from_files
            
    return settings
