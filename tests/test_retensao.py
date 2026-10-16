"""Retenção da live: o Bônus Fiel, a torcida visível e o nome de gente na voz.

O diagnóstico que originou isto (MELHORIAS.md): o voto leva 5 segundos e o
retorno demora dois minutos. O que segura o espectador é motivo para FICAR
(quem fica até o pódio leva XP dobrado), motivo para AGIR no meio da prova
(empurrar o cavalo pelo chat, agora visível) e motivo para se ver na tela
(o narrador citando o nome de quem está empurrando).
"""
import pytest

from config.settings import load_config
from fakes import FakeNarrador


async def _director(tmp_path, nome, voz=None):
    from backend.database.repository import DatabaseRepository
    from game.director import EventDirector
    from game.engine import RaceEngine

    config = load_config()
    config.voting_duration_seconds = 0.1
    config.countdown_duration_seconds = 0.05
    config.podium_duration_seconds = 0.05
    config.xp_duration_seconds = 0.05
    config.leaderboard_duration_seconds = 0.05

    repo = DatabaseRepository(db_path=str(tmp_path / nome))
    await repo.init_db()
    director = EventDirector(
        config=config, engine=RaceEngine(config), repository=repo, narrador=voz
    )
    return config, director


async def _ate_a_corrida(director):
    """Avança votação e contagem até a prova estar na pista."""
    from game.director import DirectorState

    await director.tick(0.15)
    await director.tick(0.06)
    assert director.state == DirectorState.RACING


async def _ate_o_xp(director):
    """Roda a prova até a tela de recompensas."""
    from game.director import DirectorState

    for _ in range(300):
        await director.tick(1.0)
        if director.state in (DirectorState.XP_REWARDS, DirectorState.LEADERBOARD):
            return
    raise AssertionError("a corrida não chegou às recompensas")


# ---------------------------------------------------------------------------
# 1. Bônus Fiel — quem fica até o pódio leva XP dobrado
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_voto_antes_da_largada_nao_marca_presenca(tmp_path):
    """Entrar e votar não é ficar: fora da janela da prova, nada é marcado."""
    _, director = await _director(tmp_path, "presenca.db")

    await director.handle_viewer_join("ana", "Ana")
    await director.handle_viewer_choice("ana", "Ana", 2)
    assert director._presentes == {}, "marcou presença com a votação aberta"

    await _ate_a_corrida(director)
    await director.handle_viewer_join("leo", "Leo")
    assert set(director._presentes) == {"leo"}


@pytest.mark.asyncio
async def test_quem_ficou_ate_o_podio_leva_o_dobro(tmp_path):
    """O contrato do bônus: fiel = 2x, quem só votou = XP de sempre.

    Ninguém é punido — o XP da participação continua valendo para todo mundo
    que votou. O "metade" do texto da live é a mesma conta vista do outro
    lado: o fiel levou 2x, então o ausente levou metade DELE.
    """
    voz = FakeNarrador()
    config, director = await _director(tmp_path, "fiel.db", voz)

    # Os dois votam igual na votação; só a Ana dá sinal de vida na prova.
    await director.handle_viewer_choice("ana", "Ana", 1)
    await director.handle_viewer_choice("leo", "Leo", 1)
    await _ate_a_corrida(director)
    await director.handle_viewer_join("ana", "Ana")

    await _ate_o_xp(director)

    premios = {r["display_name"]: r for r in director.last_race_rewards}
    # Os dois apostaram no MESMO cavalo: o prêmio da prova é idêntico para
    # eles, então a única diferença possível é o bônus (a prova é sorteada —
    # amarrar o teste ao vencedor daria um teste que passa e falha sozinho).
    assert premios["Leo"]["fiel"] is False
    assert premios["Ana"]["fiel"] is True
    assert premios["Ana"]["earned_xp"] == premios["Leo"]["earned_xp"] * 2

    # E a live AVISA — o bônus só existe se o público souber que existe.
    assert any(n["type"] == "FAITHFUL" for n in director.notifications_queue)
    assert ("xp_dobrado",) in voz.chamadas


