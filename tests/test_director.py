import pytest
import asyncio
from config.settings import load_config
from backend.database.repository import DatabaseRepository

@pytest.mark.asyncio
async def test_event_bus():
    from backend.event_bus import EventBus
    
    bus = EventBus()
    received = []
    
    async def listener(event):
        received.append(event)
        
    bus.subscribe("PLAYER_CHOICE", listener)
    await bus.publish({"type": "PLAYER_CHOICE", "user": "Leo", "horse_id": 1})
    
    assert len(received) == 1
    assert received[0]["user"] == "Leo"
    assert received[0]["horse_id"] == 1

@pytest.mark.asyncio
async def test_director_state_transitions(tmp_path):
    from game.director import EventDirector, DirectorState
    from game.engine import RaceEngine
    
    config = load_config()
    # Durações curtas para teste unitário ágil
    config.voting_duration_seconds = 0.1
    config.countdown_duration_seconds = 0.05
    config.podium_duration_seconds = 0.05
    config.xp_duration_seconds = 0.05
    config.leaderboard_duration_seconds = 0.05
    
    db_file = tmp_path / "test_director.db"
    repo = DatabaseRepository(db_path=str(db_file))
    await repo.init_db()
    
    engine = RaceEngine(config)
    director = EventDirector(config=config, engine=engine, repository=repo)
    
    # Estado inicial deve ser VOTING
    assert director.state == DirectorState.VOTING
    assert director.race_number == 1
    
    # Registra escolha de cavalo de um viewer
    await director.handle_viewer_choice("leo", "Leonardo", 1)
    choices = director.get_current_choices_summary()
    assert choices[1]["supporters_count"] == 1
    
    # Executa step de tempo que transiciona VOTING -> COUNTDOWN
    await director.tick(0.15)
    assert director.state == DirectorState.COUNTDOWN

    # Transiciona COUNTDOWN -> RACING
    await director.tick(0.06)
    assert director.state == DirectorState.RACING


@pytest.mark.asyncio
async def test_finish_forcado_monta_o_podio_com_a_corrida_que_estava_na_pista(tmp_path):
    """🏁 no painel: o pódio tem de ser a corrida que estava acontecendo.

    O `force_finish_race` empurrava todo cavalo para a linha com o MESMO
    `finish_time_ms` e não montava `final_results` — o diretor lia o pódio do
    engine e recebia lista VAZIA. Na tela o pódio subia sem cavalo nenhum e o
    2º/3º lugar virava a ordem do arquivo de configuração (tempos iguais →
    ordenação estável). Encerrar na mão tem de respeitar quem estava na frente
    no momento do clique.
    """
    from game.director import DirectorState
    from game.director import EventDirector
    from game.engine import RaceEngine

    config = load_config()
    config.voting_duration_seconds = 0.1
    config.countdown_duration_seconds = 0.05

    repo = DatabaseRepository(db_path=str(tmp_path / "podio_forcado.db"))
    await repo.init_db()
    engine = RaceEngine(config)
    director = EventDirector(config=config, engine=engine, repository=repo)

    await director.tick(0.15)  # VOTING -> COUNTDOWN
    await director.tick(0.06)  # COUNTDOWN -> RACING
    for _ in range(20):
        await director.tick(0.5)  # 10s de prova: o pelotão já se separou

    # Quem estava na frente no exato momento do clique, do 1º ao 8º.
    na_pista = [h.id for h in sorted(engine.horses, key=lambda h: h.distance, reverse=True)]

    await director.force_finish_race()
    assert director.state == DirectorState.PODIUM

    assert len(director.podium_data) == 3, "o pódio subiu vazio"
    assert [p["horse_id"] for p in director.podium_data] == na_pista[:3], (
        "o pódio não respeitou a corrida que estava na pista"
    )
    assert [p["final_position"] for p in director.podium_data] == [1, 2, 3]
    assert engine.winner_horse_id == na_pista[0]

    # Nada de tempos empatados: com todos no mesmo milissegundo, a ordem do
    # pódio passa a ser a do arquivo de configuração.
    tempos = [p["finish_time_ms"] for p in engine.final_results]
    assert len(set(tempos)) == len(tempos), f"tempos empatados no pódio: {tempos}"
    assert tempos == sorted(tempos)


