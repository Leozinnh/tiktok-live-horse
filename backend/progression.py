import math

TITLES = [
    (1, "Iniciante das Pistas"),
    (5, "Fã de Hipódromo"),
    (10, "Torcedor Fervoroso"),
    (15, "Estrategista de Raia"),
    (20, "Veterano das Corridas"),
    (30, "Mestre dos Cascos"),
    (40, "Encantador de Cavalos"),
    (50, "Lenda do Turfe"),
    (75, "Campeão Supremo"),
    (100, "Deus das Corridas"),
]

def calculate_level(xp: int) -> int:
    """
    Calcula o nível com base no XP total acumulado.
    Fórmula equilibrada: Nível 1 começa em 0 XP.
    XP necessário para nível N: 100 * (N - 1)^1.35
    """
    if xp <= 0:
        return 1
    
    # Inverso da fórmula: (xp / 100)^(1 / 1.35) + 1
    level = math.floor((xp / 100.0) ** (1.0 / 1.35)) + 1
    return max(1, int(level))

def xp_for_level(level: int) -> int:
    """
    Retorna o XP total mínimo necessário para alcançar determinado nível.
    """
    if level <= 1:
        return 0
    return int(100.0 * ((level - 1) ** 1.35))

def get_title_for_level(level: int) -> str:
    """
    Retorna o título honorífico apropriado para o nível do jogador.
    """
    current_title = TITLES[0][1]
    for min_lvl, title in TITLES:
        if level >= min_lvl:
            current_title = title
        else:
            break
    return current_title
