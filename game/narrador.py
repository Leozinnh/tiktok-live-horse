"""A voz da corrida: presente, chegada, a locução ao vivo e os momentos da corrida viram fala no ar.

Mesmo sistema do `tiktok-live-pixel` (game/narrador.py de lá), portado inteiro:
o Narrador é uma THREAD com fila, pelo mesmo motivo da thread do TikTok — gerar
a voz e conversar com o serviço de síntese leva segundos, e o loop de eventos do
jogo não pode esperar por isso. Quem presenteia ganha o crédito no telão NA
HORA; a fala entra na fila e sai quando der.

O ciclo é o pedido original daquele projeto, literal: gera o áudio, toca e
apaga. A reprodução usa o MCI do próprio Windows (via ctypes, biblioteca
padrão): não há binário externo nem pacote de áudio para instalar. O arquivo é
gerado num temporário e apagado assim que termina de tocar.

As frases são SORTEADAS de `game/falas.py` — a lista inteira mora lá, fora
deste módulo, porque conteúdo e código envelhecem em ritmos diferentes: trocar
o texto da live não deveria ser um commit no motor da voz.

A VOZ também varia: `tts.vozes` é a lista de vozes por onde as falas rodiziam
(vazia = sempre a `tts.voz` de sempre). Uma LIVE inteira numa voz só soa como
um robô lendo avisos; o rodízio faz cada fala soar como alguém diferente
chamando na tela.

Falha aqui nunca derruba o jogo: sem internet, sem a biblioteca, sem placa de
som — o que acontece é um log, e o jogo segue em frente.
"""

from __future__ import annotations

import itertools
import logging
import os
import queue
import random
import tempfile
import threading
import time
from typing import Callable

from config.settings import TtsConfig
from game.falas import (
    BOAS_VINDAS,
    CORRIDA_ABERTURA,
    CORRIDA_DISPUTA,
    CORRIDA_PLACAR,
    FALAS,
    FOTO_FINISH,
    LARGADA,
    RETA_FINAL,
    VENCEDOR,
    VOTACAO_ABERTA,
)

logger = logging.getLogger(__name__)

VOZ_PADRAO = "pt-BR-FranciscaNeural"

# As vozes pt-BR que a edge-tts oferece HOJE (conferidas por `list_voices`):
# só estas três — as mais antigas (Brenda, Donato, Giovanna...) saíram do
# serviço. Com mais de uma em `tts.vozes`, as falas saem em rodízio; com a
# lista vazia, tudo sai na `tts.voz` de sempre:
#   "pt-BR-FranciscaNeural" (feminina), "pt-BR-AntonioNeural" (masculina),
#   "pt-BR-ThalitaMultilingualNeural" (feminina, multilíngue).
RATE_PADRAO = "+8%"
PITCH_PADRAO = "+3Hz"

# O `{quantidade}` vira "5x " (com espaço) quando há mais de um, e vazio
# quando é um só: "1x Rose" não existe na língua falada — é "mandou Rose"
# e é como uma pessoa diria.
#
# A fala padrão é a primeira da lista de propósito: se uma frase do config
# vier quebrada (um `{placeholder}` que não existe), o plano B é uma frase
# de verdade, e não uma segunda cópia que pode envelhecer.
FALA_PADRAO = FALAS[0]

# Mesmo plano B para a chegada e para os momentos da corrida, com a mesma
# âncora: a primeira frase de verdade de cada lista.
BOAS_VINDAS_PADRAO = BOAS_VINDAS[0]
VOTACAO_PADRAO = VOTACAO_ABERTA[0]
LARGADA_PADRAO = LARGADA[0]
VENCEDOR_PADRAO = VENCEDOR[0]

# A locução ao vivo (o "locutor" que fala DURANTE a corrida) segue o mesmo
# plano B — a primeira frase de verdade de cada lista.
ABERTURA_PADRAO = CORRIDA_ABERTURA[0]
DISPUTA_PADRAO = CORRIDA_DISPUTA[0]
PLACAR_PADRAO = CORRIDA_PLACAR[0]
RETA_FINAL_PADRAO = RETA_FINAL[0]
FOTO_FINISH_PADRAO = FOTO_FINISH[0]

