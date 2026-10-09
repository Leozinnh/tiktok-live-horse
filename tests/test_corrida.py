"""Provas da matemática da corrida: pódio honesto e corrida imprevisível.

Histórico dos bugs que estes testes travam:
1. O pódio exibido colocava cavalo que NÃO cruzou a linha na frente de quem
   cruzou (chave de ordenação invertida no engine) — e os pontos de top-3 iam
   para os cavalos errados.
2. A corrida era praticamente decidida antes da largada: personalidades com
   média de velocidade diferente de 1.0 + folga de stamina irrelevante faziam
   o mesmo cavalo vencer ~85% das corridas limpas.
3. A "conta de neutralidade" das personalidades era feita somando os fatores
   (0.99 tratado como ≈1.00). No relógio a conta é outra — Σ distância/fator —
   e o erro dava ao RELÂMPAGO +0.77% de velocidade fixa, de graça, para
   sempre. Personalidade é QUANDO cada um é forte, nunca vantagem fixa.
"""
import math
import random

import pytest

from config.settings import load_config
from game.engine import RaceEngine
from game.horses import HorseState
from game.weather_events import WeatherType

SEED = 20261008


def test_pista_3x_e_um_oval_uniforme_de_3000m():
    """A pista da live é um oval de 3000m: retas de 900m, curvas de 600m
    (raio ~190,99m) — 3x o oval original, mesma forma.

    Estas medidas são contrato: o front-end 3D desenha o MESMO traçado em
    metros (consome x/z do servidor 1:1), então se a física encolher ou
    crescer sozinha o cavalo aparece correndo fora da cerca.
    """
    from game.physics import TrackGeometry

    pista = TrackGeometry(3000.0)
    assert pista.straight_len == 900.0
    assert pista.curve_len == 600.0
    assert pista.radius == pytest.approx(600.0 / math.pi)  # ~190,99m
    assert 2 * pista.straight_len + 2 * pista.curve_len == 3000.0, \
        "o perímetro do oval tem que fechar 1 volta da pista"
    assert pista.base_lane_r == pytest.approx(pista.radius - 11.2)  # ~179,79m

    # Pontos-âncora do traçado (raia 1, a interna)
    raio_raia1 = pista.base_lane_r
    x, _, z, _ = pista.get_coordinates(0.0, 1)  # largada/chegada, reta principal
    assert (x, z) == (pytest.approx(-450.0), pytest.approx(raio_raia1))
    x, _, z, _ = pista.get_coordinates(1200.0, 1)  # ápice da curva 1
    assert (x, z) == (pytest.approx(450.0 + raio_raia1), pytest.approx(0.0, abs=1e-6))
    x, _, z, _ = pista.get_coordinates(2400.0, 1)  # entrada da reta final
    assert (x, z) == (pytest.approx(-450.0), pytest.approx(-raio_raia1))

    # Largura e raias continuam as de sempre — o que cresceu foi o traçado
    assert pista.lane_width == 3.2
    assert pista.get_coordinates(0.0, 8)[2] == pytest.approx(raio_raia1 + 7 * 3.2)


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
    h.distance = 2999.9
    h.speed = 30.0

    dt = 1.0 / 60.0
    h.update_physics(
        dt=dt, track_length=3000.0, current_rank=1,
        weather_mult=1.0, race_elapsed_ms=110000,
    )
    assert h.finished

    # O passo real do tick sai da velocidade já interpolada pelo update.
    passo = h.speed * dt
    frac = 0.1 / passo
    esperado = 110000 - (1.0 - frac) * dt * 1000.0
    assert abs(h.finish_time_ms - esperado) < 0.05
    assert h.finish_time_ms < 110000  # chegou ANTES do fim do tick


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


def test_personalidade_decide_quando_vence_nao_se_vence():
    """O contrato das personalidades: no relógio, todas empatam em 1.00.

    Quem decide corrida é o TEMPO (tempo = distância / velocidade), então a
    conta de neutralidade é Σ (fração da pista / fator) = 1.00 — média
    harmônica, não a soma dos fatores. Os comentários juravam que essa conta
    dava 1.00, mas estava errada em até +0.77% (RELÂMPAGO): velocidade de
    graça, a corrida inteira, disfarçada de personalidade.
    """
    config = load_config()
    fatias = 200
    for hc in config.horses:
        h = HorseState(hc)
        soma = 0.0
        for i in range(fatias):
            progresso = (i + 0.5) / fatias
            if hc.personality == "DRAFTER":
                # O vácuo do RAIO depende da posição no páreo: o contrato
                # assume a fatia de liderança anotada em horses.py (22% do
                # trajeto na frente; 78% caçando).
                soma += (
                    0.78 / h.calculate_personality_factor(progresso, 2)
                    + 0.22 / h.calculate_personality_factor(progresso, 1)
                )
            else:
                soma += 1.0 / h.calculate_personality_factor(progresso, 2)
        media = soma / fatias
        vantagem = (1.0 / media - 1.0) * 100.0
        assert media == pytest.approx(1.0, abs=0.001), (
            f"{hc.name} ({hc.personality}): média harmônica {media:.4f} — "
            f"vantagem fixa de {vantagem:+.2f}% em cima de todos os outros"
        )


