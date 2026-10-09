"""Testes da voz da live (game/narrador.py) e da fiação no director.

Sem internet e sem placa de som: o gerador e o tocador entram injetados, do
mesmo jeito que o narrador do tiktok-live-pixel permite.
"""
import time

import pytest

from config.settings import TtsConfig, load_config
from game.falas import (
    CORRIDA_ABERTURA,
    CORRIDA_DISPUTA,
    CORRIDA_PLACAR,
    FOTO_FINISH,
    RETA_FINAL,
)
from game.narrador import DISPUTA_PADRAO, FALA_PADRAO, VOZ_PADRAO, Narrador

from fakes import FakeNarrador


def _narrador(**cfg) -> Narrador:
    """Narrador de teste: nada de edge-tts nem MCI de verdade."""
    return Narrador(
        TtsConfig(**cfg),
        gerar=lambda texto: "caminho-fake.mp3",
        tocar=lambda caminho: None,
    )


# ---------------------------------------------------------------------------
# As frases
# ---------------------------------------------------------------------------

def test_falas_preenchem_os_valores():
    n = _narrador(falas=["{nome} mandou {quantidade}{presente} pro {cavalo}"])
    texto = n.texto_do_presente("leo", 5, "Rose", "RELÂMPAGO")
    # Nome próprio falado em caixa alta soaria como grito (e nome curto em
    # maiúsculas sai letra por letra): a voz recebe "Relâmpago".
    assert texto == "leo mandou 5x Rose pro Relâmpago"


def test_quantidade_some_quando_e_um_presente_so():
    n = _narrador(falas=["{nome} mandou {quantidade}{presente}"])
    assert n.texto_do_presente("leo", 1, "Rose", "RAIO") == "leo mandou Rose"


def test_placeholder_quebrado_cai_na_frase_padrao():
    n = _narrador(falas=["frase quebrada {naoexiste}"])
    esperado = FALA_PADRAO.format(
        nome="leo", quantidade="", presente="Rose", cavalo="Relâmpago"
    )
    assert n.texto_do_presente("leo", 1, "Rose", "RELÂMPAGO") == esperado


def test_entrada_tira_o_arroba_e_vencedor_fala_o_cavalo():
    n = _narrador(
        boas_vindas=["Chegou {nome}!"],
        vencedor=["Venceu o {numero} {nome}!"],
    )
    assert n.texto_de_entrada("@leo") == "Chegou leo!"
    assert n.texto_do_vencedor(2, "FANTASMA") == "Venceu o 2 Fantasma!"


def test_vozes_do_config_rodiziam():
    n = _narrador(vozes=["voz-a", "voz-b"])
    assert [n._proxima_voz() for _ in range(3)] == ["voz-a", "voz-b", "voz-a"]


# ---------------------------------------------------------------------------
# A locução ao vivo
# ---------------------------------------------------------------------------

def test_locucao_preenche_a_dupla_da_frente():
    n = _narrador(
        corrida_abertura=["{lider} puxa e {segundo} vem colado!"],
        corrida_placar=["{lider}, {segundo} e {terceiro} na frente!"],
        reta_final=["Reta final! {lider} contra {segundo}!"],
        foto_finish=["No fio do bigode! {vencedor} bateu {segundo}!"],
    )
    assert n.texto_da_abertura("RAIO", "TITÃ") == "Raio puxa e Titã vem colado!"
    assert n.texto_do_placar("RAIO", "TITÃ", "NEVASCA") == "Raio, Titã e Nevasca na frente!"
    assert n.texto_da_reta_final("RAIO", "TITÃ") == "Reta final! Raio contra Titã!"
    # Na foto-finish o primeiro nome é o VENCEDOR, não o líder do caminho.
    assert (
        n.texto_da_foto_finish("FANTASMA", "RAIO")
        == "No fio do bigode! Fantasma bateu Raio!"
    )


def test_locucao_com_placeholder_quebrado_cai_na_padrao():
    n = _narrador(corrida_disputa=["frase quebrada {naoexiste}"])
    esperado = DISPUTA_PADRAO.format(lider="Raio", segundo="Titã")
    assert n.texto_da_disputa("RAIO", "TITÃ") == esperado


def test_frases_da_locucao_do_jogo_formatam_sem_erro():
    """Toda frase padrão aceita os placeholders — pega typo em frase nova."""
    for frase in (*CORRIDA_ABERTURA, *CORRIDA_DISPUTA, *RETA_FINAL):
        assert "{" not in frase.format(lider="Raio", segundo="Titã")
    for frase in CORRIDA_PLACAR:
        assert "{" not in frase.format(lider="Raio", segundo="Titã", terceiro="Nevasca")
    for frase in FOTO_FINISH:
        assert "{" not in frase.format(vencedor="Raio", segundo="Titã")


