"""O clima da corrida: sorteio com variedade, intensidade valendo e o tempo
virando no meio da prova.

O clima era um enfeite caro: sorteado a cada corrida (e podendo repetir),
com uma intensidade sorteada que NINGUÉM usava — chuva fraca e tempestade
forte davam exatamente o mesmo efeito. Estes testes travam o que o clima
virou: troca de verdade entre corridas, efeito proporcional à intensidade,
anúncio no ar e virada ao vivo com a prova rolando.
"""
import pytest

from config.settings import load_config
from fakes import FakeNarrador


def _narrador(**cfg):
    """Narrador de teste: nada de edge-tts nem MCI de verdade."""
    from config.settings import TtsConfig
    from game.narrador import Narrador

    return Narrador(TtsConfig(**cfg), gerar=lambda texto: "x.mp3", tocar=lambda c: None)


# ---------------------------------------------------------------------------
# O sorteio
# ---------------------------------------------------------------------------

def test_sorteio_troca_de_verdade():
    """Clima novo nunca é o mesmo da corrida anterior.

    A primeira corrida pode até nascer em céu limpo (é o clima de casa), mas
    da segunda em diante o clima atual sai da urna — antes, repetir era
    sorteado e a live emendava corridas iguais.
    """
    from game.weather_events import WeatherSystem

    sistema = WeatherSystem()
    anterior = sistema.pick_random_weather()
    assert anterior == sistema.current_weather

    for _ in range(30):
        novo = sistema.pick_random_weather()
        assert novo != anterior, "o clima repetiu a corrida anterior"
        assert novo == sistema.current_weather
        anterior = novo


# ---------------------------------------------------------------------------
# A intensidade
# ---------------------------------------------------------------------------

def test_intensidade_escala_o_efeito_do_clima():
    """A intensidade sorteada (0.4–0.8) pesa no efeito do clima.

    Em 0.5 — o neutro de `set_weather` — o efeito é o de sempre (nada que
    já funcionava muda); mais forte, mais swing: maior para o dono do clima,
    menor para o resto do páreo.
    """
    from game.weather_events import WeatherSystem, WeatherType

    sistema = WeatherSystem()

    def mult(personalidade, intensidade):
        sistema.set_weather(WeatherType.RAIN, intensity=intensidade)
        return sistema.get_weather_multiplier(personalidade)

    # Moderada = comportamento antigo, de propósito.
    assert mult("COLD_TACTICIAN", 0.5) == pytest.approx(1.012)
    assert mult("PACER", 0.5) == pytest.approx(0.993)

    assert mult("COLD_TACTICIAN", 0.8) > mult("COLD_TACTICIAN", 0.4) > 1.0
    assert mult("PACER", 0.8) < mult("PACER", 0.4) < 1.0


def test_rotulo_conta_a_intensidade():
    """O rótulo é o que o locutor fala: clima e força num nome só."""
    from game.weather_events import WeatherSystem, WeatherType

    sistema = WeatherSystem()
    sistema.set_weather(WeatherType.RAIN, intensity=0.8)
    assert sistema.rotulo() == "chuva forte"
    sistema.set_weather(WeatherType.RAIN, intensity=0.5)
    assert sistema.rotulo() == "chuva moderada"
    sistema.set_weather(WeatherType.WIND, intensity=0.4)
    assert sistema.rotulo() == "vento fraco"  # vento é masculino
    sistema.set_weather(WeatherType.CLEAR)
    assert sistema.rotulo() == "céu limpo"  # sem intensidade na frase


def test_favoritos_do_clima():
    """Quem o clima favorece — é o que o anúncio promete ao público."""
    from game.weather_events import WeatherSystem, WeatherType

    sistema = WeatherSystem()
    sistema.set_weather(WeatherType.RAIN)
    assert set(sistema.favoritos()) == {"COLD_TACTICIAN", "JUGGERNAUT"}
    sistema.set_weather(WeatherType.WIND)
    assert set(sistema.favoritos()) == {"DRAFTER", "COLD_TACTICIAN"}
    sistema.set_weather(WeatherType.CLEAR)
    assert sistema.favoritos() == []


# ---------------------------------------------------------------------------
# A voz do clima
# ---------------------------------------------------------------------------

def test_texto_do_clima_cita_quem_se_da_bem():
    n = _narrador(clima=["Tempo de {clima} na pista!{quem}"])
    assert (
        n.texto_do_clima("chuva forte", ["NEVASCA", "TITÃ"])
        == "Tempo de chuva forte na pista! Quem se dá bem nisso: Nevasca e Titã!"
    )


def test_texto_do_clima_sem_favoritos_nao_deixa_buraco():
    """Céu limpo não favorece ninguém: a frase sai inteira, sem sobra."""
    n = _narrador(clima=["Tempo de {clima} na pista!{quem}"])
    assert n.texto_do_clima("céu limpo", []) == "Tempo de céu limpo na pista!"


def test_texto_da_virada_do_clima():
    n = _narrador(clima_virada=["Olha o tempo virando! Agora é {clima}!{quem}"])
    assert (
        n.texto_da_virada_do_clima("vento forte", ["RAIO"])
        == "Olha o tempo virando! Agora é vento forte! Quem se dá bem nisso: Raio!"
    )


