from enum import Enum
import random
from typing import Dict, Any

class WeatherType(str, Enum):
    CLEAR = "CLEAR"
    RAIN = "RAIN"
    STORM = "STORM"
    WIND = "WIND"
    SUNSET = "SUNSET"
    NIGHT_LIGHTS = "NIGHT_LIGHTS"


# ---------------------------------------------------------------------------
# A tabela do clima: UMA fonte de verdade do que cada tempo faz com cada
# personalidade. O valor é o DESVIO somado a 1.0 no multiplicador de
# velocidade, modulado pela força do clima na hora (ver `_forca`).
#
# "Eleição" do clima, sem entrega: o dono do clima leva vantagem clara, mas o
# resto do páreo continua na briga (antes, chuva = -8% pra todos e o dono do
# clima vencia 100% das vezes). "_outros" é o desvio de quem não tem vocação;
# clima sem "_outros" (vento) não prejudica ninguém por si só.
# ---------------------------------------------------------------------------
VANTAGEM_CLIMA: Dict[WeatherType, Dict[str, float]] = {
    WeatherType.RAIN: {
        "COLD_TACTICIAN": +0.012,  # NEVASCA: dia perfeito
        "JUGGERNAUT": +0.006,      # TITÃ: adora lama
        "_outros": -0.007,         # o resto perde um pouco de tração
    },
    WeatherType.STORM: {
        "FRONT_RUNNER": +0.010,    # estimulados pela tempestade
        "DRAFTER": +0.010,
        "JUGGERNAUT": +0.005,
        "COLD_TACTICIAN": +0.005,
        "_outros": -0.015,
    },
    WeatherType.WIND: {
        "DRAFTER": +0.020,         # RAIO vive de vácuo, até no vento
        "COLD_TACTICIAN": +0.020,  # NEVASCA também cresce no vento
    },
}

# O vento é um caso à parte: além da vocação acima, o vento sorteado
# (wind_speed, -0.8 a +0.8) empurra TODO mundo — a favor ou contra.
VENTO_POR_UNIDADE = 0.03

# O que a voz fala: o locutor não diz "RAIN", diz "chuva forte".
ROTULOS: Dict[WeatherType, str] = {
    WeatherType.CLEAR: "céu limpo",
    WeatherType.RAIN: "chuva",
    WeatherType.STORM: "tempestade",
    WeatherType.WIND: "vento",
    WeatherType.SUNSET: "fim de tarde",
    WeatherType.NIGHT_LIGHTS: "noite de luzes",
}
EMOJIS: Dict[WeatherType, str] = {
    WeatherType.CLEAR: "☀️",
    WeatherType.RAIN: "🌧️",
    WeatherType.STORM: "⛈️",
    WeatherType.WIND: "💨",
    WeatherType.SUNSET: "🌇",
    WeatherType.NIGHT_LIGHTS: "🌙",
}

# Climas em que a força entra no rótulo ("chuva FRACA", "vento FORTE") e os
# de rótulo masculino (a palavra da força flexiona: fraco/fraca).
_COM_INTENSIDADE = {WeatherType.RAIN, WeatherType.STORM, WeatherType.WIND}
_MASCULINOS = {WeatherType.WIND}


def _palavra_da_forca(intensidade: float, masculino: bool) -> str:
    if intensidade < 0.5:
        return "fraco" if masculino else "fraca"
    if intensidade < 0.7:
        return "moderado" if masculino else "moderada"
    return "forte"


class WeatherSystem:
    def __init__(self):
        self.current_weather: WeatherType = WeatherType.CLEAR
        self.wind_speed: float = 0.0  # -1.0 a +1.0
        # Neutro por padrão: força 1.0 = o efeito de sempre (o mesmo da
        # `set_weather` sem intensidade). A corrida de verdade sorteia.
        self.intensity: float = 0.5
        # A primeira corrida pode sair em qualquer clima (inclusive CLEAR, o
        # de casa); da segunda em diante, o sorteio foge do clima atual.
        self._inicial: bool = True

    def set_weather(self, weather: WeatherType, intensity: float = 0.5) -> None:
        self.current_weather = weather
        self.intensity = intensity
        if weather == WeatherType.WIND:
            self.wind_speed = random.uniform(-0.8, 0.8)
        else:
            self.wind_speed = 0.0

    def pick_random_weather(self) -> WeatherType:
        """Sorteia o clima da próxima corrida — nunca o mesmo da anterior.

        Repetir era sorteado: a live emendava corridas com a mesma cara. O
        clima atual sai da urna; só a PRIMEIRA corrida pode nascer repetida
        (nasce CLEAR, e o primeiro sorteio é livre).
        """
        choices = [
            (WeatherType.CLEAR, 0.35),
            (WeatherType.SUNSET, 0.20),
            (WeatherType.NIGHT_LIGHTS, 0.15),
            (WeatherType.RAIN, 0.15),
            (WeatherType.WIND, 0.10),
            (WeatherType.STORM, 0.05),
        ]
        if self._inicial:
            self._inicial = False
        else:
            choices = [c for c in choices if c[0] != self.current_weather]
        types, weights = zip(*choices)
        chosen = random.choices(types, weights=weights, k=1)[0]
        self.set_weather(chosen, random.uniform(0.4, 0.8))
        return chosen

    def _forca(self) -> float:
        """A força do clima agora: 0.5 = neutro (o efeito de sempre).

        A intensidade sorteada (0.4–0.8) vira 0.9–1.3: chuva fraca incomoda
        menos, tempestade forte mexe mais com a corrida.
        """
        return 0.5 + self.intensity

    def rotulo(self) -> str:
        """O clima como a voz fala: "chuva forte", "céu limpo"."""
        base = ROTULOS[self.current_weather]
        if self.current_weather not in _COM_INTENSIDADE:
            return base
        flexao = _palavra_da_forca(self.intensity, self.current_weather in _MASCULINOS)
        return f"{base} {flexao}"

    def favoritos(self) -> list[str]:
        """As personalidades que ESTE clima favorece (só desvio positivo)."""
        vantagens = VANTAGEM_CLIMA.get(self.current_weather, {})
        return [p for p, desvio in vantagens.items() if desvio > 0]

    def emoji(self) -> str:
        """O emoji do clima, para o telão."""
        return EMOJIS[self.current_weather]

    def get_weather_multiplier(self, horse_personality: str) -> float:
        """
        Multiplicador de velocidade com base no clima e personalidade.

        O desvio sorteia da tabela VANTAGEM_CLIMA e é modulado pela força do
        clima na hora — o dono do clima leva vantagem clara (uns poucos %),
        nunca a corrida entregue. O vento ainda soma o empurrão global do
        wind_speed (a favor ou contra), que vale para todos.
        """
        vantagens = VANTAGEM_CLIMA.get(self.current_weather, {})
        desvio = vantagens.get(horse_personality, vantagens.get("_outros", 0.0))
        mult = 1.0 + desvio * self._forca()
        if self.current_weather == WeatherType.WIND:
            mult += self.wind_speed * VENTO_POR_UNIDADE
        return mult
