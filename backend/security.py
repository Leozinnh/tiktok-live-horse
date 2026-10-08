import time
import re
from typing import Dict, Tuple

class SecurityManager:
    def __init__(self, rate_limit_per_second: float = 3.0, max_name_len: int = 24):
        self.rate_limit_per_second = rate_limit_per_second
        self.max_name_len = max_name_len
        # user -> list of timestamps
        self._user_events: Dict[str, list[float]] = {}
        # (user, action_name) -> last_time
        self._cooldowns: Dict[Tuple[str, str], float] = {}

    def sanitize_name(self, raw_name: str) -> str:
        """
        Remove tags HTML, caracteres perigosos e limita comprimento.
        """
        if not raw_name:
            return "Anônimo"
        # Remove tags html
        clean = re.sub(r"<[^>]*>", "", raw_name)
        # Remove quebras de linha e caracteres de controle
        clean = re.sub(r"[\r\n\t]", "", clean)
        clean = clean.strip()
        if not clean:
            clean = "Anônimo"
        return clean[: self.max_name_len]

    def is_rate_limited(self, user_id: str) -> bool:
        """
        Verifica se o usuário excedeu o rate limit (janela deslizante de 1 segundo).
        """
        now = time.time()
        user_key = user_id.lower()
        timestamps = self._user_events.get(user_key, [])
        
        # Filtra timestamps dos últimos 1.0 segundos
        cutoff = now - 1.0
        timestamps = [t for t in timestamps if t > cutoff]
        
        if len(timestamps) >= self.rate_limit_per_second:
            self._user_events[user_key] = timestamps
            return True
            
        timestamps.append(now)
        self._user_events[user_key] = timestamps
        return False

    def check_and_set_cooldown(self, user_id: str, action: str, cooldown_seconds: float) -> bool:
        """
        Retorna True se a ação foi permitida e reseta o timer.
        Retorna False se o usuário ainda está sob cooldown para essa ação.
        """
        now = time.time()
        key = (user_id.lower(), action)
        last_time = self._cooldowns.get(key, 0.0)
        
        if now - last_time < cooldown_seconds:
            return False
            
        self._cooldowns[key] = now
        return True

    def cleanup_old_entries(self) -> None:
        """
        Limpa registros com mais de 60 segundos para evitar memory leak em transmissões longas.
        """
        now = time.time()
        cutoff = now - 60.0
        
        # Limpa rate limiters
        keys_to_del = []
        for k, v in self._user_events.items():
            valid = [t for t in v if t > cutoff]
            if valid:
                self._user_events[k] = valid
            else:
                keys_to_del.append(k)
        for k in keys_to_del:
            del self._user_events[k]
            
        # Limpa cooldowns
        cd_to_del = [k for k, t in self._cooldowns.items() if t < cutoff]
        for k in cd_to_del:
            del self._cooldowns[k]
