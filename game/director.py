import asyncio
import logging
import random
from enum import Enum
from typing import Dict, Any, List, Optional
from config.settings import Settings
from game.engine import RaceEngine
from game.narrador import Narrador
from backend.database.repository import DatabaseRepository

logger = logging.getLogger(__name__)

class DirectorState(str, Enum):
    VOTING = "VOTING"
    COUNTDOWN = "COUNTDOWN"
    RACING = "RACING"
    PODIUM = "PODIUM"
    XP_REWARDS = "XP_REWARDS"
    LEADERBOARD = "LEADERBOARD"

# ---------------------------------------------------------------------------
# Tabela de presentes: quanto mais valioso, maior o bônus (velocidade + duração).
# `keywords` casa por substring no nome do presente (inglês e português).
# `xp` aceita "small"/"medium"/"large" (vem do config) ou um número fixo.
# Calibre power/duration/xp aqui sem tocar na lógica.
# ---------------------------------------------------------------------------
GIFT_TIERS = [
    {"keywords": ["lion", "leao", "leão"], "power": 1.70, "duration": 9.0, "xp": 2000,
     "label": "FÚRIA DO LEÃO DOURADO", "legendary": "LION", "emoji": "🦁"},
    {"keywords": ["dragon", "dragao", "dragão"], "power": 1.65, "duration": 8.5, "xp": 1800,
     "label": "IMPACTO DO DRAGÃO CÓSMICO", "legendary": "DRAGON", "emoji": "🐉"},
    {"keywords": ["galaxy", "galaxia", "universe", "universo"], "power": 1.60, "duration": 8.0, "xp": 1500,
     "label": "OVERDRIVE GALÁCTICO", "legendary": "GALAXY", "emoji": "🌌"},
    {"keywords": ["cap", "bone", "boné"], "power": 1.35, "duration": 5.5, "xp": "medium",
     "label": "SUPER BOOST", "legendary": None, "emoji": "🧢"},
    {"keywords": ["donut"], "power": 1.35, "duration": 5.5, "xp": "medium",
     "label": "SUPER BOOST", "legendary": None, "emoji": "🍩"},
    {"keywords": ["coffee", "cafe", "café"], "power": 1.20, "duration": 4.5, "xp": "small",
     "label": "TURBO", "legendary": None, "emoji": "☕"},
    {"keywords": ["rose", "rosa", "heart", "coracao", "coração", "perfume"], "power": 1.20, "duration": 4.0, "xp": "small",
     "label": "TURBO", "legendary": None, "emoji": "🌹"},
]
GIFT_DEFAULT = {"keywords": [], "power": 1.12, "duration": 3.0, "xp": "small",
                "label": "TURBO", "legendary": None, "emoji": "🎁"}

# Quantidade enviada amplia o bônus: cada unidade extra soma 10% do delta do tier
# (teto de 5 extras) e o multiplicador final nunca passa de 1.8.
# Ex.: 10 rosas = 1.30 (acima de 1 rosa = 1.20, abaixo de 1 galáxia = 1.60).
GIFT_COUNT_STEP = 0.10
GIFT_COUNT_MAX_EXTRA = 5
GIFT_POWER_CAP = 1.8

# Curtidas em rajada (>= LIKE_BURST_MIN de uma vez) dão um empurrão BEM leve.
# Curtida é gratuita e infinita: não pode competir com presente.
LIKE_BURST_MIN = 5
LIKE_DURATION_SECONDS = 3.0
LIKE_POWER_BASE = 1.02
LIKE_POWER_MAX = 1.05

# O número digitado com a corrida ROLANDO é torcida: um empurrãozinho leve e
# curto no cavalo citado, só para o público sentir que o comentário mexeu na
# prova. Bem leve de propósito: quem quer decidir a corrida manda presente.
TORCIDA_POWER = 1.03
TORCIDA_DURATION_SECONDS = 2.5

# A virada do tempo no meio da prova: com essa chance, a corrida sorteia na
# largada um ponto do trajeto (entre 35% e 70% da pista) em que o clima vira
# — com aviso da voz e do telão. O visual acompanha (scene.js).
CLIMA_VIRADA_CHANCE = 0.35
CLIMA_VIRADA_ENTRE = (0.35, 0.70)

