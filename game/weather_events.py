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
        Retorna multiplicador de velocidade com base no clima e personalidade.
        """
        mult = 1.0
        if self.current_weather == WeatherType.RAIN:
            if horse_personality == "JUGGERNAUT":  # Titã
                mult = 1.02  # Ganha vantagem na lama
            elif horse_personality == "COLD_TACTICIAN":  # Nevasca
                mult = 1.05  # Excelente na chuva
            else:
                mult = 0.92  # Outros perdem tração
        elif self.current_weather == WeatherType.STORM:
            if horse_personality in ["FRONT_RUNNER", "DRAFTER"]:
                mult = 1.04  # Estimulado por tempestade
            elif horse_personality == "JUGGERNAUT":
                mult = 1.01
            else:
                mult = 0.88
        elif self.current_weather == WeatherType.WIND:
            # Vento frontal ou a favor
            mult = 1.0 + (self.wind_speed * 0.05)
            if horse_personality == "DRAFTER":  # Raio se beneficia muito de vácuo no vento
                mult += 0.04
        return mult
