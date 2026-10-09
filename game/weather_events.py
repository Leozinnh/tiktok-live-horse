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

class WeatherSystem:
    def __init__(self):
        self.current_weather: WeatherType = WeatherType.CLEAR
        self.wind_speed: float = 0.0  # -1.0 a +1.0
        self.intensity: float = 0.0
        
    def set_weather(self, weather: WeatherType, intensity: float = 0.5) -> None:
        self.current_weather = weather
        self.intensity = intensity
        if weather == WeatherType.WIND:
            self.wind_speed = random.uniform(-0.8, 0.8)
        else:
            self.wind_speed = 0.0

    def pick_random_weather(self) -> WeatherType:
        # 60% limpo/entardecer/noite, 40% climas dinâmicos
        choices = [
            (WeatherType.CLEAR, 0.35),
            (WeatherType.SUNSET, 0.20),
            (WeatherType.NIGHT_LIGHTS, 0.15),
            (WeatherType.RAIN, 0.15),
            (WeatherType.WIND, 0.10),
            (WeatherType.STORM, 0.05),
        ]
        types, weights = zip(*choices)
        chosen = random.choices(types, weights=weights, k=1)[0]
        self.set_weather(chosen, random.uniform(0.4, 0.8))
        return chosen

    def get_weather_multiplier(self, horse_personality: str) -> float:
        """
        Multiplicador de velocidade com base no clima e personalidade.

        O clima dá vantagem a quem tem vocação — mas nenhum clima pode ser uma
        roleta: os desvios ficam na casa de ±2% para o resto do páreo continuar
        na briga (antes, chuva = 0.92 pra todos e o dono do clima vencia 100%;
        com +2%/-1% de swing o dono do clima vence ~40% das vezes — vantagem
        clara, sem entregar a corrida).
        """
        mult = 1.0
        if self.current_weather == WeatherType.RAIN:
            if horse_personality == "JUGGERNAUT":  # Titã: adora lama
                mult = 1.006
            elif horse_personality == "COLD_TACTICIAN":  # Nevasca: dia perfeito
                mult = 1.012
            else:
                mult = 0.993  # Perdem um pouco de tração
        elif self.current_weather == WeatherType.STORM:
            if horse_personality in ["FRONT_RUNNER", "DRAFTER"]:
                mult = 1.01  # Estimulados pela tempestade
            elif horse_personality == "JUGGERNAUT":
                mult = 1.005
            elif horse_personality == "COLD_TACTICIAN":
                mult = 1.005
            else:
                mult = 0.985
        elif self.current_weather == WeatherType.WIND:
            # Vento frontal ou a favor
            mult = 1.0 + (self.wind_speed * 0.03)
            if horse_personality == "DRAFTER":  # Raio vive de vácuo, até no vento
                mult += 0.02
            elif horse_personality == "COLD_TACTICIAN":  # Nevasca também cresce no vento
                mult += 0.02
        return mult
