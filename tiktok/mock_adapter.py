import asyncio
from typing import Dict, Any, Callable, Awaitable, Optional
from tiktok.parser import CommandParser
from backend.security import SecurityManager

class MockTikTokAdapter:
    """
    Emulador para o Test Mode. Permite simular comentários, presentes,
    likes, shares e rajadas de torcida em tempo real.
    """
    def __init__(
        self,
        director,
        security_manager: Optional[SecurityManager] = None
    ):
        self.director = director
        self.security = security_manager or SecurityManager()
        self.parser = CommandParser()

    async def inject_comment(self, username: str, display_name: str, text: str) -> Dict[str, Any]:
        clean_user = self.security.sanitize_name(username)
        clean_name = self.security.sanitize_name(display_name)
        
        if self.security.is_rate_limited(clean_user):
            return {"status": "rate_limited", "message": "Comando bloqueado por taxa de disparo excessiva."}
            
        parsed = self.parser.parse_comment(text)
        if not parsed:
            return {"status": "ignored", "message": "Comentário não reconhecido como comando."}
            
        action = parsed["action"]
        if action == "CHOOSE_HORSE":
            # Cooldown de troca de escolha
            if not self.security.check_and_set_cooldown(clean_user, "choose", cooldown_seconds=1.5):
                return {"status": "cooldown", "message": "Aguarde antes de mudar de cavalo novamente."}
                
            success = await self.director.handle_viewer_choice(
                clean_user, clean_name, parsed["horse_id"]
            )
            return {"status": "ok" if success else "rejected", "action": action, "horse_id": parsed["horse_id"]}
            
        elif action == "CHEER":
            await self.director.handle_cheer_command(clean_user, clean_name)
            return {"status": "ok", "action": action}

        return {"status": "unhandled"}

    async def inject_gift(self, username: str, display_name: str, gift_name: str, count: int = 1) -> Dict[str, Any]:
        clean_user = self.security.sanitize_name(username)
        clean_name = self.security.sanitize_name(display_name)

        await self.director.handle_viewer_gift(
            clean_user, clean_name, gift_name, count
        )
        return {"status": "ok", "action": "GIFT", "gift_name": gift_name, "count": count}

    async def inject_join(self, username: str, display_name: str) -> Dict[str, Any]:
        clean_user = self.security.sanitize_name(username)
        clean_name = self.security.sanitize_name(display_name)
        await self.director.handle_viewer_join(clean_user, clean_name)
        return {"status": "ok", "action": "JOIN", "user": clean_user, "display_name": clean_name}

    async def inject_follow(self, username: str, display_name: str) -> Dict[str, Any]:
        clean_user = self.security.sanitize_name(username)
        clean_name = self.security.sanitize_name(display_name)
        await self.director.handle_viewer_follow(clean_user, clean_name)
        return {"status": "ok", "action": "FOLLOW", "user": clean_user, "display_name": clean_name}

    async def inject_like(self, username: str, display_name: str, count: int = 5) -> Dict[str, Any]:
        clean_user = self.security.sanitize_name(username)
        clean_name = self.security.sanitize_name(display_name)

        await self.director.handle_viewer_like(clean_user, clean_name, count)
        return {"status": "ok", "action": "LIKE", "count": count}

    async def simulate_crowd_burst(self, count: int = 20) -> Dict[str, Any]:
        """
        Simula múltiplos usuários comentando e escolhendo cavalos ao mesmo tempo.
        """
        import random
        names = ["Marcos", "Julia", "Lucas", "Beatriz", "Gabriel", "Camila", "Rafael", "Larissa", "Felipe", "Mariana"]
        for i in range(count):
            name = f"{random.choice(names)}_{random.randint(10, 99)}"
            hid = random.randint(1, 8)
            await self.director.handle_viewer_choice(
                name.lower(), name, hid
            )
        return {"status": "ok", "simulated_viewers": count}
