import asyncio
import logging
from typing import Optional
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, GiftEvent, LikeEvent
from tiktok.parser import CommandParser
from backend.security import SecurityManager

logger = logging.getLogger(__name__)

class TikTokLiveAdapter:
    def __init__(self, tiktok_username: str, director, security_manager: Optional[SecurityManager] = None):
        self.tiktok_username = tiktok_username
        self.director = director
        self.security = security_manager or SecurityManager()
        self.parser = CommandParser()
        self.client: Optional[TikTokLiveClient] = None
        self.is_running: bool = False
        self._reconnect_delay = 5.0

    async def start(self) -> None:
        self.is_running = True
        while self.is_running:
            try:
                logger.info(f"Conectando ao TikTok LIVE do usuário @{self.tiktok_username}...")
                self.client = TikTokLiveClient(unique_id=f"@{self.tiktok_username}")
                
                @self.client.on(CommentEvent)
                async def on_comment(event: CommentEvent):
                    user = event.user.unique_id
                    nick = event.user.nickname or user
                    parsed = self.parser.parse_comment(event.comment)
                    if parsed:
                        if parsed["action"] == "CHOOSE_HORSE":
                            if not self.security.is_rate_limited(user):
                                await self.director.handle_viewer_choice(user, nick, parsed["horse_id"])
                        elif parsed["action"] == "CHEER":
                            await self.director.handle_cheer_command(user, nick)

                @self.client.on(GiftEvent)
                async def on_gift(event: GiftEvent):
                    # Ignora se for sequência não finalizada
                    if event.gift.streakable and not event.gift.streaking:
                        return
                    user = event.user.unique_id
                    nick = event.user.nickname or user
                    g_name = event.gift.name
                    count = event.gift.count or 1
                    await self.director.handle_viewer_gift(user, nick, g_name, count)

                await self.client.start()
                
            except Exception as e:
                logger.warning(f"Conexão com TikTok interrompida ({e}). Reconectando em {self._reconnect_delay}s...")
                await asyncio.sleep(self._reconnect_delay)

    def stop(self) -> None:
        self.is_running = False
        if self.client:
            try:
                self.client.stop()
            except Exception:
                pass
