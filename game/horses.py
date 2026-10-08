import math
import random
from typing import Dict, Any, List
from config.settings import HorseConfig

class ActiveBoost:
    def __init__(
        self,
        name: str,
        power: float,
        remaining_seconds: float,
        is_legendary: bool = False,
        legendary_kind: str | None = None,
        gift_emoji: str = "⚡",
        donor_name: str = ""
    ):
        self.name = name
        self.power = power
        self.remaining_seconds = remaining_seconds
        self.is_legendary = is_legendary
        self.legendary_kind = legendary_kind
        self.gift_emoji = gift_emoji
        self.donor_name = donor_name

class HorseState:
    def __init__(self, config: HorseConfig, lane: int = 1):
        self.config = config
        self.id = config.id
        self.number = config.number
        self.name = config.name
        self.color_hex = config.color_hex
        self.secondary_color_hex = config.secondary_color_hex
        self.personality = config.personality
        self.lane = lane
        
        # Estado dinâmico da corrida
        self.distance: float = 0.0
        self.speed: float = 0.0
        self.stamina: float = 100.0
        self.finished: bool = False
        self.finish_time_ms: int = 0
        self.active_boosts: List[ActiveBoost] = []
        self.cheer_count: int = 0
        self.supporter_count: int = 0
        
    def reset(self) -> None:
        self.distance = 0.0
        self.speed = 0.0
        self.stamina = 100.0
        self.finished = False
        self.finish_time_ms = 0
        self.active_boosts = []
        self.cheer_count = 0
        self.supporter_count = 0

    def add_boost(
        self,
        name: str,
        power: float,
        duration_seconds: float,
        is_legendary: bool = False,
        legendary_kind: str | None = None,
        gift_emoji: str = "⚡",
        donor_name: str = ""
    ) -> None:
        self.active_boosts.append(
            ActiveBoost(name, power, duration_seconds, is_legendary, legendary_kind, gift_emoji, donor_name)
        )

    def add_cheer(self) -> None:
        self.cheer_count += 1

    def calculate_personality_factor(self, progress_ratio: float, current_rank: int) -> float:
        """
        Modulador comportamental de 0.0 a 1.0 de progresso na pista.
        """
        p = self.personality
        factor = 1.0
        
        if p == "FRONT_RUNNER":  # Relâmpago
            # Início estrondoso, queda drástica na reta final
            if progress_ratio < 0.4:
                factor = 1.12
            elif progress_ratio < 0.75:
                factor = 1.02
            else:
                factor = 0.90  # Cansaço acentuado
                
        elif p == "CLOSER":  # Trovão
            # Início reservado, arranque avassalador no final
            if progress_ratio < 0.5:
                factor = 0.94
            elif progress_ratio < 0.75:
                factor = 1.04
            else:
                factor = 1.15  # Surto final
                
        elif p == "PACER":  # Furacão
            # Totalmente estável do início ao fim
            factor = 1.01
            
        elif p == "DRAFTER":  # Raio
            # Agressivo se estiver atrás do 1º lugar (no vácuo)
            if current_rank > 1:
                factor = 1.07
            else:
                factor = 0.98
                
        elif p == "CORNER_SPECIALIST":  # Pantera
            # Pista oval tem curvas em 20%-40% e 70%-90%
            in_curve = (0.20 <= progress_ratio <= 0.40) or (0.70 <= progress_ratio <= 0.90)
            factor = 1.08 if in_curve else 0.98
            
        elif p == "JUGGERNAUT":  # Titã
            # Lento no início, constante e imparável
            if progress_ratio < 0.2:
                factor = 0.92
            else:
                factor = 1.03
                
        elif p == "COLD_TACTICIAN":  # Nevasca
            # Mantém ritmo equilibrado
            factor = 1.02
            
        elif p == "WILDCARD":  # Fantasma
            # Sorte caótica: pode ter picos aleatórios
            if random.random() < 0.15:
                factor = 1.18
            else:
                factor = 0.98
                
        return factor

    def update_physics(
        self,
        dt: float,
        track_length: float,
        current_rank: int,
        weather_mult: float,
        race_elapsed_ms: int
    ) -> None:
        if self.finished:
            return

        progress = min(1.0, self.distance / max(1.0, track_length))
        
        # 1. Atualizar timers de boosts ativos
        boost_mult = 1.0
        remaining_boosts = []
        for b in self.active_boosts:
            b.remaining_seconds -= dt
            if b.remaining_seconds > 0:
                boost_mult *= b.power
                remaining_boosts.append(b)
        self.active_boosts = remaining_boosts
        
        # 2. Bônus de torcida coletiva (máx +5%)
        cheer_bonus = min(0.05, (self.cheer_count * 0.002))
        
        # 3. Fator de personalidade
        personality_mult = self.calculate_personality_factor(progress, current_rank)
        
        # 4. Fadiga da stamina
        stamina_loss = dt * (3.0 - (self.config.stamina * 0.15))
        self.stamina = max(10.0, self.stamina - stamina_loss)
        stamina_mult = 0.85 + (self.stamina / 100.0) * 0.15
        
        # 5. Ruído orgânico de galope
        organic_jitter = 1.0 + random.uniform(-0.02, 0.02) * (self.config.luck / 10.0)
        
        # Velocidade instantânea alvo
        target_speed = (
            self.config.base_speed
            * personality_mult
            * weather_mult
            * boost_mult
            * (1.0 + cheer_bonus)
            * stamina_mult
            * organic_jitter
        )
        
        # Interpolação suave de aceleração (lerp)
        accel_rate = self.config.acceleration * 1.5 * dt
        self.speed += (target_speed - self.speed) * min(1.0, accel_rate)
        
        # Atualiza distância
        self.distance += self.speed * dt
        
        # Verifica linha de chegada
        if self.distance >= track_length:
            self.distance = track_length
            self.finished = True
            self.finish_time_ms = race_elapsed_ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "number": self.number,
            "name": self.name,
            "color_hex": self.color_hex,
            "secondary_color_hex": self.secondary_color_hex,
            "personality": self.personality,
            "lane": self.lane,
            "distance": round(self.distance, 2),
            "speed": round(self.speed, 2),
            "stamina": round(self.stamina, 1),
            "finished": self.finished,
            "finish_time_ms": self.finish_time_ms,
            "boost_active": len(self.active_boosts) > 0,
            "is_legendary_boost": any(b.is_legendary for b in self.active_boosts),
            "legendary_kind": next((b.legendary_kind for b in self.active_boosts if b.is_legendary), None),
            "gift_emoji": self.active_boosts[-1].gift_emoji if self.active_boosts else None,
            "donor_name": self.active_boosts[-1].donor_name if self.active_boosts else None,
            "boosts": [{"name": b.name, "power": round(b.power, 2), "legendary": b.is_legendary, "emoji": b.gift_emoji} for b in self.active_boosts],
            "supporter_count": self.supporter_count,
            "cheer_count": self.cheer_count,
            "description": self.config.description
        }