# O teto da fila. Numa chuva de rosas, falas atrasadas viram ruído: é melhor
# calar o presente antigo do que narrar o que já passou.
FILA_MAXIMA = 20

_ALIASES = itertools.count(1)
_WINMM = None


def _frases_do_config(valor, padrao: tuple[str, ...]) -> list[str]:
    """A lista de frases do config, limpa; vazia ou ausente usa a do jogo.

    Lista vazia é "usa as frases do jogo" de propósito: um `[]` no config
    não pode deixar a live muda — é o mesmo contrato de `tts.falas`.
    """
    if isinstance(valor, list):
        limpas = [frase.strip() for frase in map(str, valor) if frase.strip()]
        if limpas:
            return limpas
    return list(padrao)


def _vozes_do_config(valor, padrao: str) -> list[str]:
    """A lista de vozes do config, limpa; vazia ou ausente usa a voz de sempre."""
    if isinstance(valor, list):
        limpas = [str(voz).strip() for voz in valor if str(voz).strip()]
        if limpas:
            return limpas
    return [padrao]


def _winmm():
    """O winmm.dll, carregado na primeira fala (nem todo mundo tem Windows)."""
    global _WINMM
    if _WINMM is None:
        import ctypes

        _WINMM = ctypes.WinDLL("winmm")
    return _WINMM


def _motivo_do_erro(codigo: int) -> str:
    import ctypes

    buffer = ctypes.create_unicode_buffer(256)
    _winmm().mciGetErrorStringW(codigo, buffer, 256)
    return buffer.value or f"codigo {codigo}"


def _enviar(comando: str, tamanho_resposta: int = 0) -> str:
    """Manda um comando de texto ao MCI e devolve a resposta (se pedida).

    O MCI é a API de mídia mais antiga do Windows e continua a mais direta
    que toca mp3 sem instalar nada: tudo — abrir, tocar, consultar — é uma
    string de comando com resposta em texto.
    """
    import ctypes

    buffer = (
        ctypes.create_unicode_buffer(tamanho_resposta) if tamanho_resposta else None
    )
    erro = _winmm().mciSendStringW(comando, buffer, tamanho_resposta, None)
    if erro:
        raise OSError(f"MCI: {_motivo_do_erro(erro)} (comando: {comando})")
    return buffer.value if buffer is not None else ""


