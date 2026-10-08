import pytest
import time

def test_security_sanitization():
    from backend.security import SecurityManager
    
    sec = SecurityManager()
    assert sec.sanitize_name("<script>alert(1)</script>Leo") == "alert(1)Leo"
    assert sec.sanitize_name("  João  ") == "João"
    assert sec.sanitize_name("A" * 100) == "A" * 24  # Limita tamanho máximo

def test_security_rate_limiting():
    from backend.security import SecurityManager
    
    sec = SecurityManager(rate_limit_per_second=2.0)
    user = "spammer_user"
    
    # Primeiro e segundo comandos no mesmo segundo: permitidos
    assert sec.is_rate_limited(user) is False
    assert sec.is_rate_limited(user) is False
    
    # Terceiro comando no mesmo instante: bloqueado
    assert sec.is_rate_limited(user) is True

def test_security_cooldown():
    from backend.security import SecurityManager
    
    sec = SecurityManager()
    user = "viewer_1"
    
    # Primeira ação com cooldown de 5 segundos
    assert sec.check_and_set_cooldown(user, "horse_vote", cooldown_seconds=0.1) is True
    # Imediatamente após: em cooldown
    assert sec.check_and_set_cooldown(user, "horse_vote", cooldown_seconds=0.1) is False
    
    # Espera cooldown passar
    time.sleep(0.12)
    assert sec.check_and_set_cooldown(user, "horse_vote", cooldown_seconds=0.1) is True
