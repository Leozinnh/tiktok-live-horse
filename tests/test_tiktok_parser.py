import pytest

def test_command_parser_choices():
    from tiktok.parser import CommandParser
    
    parser = CommandParser()
    
    # Escolha por número
    assert parser.parse_comment("1") == {"action": "CHOOSE_HORSE", "horse_id": 1}
    assert parser.parse_comment(" 8 ") == {"action": "CHOOSE_HORSE", "horse_id": 8}
    assert parser.parse_comment("9") is None  # Apenas cavalos 1..8
    
    # Escolha por nome do cavalo (sem acento, maiúsculo/minúsculo)
    assert parser.parse_comment("relampago") == {"action": "CHOOSE_HORSE", "horse_id": 1}
    assert parser.parse_comment("RELÂMPAGO") == {"action": "CHOOSE_HORSE", "horse_id": 1}
    assert parser.parse_comment("trovao") == {"action": "CHOOSE_HORSE", "horse_id": 2}
    assert parser.parse_comment("Trovão") == {"action": "CHOOSE_HORSE", "horse_id": 2}
    assert parser.parse_comment("furacao") == {"action": "CHOOSE_HORSE", "horse_id": 3}
    assert parser.parse_comment("fantasma") == {"action": "CHOOSE_HORSE", "horse_id": 8}
    
    # Comandos prefixados com /cavalo
    assert parser.parse_comment("/cavalo 4") == {"action": "CHOOSE_HORSE", "horse_id": 4}
    assert parser.parse_comment("/cavalo raio") == {"action": "CHOOSE_HORSE", "horse_id": 4}

    # Variações reais de chat do TikTok
    assert parser.parse_comment("#1") == {"action": "CHOOSE_HORSE", "horse_id": 1}
    assert parser.parse_comment("# 2") == {"action": "CHOOSE_HORSE", "horse_id": 2}
    assert parser.parse_comment("111") == {"action": "CHOOSE_HORSE", "horse_id": 1}
    assert parser.parse_comment("vai 1") == {"action": "CHOOSE_HORSE", "horse_id": 1}
    assert parser.parse_comment("bora 3!") == {"action": "CHOOSE_HORSE", "horse_id": 3}
    assert parser.parse_comment("relampagooo") == {"action": "CHOOSE_HORSE", "horse_id": 1}
    assert parser.parse_comment("vai trovaooo") == {"action": "CHOOSE_HORSE", "horse_id": 2}
    assert parser.parse_comment("cavalo 5") == {"action": "CHOOSE_HORSE", "horse_id": 5}

def test_voto_por_nome_sobrevive_a_texto_corrompido():
    """O nome do cavalo vale mesmo com o texto quebrado no caminho.

    Na live apareceu gente digitando "relâmpago" e ficando sem voto: o
    comentário chega do TikTok com o acento corrompido ("relÃ¢mpago") ou com
    invisíveis no meio da palavra. Tirando do texto o que não é letra,
    número ou espaço, o nome digitado volta a aparecer inteiro.
    """
    from tiktok.parser import CommandParser

    parser = CommandParser()

    # Acento corrompido no caminho (UTF-8 lido como latin-1)
    assert parser.parse_comment("relÃ¢mpago") == {"action": "CHOOSE_HORSE", "horse_id": 1}
    assert parser.parse_comment("TrovÃ£o") == {"action": "CHOOSE_HORSE", "horse_id": 2}
    # Invisível no meio da palavra (o TikTok enfia em comentário repetido)
    invisivel = "rel" + chr(0x200B) + "âmpago"  # ZWSP no meio da palavra
    assert parser.parse_comment(invisivel) == {"action": "CHOOSE_HORSE", "horse_id": 1}
    # Emoji colado nas letras
    assert parser.parse_comment("relâmpago🔥") == {"action": "CHOOSE_HORSE", "horse_id": 1}


def test_palpite_de_voto_para_o_log():
    """O que ainda escapar do parser vira palpite no LOG, nunca voto.

    É a sonda para a próxima quebra: se alguém digitar o nome de um jeito
    que a gente ainda não previu, o console mostra o comentário cru e o
    nome mais parecido — sem inventar voto que ninguém deu.
    """
    from tiktok.parser import CommandParser

    parser = CommandParser()
    assert parser.parece_voto("relanpago") == "relampago"  # letra trocada
    assert parser.parece_voto("relampag") == "relampago"  # letra faltando
    assert parser.parece_voto("bom dia galera, tudo bem?") is None


def test_command_parser_cheers_and_fun_commands():
    from tiktok.parser import CommandParser
    
    parser = CommandParser()
    assert parser.parse_comment("/turbo") == {"action": "CHEER", "command": "turbo"}
    assert parser.parse_comment("bora bora bora") == {"action": "CHEER", "command": "cheer"}
    assert parser.parse_comment("forca torcida!") == {"action": "CHEER", "command": "cheer"}

def test_command_parser_gifts():
    from tiktok.parser import CommandParser
    
    parser = CommandParser()
    g1 = parser.parse_gift("Rose", repeat_count=1)
    assert g1["action"] == "GIFT"
    assert g1["gift_name"] == "Rose"
    assert g1["count"] == 1
    
    g2 = parser.parse_gift("Leon", repeat_count=2)
    assert g2["action"] == "GIFT"
    assert g2["gift_name"] == "Leon"
    assert g2["count"] == 2