def test_config_do_jogo_traz_a_secao_tts():
    config = load_config()
    assert config.tts.active is True
    assert config.tts.anunciar_entrada is True
    assert VOZ_PADRAO in config.tts.vozes


# ---------------------------------------------------------------------------
# A fila
# ---------------------------------------------------------------------------

def test_inativo_fica_mudo():
    n = _narrador(active=False)
    assert n.anunciar_votacao(1) is None
    assert n.anunciar_presente("leo", 1, "Rose", "RAIO") is None
    assert n.anunciar_abertura("RAIO", "TITÃ") is None
    assert n.anunciar_placar("RAIO", "TITÃ", "NEVASCA") is None
    assert n.anunciar_foto_finish("RAIO", "TITÃ") is None
    assert n.pendentes() == 0


def test_entrada_desligada_silencia_so_a_chegada():
    n = _narrador(anunciar_entrada=False)
    assert n.anunciar_entrada("leo") is None
    assert n.anunciar_largada(1) is not None


def test_fila_cheia_derruba_a_mais_antiga():
    n = _narrador(falas=["{nome} na fila"])
    for i in range(25):
        n.anunciar_presente(str(i), 1, "Rose", "RAIO")  # thread não ligada: fila enche
    assert n.pendentes() == 20
    # As cinco primeiras ficaram sem voz (fala atrasada é pior que silêncio).
    # Cada item da fila é (texto, categoria): a categoria marca a locução da
    # corrida, que pode ser descartada quando a prova termina.
    assert n._fila.queue[0][0] == "5 na fila"


def test_descartar_locucao_tira_so_a_locucao_da_fila():
    """Prova decidida não se narra: a locução pendente sai da fila.

    Só a locução da corrida é passado — presente, entrada, foto-finish e
    vencedor são momentos da live e ficam, na ordem (a fila é FIFO: o
    descarte não pode bagunçar o que sobra).
    """
    n = _narrador()
    n.anunciar_abertura("RAIO", "TITÃ")
    n.anunciar_placar("RAIO", "TITÃ", "NEVASCA")
    presente = n.anunciar_presente("leo", 1, "Rose", "RAIO")
    n.anunciar_clima("chuva forte", ["NEVASCA"])
    n.anunciar_disputa("RAIO", "TITÃ")
    entrada = n.anunciar_entrada("leo")
    n.anunciar_reta_final("RAIO", "TITÃ")
    chegada = n.anunciar_foto_finish("RAIO", "TITÃ")
    vencedor = n.anunciar_vencedor(1, "RAIO")

    # Abertura, placar, clima, disputa e reta final: cinco falas da prova.
    assert n.descartar_locucao() == 5

    assert [texto for texto, _ in n._fila.queue] == [
        presente,
        entrada,
        chegada,
        vencedor,
    ]
    # Descartar de novo não encontra mais nada.
    assert n.descartar_locucao() == 0


@pytest.mark.asyncio
async def test_director_descarta_a_locucao_quando_a_corrida_e_decidida(tmp_path):
    """O líder cruzou: o resto da locução era passado — sai da fila.

    Sem isso, a voz narrava uma prova já vencida: as falas de meio de
    corrida ainda na fila saíam DEPOIS de o vencedor cruzar, como se a
    corrida estivesse rolando.
    """
    from backend.database.repository import DatabaseRepository
    from game.director import EventDirector
    from game.engine import RaceEngine

    config = load_config()
    config.voting_duration_seconds = 0.1
    config.countdown_duration_seconds = 0.05

    repo = DatabaseRepository(db_path=str(tmp_path / "locucao.db"))
    await repo.init_db()
    voz = FakeNarrador()
    director = EventDirector(
        config=config, engine=RaceEngine(config), repository=repo, narrador=voz
    )

    await director.tick(0.15)  # VOTING -> COUNTDOWN
    await director.tick(0.06)  # COUNTDOWN -> RACING
    for _ in range(120):
        await director.tick(1.0)
        if any(c[0] == "vencedor" for c in voz.chamadas):
            break

    tipos = [c[0] for c in voz.chamadas]
    assert "descartar_locucao" in tipos, "a corrida terminou sem descartar a locução"

    # O descarte acontece na chegada do líder; o campeão é anunciado depois.
    descarte = tipos.index("descartar_locucao")
    assert tipos.index("vencedor") > descarte

    # E nenhuma locução da prova entra na fila depois do descarte.
    locucao = {"abertura", "placar", "disputa", "reta_final"}
    assert not locucao.intersection(tipos[descarte + 1:])