@pytest.mark.asyncio
async def test_finish_forcado_nao_grava_o_podio_duas_vezes(tmp_path):
    """O tick de 60Hz não pode fechar a corrida de novo durante a gravação.

    `force_finish_race` grava os resultados no banco — um `await`, e o loop de
    simulação roda justamente aí. Se o diretor ainda estivesse em RACING nesse
    instante, o tick veria o engine FINISHED e fecharia a corrida outra vez: o
    campeão saía duas vezes no log e as 8 linhas do pódio entravam em dobro em
    `race_results`.
    """
    import sqlite3
    from game.director import DirectorState
    from game.director import EventDirector
    from game.engine import RaceEngine

    config = load_config()
    config.voting_duration_seconds = 0.1
    config.countdown_duration_seconds = 0.05

    caminho = tmp_path / "podio_unico.db"
    repo = DatabaseRepository(db_path=str(caminho))
    await repo.init_db()
    engine = RaceEngine(config)
    director = EventDirector(config=config, engine=engine, repository=repo)

    await director.tick(0.15)
    await director.tick(0.06)  # RACING
    for _ in range(8):
        await director.tick(0.5)

    gravacoes = []
    original = repo.finish_race

    async def finish_race_com_o_tick_rodando(*args, **kwargs):
        gravacoes.append(kwargs.get("race_id"))
        await director.tick(0.1)  # é o que o loop de simulação faz nesse await
        return await original(*args, **kwargs)

    repo.finish_race = finish_race_com_o_tick_rodando

    await director.force_finish_race()
    assert director.state == DirectorState.PODIUM
    assert len(gravacoes) == 1, "o pódio foi gravado mais de uma vez"

    with sqlite3.connect(str(caminho)) as db:
        linhas = db.execute(
            "SELECT final_position, COUNT(*) FROM race_results GROUP BY final_position"
        ).fetchall()
    assert linhas, "o pódio forçado não foi gravado"
    assert all(qtd == 1 for _, qtd in linhas), f"posições repetidas no banco: {linhas}"


async def _director_votando(tmp_path, nome):
    """Director em VOTING (votação longa: quem manda no relógio é o teste)."""
    from game.director import EventDirector
    from game.engine import RaceEngine

    config = load_config()
    repo = DatabaseRepository(db_path=str(tmp_path / nome))
    await repo.init_db()
    return EventDirector(config=config, engine=RaceEngine(config), repository=repo)


@pytest.mark.asyncio
async def test_numero_digitado_com_a_corrida_rodando_empurra_o_cavalo(tmp_path):
    """Com a corrida rodando, o número digitado vira torcida: um empurrão
    LEVE no cavalo citado — e o voto (já travado na largada) não muda."""
    from game.director import (
        TORCIDA_DURATION_SECONDS,
        TORCIDA_EXTRA_SPEED,
        DirectorState,
    )
    from game.director import EventDirector
    from game.engine import RaceEngine

    config = load_config()
    config.voting_duration_seconds = 0.1
    config.countdown_duration_seconds = 0.05

    repo = DatabaseRepository(db_path=str(tmp_path / "torcida.db"))
    await repo.init_db()
    director = EventDirector(config=config, engine=RaceEngine(config), repository=repo)

    await director.handle_viewer_choice("leo", "Leonardo", 3)  # voto de verdade
    await director.tick(0.15)  # VOTING -> COUNTDOWN
    await director.tick(0.06)  # COUNTDOWN -> RACING
    assert director.state == DirectorState.RACING

    assert await director.handle_viewer_choice("ana", "Ana", 5) is True

    cavalo = next(h for h in director.engine.horses if h.id == 5)
    boost = next(b for b in cavalo.active_boosts if b.name == "TORCIDA NO CHAT")
    assert boost.power == TORCIDA_EXTRA_SPEED
    assert boost.additive is True
    assert boost.remaining_seconds == TORCIDA_DURATION_SECONDS

    # Torcida de chat não é voto: a votação fechou na largada e ninguém
    # entrou como apoiador novo.
    apoiadores = [
        s["tiktok_username"]
        for sups in director.horse_supporters.values()
        for s in sups
    ]
    assert apoiadores == ["leo"]

    assert any(
        n["type"] == "CHEER" and "Ana" in n["text"] and n["horse_id"] == 5
        for n in director.notifications_queue
    )


