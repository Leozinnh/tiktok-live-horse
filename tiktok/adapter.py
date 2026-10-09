"""Conexão com a LIVE real do TikTok via TikTokLive (v7).

As armadilhas resolvidas neste arquivo foram validadas no projeto
`tiktok-live-pixel`, portado de um jogo que já rodava em LIVE de verdade:

1. `client.start()` NÃO bloqueia — retorna a Task na hora. Num loop de
   reconexão isso vira uma rajada de conexões e estoura o rate limit do
   servidor de assinatura (Euler Stream) com HTTP 429. Use `client.connect()`,
   que só retorna quando o websocket fecha.
2. O cliente não é reutilizável: depois que cai, cada tentativa monta um
   cliente NOVO.
3. `client.close()` / `close_client=True` fazem `run_until_complete` num loop
   já rodando → `RuntimeError` que mata a task. Só usar `disconnect()`.
4. No v7 o comentário chega em `event.content` (não `event.comment`), o
   streak de presente em `event.streaking` / `event.repeat_count`, e
   `event.gift` só resolve com `fetch_gift_info=True`.
"""
import asyncio
import logging
import random
from typing import Optional

from TikTokLive import TikTokLiveClient
from TikTokLive.client.errors import UserNotFoundError, UserOfflineError, WebcastBlockedError
from TikTokLive.events import CommentEvent, GiftEvent

from tiktok.parser import CommandParser
from backend.security import SecurityManager

logger = logging.getLogger(__name__)

BACKOFF_INICIAL = 5.0
BACKOFF_MAX = 60.0
DORMIR_OFFLINE = 30.0
DORMIR_BLOQUEADO = 60.0


class TikTokLiveAdapter:
    def __init__(self, tiktok_username: str, director, security_manager: Optional[SecurityManager] = None):
        self.tiktok_username = tiktok_username
        self.director = director
        self.security = security_manager or SecurityManager()
        self.parser = CommandParser()
        self.client: Optional[TikTokLiveClient] = None
        self.is_running: bool = False

    async def start(self) -> None:
        """Conecta e reconecta para sempre, com backoff, até stop()."""
        self.is_running = True
        backoff = BACKOFF_INICIAL

        while self.is_running:
            client = None
            try:
                logger.info(f"Conectando ao TikTok LIVE do usuário @{self.tiktok_username}...")
                # Cliente NOVO a cada tentativa: um cliente que caiu não volta a funcionar.
                client = TikTokLiveClient(unique_id=f"@{self.tiktok_username}")
                self.client = client

                @client.on(CommentEvent)
                async def on_comment(event: CommentEvent):
                    user, nick = self._identidade(event)
                    if self.security.is_rate_limited(user):
                        return
                    text = getattr(event, "content", None) or getattr(event, "comment", None) or ""
                    parsed = self.parser.parse_comment(text)
                    if not parsed:
                        return
                    if parsed["action"] == "CHOOSE_HORSE":
                        # Cooldown de troca de escolha (mesma regra do mock_adapter)
                        if not self.security.check_and_set_cooldown(user, "choose", cooldown_seconds=1.5):
                            return
                        await self.director.handle_viewer_choice(user, nick, parsed["horse_id"])
                    elif parsed["action"] == "CHEER":
                        await self.director.handle_cheer_command(user, nick)

                @client.on(GiftEvent)
                async def on_gift(event: GiftEvent):
                    gift = event.gift
                    if gift is None:
                        # Presente não resolvido (fetch_gift_info não achou o catálogo).
                        return
                    if event.streaking:
                        # No meio de um streak: só o evento final traz o repeat_count cheio.
                        return
                    user, nick = self._identidade(event)
                    count = max(1, int(event.repeat_count or 1))
                    await self.director.handle_viewer_gift(user, nick, gift.name, count)

                # connect() só retorna quando o websocket fecha.
                # NÃO trocar por start(): ele retorna imediatamente e o while dispara
                # conexões em rajada, estourando o rate limit do Euler Stream (HTTP 429).
                await client.connect(fetch_room_info=False, fetch_gift_info=True, fetch_live_check=True)
                backoff = BACKOFF_INICIAL

            except UserNotFoundError:
                # @ errado: reconectar não conserta; insistir só gasta cota do servidor de assinatura.
                logger.error(f"Não existe usuário @{self.tiktok_username} no TikTok. Confira o nome (sem @).")
                self.is_running = False
                return

            except UserOfflineError:
                logger.info(f"A LIVE de @{self.tiktok_username} está offline. Aguardando o início...")
                await self._descartar(client)
                await self._dormir(DORMIR_OFFLINE)
                continue

            except Exception as e:
                if "already running" in str(e):
                    # Cancelamento (Ctrl+C/shutdown): a biblioteca tentou `run_until_complete`
                    # num loop em execução. Não há o que reconectar — encerra limpo.
                    logger.info("Desconexão forçada (shutdown). Encerrando reconexão do TikTok.")
                    self.is_running = False
                    return
                if isinstance(e, WebcastBlockedError):
                    logger.warning(f"O Webcast bloqueou a conexão ({e}). Aguardando {DORMIR_BLOQUEADO:.0f}s...")
                    await self._descartar(client)
                    await self._dormir(DORMIR_BLOQUEADO)
                    continue
                espera = self._espera(backoff)
                logger.warning(f"Conexão com TikTok interrompida ({e}). Reconectando em {espera:.0f}s...")
                await self._descartar(client)
                await self._dormir(espera)
                backoff = min(BACKOFF_MAX, backoff * 2)
                continue

            # Só chega aqui quando a conexão caiu com o websocket fechando normalmente.
            logger.warning("Conexão com TikTok encerrada pelo servidor.")
            await self._descartar(client)
            if not self.is_running:
                break
            espera = self._espera(backoff)
            await self._dormir(espera)
            backoff = min(BACKOFF_MAX, backoff * 2)

    def _identidade(self, event) -> tuple[str, str]:
        """(username, display_name) sanitizados. `user` pode vir None em eventos de like."""
        user_obj = getattr(event, "user", None)
        raw_user = getattr(user_obj, "unique_id", None) or getattr(user_obj, "display_id", None) or ""
        raw_nick = getattr(user_obj, "nickname", None) or raw_user
        return self.security.sanitize_name(raw_user), self.security.sanitize_name(raw_nick)

    @staticmethod
    def _espera(backoff: float) -> float:
        """Backoff com jitter: sem ele, todos os clientes voltam no mesmo instante."""
        return backoff * (0.5 + random.random())

    async def _descartar(self, client: Optional[TikTokLiveClient]) -> None:
        """Só `disconnect()`: `close()` faria `run_until_complete` num loop já rodando → RuntimeError."""
        if client is None:
            return
        try:
            await client.disconnect()
        except Exception:
            logger.debug("Falha ao desconectar o cliente TikTok", exc_info=True)

    async def _dormir(self, segundos: float) -> None:
        """Dorme em fatias para que stop() responda rápido."""
        fatia = 0.25
        restante = max(0.0, segundos)
        while restante > 0 and self.is_running:
            await asyncio.sleep(min(fatia, restante))
            restante -= fatia

    def stop(self) -> None:
        """Interrompe o ciclo de reconexão (idempotente)."""
        self.is_running = False