async def _director_em_corrida(tmp_path, nome, voz):
    """Director pronto para largar — atalho para os testes de descarte."""
    from backend.database.repository import DatabaseRepository
    from game.director import EventDirector
    from game.engine import RaceEngine

    config = load_config()
    config.voting_duration_seconds = 0.1
    config.countdown_duration_seconds = 0.05

    repo = DatabaseRepository(db_path=str(tmp_path / nome))
    await repo.init_db()
    return EventDirector(
        config=config, engine=RaceEngine(config), repository=repo, narrador=voz
    )


@pytest.mark.asyncio
async def test_finish_forcado_descarta_a_locucao(tmp_path):
    """O painel pula direto pro pódio: a locução pendente morre aqui também."""
    voz = FakeNarrador()
    director = await _director_em_corrida(tmp_path, "forcado.db", voz)

    await director.tick(0.15)
    await director.tick(0.06)  # RACING
    voz.chamadas.clear()

    await director.force_finish_race()
    assert ("descartar_locucao",) in voz.chamadas


@pytest.mark.asyncio
async def test_reset_no_meio_da_corrida_descarta_a_locucao(tmp_path):
    """Reiniciar o ciclo no meio da prova: a locução da corrida velha sai."""
    voz = FakeNarrador()
    director = await _director_em_corrida(tmp_path, "reset.db", voz)

    await director.tick(0.15)
    await director.tick(0.06)  # RACING
    voz.chamadas.clear()

    await director.reset_to_new_race()
    assert ("descartar_locucao",) in voz.chamadas


def test_thread_gera_toca_e_apaga():
    gerados, tocados = [], []

    def gerar(texto: str) -> str:
        gerados.append(texto)
        return "nao-existe.mp3"  # _apagar tolera arquivo ausente

    n = Narrador(TtsConfig(), gerar=gerar, tocar=tocados.append)
    texto = n.anunciar_presente("leo", 1, "Rose", "RAIO")
    n.ligar()
    try:
        limite = time.monotonic() + 3.0
        while not tocados and time.monotonic() < limite:
            time.sleep(0.01)
    finally:
        n.parar()

    assert gerados == [texto]
    assert tocados == ["nao-existe.mp3"]


# ---------------------------------------------------------------------------
# A fiação no director
# ---------------------------------------------------------------------------

# O dublê da voz mora em `tests/fakes.py` (compartilhado com test_clima.py).


@pytest.mark.asyncio
async def test_director_chama_a_voz_nos_momentos_certos(tmp_path):
    from backend.database.repository import DatabaseRepository
    from game.director import EventDirector
    from game.engine import RaceEngine

    config = load_config()
    config.voting_duration_seconds = 0.1
    config.countdown_duration_seconds = 0.05
    config.podium_duration_seconds = 0.05
    config.xp_duration_seconds = 0.05
    config.leaderboard_duration_seconds = 0.05

    repo = DatabaseRepository(db_path=str(tmp_path / "test_voz.db"))
    await repo.init_db()
    voz = FakeNarrador()
    director = EventDirector(
        config=config, engine=RaceEngine(config), repository=repo, narrador=voz
    )

    # Votação da corrida 1 anunciada já na criação do director.
    assert ("votacao", 1) in voz.chamadas

    await director.handle_viewer_join("leo", "Leonardo")
    assert ("entrada", "Leonardo") in voz.chamadas

    await director.handle_viewer_choice("leo", "Leonardo", 2)
    await director.handle_viewer_gift("leo", "Leonardo", "Rose", 3)
    assert ("presente", "Leonardo", 3, "Rose", "TROVÃO") in voz.chamadas

    await director.tick(0.15)  # VOTING -> COUNTDOWN
    await director.tick(0.06)  # COUNTDOWN -> RACING
    assert ("largada", 1) in voz.chamadas

    # A corrida leva ~35s de simulação: avança em passos de 1s até o vencedor.
    for _ in range(120):
        await director.tick(1.0)
        if any(c[0] == "vencedor" for c in voz.chamadas):
            break
    vencedor = next(c for c in voz.chamadas if c[0] == "vencedor")
    assert vencedor[1] in [h.id for h in config.horses]
    assert vencedor[2]

    # A locução ao vivo cobre a corrida inteira, na ordem da prova: abertura,
    # três placares, disputa e reta final — cada marco UMA vez.
    tipos = [c[0] for c in voz.chamadas]
    for tipo in ("abertura", "disputa", "reta_final"):
        assert tipos.count(tipo) == 1
    assert tipos.count("placar") == 3
    da_corrida = ("largada", "abertura", "placar", "disputa", "reta_final", "vencedor")
    assert [t for t in tipos if t in da_corrida] == [
        "largada",
        "abertura",
        "placar",
        "disputa",
        "placar",
        "placar",
        "reta_final",
        "vencedor",
    ]
    # A foto-finish é sorte da corrida (só nas decididas no detalhe); quando
    # sai, sai UMA vez e antes do anúncio do campeão (a fila é FIFO).
    if "foto_finish" in tipos:
        assert tipos.count("foto_finish") == 1
        assert tipos.index("foto_finish") < tipos.index("vencedor")


