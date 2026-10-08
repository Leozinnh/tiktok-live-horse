import re
import unicodedata
from typing import Optional, Dict, Any

def normalize_text(text: str) -> str:
    """
    Remove acentuação, caracteres especiais e converte para minúsculas.
    Ex: 'RELÂMPAGO' -> 'relampago', 'Trovão' -> 'trovao'
    """
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    cleaned = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return cleaned.strip().lower()

HORSE_NAME_MAP = {
    "relampago": 1,
    "trovao": 2,
    "furacao": 3,
    "raio": 4,
    "pantera": 5,
    "tita": 6,
    "titan": 6,
    "nevasca": 7,
    "fantasma": 8,
}

class CommandParser:
    def __init__(self, valid_horse_ids: Optional[list[int]] = None):
        self.valid_horse_ids = valid_horse_ids or list(range(1, 9))

    def parse_comment(self, comment_text: str) -> Optional[Dict[str, Any]]:
        norm = normalize_text(comment_text)
        if not norm:
            return None

        # 1. Checa escolha direta por número (ex: "1", " 3 ", "8")
        if re.fullmatch(r"[1-8]", norm):
            hid = int(norm)
            if hid in self.valid_horse_ids:
                return {"action": "CHOOSE_HORSE", "horse_id": hid}

        # 2. Checa comando /cavalo <id ou nome>
        cavalo_match = re.search(r"/(?:cavalo|horse)\s+([a-z0-9]+)", norm)
        if cavalo_match:
            param = cavalo_match.group(1)
            if param.isdigit():
                hid = int(param)
                if hid in self.valid_horse_ids:
                    return {"action": "CHOOSE_HORSE", "horse_id": hid}
            elif param in HORSE_NAME_MAP:
                return {"action": "CHOOSE_HORSE", "horse_id": HORSE_NAME_MAP[param]}

        # 3. Checa menção direta ao nome do cavalo
        for name, hid in HORSE_NAME_MAP.items():
            # Palavra exata ou início/fim
            pattern = rf"\b{name}\b"
            if re.search(pattern, norm):
                return {"action": "CHOOSE_HORSE", "horse_id": hid}

        # 4. Checa comandos divertidos (/turbo, /chuva, /caos, /sorte)
        fun_match = re.search(r"/(turbo|chuva|fogo|caos|sorte)", norm)
        if fun_match:
            return {"action": "CHEER", "command": fun_match.group(1)}

        # 5. Frases de torcida ("vai relampago", "bora bora", "torcida", etc)
        if any(w in norm for w in ["vai", "bora", "forca", "corre", "ganha", "cheer"]):
            return {"action": "CHEER", "command": "cheer"}

        return None

    def parse_gift(self, gift_name: str, repeat_count: int = 1) -> Dict[str, Any]:
        return {
            "action": "GIFT",
            "gift_name": gift_name,
            "count": max(1, repeat_count)
        }