# Locução ao vivo: os marcos de distância do líder (metros) que disparam cada
# chamada e a margem de chegada (ms) que faz a corrida ganhar a exclamação da
# foto-finish. Cada marco fala UMA vez por corrida.
#
# Os marcos são DENSOS de propósito: a ~28m/s, um a cada ~120-160m dá uma
# fala a cada ~5s — a corrida fica narrada do começo ao fim, como numa
# transmissão de turfe de verdade. Com só três marcos (abertura, disputa e
# reta), sobravam buracos de 10-12s de silêncio no meio da prova.
# O de 880m cai a ~4s da linha: é o tempo de gerar o áudio e a voz entrar no
# ar antes do vencedor cruzar (a fila do narrador é uma só).
MARCOS_LOCUCAO = (
    (120.0, "abertura"),
    (320.0, "placar"),
    (480.0, "disputa"),
    (620.0, "placar"),
    (760.0, "placar"),
    (880.0, "reta_final"),
)
MARGEM_FOTO_FINISH_MS = 50.0

# De quanto em quanto tempo a votação é RE-chamada na voz. A chamada de
# abertura sozinha deixava 30s de silêncio na fase em que o público precisa
# de lembrete — o locutor de rádio não fica mudo pedindo voto.
CHAMADA_VOTACAO_INTERVALO = 12.0