class Narrador:
    """Fila de falas: gera o áudio, toca e apaga, uma por vez.

    `gerar` e `tocar` são injetáveis para o teste rodar sem internet e sem
    placa de som — o motor de verdade é o edge-tts (voz do tts.py do pixel)
    e o MCI.
    """

    def __init__(
        self,
        tts: TtsConfig | None = None,
        gerar: Callable[[str], str] | None = None,
        tocar: Callable[[str], None] | None = None,
    ):
        cfg = tts or TtsConfig()
        self.ativo = bool(cfg.active)
        self.voz = str(cfg.voz or VOZ_PADRAO)
        self.rate = str(cfg.rate or RATE_PADRAO)
        self.pitch = str(cfg.pitch or PITCH_PADRAO)
        # O oi de quem chegou tem chave própria: em live cheia, dá pra calar
        # só a chegada e deixar a voz para os momentos da corrida.
        self.entrada_ativa = bool(cfg.anunciar_entrada)

        # O rodízio de vozes (`tts.vozes`): com mais de uma, cada fala sai
        # numa voz — a LIVE para de soar como um robô só. A ordem é fixa (e
        # não sorteada): dá para prever, testar e ouvir a fila.
        self.vozes = _vozes_do_config(cfg.vozes, self.voz)
        self._rodizio = itertools.cycle(self.vozes)

        # As frases do jogo vivem em `game/falas.py`; as chaves equivalentes
        # do config (`tts.falas`, `tts.boas_vindas`, `tts.votacao`,
        # `tts.largada`, `tts.vencedor`, `tts.corrida_abertura`,
        # `tts.corrida_disputa`, `tts.reta_final`, `tts.foto_finish`)
        # substituem as listas inteiras para quem quiser improvisar sem mexer
        # no código.
        self.falas = _frases_do_config(cfg.falas, FALAS)
        self.boas_vindas = _frases_do_config(cfg.boas_vindas, BOAS_VINDAS)
        self.votacao = _frases_do_config(cfg.votacao, VOTACAO_ABERTA)
        self.largada = _frases_do_config(cfg.largada, LARGADA)
        self.vencedor = _frases_do_config(cfg.vencedor, VENCEDOR)
        self.corrida_abertura = _frases_do_config(cfg.corrida_abertura, CORRIDA_ABERTURA)
        self.corrida_disputa = _frases_do_config(cfg.corrida_disputa, CORRIDA_DISPUTA)
        self.corrida_placar = _frases_do_config(cfg.corrida_placar, CORRIDA_PLACAR)
        self.reta_final = _frases_do_config(cfg.reta_final, RETA_FINAL)
        self.foto_finish = _frases_do_config(cfg.foto_finish, FOTO_FINISH)

        self._gerar = gerar or self._gerar_edge
        self._tocar = tocar or self._tocar_mci
        self._fila: queue.Queue[str | None] = queue.Queue(maxsize=FILA_MAXIMA)
        self._parar = threading.Event()
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------

    def ligar(self) -> None:
        """Sobe a thread da voz. Idempotente, como o `start` do adapter.

        Desligado no config nem sobe thread: não há o que dizer.
        """
        if not self.ativo:
            return
        if self._thread is not None and self._thread.is_alive():
            return
        self._parar.clear()
        self._thread = threading.Thread(
            target=self._trabalhar, name="narrador", daemon=True
        )
        self._thread.start()

    def parar(self) -> None:
        """Encerra a thread. Uma fala no meio é cortada na hora."""
        self._parar.set()
        try:
            self._fila.put_nowait(None)  # acorda a thread, se ela estiver esperando
        except queue.Full:
            pass

    def pendentes(self) -> int:
        """Quantas falas esperam na fila."""
        return self._fila.qsize()

    # ------------------------------------------------------------------
    # A fala
    # ------------------------------------------------------------------

    def _sorteada(
        self, lista: list[str], padrao: str, valores: dict[str, str], o_que: str
    ) -> str:
        """Uma frase da lista, com os valores preenchidos.

        O sorteio é o que impede a voz de virar disco riscado: com dezenas
        de frases, a mesma fala demora a se repetir e a live soa viva.

        E as frases são editáveis por quem quiser: um `{placeholder}`
        inválido em uma delas não pode deixar a live muda — vira um aviso no
        log e a frase padrão entra no lugar (ver `FALA_PADRAO`).
        """
        modelo = random.choice(lista)
        try:
            return modelo.format(**valores)
        except (KeyError, IndexError, ValueError):
            logger.warning("%s com placeholder inválido: %r", o_que, modelo)
            return padrao.format(**valores)

    @staticmethod
    def _numero(valor) -> str:
        """O número como a voz deve ler: "3", e não "3.0" nem "{...}"."""
        try:
            return str(int(valor))
        except (TypeError, ValueError):
            return str(valor or "")

    @staticmethod
    def _nome_falado(valor: str) -> str:
        """Nome próprio como a voz lê melhor: "RELÂMPAGO" vira "Relâmpago".

        Os cavalos têm nome em CAIXA ALTA no telão (onde ele é título); numa
        frase falada, caixa alta soa como grito — e nome curtinho todo em
        maiúsculas corre o risco de sair letra por letra.
        """
        return (valor or "").strip().capitalize()

    def texto_do_presente(
        self, nome: str, quantidade: int, presente: str, cavalo: str
    ) -> str:
        """A fala do presente, sorteada entre as frases do jogo.

        O arroba não se pronuncia ("@ana" vira "ana").
        """
        return self._sorteada(
            self.falas,
            FALA_PADRAO,
            {
                "nome": (nome or "").strip().lstrip("@"),
                "quantidade": f"{int(quantidade)}x " if int(quantidade) > 1 else "",
                "presente": presente or "presente",
                "cavalo": self._nome_falado(cavalo),
            },
            "Fala",
        )

    def texto_de_entrada(self, nome: str) -> str:
        """A fala de quem acabou de chegar, sorteada entre as do jogo.

        Sem `{quantidade}` nem `{presente}`: a chegada não tem prêmio, tem
        só um nome — e é por ele que a voz chama.
        """
        return self._sorteada(
            self.boas_vindas,
            BOAS_VINDAS_PADRAO,
            {"nome": (nome or "").strip().lstrip("@")},
            "Boas-vindas",
        )

    def texto_da_votacao(self, numero: int) -> str:
        """O anúncio de que a votação da corrida abriu."""
        return self._sorteada(
            self.votacao,
            VOTACAO_PADRAO,
            {"numero": self._numero(numero)},
            "Anúncio de votação",
        )

    def texto_da_largada(self, numero: int) -> str:
        """O anúncio da largada: a corrida começou AGORA."""
        return self._sorteada(
            self.largada,
            LARGADA_PADRAO,
            {"numero": self._numero(numero)},
            "Anúncio de largada",
        )

    def texto_do_vencedor(self, numero: int, nome: str) -> str:
        """O anúncio do cavalo campeão. `{nome}` aqui é o nome do CAVALO."""
        return self._sorteada(
            self.vencedor,
            VENCEDOR_PADRAO,
            {"numero": self._numero(numero), "nome": self._nome_falado(nome)},
            "Anúncio de vencedor",
        )

    # ------------------------------------------------------------------
    # A locução ao vivo (durante a corrida)
    #
    # Quem decide a HORA de cada chamada é o director (MARCOS_LOCUCAO —
    # abertura, disputa e reta final por distância do líder; a foto-finish
    # pela margem da chegada). Aqui é só o texto — de propósito: a mesma
    # fila única do narrador serve o presente, a chegada e a corrida, e o
    # disparo mora no mesmo lugar que já conhece o estado do jogo.
    # ------------------------------------------------------------------

    def _texto_da_dupla(
        self, lista: list[str], padrao: str, lider: str, segundo: str, o_que: str
    ) -> str:
        """Uma chamada da locução com a dupla da frente preenchida.

        `{lider}` é quem puxa e `{segundo}` quem vem na cola — os dois
        entram sempre, porque a tensão da fala está justamente no duelo.
        """
        return self._sorteada(
            lista,
            padrao,
            {
                "lider": self._nome_falado(lider),
                "segundo": self._nome_falado(segundo),
            },
            o_que,
        )

    def texto_da_abertura(self, lider: str, segundo: str) -> str:
        """A chamada dos primeiros metros: quem abriu na ponta."""
        return self._texto_da_dupla(
            self.corrida_abertura,
            ABERTURA_PADRAO,
            lider,
            segundo,
            "Locução de abertura",
        )

    def texto_da_disputa(self, lider: str, segundo: str) -> str:
        """A chamada do meio da corrida: a briga pela ponta."""
        return self._texto_da_dupla(
            self.corrida_disputa,
            DISPUTA_PADRAO,
            lider,
            segundo,
            "Locução de disputa",
        )

    def texto_do_placar(self, lider: str, segundo: str, terceiro: str) -> str:
        """A chamada de POSIÇÕES: o trio da frente, no estilo do turfe.

        É a fala que preenche os vãos entre um marco e outro — sem ela, a
        corrida tinha buracos de ~10s de silêncio no meio da prova.
        """
        return self._sorteada(
            self.corrida_placar,
            PLACAR_PADRAO,
            {
                "lider": self._nome_falado(lider),
                "segundo": self._nome_falado(segundo),
                "terceiro": self._nome_falado(terceiro),
            },
            "Locução de placar",
        )

    def texto_da_reta_final(self, lider: str, segundo: str) -> str:
        """A chamada dos metros finais: a decisão se aproximando."""
        return self._texto_da_dupla(
            self.reta_final,
            RETA_FINAL_PADRAO,
            lider,
            segundo,
            "Locução de reta final",
        )

    def texto_da_foto_finish(self, vencedor: str, segundo: str) -> str:
        """A exclamação da chegada apertada (menos de 50ms de diferença).

        Usa o mesmo `{segundo}` da locução, mas o vencedor entra como
        `{vencedor}`: a frase da foto-finish fala de quem GANHOU, não de
        quem liderava no caminho.
        """
        return self._sorteada(
            self.foto_finish,
            FOTO_FINISH_PADRAO,
            {
                "vencedor": self._nome_falado(vencedor),
                "segundo": self._nome_falado(segundo),
            },
            "Locução de foto-finish",
        )

    def anunciar_presente(
        self, nome: str, quantidade: int, presente: str, cavalo: str
    ) -> str | None:
        """Enfileira a fala de um presente. Devolve o texto, ou None se calou.

        Nunca bloqueia: quem chama é o loop de eventos da live, e um presente
        não pode esperar a voz do anterior para ser creditado.
        """
        if not self.ativo:
            return None

        return self._enfileirar(
            self.texto_do_presente(nome, quantidade, presente, cavalo), nome
        )

    def anunciar_entrada(self, nome: str) -> str | None:
        """Enfileira o oi de quem chegou. Devolve o texto, ou None se calou.

        Mesma fila e mesmo ciclo do presente — a diferença é só a lista de
        onde a frase sai. Sem valor mínimo: chegar não rende nada, e o oi é
        justamente para quem ainda não fez nada.
        """
        if not self.ativo or not self.entrada_ativa:
            return None

        return self._enfileirar(self.texto_de_entrada(nome), nome)

    def anunciar_votacao(self, numero: int) -> str | None:
        """Enfileira o anúncio de votação aberta da corrida `numero`."""
        if not self.ativo:
            return None

        return self._enfileirar(
            self.texto_da_votacao(numero), f"a votação da corrida {self._numero(numero)}"
        )

    def anunciar_largada(self, numero: int) -> str | None:
        """Enfileira o anúncio da largada da corrida `numero`."""
        if not self.ativo:
            return None

        return self._enfileirar(
            self.texto_da_largada(numero), f"a largada da corrida {self._numero(numero)}"
        )

    def anunciar_vencedor(self, numero: int, nome: str) -> str | None:
        """Enfileira o anúncio do campeão da corrida."""
        if not self.ativo:
            return None

        return self._enfileirar(
            self.texto_do_vencedor(numero, nome),
            f"o vencedor da corrida {self._numero(numero)}",
        )

    def anunciar_abertura(self, lider: str, segundo: str) -> str | None:
        """Enfileira a chamada de abertura: `lider` puxa, `segundo` na cola."""
        if not self.ativo:
            return None

        return self._enfileirar(
            self.texto_da_abertura(lider, segundo), f"a abertura ({lider} na frente)"
        )

    def anunciar_disputa(self, lider: str, segundo: str) -> str | None:
        """Enfileira a chamada do meio da corrida."""
        if not self.ativo:
            return None

        return self._enfileirar(
            self.texto_da_disputa(lider, segundo), f"a disputa ({lider} na frente)"
        )

    def anunciar_placar(self, lider: str, segundo: str, terceiro: str) -> str | None:
        """Enfileira a chamada de posições (o trio da frente)."""
        if not self.ativo:
            return None

        return self._enfileirar(
            self.texto_do_placar(lider, segundo, terceiro),
            f"o placar ({lider}, {segundo}, {terceiro})",
        )

    def anunciar_reta_final(self, lider: str, segundo: str) -> str | None:
        """Enfileira a chamada da reta final."""
        if not self.ativo:
            return None

        return self._enfileirar(
            self.texto_da_reta_final(lider, segundo),
            f"a reta final ({lider} na frente)",
        )

    def anunciar_foto_finish(self, vencedor: str, segundo: str) -> str | None:
        """Enfileira a exclamação da chegada decidida no detalhe."""
        if not self.ativo:
            return None

        return self._enfileirar(
            self.texto_da_foto_finish(vencedor, segundo),
            f"a foto-finish ({vencedor} na frente de {segundo})",
        )

    def _enfileirar(self, texto: str, nome: str) -> str:
        """Põe na fila sem bloquear. Cheia, a fala mais antiga sai.

        Num pico, narrar o que está acontecendo agora vale mais do que o
        atrasado — e o aviso no log diz quem ficou sem voz.
        """
        try:
            self._fila.put_nowait(texto)
        except queue.Full:
            try:
                self._fila.get_nowait()
                self._fila.put_nowait(texto)
            except (queue.Empty, queue.Full):
                logger.warning("Fila de falas cheia; %s ficou sem voz", nome)
        return texto

    # ------------------------------------------------------------------
    # O trabalho da thread
    # ------------------------------------------------------------------

    def _trabalhar(self) -> None:
        while not self._parar.is_set():
            try:
                texto = self._fila.get(timeout=0.5)
            except queue.Empty:
                continue
            if texto is None:
                return

            caminho: str | None = None
            try:
                caminho = self._gerar(texto)
                self._tocar(caminho)
            except Exception as erro:
                # Áudio é enfeite: um tropeço aqui (internet, codec, placa de
                # som) não pode nem derrubar a thread nem parar o jogo.
                logger.warning("Não consegui falar %r: %s", texto, erro)
            finally:
                if caminho:
                    self._apagar(caminho)

    # ------------------------------------------------------------------
    # Motores de verdade: edge-tts gera, MCI toca
    # ------------------------------------------------------------------

    def _proxima_voz(self) -> str:
        """A voz da próxima fala: o próximo nome do rodízio."""
        return next(self._rodizio)

    def _gerar_edge(self, texto: str) -> str:
        """Gera o mp3 da fala e devolve o caminho."""
        import asyncio

        import edge_tts  # import tardio: sem a lib o jogo só fica mudo

        descritor, caminho = tempfile.mkstemp(prefix="horserace_tts_", suffix=".mp3")
        os.close(descritor)

        async def salvar(voz_nome: str) -> None:
            voz = edge_tts.Communicate(
                text=texto, voice=voz_nome, rate=self.rate, pitch=self.pitch
            )
            await voz.save(caminho)

        escolhida = self._proxima_voz()
        try:
            asyncio.run(salvar(escolhida))
        except Exception:
            # Um nome de voz errado no config (ou uma voz aposentada pelo
            # serviço, como aconteceu com as pt-BR antigas) não pode deixar a
            # LIVE muda: a fala sai na voz padrão, que é a única que a gente
            # sabe que existe.
            if escolhida == VOZ_PADRAO:
                raise
            logger.warning("A voz %s falhou; falando com %s", escolhida, VOZ_PADRAO)
            asyncio.run(salvar(VOZ_PADRAO))
        return caminho

    def _tocar_mci(self, caminho: str) -> None:
        """Toca o mp3 do início ao fim; só volta quando acabar.

        `play` sem `wait` + `status mode` em laço, em vez do `wait`
        bloqueante: assim uma fala no meio pode ser cortada quando o jogo
        está encerrando, em vez de segurar o desligamento.
        """
        alias = f"horsetts{next(_ALIASES)}"
        _enviar(f'open "{caminho}" type mpegvideo alias {alias}')
        try:
            _enviar(f"play {alias}")
            limite = time.monotonic() + self._duracao(alias) + 2.0
            while time.monotonic() < limite:
                if self._parar.is_set():
                    _enviar(f"stop {alias}")
                    return
                if _enviar(f"status {alias} mode", 64) == "stopped":
                    return
                time.sleep(0.05)
            logger.warning("A fala passou do tempo do áudio: %s", caminho)
        finally:
            _enviar(f"close {alias}")

    @staticmethod
    def _duracao(alias: str) -> float:
        """Duração do áudio em segundos; 10s de teto se o MCI não souber."""
        try:
            milissegundos = int(_enviar(f"status {alias} length", 64) or 0)
        except (OSError, ValueError):
            milissegundos = 0
        return milissegundos / 1000.0 if milissegundos > 0 else 10.0

    @staticmethod
    def _apagar(caminho: str) -> None:
        """Tocou, apagou.

        O Windows pode segurar o arquivo por um instante depois do close
        (antivírus, indexador); algumas tentativas e só então um aviso.
        """
        for _ in range(10):
            try:
                os.remove(caminho)
                return
            except FileNotFoundError:
                return
            except OSError:
                time.sleep(0.05)
        logger.warning("Não consegui apagar o áudio: %s", caminho)