@pytest.mark.asyncio
async def test_numero_digitado_no_podio_nao_empurra_ninguem(tmp_path):
    """Número digitado só EMPURRA cavalo na votação (voto) ou na corrida
    (torcida): comentário que chega no pódio não mexe mais na prova que
    acabou — ele vira voto para a próxima (ver os testes de pré-voto)."""
    from game.director import DirectorState, EventDirector
    from game.engine import RaceEngine

    config = load_config()
    config.track_length_meters = 120.0
    config.voting_duration_seconds = 0.1
    config.countdown_duration_seconds = 0.05
    config.podium_duration_seconds = 30.0  # não sai do pódio durante o teste

    repo = DatabaseRepository(db_path=str(tmp_path / "atrasado.db"))
    await repo.init_db()
    director = EventDirector(config=config, engine=RaceEngine(config), repository=repo)

    await director.tick(0.15)
    await director.tick(0.06)
    for _ in range(400):
        await director.tick(0.1)
        if director.state == DirectorState.PODIUM:
            break
    assert director.state == DirectorState.PODIUM

    await director.handle_viewer_choice("ana", "Ana", 5)
    assert not any(n["type"] == "CHEER" for n in director.notifications_queue)
    assert all(not h.active_boosts for h in director.engine.horses)
    # A corrida que acabou não ganha apoiador retroativo.
    assert all(not sups for sups in director.horse_supporters.values())


@pytest.mark.asyncio
async def test_voto_durante_o_xp_conta_para_a_corrida_seguinte(tmp_path):
    """O chat digita número com o XP/ranking na tela: o voto não pode sumir.

    Antes o comentário era descartado (`return False`) e o espectador via a
    escolha não contabilizar. Agora ele espera a votação nova abrir e entra
    nela como qualquer outro voto — no placar da grade e na largada.
    """
    from game.director import DirectorState, EventDirector
    from game.engine import RaceEngine

    config = load_config()
    config.track_length_meters = 120.0
    config.voting_duration_seconds = 0.1
    config.countdown_duration_seconds = 0.05
    config.podium_duration_seconds = 0.05
    config.xp_duration_seconds = 30.0  # segura a fase de XP para o teste

    repo = DatabaseRepository(db_path=str(tmp_path / "prevoto.db"))
    await repo.init_db()
    director = EventDirector(config=config, engine=RaceEngine(config), repository=repo)

    await director.tick(0.15)
    await director.tick(0.06)
    for _ in range(400):
        await director.tick(0.1)
        if director.state == DirectorState.XP_REWARDS:
            break
    assert director.state == DirectorState.XP_REWARDS

    assert await director.handle_viewer_choice("ana", "Ana", 4) is True
    assert director._pre_votos["ana"]["horse_id"] == 4
    # Enquanto o XP está na tela ninguém apoia a corrida que acabou.
    assert all(not sups for sups in director.horse_supporters.values())

    # A votação nova abre: o pré-voto tem de estar contando.
    config.xp_duration_seconds = 0.05
    config.leaderboard_duration_seconds = 0.05
    for _ in range(40):
        await director.tick(0.05)
        if director.state == DirectorState.VOTING:
            break
    assert director.state == DirectorState.VOTING
    assert director.race_number == 2
    assert director.get_current_choices_summary()[4]["supporters_count"] == 1
    assert director.get_current_choices_summary()[4]["recent_supporters"] == ["Ana"]
    assert not director._pre_votos  # despejado, não sobra para a corrida seguinte


@pytest.mark.asyncio
async def test_trocar_de_ideia_no_ranking_vale_so_o_ultimo_numero(tmp_path):
    """Dois números digitados na mesma fase de fim de corrida: vale o último."""
    from game.director import DirectorState, EventDirector
    from game.engine import RaceEngine

    config = load_config()
    config.voting_duration_seconds = 0.1

    repo = DatabaseRepository(db_path=str(tmp_path / "troca.db"))
    await repo.init_db()
    director = EventDirector(config=config, engine=RaceEngine(config), repository=repo)
    director.state = DirectorState.LEADERBOARD

    await director.handle_viewer_choice("ana", "Ana", 3)
    await director.handle_viewer_choice("ana", "Ana", 7)

    assert list(director._pre_votos) == ["ana"]
    await director.reset_to_new_race()
    resumo = director.get_current_choices_summary()
    assert resumo[7]["supporters_count"] == 1
    assert resumo[3]["supporters_count"] == 0


