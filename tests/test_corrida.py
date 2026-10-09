"""Provas da matemática da corrida: pódio honesto e corrida imprevisível.

Histórico dos bugs que estes testes travam:
1. O pódio exibido colocava cavalo que NÃO cruzou a linha na frente de quem
   cruzou (chave de ordenação invertida no engine) — e os pontos de top-3 iam
   para os cavalos errados.
2. A corrida era praticamente decidida antes da largada: personalidades com
   média de velocidade diferente de 1.0 + folga de stamina irrelevante faziam
   o mesmo cavalo vencer ~85% das corridas limpas.
"""
import random

from config.settings import load_config
from game.engine import RaceEngine
from game.horses import HorseState
from game.weather_events import WeatherType

SEED = 20261008


def test_podio_nao_coloca_quem_nao_terminou_na_frente():
    """Quem não cruzou a linha jamais pode subir ao pódio na frente de quem cruzou."""
    random.seed(7)
    config = load_config()
    config.track_length_meters = 30.0       # pista curtinha: teste rápido
    config.horses[7].base_speed = 2.0       # FANTASMA fica para trás e não termina
    config.horses[7].luck = 0.0             # sem arrancadas de sorte

    engine = RaceEngine(config)
    engine.reset()
    engine.start_race()

    dt = 1.0 / 60.0
    for _ in range(1200):
        engine.update(dt)
        if engine.is_finished():
            break
    assert engine.is_finished()

    resultados = engine.final_results
    assert len(resultados) == 8

    # O pódio é dos que cruzaram a linha...
    for posicao in resultados[:3]:
        cavalo = next(h for h in engine.horses if h.id == posicao["horse_id"])
        assert cavalo.finished, f"{posicao['name']} subiu ao pódio sem cruzar a linha!"

    # ...e quem não terminou só aparece DEPOIS de todos os que terminaram...
    terminados = [
        r for r in resultados
        if next(h for h in engine.horses if h.id == r["horse_id"]).finished
    ]
    nao_terminados = [r for r in resultados if r not in terminados]
    primeiro_nao_terminado = resultados.index(nao_terminados[0]) if nao_terminados else len(resultados)
    assert all(resultados.index(r) < primeiro_nao_terminado for r in terminados)

    # ...e a ordem entre os que terminaram é a ordem de chegada.
    tempos = [r["finish_time_ms"] for r in terminados]
    assert tempos == sorted(tempos)


def test_tempo_de_chegada_usa_fracao_do_tick():
    """Foto-finish de verdade: cruzar no meio do tick devolve o instante exato, não o fim do tick."""
    random.seed(3)
    config = load_config()
    h = HorseState(config.horses[0], lane=1)
    h.distance = 999.9
    h.speed = 30.0

    dt = 1.0 / 60.0
    h.update_physics(
        dt=dt, track_length=1000.0, current_rank=1,
        weather_mult=1.0, race_elapsed_ms=100000,
    )
    assert h.finished

    # O passo real do tick sai da velocidade já interpolada pelo update.
    passo = h.speed * dt
    frac = 0.1 / passo
    esperado = 100000 - (1.0 - frac) * dt * 1000.0
    assert abs(h.finish_time_ms - esperado) < 0.05
    assert h.finish_time_ms < 100000  # chegou ANTES do fim do tick


def test_cada_corrida_tem_o_dia_do_cavalo():
    """A 'forma' de cada cavalo é sorteada de novo a cada corrida (ninguém vence sempre)."""
    random.seed(99)
    config = load_config()
    engine = RaceEngine(config)

    formas = []
    for _ in range(6):
        engine.reset()
        formas.append(tuple(round(h.form, 6) for h in engine.horses))
    assert len(set(formas)) > 1, "a forma não está variando entre corridas"


def test_sorte_alta_rende_arrancadas_surpresa():
    """FANTASMA (sorte 10) dá arrancadas; TITÃ (sorte 5.2) quase nunca."""
    random.seed(11)
    config = load_config()
    fantasma = HorseState(config.horses[7], lane=8)
    tita = HorseState(config.horses[5], lane=6)

    dt = 1.0 / 60.0
    for _ in range(600):  # 10 segundos de corrida
        fantasma.update_physics(dt=dt, track_length=1000.0, current_rank=4, weather_mult=1.0, race_elapsed_ms=0)
        tita.update_physics(dt=dt, track_length=1000.0, current_rank=4, weather_mult=1.0, race_elapsed_ms=0)

    assert fantasma.surge_count > tita.surge_count, "o cavalo da sorte não recebeu mais arrancadas"


def test_nenhum_cavalo_domina_a_corrida():
    """Em 100 corridas com clima variado, TODOS os 8 vencem e ninguém passa de 1/3."""
    random.seed(SEED)
    config = load_config()
    engine = RaceEngine(config)

    corridas = 100
    vitorias = {h.id: 0 for h in engine.horses}
    dt = 1.0 / 60.0
    for _ in range(corridas):
        engine.reset()
        engine.weather_system.pick_random_weather()
        engine.start_race()
        for _ in range(4000):
            engine.update(dt)
            if engine.is_finished():
                break
        assert engine.is_finished(), "corrida não terminou dentro do limite de ticks"
        vitorias[engine.winner_horse_id] += 1

    nunca = [hid for hid, n in vitorias.items() if n == 0]
    assert not nunca, f"cavalos que nunca venceram em {corridas} corridas: {nunca}"
    campeao, maior = max(vitorias.items(), key=lambda kv: kv[1])
    assert maior <= corridas // 3, f"#{campeao} venceu {maior}/{corridas} — dominou demais"


def test_chuva_ajuda_mas_nao_entrega_a_corrida():
    """Na chuva a NEVASCA é favorita, mas não pode vencer TODA vez."""
    random.seed(SEED + 1)
    config = load_config()
    engine = RaceEngine(config)

    corridas = 36
    vitorias = {}
    dt = 1.0 / 30.0
    for _ in range(corridas):
        engine.reset()
        engine.set_weather(WeatherType.RAIN)
        engine.start_race()
        for _ in range(2500):
            engine.update(dt)
            if engine.is_finished():
                break
        vitorias[engine.winner_horse_id] = vitorias.get(engine.winner_horse_id, 0) + 1

    nevasca = vitorias.get(7, 0)
    assert nevasca <= corridas // 2, f"NEVASCA venceu {nevasca}/{corridas} na chuva — chuva virou roleta"
    assert len(vitorias) >= 3, f"na chuva só {len(vitorias)} cavalos venceram — clima decidiu sozinho"
