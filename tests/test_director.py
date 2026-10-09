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
async def test_numero_digitado_fora_da_corrida_nao_empurra(tmp_path):
    """Número digitado só vale na votação (voto) ou na corrida (torcida):
    comentário atrasado no pódio não empurra mais ninguém."""
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

    assert await director.handle_viewer_choice("ana", "Ana", 5) is False
    assert not any(n["type"] == "CHEER" for n in director.notifications_queue)
    assert all(not h.active_boosts for h in director.engine.horses)


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