@pytest.mark.asyncio
async def test_presente_de_quem_torceu_segue_o_cavalo_da_torcida(tmp_path):
    """Quem torceu no chat não pode ver o presente cair em OUTRO cavalo.

    O presente só procurava o VOTO do espectador, e a torcida (número
    digitado com a prova rolando) não deixava registro nenhum: quem torcia
    pelo #7 e mandava uma galáxia via o boost cair num cavalo sorteado, na
    frente da live inteira ("torceu pelo #7" e "presente pro #3" no mesmo
    minuto). A torcida continua não sendo voto — não rende XP nem entra na
    contagem de apoiadores.
    """
    from game.director import DirectorState, EventDirector
    from game.engine import RaceEngine

    config = load_config()
    config.voting_duration_seconds = 0.1
    config.countdown_duration_seconds = 0.05

    repo = DatabaseRepository(db_path=str(tmp_path / "torcida_presente.db"))
    await repo.init_db()
    director = EventDirector(config=config, engine=RaceEngine(config), repository=repo)

    await director.tick(0.15)  # VOTING -> COUNTDOWN
    await director.tick(0.06)  # COUNTDOWN -> RACING
    assert director.state == DirectorState.RACING

    # "Ana" (grafada assim no chat) torce pelo 7 e manda uma galáxia
    await director.handle_viewer_choice("Ana", "Ana", 7)
    await director.handle_viewer_gift("ana", "Ana", "Galaxy", 1)

    cavalo7 = next(h for h in director.engine.horses if h.id == 7)
    boost_presente = [b for b in cavalo7.active_boosts if b.name != "TORCIDA NO CHAT"]
    assert boost_presente, "o presente não caiu no cavalo pelo qual ela torceu"
    assert not [
        h.id for h in director.engine.horses if h.id != 7 and h.active_boosts
    ], "o presente vazou pra outro cavalo"

    # Torcida não é voto: ninguém entrou como apoiador.
    assert all(not sups for sups in director.horse_supporters.values())

    # A torcida morre com a corrida: no ciclo novo o presente volta a sortear.
    await director.reset_to_new_race()
    assert director.torcida_por_viewer == {}


@pytest.mark.asyncio
async def test_presente_de_quem_nao_escolheu_cai_em_cavalo_sorteado(tmp_path):
    """Presente sem dono cai em cavalo SORTEADO, não sempre no #1.

    Era esse o furo do "#1 sempre ganha": quem não votou tinha o presente
    empurrado pro líder — e na votação o líder é sempre o #1. Uma live de
    galera sem voto virava uma corrida de um cavalo só.
    """
    director = await _director_votando(tmp_path, "presente.db")

    for i in range(40):
        await director.handle_viewer_gift(f"g{i}", f"G{i}", "Rose", 1)

    empurrados = {h.id for h in director.engine.horses if h.active_boosts}
    assert len(empurrados) >= 2, "todo presente sem dono foi pro mesmo cavalo"


@pytest.mark.asyncio
async def test_aviso_de_presente_leva_o_que_a_tela_precisa(tmp_path):
    """O cartão de presente do HUD monta o aviso com o que vem na notificação.

    Sem esses campos o aviso da live volta a ser uma linha de texto crua: quem
    mandou, o que mandou, quantos e em qual cavalo o boost caiu.
    """
    director = await _director_votando(tmp_path, "aviso.db")

    await director.handle_viewer_gift("leo", "Leonardo", "Rose", 3)

    avisos = [n for n in director.notifications_queue if n["type"] == "GIFT"]
    assert avisos, "presente não gerou aviso na tela"
    aviso = avisos[-1]
    assert aviso["sender_name"] == "Leonardo"
    assert aviso["gift_name"] == "Rose"
    assert aviso["gift_emoji"] == "🌹"
    assert aviso["gift_count"] == 3
    assert aviso["boost_label"] == "TURBO"
    assert aviso["horse_name"], "o aviso precisa dizer em qual cavalo o boost caiu"
    assert aviso["horse_id"] in {h.id for h in director.engine.horses}


def test_presente_dura_uma_fatia_visivel_da_prova():
    """Presente não pode ser um piscar: a aura no cavalo tem de durar.

    Quando a pista triplicou (1000m→3000m, ~35s→~110s), as durações dos
    presentes ficaram com o valor da prova velha: uma rosa de 4s, que antes
    era 11% da corrida, virou 3% — o efeito sumia antes de a live ver.
    Piso: todo presente dura ao menos 10% da prova; lendário, ao menos 20%.
    """
    from game.director import GIFT_DEFAULT, GIFT_TIERS

    prova = load_config().race_duration_seconds
    for tier in GIFT_TIERS + [GIFT_DEFAULT]:
        assert tier["duration"] >= prova * 0.10, (
            f"{tier['label']} ({tier['duration']}s) pisca rápido demais "
            f"para uma prova de {prova}s"
        )
    for tier in GIFT_TIERS:
        if tier["legendary"]:
            assert tier["duration"] >= prova * 0.20, (
                f"{tier['label']} é lendário e devia segurar a aura por mais tempo"
            )


