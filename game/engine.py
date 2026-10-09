from typing import List, Dict, Any, Optional
from config.settings import Settings
from game.horses import HorseState
from game.weather_events import WeatherSystem, WeatherType
from game.physics import TrackGeometry

class RaceEngine:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.track_length = settings.track_length_meters
        self.weather_system = WeatherSystem()
        self.track_geometry = TrackGeometry(self.track_length)
        
        # Cria os 8 cavalos
        self.horses: List[HorseState] = []
        for i, h_cfg in enumerate(settings.horses):
            self.horses.append(HorseState(config=h_cfg, lane=i + 1))
            
        self.status: str = "READY"  # READY, RACING, FINISHED
        self.race_elapsed_ms: float = 0.0
        self.winner_horse_id: Optional[int] = None
        self.final_results: List[Dict[str, Any]] = []
        self.leader_horse_id: Optional[int] = None
        
    def reset(self) -> None:
        self.status = "READY"
        self.race_elapsed_ms = 0
        self.winner_horse_id = None
        if hasattr(self, "_winner_crossed_time_ms"):
            delattr(self, "_winner_crossed_time_ms")
        self.final_results = []
        for h in self.horses:
            h.reset()
        self.leader_horse_id = self.horses[0].id

    def set_weather(self, weather: WeatherType) -> None:
        self.weather_system.set_weather(weather)

    def start_race(self) -> None:
        self.status = "RACING"
        self.race_elapsed_ms = 0
        self.winner_horse_id = None
        self.final_results = []

    def is_finished(self) -> bool:
        return self.status == "FINISHED"

    def apply_boost(
        self,
        horse_id: int,
        boost_name: str,
        power: float,
        duration_seconds: float,
        is_legendary: bool = False,
        legendary_kind: Optional[str] = None,
        gift_emoji: str = "⚡",
        donor_name: str = ""
    ) -> bool:
        for h in self.horses:
            if h.id == horse_id:
                h.add_boost(boost_name, power, duration_seconds, is_legendary, legendary_kind, gift_emoji, donor_name)
                return True
        return False

    def add_cheer(self, horse_id: int) -> bool:
        for h in self.horses:
            if h.id == horse_id:
                h.add_cheer()
                return True
        return False

    def set_supporter_count(self, horse_id: int, count: int) -> None:
        for h in self.horses:
            if h.id == horse_id:
                h.supporter_count = count

    def update(self, dt: float) -> None:
        if self.status != "RACING":
            return
            
        # Relógio em ms SEM arredondar por tick: int(dt*1000) acumulava ~1,4s de
        # drift numa corrida de 35s e sujava o foto-finish dos tempos de chegada.
        self.race_elapsed_ms += dt * 1000.0
        
        # Ordena cavalos por distância para calcular posições correntes
        sorted_by_dist = sorted(self.horses, key=lambda h: h.distance, reverse=True)
        if sorted_by_dist:
            self.leader_horse_id = sorted_by_dist[0].id
            
        for rank_idx, h in enumerate(sorted_by_dist, start=1):
            w_mult = self.weather_system.get_weather_multiplier(h.personality)
            h.update_physics(
                dt=dt,
                track_length=self.track_length,
                current_rank=rank_idx,
                weather_mult=w_mult,
                race_elapsed_ms=self.race_elapsed_ms
            )
            
        # Verifica se o primeiro cavalo cruzou a linha
        finished_horses = [h for h in self.horses if h.finished]
        if finished_horses and self.winner_horse_id is None:
            # O primeiro a cruzar é o vencedor
            fastest = min(finished_horses, key=lambda h: h.finish_time_ms)
            self.winner_horse_id = fastest.id
            self._winner_crossed_time_ms = self.race_elapsed_ms
            
        # A corrida é finalizada quando todos terminam, ou 3.5s após o primeiro cruzar a linha, ou timeout de 60s
        all_finished = all(h.finished for h in self.horses)
        post_win_timeout = hasattr(self, "_winner_crossed_time_ms") and (self.race_elapsed_ms - self._winner_crossed_time_ms >= 3500)
        timeout = self.race_elapsed_ms > int((self.settings.race_duration_seconds + 10) * 1000)
        
        if (all_finished or post_win_timeout or timeout) and self.status == "RACING":
            self.status = "FINISHED"

            # Garante que qualquer cavalo retardatário cruze a linha final de 1000m
            # para que nenhum animal fique travado na pista fora da linha de chegada!
            for h in self.horses:
                if not h.finished:
                    h.distance = self.track_length
                    h.finished = True
                    h.finish_time_ms = round(self.race_elapsed_ms, 1)

            # Monta pódio final ordenado
            # Quem terminou vem SEMPRE na frente de quem não terminou; entre os
            # que terminaram, vale o tempo de chegada (foto-finish).
            results_order = sorted(
                self.horses,
                key=lambda h: (h.finished, -h.finish_time_ms if h.finished else h.distance),
                reverse=True
            )
            self.final_results = []
            for pos, h in enumerate(results_order, start=1):
                self.final_results.append({
                    "horse_id": h.id,
                    "final_position": pos,
                    "name": h.name,
                    "color_hex": h.color_hex,
                    "finish_time_ms": h.finish_time_ms if h.finished else round(self.race_elapsed_ms, 1)
                })

    def get_snapshot(self) -> Dict[str, Any]:
        # Ordena leaderboard corrente
        sorted_horses = sorted(self.horses, key=lambda h: h.distance, reverse=True)
        leaderboard = []
        for pos, h in enumerate(sorted_horses, start=1):
            leaderboard.append({
                "position": pos,
                "horse_id": h.id,
                "name": h.name,
                "color_hex": h.color_hex,
                "distance": round(h.distance, 1),
                "speed": round(h.speed, 1),
                "supporter_count": h.supporter_count,
                "boost_active": len(h.active_boosts) > 0
            })
            
        # Constrói dados 3D das coordenadas
        horses_data = []
        for h in self.horses:
            h_dict = h.to_dict()
            x, y, z, rot_y = self.track_geometry.get_coordinates(h.distance, h.lane)
            h_dict["x"] = round(x, 2)
            h_dict["y"] = round(y, 2)
            h_dict["z"] = round(z, 2)
            h_dict["rotation_y"] = round(rot_y, 3)
            horses_data.append(h_dict)
            
        return {
            "status": self.status,
            "race_elapsed_ms": int(self.race_elapsed_ms),
            "track_length": self.track_length,
            "weather": self.weather_system.current_weather.value,
            "wind_speed": round(self.weather_system.wind_speed, 2),
            "leader_horse_id": self.leader_horse_id,
            "winner_horse_id": self.winner_horse_id,
            "leaderboard": leaderboard,
            "horses": horses_data,
            "final_results": self.final_results
        }
