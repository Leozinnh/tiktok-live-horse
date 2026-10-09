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
        self.finish_time_ms: float = 0.0
        self.active_boosts: List[ActiveBoost] = []
        self.cheer_count: int = 0
        self.supporter_count: int = 0

        # O "dia do cavalo": sorteado a cada corrida (ver _draw_form e reset)
        self.form: float = self._draw_form()
        # Arrancadas de sorte: duração restante e multiplicador do surto atual
        self.surge_remaining: float = 0.0
        self.surge_mult: float = 1.0
        self.surge_count: int = 0

    def _draw_form(self) -> float:
        """
        O "dia do cavalo": cada corrida sorteia uma forma levemente boa ou ruim.
        Escala com a sorte (FANTASMA varia mais, TITÃ quase não) e é limitada a
        ±3% — o bastante para que nenhuma corrida esteja decidida na largada.
        """
        sigma = 0.010 * (self.config.luck / 10.0) + 0.002
        return max(0.97, min(1.03, 1.0 + random.gauss(0.0, sigma)))

    def reset(self) -> None:
        self.distance = 0.0
        self.speed = 0.0
        self.stamina = 100.0
        self.finished = False
        self.finish_time_ms = 0.0
        self.active_boosts = []
        self.cheer_count = 0
        self.supporter_count = 0
        self.form = self._draw_form()
        self.surge_remaining = 0.0
        self.surge_mult = 1.0
        self.surge_count = 0

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
        Modulador comportamental (0.0 a 1.0 de progresso na pista).

        Regra de ouro: para cada personalidade, Σ (fração da pista / fator)
        tem que dar 1.00 — a conta está anotada em cada faixa e é travada
        pelo teste `test_personalidade_decide_quando_vence_nao_se_vence`.

        Por que essa conta: o que decide a corrida é o TEMPO
        (tempo = distância / velocidade), então cada fração da pista entra
        DIVIDIDA pelo fator. E por que 1.00 cravado, não "≈1.00": uma soma
        em 0.99 parecia inofensiva, mas valia +0.77% de velocidade fixa ao
        RELÂMPAGO — um multiplicador grátis, a corrida inteira, invisível.
        Personalidade decide QUANDO cada um é forte; nunca se é mais rápido
        no total.
        """
        p = self.personality
        factor = 1.0

        if p == "FRONT_RUNNER":  # Relâmpago
            # Explode na largada e paga a conta na reta final
            # 0.40/1.075 + 0.35/1.00 + 0.25/0.90 = 1.00
            if progress_ratio < 0.4:
                factor = 1.075
            elif progress_ratio < 0.75:
                factor = 1.00
            else:
                factor = 0.90

        elif p == "CLOSER":  # Trovão
            # Economiza e dispara nos últimos 250m
            # 0.50/0.945 + 0.25/1.00 + 0.25/1.135 = 1.00
            if progress_ratio < 0.5:
                factor = 0.945
            elif progress_ratio < 0.75:
                factor = 1.00
            else:
                factor = 1.135

        elif p == "PACER":  # Furacão
            # Metrônomo: o mesmo ritmo do início ao fim
            factor = 1.00

        elif p == "DRAFTER":  # Raio
            # Forte no vácuo; QUANDO assume a ponta, perde rendimento de verdade
            # (0.78/1.018 + 0.22/0.94 = 1.00 — o vaivém fecha a conta: sem a
            # penalidade de líder, o vácuo virava motor perpétuo e ele vencia
            # ~80% das corridas)
            if current_rank > 1:
                factor = 1.018
            else:
                factor = 0.94

        elif p == "CORNER_SPECIALIST":  # Pantera
            # Pista oval tem curvas em 20%-40% e 70%-90% do traçado
            # 0.40/1.06 (curvas) + 0.60/0.964 (retas) = 1.00
            in_curve = (0.20 <= progress_ratio <= 0.40) or (0.70 <= progress_ratio <= 0.90)
            factor = 1.06 if in_curve else 0.964

        elif p == "JUGGERNAUT":  # Titã
            # Arrancada pesada, mas depois não para mais
            # 0.20/0.90 + 0.80/1.029 = 1.00
            if progress_ratio < 0.2:
                factor = 0.90
            else:
                factor = 1.029

        elif p == "COLD_TACTICIAN":  # Nevasca
            # Ritmo frio e constante; quem decide é o clima (ver weather_events)
            factor = 1.00

        elif p == "WILDCARD":  # Fantasma
            # Base neutra: o caos vem das arrancadas de sorte (ver update_physics)
            factor = 1.00

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
        
        # 4. Fadiga da stamina: agora pesa de verdade na reta final
        #    (quem tem 6.3 de stamina termina bem mais lento que quem tem 10)
        stamina_loss = dt * (2.7 - (self.config.stamina * 0.16))
        self.stamina = max(10.0, self.stamina - stamina_loss)
        stamina_mult = 0.86 + (self.stamina / 100.0) * 0.14

        # 5. Sorte: o "dia do cavalo" (form) + arrancadas surpresa
        #    Sorte alta = arrancadas mais frequentes e mais fortes (Fantasma),
        #    mas ninguém fica imune a um dia ruim.
        if self.surge_remaining > 0.0:
            self.surge_remaining -= dt
        else:
            self.surge_mult = 1.0
            if random.random() < dt * (0.03 + self.config.luck * 0.012):
                self.surge_remaining = random.uniform(0.4, 1.2)
                self.surge_mult = 1.05 + self.config.luck * 0.003
                self.surge_count += 1
        organic_jitter = 1.0 + random.uniform(-0.02, 0.02) * (self.config.luck / 10.0)

        # Velocidade instantânea alvo
        target_speed = (
            self.config.base_speed
            * personality_mult
            * weather_mult
            * boost_mult
            * (1.0 + cheer_bonus)
            * stamina_mult
            * self.form
            * self.surge_mult
            * organic_jitter
        )
        
        # Interpolação suave de aceleração (lerp)
        accel_rate = self.config.acceleration * 1.5 * dt
        self.speed += (target_speed - self.speed) * min(1.0, accel_rate)
        
        # Atualiza distância
        prev_distance = self.distance
        self.distance += self.speed * dt

        # Verifica linha de chegada — tempo com precisão de foto-finish:
        # cruzou no meio do tick? O tempo é o instante exato do cruzamento,
        # não o fim do tick (sem isso, empates falsos e 17ms de erro).
        if self.distance >= track_length:
            step = self.distance - prev_distance
            frac = 1.0 if step <= 0.0 else (track_length - prev_distance) / step
            self.distance = track_length
            self.finished = True
            self.finish_time_ms = round(race_elapsed_ms - (1.0 - frac) * dt * 1000.0, 1)

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
