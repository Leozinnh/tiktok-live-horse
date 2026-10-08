import asyncio
from enum import Enum
from typing import Dict, Any, List, Optional
from config.settings import Settings
from game.engine import RaceEngine
from backend.database.repository import DatabaseRepository

class DirectorState(str, Enum):
    VOTING = "VOTING"
    COUNTDOWN = "COUNTDOWN"
    RACING = "RACING"
    PODIUM = "PODIUM"
    XP_REWARDS = "XP_REWARDS"
    LEADERBOARD = "LEADERBOARD"

class EventDirector:
    def __init__(self, config: Settings, engine: RaceEngine, repository: DatabaseRepository):
        self.config = config
        self.engine = engine
        self.repository = repository
        
        self.state: DirectorState = DirectorState.VOTING
        self.race_number: int = 1
        self.current_db_race_id: Optional[int] = None
        self.state_timer: float = 0.0
        
        # Mapa: horse_id -> lista de dicionários de espectadores que escolheram
        self.horse_supporters: Dict[int, List[Dict[str, Any]]] = {h.id: [] for h in self.config.horses}
        # Mapa: user_id -> viewer_dict
        self.viewers_cache: Dict[str, Dict[str, Any]] = {}
        # Fila de notificações para o HUD
        self.notifications_queue: List[Dict[str, Any]] = []
        # Resultados e recompensas da última corrida
        self.last_race_rewards: List[Dict[str, Any]] = []
        self.podium_data: List[Dict[str, Any]] = []
        self.leaderboard_data: List[Dict[str, Any]] = []

    def get_current_choices_summary(self) -> Dict[int, Dict[str, Any]]:
        summary = {}
        for h in self.config.horses:
            supporters = self.horse_supporters.get(h.id, [])
            summary[h.id] = {
                "horse_id": h.id,
                "horse_name": h.name,
                "color_hex": h.color_hex,
                "supporters_count": len(supporters),
                "recent_supporters": [s["display_name"] for s in supporters[-5:]]
            }
        return summary

    async def handle_viewer_choice(self, tiktok_username: str, display_name: str, horse_id: int) -> bool:
        if self.state != DirectorState.VOTING:
            return False
            
        if horse_id not in [h.id for h in self.config.horses]:
            return False
            
        viewer = await self.repository.get_or_create_viewer(tiktok_username, display_name)
        self.viewers_cache[viewer["tiktok_username"]] = viewer
        
        # Remove escolha anterior do mesmo viewer se já existia
        for hid in self.horse_supporters:
            self.horse_supporters[hid] = [
                s for s in self.horse_supporters[hid] if s["tiktok_username"] != viewer["tiktok_username"]
            ]
            
        # Adiciona ao novo cavalo
        self.horse_supporters[horse_id].append({
            "viewer_id": viewer["id"],
            "tiktok_username": viewer["tiktok_username"],
            "display_name": viewer["display_name"],
            "level": viewer["level"]
        })
        
        # Atualiza contagem na engine
        self.engine.set_supporter_count(horse_id, len(self.horse_supporters[horse_id]))
        
        # Adiciona notificação para o HUD
        h_name = next(h.name for h in self.config.horses if h.id == horse_id)
        self.notifications_queue.append({
            "type": "CHOICE",
            "text": f"{viewer['display_name']} escolheu {h_name}!",
            "horse_id": horse_id,
            "badge": "🏇"
        })
        
        return True

    async def handle_viewer_gift(
        self,
        tiktok_username: str,
        display_name: str,
        gift_name: str,
        gift_count: int = 1
    ) -> None:
        viewer = await self.repository.get_or_create_viewer(tiktok_username, display_name)
        self.viewers_cache[viewer["tiktok_username"]] = viewer
        
        # Determina cavalo do espectador (ou o líder/aleatório se não escolheu)
        chosen_horse_id = None
        for hid, sups in self.horse_supporters.items():
            if any(s["tiktok_username"] == viewer["tiktok_username"] for s in sups):
                chosen_horse_id = hid
                break
                
        if not chosen_horse_id:
            chosen_horse_id = self.engine.leader_horse_id or 1
            
        h_name = next(h.name for h in self.config.horses if h.id == chosen_horse_id)
        
        # Determina impacto do presente
        gift_lower = gift_name.lower()
        is_legendary = False
        legendary_kind = None

        gift_emoji_map = {
            "galaxy": "🌌", "galaxia": "🌌",
            "lion": "🦁", "leao": "🦁", "leão": "🦁",
            "dragon": "🐉", "dragao": "🐉", "dragão": "🐉",
            "universe": "🪐", "universo": "🪐",
            "rose": "🌹", "rosa": "🌹",
            "donut": "🍩",
            "cap": "🧢", "bone": "🧢", "boné": "🧢",
            "coffee": "☕", "cafe": "☕", "café": "☕",
            "coracao": "💖", "coração": "💖", "heart": "💖",
            "fire": "🔥", "fogo": "🔥"
        }
        gift_emoji = "🎁"
        for k, e in gift_emoji_map.items():
            if k in gift_lower:
                gift_emoji = e
                break

        if any(w in gift_lower for w in ["galaxy", "galaxia"]):
            power, dur, xp = 1.30, 6.0, 1500
            b_label = "OVERDRIVE GALÁCTICO"
            is_legendary = True
            legendary_kind = "GALAXY"
        elif any(w in gift_lower for w in ["lion", "leao", "leão"]):
            power, dur, xp = 1.35, 6.5, 2000
            b_label = "FÚRIA DO LEÃO DOURADO"
            is_legendary = True
            legendary_kind = "LION"
        elif any(w in gift_lower for w in ["dragon", "dragao", "dragão", "universe", "universo"]):
            power, dur, xp = 1.32, 6.0, 1800
            b_label = "IMPACTO DO DRAGÃO CÓSMICO"
            is_legendary = True
            legendary_kind = "DRAGON"
        elif any(w in gift_lower for w in ["cap", "donut", "coffee", "perfume", "coracao"]):
            power, dur, xp = 1.15, 3.5, self.config.xp.gift_medium
            b_label = "SUPER BOOST"
        else:
            power, dur, xp = 1.08, 2.5, self.config.xp.gift_small
            b_label = "TURBO"
            
        # Aplica boost na engine (tanto em RACING quanto acumulando em VOTING/COUNTDOWN!)
        self.engine.apply_boost(
            horse_id=chosen_horse_id,
            boost_name=b_label,
            power=power,
            duration_seconds=dur,
            is_legendary=is_legendary,
            legendary_kind=legendary_kind,
            gift_emoji=gift_emoji,
            donor_name=viewer['display_name']
        )
            
        # Adiciona XP ao viewer
        await self.repository.add_gift_xp(viewer["id"], xp * gift_count)
        
        # Log visível no terminal Python do servidor
        print(f"\n[PRESENTE RECEBIDO] {gift_emoji} @{viewer['display_name']} enviou {gift_name} x{gift_count} para o Cavalo #{chosen_horse_id} ({h_name})! (+{xp * gift_count} XP)\n")

        self.notifications_queue.append({
            "type": "GIFT",
            "is_legendary": is_legendary,
            "legendary_kind": legendary_kind,
            "sender_name": viewer['display_name'],
            "gift_name": gift_name,
            "gift_emoji": gift_emoji,
            "boost_label": b_label,
            "text": f"{gift_emoji} {viewer['display_name']} enviou {gift_name}! {b_label} em {h_name}!",
            "horse_id": chosen_horse_id,
            "horse_name": h_name,
            "badge": gift_emoji
        })

    async def handle_cheer_command(self, tiktok_username: str, display_name: str) -> None:
        viewer = await self.repository.get_or_create_viewer(tiktok_username, display_name)
        chosen_horse_id = None
        for hid, sups in self.horse_supporters.items():
            if any(s["tiktok_username"] == viewer["tiktok_username"] for s in sups):
                chosen_horse_id = hid
                break
        if chosen_horse_id:
            self.engine.add_cheer(chosen_horse_id)

    async def skip_to_countdown(self) -> None:
        """Pula o tempo de votação e inicia a contagem de largada imediatamente."""
        self.state = DirectorState.COUNTDOWN
        self.state_timer = 0.0

    async def force_finish_race(self) -> None:
        """Força a finalização da corrida e avança para o pódio."""
        if self.state == DirectorState.RACING:
            # Força avanço dos cavalos para cruzar a linha
            for h in self.engine.horses:
                if not h.finished:
                    h.distance = self.engine.track_length
                    h.finished = True
                    h.finish_time_ms = self.engine.race_elapsed_ms or 34000
            self.engine.status = "FINISHED"
            self.state = DirectorState.PODIUM
            self.state_timer = 0.0
            snapshot = self.engine.get_snapshot()
            self.podium_data = snapshot.get("final_results", [])[:3]

    async def reset_to_new_race(self) -> None:
        """Reinicia o ciclo imediatamente para uma nova corrida."""
        self.race_number += 1
        self.engine.reset()
        self.horse_supporters = {h.id: [] for h in self.config.horses}
        self.state = DirectorState.VOTING
        self.state_timer = 0.0
        self.last_race_rewards = []

    async def tick(self, dt: float) -> None:
        self.state_timer += dt
        
        if self.state == DirectorState.VOTING:
            if self.state_timer >= self.config.voting_duration_seconds:
                # Transiciona para COUNTDOWN
                self.state = DirectorState.COUNTDOWN
                self.state_timer = 0.0
                
        elif self.state == DirectorState.COUNTDOWN:
            if self.state_timer >= self.config.countdown_duration_seconds:
                # Inicia corrida real
                self.state = DirectorState.RACING
                self.state_timer = 0.0
                self.engine.start_race()
                
                # Registra corrida no banco SQLite
                self.current_db_race_id = await self.repository.create_race(self.race_number)
                
                # Registra escolhas de todos os espectadores no banco
                for hid, sups in self.horse_supporters.items():
                    for s in sups:
                        await self.repository.record_choice(
                            race_id=self.current_db_race_id,
                            viewer_id=s["viewer_id"],
                            horse_id=hid
                        )
                        
        elif self.state == DirectorState.RACING:
            self.engine.update(dt)
            if self.engine.is_finished():
                self.state = DirectorState.PODIUM
                self.state_timer = 0.0
                snapshot = self.engine.get_snapshot()
                self.podium_data = snapshot.get("final_results", [])[:3]
                
                # Salva resultados no banco
                if self.current_db_race_id and snapshot.get("winner_horse_id"):
                    await self.repository.finish_race(
                        race_id=self.current_db_race_id,
                        winner_horse_id=snapshot["winner_horse_id"],
                        results=snapshot["final_results"]
                    )
                    
        elif self.state == DirectorState.PODIUM:
            if self.state_timer >= self.config.podium_duration_seconds:
                self.state = DirectorState.XP_REWARDS
                self.state_timer = 0.0
                
                # Distribuir XP e obter quem subiu de nível
                winner_id = self.engine.winner_horse_id or 1
                top_3_ids = [r["horse_id"] for r in self.podium_data]
                if self.current_db_race_id:
                    self.last_race_rewards = await self.repository.distribute_race_xp(
                        race_id=self.current_db_race_id,
                        winner_horse_id=winner_id,
                        top_3_horse_ids=top_3_ids,
                        xp_participation=self.config.xp.participation,
                        xp_win=self.config.xp.win,
                        xp_top3=self.config.xp.top_3
                    )
                    
        elif self.state == DirectorState.XP_REWARDS:
            if self.state_timer >= self.config.xp_duration_seconds:
                self.state = DirectorState.LEADERBOARD
                self.state_timer = 0.0
                self.leaderboard_data = await self.repository.get_leaderboard(limit=10)
                
        elif self.state == DirectorState.LEADERBOARD:
            if self.state_timer >= self.config.leaderboard_duration_seconds:
                # Reinicia novo ciclo
                self.race_number += 1
                self.engine.reset()
                self.engine.weather_system.pick_random_weather()
                self.horse_supporters = {h.id: [] for h in self.config.horses}
                self.state = DirectorState.VOTING
                self.state_timer = 0.0
                self.last_race_rewards = []

    def get_state_payload(self) -> Dict[str, Any]:
        engine_snap = self.engine.get_snapshot()
        
        # Coleta notificações recentes (máx 3)
        recent_notifications = self.notifications_queue[-3:] if self.notifications_queue else []
        if len(self.notifications_queue) > 20:
            self.notifications_queue = self.notifications_queue[-10:]
            
        remaining_time = 0.0
        if self.state == DirectorState.VOTING:
            remaining_time = max(0.0, self.config.voting_duration_seconds - self.state_timer)
        elif self.state == DirectorState.COUNTDOWN:
            remaining_time = max(0.0, self.config.countdown_duration_seconds - self.state_timer)
            
        return {
            "race_number": self.race_number,
            "director_state": self.state.value,
            "state_timer": round(self.state_timer, 2),
            "remaining_seconds": round(remaining_time, 1),
            "engine": engine_snap,
            "voting_summary": self.get_current_choices_summary(),
            "notifications": recent_notifications,
            "podium": self.podium_data,
            "rewards": self.last_race_rewards[:6],
            "leaderboard": self.leaderboard_data
        }