class EventDirector:
    def __init__(
        self,
        config: Settings,
        engine: RaceEngine,
        repository: DatabaseRepository,
        narrador: Optional[Narrador] = None,
    ):
        self.config = config
        self.engine = engine
        self.repository = repository
        # A voz da live (opcional): None = jogo mudo, como nos testes.
        self.narrador = narrador
        
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
        # Marcos da locução ao vivo já falados NESTA corrida (abertura,
        # disputa, reta final) — zerado na largada, pra nenhum marco repetir.
        self._marcos_falados: set[str] = set()
        # O líder já cruzou e a locução pendente já foi descartada? (uma vez
        # por corrida: o descarte não fica varrendo a fila a cada tick)
        self._locucao_encerrada: bool = False
        self._vitoria_anunciada: bool = False
        # Distância do líder em que o tempo VIRA nesta corrida (None = clima
        # estável) — sorteada na largada, ver `_sortear_hora_da_virada`.
        self._virada_clima_em: Optional[float] = None

        self._anunciar_votacao_aberta()

    def _nome_cavalo(self, horse_id: int) -> str:
        return next((h.name for h in self.config.horses if h.id == horse_id), f"#{horse_id}")

    def _sortear_clima_da_corrida(self) -> None:
        """Sorteia o clima da corrida que está abrindo e conta pro público.

        O sorteio mora AQUI, na abertura da votação, e não no meio do ciclo:
        é o ponto por onde passam os três caminhos que abrem votação —
        criação do director, reset e virada do ranking. O clima nunca repete
        o da corrida anterior (regra do próprio WeatherSystem).
        """
        weather = self.engine.weather_system
        weather.pick_random_weather()
        rotulo = weather.rotulo()
        nomes = self._favoritos_do_clima()
        logger.info(
            f"🌦️ Clima da corrida #{self.race_number}: {rotulo}."
            + (f" Favorece: {', '.join(nomes)}." if nomes else "")
        )
        if self.narrador is not None:
            self.narrador.anunciar_clima(rotulo, nomes)
        self.notifications_queue.append({
            "type": "WEATHER",
            "text": f"{weather.emoji()} Clima da corrida: {rotulo}!"
            + (f" Favorece {', '.join(nomes)}!" if nomes else ""),
            "horse_id": None,
            "badge": weather.emoji(),
        })

    def _favoritos_do_clima(self) -> List[str]:
        """Os cavalos que o clima atual favorece, pelo NOME (é o que se fala)."""
        return [
            next((h.name for h in self.config.horses if h.personality == p), p)
            for p in self.engine.weather_system.favoritos()
        ]

    def _anunciar_votacao_aberta(self) -> None:
        self._sortear_clima_da_corrida()
        logger.info(
            f"🗳️ Corrida #{self.race_number} — votação aberta por "
            f"{self.config.voting_duration_seconds:.0f}s! Comenta 1-8 pra escolher teu cavalo."
        )
        if self.narrador is not None:
            self.narrador.anunciar_votacao(self.race_number)
        # Daqui a CHAMADA_VOTACAO_INTERVALO sai o primeiro LEMBRETE de voto
        # (o relógio do estado acabou de zerar nos três pontos que chamam
        # este método: criação, reset e virada do ranking).
        self._proxima_chamada_votacao = self.state_timer + CHAMADA_VOTACAO_INTERVALO

    def _resumo_votos(self) -> str:
        """Linha única e agregada: nada de logar voto por voto (viraria spam em live cheia)."""
        votos = sum(len(s) for s in self.horse_supporters.values())
        if not votos:
            return "nenhum voto"
        hid, sups = max(self.horse_supporters.items(), key=lambda kv: len(kv[1]))
        return f"{votos} voto(s), favorito #{hid} {self._nome_cavalo(hid)} ({len(sups)})"

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
        """O número do cavalo digitado no chat.

        Na votação é o VOTO (vale XP e entra no banco); com a corrida
        ROLANDO é torcida — um empurrãozinho leve no cavalo citado, sem
        tocar em voto nem em banco (ver `_empurrao_da_torcida`). Fora
        desses dois momentos o comentário chegou tarde: é ignorado.
        """
        if horse_id not in [h.id for h in self.config.horses]:
            return False

        if self.state == DirectorState.RACING:
            self._empurrao_da_torcida(tiktok_username, display_name, horse_id)
            return True

        if self.state != DirectorState.VOTING:
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

    def _empurrao_da_torcida(self, tiktok_username: str, display_name: str, horse_id: int) -> None:
        """O empurrãozinho de quem digita o número com a corrida rolando.

        Leve e curto por escolha: é para o público SENTIR que o comentário
        mexeu na prova, não para decidir a corrida — quem quer decidir manda
        presente. Não grava nada (torcida não rende XP) e não fala na voz:
        a fila do narrador é uma só e a locução da corrida manda nela.
        """
        nome = display_name or tiktok_username or "Torcida"
        h_name = self._nome_cavalo(horse_id)
        self.engine.apply_boost(
            horse_id=horse_id,
            boost_name="TORCIDA NO CHAT",
            power=TORCIDA_POWER,
            duration_seconds=TORCIDA_DURATION_SECONDS,
            is_legendary=False,
            legendary_kind=None,
            gift_emoji="💬",
            donor_name=nome
        )
        self.notifications_queue.append({
            "type": "CHEER",
            "text": f"{nome} torce pelo {h_name}!",
            "horse_id": horse_id,
            "horse_name": h_name,
            "badge": "💬"
        })
        logger.info(f"💬 {nome} torceu pelo #{horse_id} {h_name} ({TORCIDA_POWER:.2f}x)")

    async def handle_viewer_gift(
        self,
        tiktok_username: str,
        display_name: str,
        gift_name: str,
        gift_count: int = 1
    ) -> None:
        viewer = await self.repository.get_or_create_viewer(tiktok_username, display_name)
        self.viewers_cache[viewer["tiktok_username"]] = viewer
        
        # Determina cavalo do espectador (ou um SORTEADO se não escolheu)
        chosen_horse_id = None
        for hid, sups in self.horse_supporters.items():
            if any(s["tiktok_username"] == viewer["tiktok_username"] for s in sups):
                chosen_horse_id = hid
                break

        if not chosen_horse_id:
            # Sem voto do espectador, o presente vai pra um cavalo SORTEADO.
            # "Pro líder" parecia justo, mas na votação o líder é SEMPRE o
            # #1 (a engine o inicializa assim): uma live de galera sem voto
            # empilhava tudo no #1 e o #1 vencia sempre.
            chosen_horse_id = random.choice(self.config.horses).id
            
        h_name = next(h.name for h in self.config.horses if h.id == chosen_horse_id)
        
        # Determina o tier do presente (tabela no topo do módulo)
        gift_lower = gift_name.lower()
        tier = GIFT_DEFAULT
        for t in GIFT_TIERS:
            if any(k in gift_lower for k in t["keywords"]):
                tier = t
                break

        xp_map = {
            "small": self.config.xp.gift_small,
            "medium": self.config.xp.gift_medium,
            "large": self.config.xp.gift_large,
        }
        xp = tier["xp"] if isinstance(tier["xp"], int) else xp_map[tier["xp"]]
        b_label = tier["label"]
        gift_emoji = tier["emoji"]
        is_legendary = tier["legendary"] is not None
        legendary_kind = tier["legendary"]

        # Quantidade amplia o bônus: cada unidade extra soma 10% do delta do tier
        # (teto de 5 extras). Ex.: 10 rosas (1.30) > 1 rosa (1.20) < 1 galáxia (1.60).
        extras = min(max(gift_count - 1, 0), GIFT_COUNT_MAX_EXTRA)
        power = min(GIFT_POWER_CAP, 1.0 + (tier["power"] - 1.0) * (1.0 + GIFT_COUNT_STEP * extras))
        dur = tier["duration"]
            
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
        
        logger.info(
            f"🎁 @{viewer['display_name']} enviou {gift_name} x{gift_count} → #{chosen_horse_id} {h_name} "
            f"({b_label} {power:.2f}x por {dur:.0f}s, +{xp * gift_count} XP)"
        )
        if self.narrador is not None:
            self.narrador.anunciar_presente(
                viewer["display_name"], gift_count, gift_name, h_name
            )

        self.notifications_queue.append({
            "type": "GIFT",
            "is_legendary": is_legendary,
            "legendary_kind": legendary_kind,
            "sender_name": viewer['display_name'],
            "gift_name": gift_name,
            "gift_emoji": gift_emoji,
            "boost_label": b_label,
            "text": f"{gift_emoji} {viewer['display_name']} enviou {gift_name}{f' x{gift_count}' if gift_count > 1 else ''}! {b_label} em {h_name}!",
            "horse_id": chosen_horse_id,
            "horse_name": h_name,
            "badge": gift_emoji
        })

    async def handle_viewer_join(self, tiktok_username: str, display_name: str) -> None:
        """Quem chegou ganha um oi da voz (se o narrador estiver ligado).

        Não grava nada no banco: entrada é presença, não voto — criar linha
        de viewer para cada chegada encheria o ranking de gente sem XP.
        """
        if self.narrador is not None:
            self.narrador.anunciar_entrada(display_name or tiktok_username)

    async def handle_cheer_command(self, tiktok_username: str, display_name: str) -> None:
        viewer = await self.repository.get_or_create_viewer(tiktok_username, display_name)
        chosen_horse_id = None
        for hid, sups in self.horse_supporters.items():
            if any(s["tiktok_username"] == viewer["tiktok_username"] for s in sups):
                chosen_horse_id = hid
                break
        if chosen_horse_id:
            self.engine.add_cheer(chosen_horse_id)

    async def handle_viewer_like(self, tiktok_username: str, display_name: str, count: int) -> None:
        """Rajada de curtidas (>= LIKE_BURST_MIN de uma vez) dá um empurrão leve.

        Bem leve de propósito: curtida é gratuita e infinita, então só empurra
        o cavalo do apoiador — ou um SORTEADO, quando o autor não é
        identificável (o TikTok para de mandar o autor depois de muitas
        curtidas seguidas; o fallback velho, "o líder", empilhava tudo no
        mesmo cavalo). Não grava nada no banco: curtida não rende XP.
        """
        if count < LIKE_BURST_MIN:
            return

        chosen_horse_id = None
        if tiktok_username:
            for hid, sups in self.horse_supporters.items():
                if any(s["tiktok_username"] == tiktok_username for s in sups):
                    chosen_horse_id = hid
                    break
        if chosen_horse_id is None:
            chosen_horse_id = random.choice(self.config.horses).id

        power = min(LIKE_POWER_MAX, LIKE_POWER_BASE + 0.002 * min(count - LIKE_BURST_MIN, 10))
        self.engine.apply_boost(
            horse_id=chosen_horse_id,
            boost_name="GALERA CURTIU",
            power=power,
            duration_seconds=LIKE_DURATION_SECONDS,
            is_legendary=False,
            legendary_kind=None,
            gift_emoji="❤️",
            donor_name=display_name or "Torcida"
        )
        logger.info(
            f"❤️ Rajada de {count} curtidas de {display_name or 'anônimo'} → "
            f"empurrão no #{chosen_horse_id} {self._nome_cavalo(chosen_horse_id)} ({power:.2f}x)"
        )

    async def skip_to_countdown(self) -> None:
        """Pula o tempo de votação e inicia a contagem de largada imediatamente."""
        logger.info(
            f"⏩ Votação pulada pelo painel — {self._resumo_votos()}. "
            f"Largada em {self.config.countdown_duration_seconds:.0f}s!"
        )
        self.state = DirectorState.COUNTDOWN
        self.state_timer = 0.0

    async def force_finish_race(self) -> None:
        """Força a finalização da corrida e avança para o pódio."""
        if self.state == DirectorState.RACING:
            logger.info("⏭️ Corrida finalizada manualmente pelo painel.")
            # Força avanço dos cavalos para cruzar a linha
            for h in self.engine.horses:
                if not h.finished:
                    h.distance = self.engine.track_length
                    h.finished = True
                    h.finish_time_ms = self.engine.race_elapsed_ms or 34000
            self.engine.status = "FINISHED"
            self.state = DirectorState.PODIUM
            self.state_timer = 0.0
            # A prova acabou por decisão do painel: a locução que sobrou na
            # fila era passado, e o tempo não vira mais nesta corrida.
            self._virada_clima_em = None
            self._descartar_locucao()
            snapshot = self.engine.get_snapshot()
            self.podium_data = snapshot.get("final_results", [])[:3]

    def _descartar_locucao(self) -> None:
        """Manda a voz jogar fora a locução da prova já decidida.

        A chamada é guardada: sem narrador (jogo mudo) não há fila.
        """
        if self.narrador is None:
            return
        descartadas = self.narrador.descartar_locucao()
        if descartadas:
            logger.info(
                f"🔇 Locução descartada: {descartadas} fala(s) de uma prova "
                f"já decidida não vão mais ao ar."
            )

    def _locucao_da_corrida(self) -> None:
        """As chamadas ao vivo da corrida, por MARCO de distância do líder.

        A corrida era o único trecho silencioso da transmissão: saía a
        largada e depois só o vencedor, ~35s de vazio. Aqui a voz acompanha
        a prova — quem puxa e quem vem na cola, na abertura, no meio e na
        reta final. Cada marco fala uma vez por corrida; quem decide a HORA
        é este método, o TEXTO é do narrador.
        """
        if self.narrador is None:
            return
        ordenados = sorted(self.engine.horses, key=lambda h: h.distance, reverse=True)
        if len(ordenados) < 2:
            return
        lider = ordenados[0]
        if lider.finished:
            # Já cruzou: a fila é do vencedor agora. O que ainda estava na
            # fila era passado — prova decidida não se narra — e sai UMA vez
            # (o pós-corrida cuida do que ainda chegar).
            if not self._locucao_encerrada:
                self._locucao_encerrada = True
                self._descartar_locucao()
            return
        segundo = ordenados[1]
        terceiro = ordenados[2] if len(ordenados) > 2 else segundo
        for marco, tipo in MARCOS_LOCUCAO:
            # A chave é o PAR (tipo, marco): "placar" aparece três vezes na
            # tabela e cada um fala uma vez, no seu próprio marco.
            chave = f"{tipo}@{marco}"
            if chave in self._marcos_falados or lider.distance < marco:
                continue
            self._marcos_falados.add(chave)
            if tipo == "abertura":
                self.narrador.anunciar_abertura(lider.name, segundo.name)
            elif tipo == "disputa":
                self.narrador.anunciar_disputa(lider.name, segundo.name)
            elif tipo == "placar":
                self.narrador.anunciar_placar(
                    lider.name, segundo.name, terceiro.name
                )
            else:
                self.narrador.anunciar_reta_final(lider.name, segundo.name)

    def _sortear_hora_da_virada(self) -> Optional[float]:
        """A hora (distância do líder) da virada do tempo — ou None.

        Sorteada na largada: com CLIMA_VIRADA_CHANCE de chance, o tempo vira
        quando o líder alcançar um ponto entre 35% e 70% da pista. A virada
        é UMA por corrida: depois de acontecer (ou de a prova se decidir),
        a agenda morre.
        """
        if random.random() >= CLIMA_VIRADA_CHANCE:
            return None
        return random.uniform(*CLIMA_VIRADA_ENTRE) * self.engine.track_length

    def _talvez_virar_o_clima(self) -> None:
        """O tempo vira no meio da prova — se a corrida sorteou essa hora.

        A virada muda o clima NA HORA (efeito e visual, o scene.js anima a
        troca), com aviso da voz e do telão. Só dispara com a prova viva:
        prova decidida não tem mais "meio de corrida".
        """
        if self._virada_clima_em is None:
            return
        lider = max(self.engine.horses, key=lambda h: h.distance)
        if lider.finished:
            self._virada_clima_em = None
            return
        if lider.distance < self._virada_clima_em:
            return

        self._virada_clima_em = None
        weather = self.engine.weather_system
        weather.pick_random_weather()
        rotulo = weather.rotulo()
        nomes = self._favoritos_do_clima()
        logger.info(f"🌦️ O tempo virou na corrida #{self.race_number}: {rotulo}.")
        if self.narrador is not None:
            self.narrador.anunciar_virada_do_clima(rotulo, nomes)
        self.notifications_queue.append({
            "type": "WEATHER_CHANGE",
            "text": f"{weather.emoji()} O tempo virou: {rotulo}!"
            + (f" Favorece {', '.join(nomes)}!" if nomes else ""),
            "horse_id": None,
            "badge": weather.emoji(),
        })

    def _foto_finish_apertada(self) -> bool:
        """A chegada foi decidida no detalhe (menos de MARGEM_FOTO_FINISH_MS)?

        A margem sai dos TEMPOS de chegada (não das distâncias): é a mesma
        medida que diz se a corrida foi um duelo de verdade — em ~1/3 delas
        é, e é aí que a exclamação da foto-finish entra.
        """
        if self.podium_data and len(self.podium_data) >= 2:
            return (
                self.podium_data[1]["finish_time_ms"] - self.podium_data[0]["finish_time_ms"]
            ) < MARGEM_FOTO_FINISH_MS
        finished = [h for h in self.engine.horses if h.finished]
        if len(finished) >= 2:
            finished.sort(key=lambda h: h.finish_time_ms)
            return (finished[1].finish_time_ms - finished[0].finish_time_ms) < MARGEM_FOTO_FINISH_MS
        return False

    async def reset_to_new_race(self) -> None:
        """Reinicia o ciclo imediatamente para uma nova corrida."""
        self.race_number += 1
        self.engine.reset()
        self.horse_supporters = {h.id: [] for h in self.config.horses}
        self.state = DirectorState.VOTING
        self.state_timer = 0.0
        self.last_race_rewards = []
        # O ciclo reiniciou (talvez no meio da prova): a locução da corrida
        # velha e a agenda de virada do tempo morrem aqui, ANTES de abrir a
        # votação nova (as falas de agora não podem ser descartadas junto).
        self._virada_clima_em = None
        self._locucao_encerrada = False
        self._vitoria_anunciada = False
        self._descartar_locucao()
        self._anunciar_votacao_aberta()

    async def tick(self, dt: float) -> None:
        self.state_timer += dt
        
        if self.state == DirectorState.VOTING:
            # Lembrete de voto: a votação é a fase em que o público precisa
            # de chamada — uma abertura e 30s de silêncio não puxam ninguém.
            if (
                self.state_timer >= self._proxima_chamada_votacao
                and self.narrador is not None
            ):
                self._proxima_chamada_votacao = (
                    self.state_timer + CHAMADA_VOTACAO_INTERVALO
                )
                self.narrador.anunciar_votacao(self.race_number)
            if self.state_timer >= self.config.voting_duration_seconds:
                # Transiciona para COUNTDOWN
                logger.info(
                    f"⏳ Votação encerrada — {self._resumo_votos()}. "
                    f"Largada em {self.config.countdown_duration_seconds:.0f}s!"
                )
                self.state = DirectorState.COUNTDOWN
                self.state_timer = 0.0

        elif self.state == DirectorState.COUNTDOWN:
            if self.state_timer >= self.config.countdown_duration_seconds:
                # Inicia corrida real
                self.state = DirectorState.RACING
                self.state_timer = 0.0
                self._marcos_falados = set()
                self._locucao_encerrada = False
                self._vitoria_anunciada = False
                self._virada_clima_em = self._sortear_hora_da_virada()
                self.engine.start_race()
                logger.info(
                    f"🏁 CORRIDA #{self.race_number} COMEÇOU! "
                    f"Clima: {self.engine.weather_system.current_weather.value}"
                )
                if self.narrador is not None:
                    self.narrador.anunciar_largada(self.race_number)
                
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
            self._locucao_da_corrida()
            self._talvez_virar_o_clima()

            # CHEGADA IMEDIATA: assim que o 1º cruzar a linha, anuncia na hora sem esperar os 3.5s!
            if self.engine.winner_horse_id and not self._vitoria_anunciada:
                self._vitoria_anunciada = True
                self._descartar_locucao()
                if self.narrador is not None:
                    self.narrador.interromper_locucao()
                    winner_id = self.engine.winner_horse_id
                    winner = next((h for h in self.engine.horses if h.id == winner_id), None)
                    if winner:
                        if self._foto_finish_apertada():
                            segundo = min(
                                (h for h in self.engine.horses if h.id != winner_id),
                                key=lambda h: h.finish_time_ms if h.finished else 999999,
                                default=None
                            )
                            if segundo:
                                self.narrador.anunciar_foto_finish(winner.name, segundo.name)
                        self.narrador.anunciar_vencedor(winner.number, winner.name)

            if self.engine.is_finished():
                self.state = DirectorState.PODIUM
                self.state_timer = 0.0
                snapshot = self.engine.get_snapshot()
                self.podium_data = snapshot.get("final_results", [])[:3]
                if self.podium_data:
                    top = self.podium_data[0]
                    resto = ", ".join(f"{p['final_position']}º #{p['horse_id']}" for p in self.podium_data[1:])
                    logger.info(
                        f"🏆 Corrida #{self.race_number}: venceu o #{top['horse_id']} {top['name']}!"
                        + (f" ({resto})" if resto else "")
                    )
                    # Fallback de segurança se não disparou no cruzamento
                    if not self._vitoria_anunciada:
                        self._vitoria_anunciada = True
                        self._descartar_locucao()
                        if self.narrador is not None:
                            self.narrador.interromper_locucao()
                            if self._foto_finish_apertada():
                                self.narrador.anunciar_foto_finish(
                                    top["name"], self.podium_data[1]["name"]
                                )
                            self.narrador.anunciar_vencedor(top["horse_id"], top["name"])

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
                    subiram = [r["display_name"] for r in self.last_race_rewards if r.get("level_up")]
                    logger.info(
                        f"⭐ XP distribuído para {len(self.last_race_rewards)} torcedor(es)"
                        + (f" — subiram de nível: {', '.join(subiram)}" if subiram else "")
                    )

        elif self.state == DirectorState.XP_REWARDS:
            if self.state_timer >= self.config.xp_duration_seconds:
                self.state = DirectorState.LEADERBOARD
                self.state_timer = 0.0
                self.leaderboard_data = await self.repository.get_leaderboard(limit=10)
                if self.leaderboard_data:
                    lider = self.leaderboard_data[0]
                    logger.info(f"🏅 Ranking: {lider['display_name']} lidera com {lider['xp']} XP.")
                
        elif self.state == DirectorState.LEADERBOARD:
            if self.state_timer >= self.config.leaderboard_duration_seconds:
                # Reinicia novo ciclo (o clima novo é sorteado lá dentro,
                # por `_anunciar_votacao_aberta` — um lugar só para isso).
                self.race_number += 1
                self.engine.reset()
                self.horse_supporters = {h.id: [] for h in self.config.horses}
                self.state = DirectorState.VOTING
                self.state_timer = 0.0
                self.last_race_rewards = []
                self._anunciar_votacao_aberta()

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