@pytest.mark.asyncio
async def test_votacao_lembra_a_galera_no_meio_do_caminho(tmp_path):
    """30s de votação com uma chamada só é silêncio demais: a voz volta."""
    from backend.database.repository import DatabaseRepository
    from game.director import EventDirector
    from game.engine import RaceEngine

    config = load_config()
    config.voting_duration_seconds = 40.0

    repo = DatabaseRepository(db_path=str(tmp_path / "lembrete.db"))
    await repo.init_db()
    voz = FakeNarrador()
    director = EventDirector(
        config=config, engine=RaceEngine(config), repository=repo, narrador=voz
    )
    voz.chamadas.clear()  # a chamada de abertura sai já na criação do director

    await director.tick(13.0)  # passa do primeiro lembrete (12s)
    await director.tick(13.0)  # 26s: segundo lembrete
    assert [c for c in voz.chamadas if c[0] == "votacao"] == [
        ("votacao", 1),
        ("votacao", 1),
    ]


def test_foto_finish_so_quando_a_margem_e_minima(tmp_path):
    """A exclamação da chegada só entra quando foi decidida no detalhe."""
    from backend.database.repository import DatabaseRepository
    from game.director import EventDirector
    from game.engine import RaceEngine

    config = load_config()
    director = EventDirector(
        config=config,
        engine=RaceEngine(config),
        repository=DatabaseRepository(db_path=str(tmp_path / "voz.db")),
    )
    director.podium_data = [
        {"final_position": 1, "finish_time_ms": 36100.0},
        {"final_position": 2, "finish_time_ms": 36130.0},  # 30ms: no detalhe
    ]
    assert director._foto_finish_apertada() is True

    director.podium_data = [
        {"final_position": 1, "finish_time_ms": 36100.0},
        {"final_position": 2, "finish_time_ms": 36800.0},  # 700ms: com folga
    ]
    assert director._foto_finish_apertada() is False

    # Corrida sem segundo lugar (não deveria acontecer, mas não pode estourar).
    director.podium_data = [{"final_position": 1, "finish_time_ms": 36100.0}]
    assert director._foto_finish_apertada() is False


@pytest.mark.asyncio
async def test_anuncio_imediato_na_linha_de_chegada_sem_esperar_timeout(tmp_path):
    """Assim que o líder cruza a linha de chegada, o vencedor é anunciado IMEDIATAMENTE (sem esperar os 3.5s)."""
    from game.director import DirectorState

    voz = FakeNarrador()
    director = await _director_em_corrida(tmp_path, "imediato.db", voz)

    await director.tick(0.15)  # VOTING -> COUNTDOWN
    await director.tick(0.06)  # COUNTDOWN -> RACING
    assert director.state == DirectorState.RACING

    # Simula o cavalo 1 cruzando a linha de chegada
    lider = director.engine.horses[0]
    lider.distance = director.engine.track_length
    lider.finished = True
    lider.finish_time_ms = 35000.0
    director.engine.winner_horse_id = lider.id

    # O engine ainda NÃO terminou (falta o timeout de 3.5s)
    assert director.engine.is_finished() is False

    # Tick durante a corrida
    await director.tick(0.016)

    # O anúncio de vencedor e descarte de locução já foram chamados na hora!
    tipos = [c[0] for c in voz.chamadas]
    assert "interromper_locucao" in tipos
    assert "descartar_locucao" in tipos
    assert "vencedor" in tipos