def test_sorte_alta_rende_arrancadas_surpresa():
    """FANTASMA (sorte 10) dá arrancadas; TITÃ (sorte 5.2) quase nunca.

    A janela é de 100s (uma prova inteira de 3000m): a taxa de arrancada foi
    dividida por 3 junto com a estamina para o arco da corrida longa ficar
    igual ao da curta — em 10s de prova agora sai arrancada de menos para
    separar os dois com folga.
    """
    random.seed(11)
    config = load_config()
    fantasma = HorseState(config.horses[7], lane=8)
    tita = HorseState(config.horses[5], lane=6)

    dt = 1.0 / 60.0
    for _ in range(6000):  # 100 segundos de corrida
        fantasma.update_physics(dt=dt, track_length=3000.0, current_rank=4, weather_mult=1.0, race_elapsed_ms=0)
        tita.update_physics(dt=dt, track_length=3000.0, current_rank=4, weather_mult=1.0, race_elapsed_ms=0)

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
        for _ in range(8000):
            engine.update(dt)
            if engine.is_finished():
                break
        assert engine.is_finished(), "corrida não terminou dentro do limite de ticks"
        vitorias[engine.winner_horse_id] += 1

    nunca = [hid for hid, n in vitorias.items() if n == 0]
    assert not nunca, f"cavalos que nunca venceram em {corridas} corridas: {nunca}"
    campeao, maior = max(vitorias.items(), key=lambda kv: kv[1])
    assert maior <= corridas // 3, f"#{campeao} venceu {maior}/{corridas} — dominou demais"


def test_nenhum_cavalo_fica_para_tras():
    """A briga tem que ser de verdade: em 200 corridas, cada cavalo vence
    entre 6% e 21% — ninguém sobra nem fica escanteado.

    A faixa é o envelope de ~2 sigma em torno do medido na pista de 3000m
    (1000 corridas, tools/monte_carlo.py, seed 1234): RELÂMPAGO 10,7%,
    TROVÃO 13,3%, FURACÃO 15,3%, RAIO 12,0%, PANTERA 9,8%, TITÃ 16,9%,
    NEVASCA 11,4%, FANTASMA 10,6% — margem média 1º/2º de 488ms e 82,3%
    das chegadas em até 900ms. Com 200 corridas o sorteio oscila ~2 pontos
    para cada lado, então a faixa é mais larga que o placar real.
    Este teste é o mesmo sorteio da live: clima trocado a cada corrida.
    """
    random.seed(SEED + 2)
    config = load_config()
    engine = RaceEngine(config)

    corridas = 200
    minimo, maximo = int(corridas * 0.06), int(corridas * 0.21)
    vitorias = {h.id: 0 for h in engine.horses}
    nomes = {h.id: h.name for h in engine.horses}
    dt = 1.0 / 60.0
    for _ in range(corridas):
        engine.reset()
        engine.weather_system.pick_random_weather()
        engine.start_race()
        for _ in range(8000):
            engine.update(dt)
            if engine.is_finished():
                break
        vitorias[engine.winner_horse_id] += 1

    placar = [f"#{hid} {nomes[hid]} {n} ({100 * n / corridas:.1f}%)"
              for hid, n in sorted(vitorias.items())]
    fora = [linha for hid, linha in zip(sorted(vitorias), placar)
            if not minimo <= vitorias[hid] <= maximo]
    assert not fora, (
        f"cavalos fora da faixa {minimo}-{maximo} vitórias em {corridas} "
        f"corridas: {fora} | placar completo: {placar}"
    )


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
        for _ in range(5000):
            engine.update(dt)
            if engine.is_finished():
                break
        vitorias[engine.winner_horse_id] = vitorias.get(engine.winner_horse_id, 0) + 1

    nevasca = vitorias.get(7, 0)
    assert nevasca <= corridas // 2, f"NEVASCA venceu {nevasca}/{corridas} na chuva — chuva virou roleta"
    assert len(vitorias) >= 3, f"na chuva só {len(vitorias)} cavalos venceram — clima decidiu sozinho"


def test_torcida_leve_soma_velocidade_direta_com_teto():
    """Curtida e comentário somam VELOCIDADE DIRETA (m/s), não multiplicam.

    Bug que este teste trava: o empurrão de curtida era um boost multiplicativo
    de 1.04x. Rajadas de 15 curtidas chegando a cada ~2s no MESMO cavalo
    sobrepunham boosts de 3s e empilhavam 1.04 × 1.04 × … — o cavalo voava na
    pista. Agora o extra é somado em m/s e travado em TORCIDA_EXTRA_CAP (0.9).

    O espelho é exato de propósito: os dois cavalos recebem os MESMOS sorteios
    por tick (random.seed antes de cada update) e o NEVASCA tem fator de
    personalidade constante 1.00 — a única diferença entre eles é o boost.
    """
    from game.horses import TORCIDA_EXTRA_CAP

    config = load_config()
    hc = next(c for c in config.horses if c.personality == "COLD_TACTICIAN")
    dt = 1.0 / 60.0

    def corre_4s(extras):
        random.seed(99)
        h = HorseState(hc, lane=1)
        for extra in extras:
            h.add_boost("TORCIDA NO CHAT", extra, 60.0, additive=True)
        for i in range(240):
            random.seed(1000 + i)
            h.update_physics(dt, 3000.0, 1, 1.0, int(i * dt * 1000))
        return h.speed

    base = corre_4s([])

    # Três rajadas seguidas: 3 × 0.2 = +0.6 m/s, somadas direto na velocidade
    tres_rajadas = corre_4s([0.2, 0.2, 0.2])
    assert tres_rajadas - base == pytest.approx(0.6, abs=0.02)

    # Vinte rajadas (4.0 m/s de extra bruto): o teto segura em +0.9 m/s
    vinte_rajadas = corre_4s([0.2] * 20)
    assert vinte_rajadas - base == pytest.approx(TORCIDA_EXTRA_CAP, abs=0.02)

    # Curtida + comentários misturados também somam — e também respeitam o teto
    misturado = corre_4s([0.2, 0.4, 0.4])
    assert misturado - base == pytest.approx(TORCIDA_EXTRA_CAP, abs=0.02)