def test_frases_do_clima_formatam_sem_erro():
    """Toda frase padrão aceita os placeholders, com e sem favoritos."""
    from game.falas import CLIMA, CLIMA_VIRADA

    for frase in (*CLIMA, *CLIMA_VIRADA):
        assert "{" not in frase.format(clima="chuva forte", quem="")
        assert "{" not in frase.format(
            clima="chuva forte", quem=" Quem se dá bem nisso: Nevasca e Titã!"
        )


# ---------------------------------------------------------------------------
# A fiação no director
# ---------------------------------------------------------------------------

async def _director_pronto(tmp_path, nome, voz=None, track=120.0):
    from backend.database.repository import DatabaseRepository
    from game.director import EventDirector
    from game.engine import RaceEngine

    config = load_config()
    config.track_length_meters = track
    config.voting_duration_seconds = 0.2
    config.countdown_duration_seconds = 0.1
    # Só o TIMEOUT da corrida: frouxo de propósito — quem termina a prova é a
    # distância, não o relógio (a virada do clima é testada bem no meio dela).
    config.race_duration_seconds = 60.0
    config.podium_duration_seconds = 0.1
    config.xp_duration_seconds = 0.1
    config.leaderboard_duration_seconds = 0.1

    repo = DatabaseRepository(db_path=str(tmp_path / nome))
    await repo.init_db()
    director = EventDirector(
        config=config, engine=RaceEngine(config), repository=repo, narrador=voz
    )
    return config, director


@pytest.mark.asyncio
async def test_abertura_anuncia_o_clima_da_corrida(tmp_path):
    """A votação abre com o clima no ar: voz falando e telão avisando."""
    voz = FakeNarrador()
    config, director = await _director_pronto(tmp_path, "clima.db", voz)

    anuncios = [c for c in voz.chamadas if c[0] == "clima"]
    assert len(anuncios) == 1, "o clima da corrida não foi anunciado na abertura"

    rotulo, favoritos = anuncios[0][1], anuncios[0][2]
    assert rotulo == director.engine.weather_system.rotulo()

    # Os favoritos chegam à voz como NOME de cavalo (é o que se fala).
    esperados = [
        next(h.name for h in config.horses if h.personality == p)
        for p in director.engine.weather_system.favoritos()
    ]
    assert favoritos == esperados

    assert any(n["type"] == "WEATHER" for n in director.notifications_queue)


@pytest.mark.asyncio
async def test_cada_corrida_troca_o_clima_e_anuncia(tmp_path):
    """Ciclo completo: corrida nova = clima novo, avisado de novo."""
    import random
    random.seed(42)
    from game.director import DirectorState

    voz = FakeNarrador()
    _, director = await _director_pronto(tmp_path, "ciclo.db", voz)

    clima_1 = director.engine.weather_system.current_weather
    assert len([c for c in voz.chamadas if c[0] == "clima"]) == 1

    for _ in range(400):
        await director.tick(0.1)
        if director.state == DirectorState.VOTING and director.race_number == 2:
            break

    assert director.race_number == 2
    assert director.engine.weather_system.current_weather != clima_1
    assert len([c for c in voz.chamadas if c[0] == "clima"]) == 2


@pytest.mark.asyncio
async def test_tempo_vira_no_meio_da_prova(tmp_path):
    """O clima pode virar com a corrida rolando: voz avisa e o telão acende."""
    voz = FakeNarrador()
    _, director = await _director_pronto(tmp_path, "virada.db", voz, track=1000.0)

    await director.tick(0.25)  # VOTING -> COUNTDOWN
    await director.tick(0.15)  # COUNTDOWN -> RACING
    antes = director.engine.weather_system.current_weather

    # Na live a hora é sorteada na largada; aqui, agendada na mão — 400m do
    # líder é o meio da prova de 1000m.
    director._virada_clima_em = 400.0
    for _ in range(60):
        await director.tick(1.0)
        if director.engine.weather_system.current_weather != antes:
            break

    assert director.engine.weather_system.current_weather != antes
    assert director._virada_clima_em is None, "a virada pode acontecer só uma vez"

    viradas = [c for c in voz.chamadas if c[0] == "virada_clima"]
    assert len(viradas) == 1
    assert viradas[0][1] == director.engine.weather_system.rotulo()
    assert any(n["type"] == "WEATHER_CHANGE" for n in director.notifications_queue)


@pytest.mark.asyncio
async def test_a_virada_do_tempo_e_sorteada_na_largada(tmp_path, monkeypatch):
    """A chance é sorteada na largada: dado a favor, a prova guarda o horário
    de virar; dado fora da chance, a prova fica com o tempo estável."""
    from game.director import DirectorState

    monkeypatch.setattr("game.director.random.random", lambda: 0.0)
    _, director = await _director_pronto(tmp_path, "sorte1.db")
    await director.tick(0.25)
    await director.tick(0.15)
    assert director.state == DirectorState.RACING
    assert director._virada_clima_em is not None
    assert 0.0 < director._virada_clima_em < 120.0  # dentro da pista do teste

    monkeypatch.setattr("game.director.random.random", lambda: 0.99)
    _, director = await _director_pronto(tmp_path, "sorte2.db")
    await director.tick(0.25)
    await director.tick(0.15)
    assert director.state == DirectorState.RACING
    assert director._virada_clima_em is None