def test_audio_ducking_boas_vindas():
    """Boas-vindas entra no canal prioritário com fila e ducking de áudio."""
    n = _narrador()
    assert n.pendentes() == 0
    assert n._fila_boas_vindas.qsize() == 0

    texto = n.anunciar_entrada("Leonardo")
    assert texto is not None
    assert "Leonardo" in texto
    # Aparece na fila de boas-vindas
    assert n._fila_boas_vindas.qsize() == 1


def test_anti_repeticao_nunca_repete_frase_consecutivamente():
    """Garante que a mesma frase nunca sai duas vezes seguidas, mesmo com vozes alternando."""
    frases = [
        "Frase um {nome}",
        "Frase dois {nome}",
        "Frase tres {nome}",
        "Frase quatro {nome}",
    ]
    n = _narrador(boas_vindas=frases)
    historico = []
    for i in range(40):
        fala = n.texto_de_entrada(f"user{i}")
        historico.append(fala)

    # Verifica que não houve nenhuma repetição consecutiva
    for i in range(len(historico) - 1):
        m1 = historico[i].split()[1]
        m2 = historico[i + 1].split()[1]
        assert m1 != m2, f"Repetição consecutiva encontrada: {historico[i]} seguido de {historico[i+1]}"


def test_normalizar_para_fala_converte_digitos_e_presentes():
    """Garante que números 1-10 viram palavras em português e presentes em inglês viram português."""
    bruto = "O cavalo 8 venceu! Ganhou 5x Rose pro cavalo 1!"
    normalizado = Narrador._normalizar_para_fala(bruto)
    assert "oito" in normalizado
    assert "8" not in normalizado
    assert "um" in normalizado
    assert "1" not in normalizado
    assert "Rosa" in normalizado
    assert "Rose" not in normalizado


def test_interromper_locucao_ativa_fade_out():
    """interromper_locucao ativa o sinal de fade-out suave se estiver tocando locução da corrida."""
    from game.narrador import CORRIDA

    n = _narrador()
    assert n._fade_out_solicitado.is_set() is False

    # Sem áudio tocando: não ativa
    n.interromper_locucao()
    assert n._fade_out_solicitado.is_set() is False

    # Com áudio da corrida tocando: ativa fade-out
    with n._lock_audio:
        n._categoria_atual = CORRIDA
        n._alias_principal = "teste_alias"

    n.interromper_locucao()
    assert n._fade_out_solicitado.is_set() is True

    # Se a fala atual for da live (ex: vencedor ou presente), não interrompe
    n._fade_out_solicitado.clear()
    with n._lock_audio:
        n._categoria_atual = "vencedor"
    n.interromper_locucao()
    assert n._fade_out_solicitado.is_set() is False


def test_limpeza_de_emojis_na_fala():
    """Garante que emojis como 🇧🇷✋🏽😛🤚🏽 são removidos e a voz fala apenas o nome limpo."""
    n = _narrador(boas_vindas=["Chegou {nome}!"])

    # 1. Nome com emojis variados (bandeira, mãos, rostos)
    fala = n.texto_de_entrada("caioba🇧🇷✋🏽😛🤚🏽", "caioba338")
    assert fala == "Chegou caioba!"
    assert "🇧🇷" not in fala
    assert "✋" not in fala

    # 2. Nome que é SÓ emoji: usa o username como fallback
    fala_so_emoji = n.texto_de_entrada("👑🔥💎", "pedro_gamer")
    assert fala_so_emoji == "Chegou pedrogamer!"

    # 3. Presente enviado por usuário com emojis
    fala_presente = n.texto_do_presente("caioba🇧🇷✋🏽😛🤚🏽", 1, "Rose", "Relâmpago")
    assert "caioba" in fala_presente
    assert "🇧🇷" not in fala_presente

    # 4. _normalizar_para_fala remove qualquer resquício de emoji
    limpo = Narrador._normalizar_para_fala("Bem-vindo caioba🇧🇷✋🏽😛🤚🏽!")
    assert limpo == "Bem-vindo caioba!"


def test_anunciar_follow_e_curtidas():
    """Garante que novo seguidor e rajadas de 20+ curtidas são agradecidos na voz."""
    n = _narrador()

    # 1. Seguidor com emojis
    follow = n.anunciar_follow("caioba🇧🇷✋🏽😛🤚🏽", fallback="caioba338")
    assert follow is not None
    assert "caioba" in follow
    assert "🇧🇷" not in follow

    # 2. Rajada de 25 curtidas
    curtidas = n.anunciar_curtidas("ana_clara", 25)
    assert curtidas is not None
    assert "anaclara" in curtidas.lower()
    assert "curtida" in curtidas.lower()