@pytest.mark.asyncio
async def test_sem_fiel_ninguem_ganha_bonus_e_a_voz_nao_mente(tmp_path):
    """Corrida em que ninguém deu sinal de vida na prova: bônus nenhum."""
    voz = FakeNarrador()
    config, director = await _director(tmp_path, "sem_fiel.db", voz)

    await director.handle_viewer_choice("leo", "Leo", 3)
    await _ate_a_corrida(director)
    await _ate_o_xp(director)

    premios = {r["display_name"]: r for r in director.last_race_rewards}
    esperado = config.xp.participation
    if director.engine.winner_horse_id == 3:
        esperado += config.xp.win
    elif 3 in [p["horse_id"] for p in director.podium_data]:
        esperado += config.xp.top_3
    assert premios["Leo"]["earned_xp"] == esperado
    assert not any(n["type"] == "FAITHFUL" for n in director.notifications_queue)
    assert ("xp_dobrado",) not in voz.chamadas


@pytest.mark.asyncio
async def test_a_presenca_vale_uma_corrida_so(tmp_path):
    """A marca é da corrida: emendar a próxima exige aparecer de novo."""
    from game.director import DirectorState

    _, director = await _director(tmp_path, "zera.db")
    await _ate_a_corrida(director)
    await director.handle_viewer_join("ana", "Ana")
    assert "ana" in director._presentes

    for _ in range(300):
        await director.tick(1.0)
        if director.state == DirectorState.VOTING and director.race_number == 2:
            break
    assert director.race_number == 2
    assert director._presentes == {}


# ---------------------------------------------------------------------------
# 2. Torcida do meio da corrida, medida no HUD
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_empurrao_do_chat_conta_pessoa_e_alimenta_o_hud(tmp_path):
    """A barra da arquibancada conta PESSOA, não comentário."""
    _, director = await _director(tmp_path, "torcida.db")
    await _ate_a_corrida(director)

    await director.handle_viewer_choice("ana", "Ana", 4)
    await director.handle_viewer_choice("ana", "Ana", 4)
    await director.handle_viewer_choice("leo", "Leo", 4)

    assert director.torcida_por_cavalo[4] == 2, "spam do mesmo nome contou duas vezes"

    torcida = director.get_state_payload()["torcida"][4]
    assert torcida["torcedores"] == 2
    assert sorted(torcida["nomes"]) == ["Ana", "Leo"]
    # O empurrão do chat é velocidade somada de verdade (m/s) — é o que a
    # barra do HUD mostra, medida no MESMO teto da física.
    assert torcida["extra"] > 0


@pytest.mark.asyncio
async def test_curtida_tambem_conta_como_presenca(tmp_path):
    """Curtir não rende XP, mas é sinal de vida: vale para o Bônus Fiel."""
    _, director = await _director(tmp_path, "curtida.db")
    await _ate_a_corrida(director)

    await director.handle_viewer_like("ana", "Ana", 20)
    assert "ana" in director._presentes


# ---------------------------------------------------------------------------
# 3. O narrador fala o nome de GENTE
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_placar_cita_quem_esta_empurrando_e_nao_repete(tmp_path):
    """O placar cita gente da live — e gente DIFERENTE a cada placar.

    São nove placares por prova: repetir os mesmos três nomes a corrida
    inteira transformaria a citação em paisagem.
    """
    voz = FakeNarrador()
    _, director = await _director(tmp_path, "nomes.db", voz)
    await _ate_a_corrida(director)

    for i, nome in enumerate(["Ana", "Leo", "Rafa", "Bia", "Caio", "Duda"], start=1):
        await director.handle_viewer_choice(f"user{i}", nome, 5)
    voz.chamadas.clear()

    for _ in range(200):
        await director.tick(1.0)
        if len([c for c in voz.chamadas if c[0] == "placar"]) >= 2:
            break

    placares = [c for c in voz.chamadas if c[0] == "placar"]
    assert len(placares) >= 2
    citados = [c[4] for c in placares[:2]]
    assert all(citados), "o placar saiu sem citar ninguém com a torcida na live"
    assert citados[0] != citados[1], "a voz repetiu os mesmos nomes no placar seguinte"

    # A torcida é a do cavalo citado, e o cavalo citado tem nome de cavalo.
    assert placares[0][5]


@pytest.mark.asyncio
async def test_placar_sem_torcida_sai_sem_nome(tmp_path):
    """Ninguém empurrou nada: o placar é o de sempre (nada de citar o vazio)."""
    voz = FakeNarrador()
    _, director = await _director(tmp_path, "sem_nomes.db", voz)
    await _ate_a_corrida(director)
    voz.chamadas.clear()

    for _ in range(200):
        await director.tick(1.0)
        if any(c[0] == "placar" for c in voz.chamadas):
            break

    placar = next(c for c in voz.chamadas if c[0] == "placar")
    assert not placar[4]