@pytest.mark.asyncio
async def test_curtida_de_anonimo_cai_em_cavalo_sorteado(tmp_path):
    """Rajada de curtidas sem autor identificável também espalha.

    O TikTok para de mandar o autor depois de muitas curtidas seguidas —
    e o fallback velho (o líder/#1) empilhava tudo num cavalo só.
    """
    director = await _director_votando(tmp_path, "curtida.db")

    for _ in range(40):
        await director.handle_viewer_like("", "", 10)

    empurrados = {h.id for h in director.engine.horses if h.active_boosts}
    assert len(empurrados) >= 2, "toda curtida sem autor foi pro mesmo cavalo"


@pytest.mark.asyncio
async def test_curtida_de_anonimo_na_corrida_empurra_o_ultimo_colocado(tmp_path):
    """Na prova, curtida de quem não escolheu cavalo vai para o ÚLTIMO colocado.

    Curtida não pode alimentar quem já lidera ("o primeiro" da pista): o
    empurrão é de recuperação e vai sempre para quem está atrás — nada de
    empilhar no líder, nem por sorteio.
    """
    from game.director import DirectorState, EventDirector
    from game.engine import RaceEngine

    config = load_config()
    config.voting_duration_seconds = 0.1
    config.countdown_duration_seconds = 0.05

    repo = DatabaseRepository(db_path=str(tmp_path / "curtida_ultimo.db"))
    await repo.init_db()
    director = EventDirector(config=config, engine=RaceEngine(config), repository=repo)

    await director.tick(0.15)  # VOTING -> COUNTDOWN
    await director.tick(0.06)  # COUNTDOWN -> RACING
    assert director.state == DirectorState.RACING

    # A prova corre um pouco para as posições se separarem
    for _ in range(150):
        await director.tick(1.0 / 60.0)

    ordenados = sorted(director.engine.horses, key=lambda h: h.distance, reverse=True)
    lider, ultimo = ordenados[0], ordenados[-1]
    assert lider.distance > ultimo.distance, "posições empatadas — corrida curta demais pro teste"

    for _ in range(5):
        await director.handle_viewer_like("", "", 10)

    assert any(b.name == "GALERA CURTIU" for b in ultimo.active_boosts), \
        "curtida de anônimo não foi para o último colocado"
    assert not any(b.name == "GALERA CURTIU" for b in lider.active_boosts), \
        "curtida de anônimo alimentou o líder"

    # Nem por sorteio: ninguém além do último colocado foi empurrado
    for h in director.engine.horses:
        if h.id != ultimo.id:
            assert not any(b.name == "GALERA CURTIU" for b in h.active_boosts), \
                f"curtida de anônimo caiu no #{h.id}, que não é o último colocado"


@pytest.mark.asyncio
async def test_narracao_da_corrida_no_console(tmp_path, caplog):
    """O console conta a história da live: votação, largada, presente, prêmios."""
    import logging
    from game.director import EventDirector
    from game.engine import RaceEngine

    config = load_config()
    config.voting_duration_seconds = 0.1
    config.countdown_duration_seconds = 0.05

    repo = DatabaseRepository(db_path=str(tmp_path / "test_narracao.db"))
    await repo.init_db()
    engine = RaceEngine(config)

    with caplog.at_level(logging.INFO, logger="game.director"):
        director = EventDirector(config=config, engine=engine, repository=repo)
        assert "votação aberta" in caplog.text

        await director.handle_viewer_choice("leo", "Leonardo", 1)
        await director.tick(0.15)
        assert "Votação encerrada" in caplog.text
        assert "favorito #1" in caplog.text

        await director.tick(0.06)
        assert "COMEÇOU" in caplog.text

        await director.handle_viewer_gift("leo", "Leonardo", "Lion", 1)
        assert "enviou Lion x1" in caplog.text

        await director.handle_viewer_like("leo", "Leonardo", 10)
        assert "10 curtidas" in caplog.text
