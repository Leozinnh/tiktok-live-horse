import difflib
import logging
import re
import unicodedata
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


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


def limpar_invisiveis(texto: str) -> str:
    """Só letra, número e espaço: emoji, invisível e acento quebrado somem.

    O TikTok enfia invisíveis no meio da palavra (truque dele contra
    comentário repetido) e às vezes entrega o acento corrompido
    ("relÃ¢mpago" = UTF-8 lido como latin-1). Sem esta limpeza, o nome
    digitado não aparece inteiro e o voto some — foi o que a live mostrou.
    """
    return re.sub(r"[^a-z0-9\s]+", "", texto)


# Os nomes que valem voto, na ordem em que são procurados: o padrão tolera
# letras repetidas ("relampagooo") e a chave é o nome colado, usado também
# pelo palpite do log (parece_voto).
PADROES_CAVALOS = [
    ("relampago", r"\bre+la+m+pa+g+o+\b", 1),
    ("trovao", r"\btro+va+o+\b", 2),
    ("furacao", r"\bfu+ra+ca+o+\b", 3),
    ("raio", r"\bra+i+o+\b", 4),
    ("pantera", r"\bpa+n+te+ra+\b", 5),
    ("tita", r"\bti+ta+[no]*\b", 6),
    ("nevasca", r"\bne+va+s*ca+\b", 7),
    ("fantasma", r"\bfa+n+ta+s*ma+\b", 8),
]

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
        # A busca do nome é na versão SEM invisíveis/emoji colados à palavra:
        # "rel<invisível>âmpago" e "relÃ¢mpago" voltam a ser "relampago".
        visivel = limpar_invisiveis(norm)

        # 1. Checa menção direta ou flexível ao nome do cavalo (inclusive com letras repetidas ex: relampagooo)
        for nome_chave, padrao, hid in PADROES_CAVALOS:
            if re.search(padrao, norm) or (nome_chave in visivel):
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

        # 3. Dígito único ou repetido do mesmo cavalo (ex: "1", " 3 ", "111", "88", "4444")
        m_rep = re.fullmatch(r"([1-8])\1*", norm)
        if m_rep:
            hid = int(m_rep.group(1))
            if hid in self.valid_horse_ids:
                return {"action": "CHOOSE_HORSE", "horse_id": hid}

        # 4. Hashtag ou prefixos comuns no chat (ex: "#1", "# 2", "n1", "no 3", "num 4", "numero 5", "cavalo 6")
        m_prefix = re.search(r"(?:#|n[ºo]?|num|numero|cavalo|horse)\s*([1-8])\b", norm)
        if m_prefix:
            hid = int(m_prefix.group(1))
            if hid in self.valid_horse_ids:
                return {"action": "CHOOSE_HORSE", "horse_id": hid}

        # 5. Dígito isolado de 1 a 8 na frase (ex: "vai 1", "bora 3!", "eu vou de 4", "1 pfv", "ganha 7")
        m_digito = re.search(r"\b([1-8])\b", norm)
        if m_digito:
            hid = int(m_digito.group(1))
            if hid in self.valid_horse_ids:
                return {"action": "CHOOSE_HORSE", "horse_id": hid}

        # 6. Checa comandos divertidos (/turbo, /chuva, /caos, /sorte)
        fun_match = re.search(r"/(turbo|chuva|fogo|caos|sorte)", norm)
        if fun_match:
            return {"action": "CHEER", "command": fun_match.group(1)}

        # 7. Frases de torcida genéricas ("bora bora", "torcida", etc)
        if any(w in norm for w in ["vai", "bora", "forca", "corre", "ganha", "cheer"]):
            return {"action": "CHEER", "command": "cheer"}

        return None

    def parece_voto(self, comment_text: str) -> Optional[str]:
        """O nome de cavalo que o comentário PARECIA citar (palpite, não voto).

        É a sonda para a próxima quebra: quando alguém digita o nome de um
        jeito que o parser ainda não entende (letra trocada, acento perdido),
        o palpite aparece no log com o comentário cru — é assim que a gente
        descobre o que a live está entregando. Nunca vira voto.
        """
        visivel = limpar_invisiveis(normalize_text(comment_text)).replace(" ", "")
        # Comentário longo é conversa, não voto: o palpite só olha o que
        # caberia num nome digitado no chat.
        if not visivel or len(visivel) > 24:
            return None
        perto = difflib.get_close_matches(
            visivel, [nome for nome, _, _ in PADROES_CAVALOS], n=1, cutoff=0.8
        )
        return perto[0] if perto else None

    def avisar_voto_perdido(self, comment_text: str) -> None:
        """Uma linha de log quando o comentário parecia voto e passou em branco.

        Mora aqui porque os DOIS adapters (a live e o simulador do painel)
        chamam isto quando o parse falha — a sonda é a mesma nas duas pontas.
        """
        palpite = self.parece_voto(comment_text)
        if palpite:
            logger.info("[voto?] %r não reconhecido (parecia %r)", comment_text, palpite)

    def parse_gift(self, gift_name: str, repeat_count: int = 1) -> Dict[str, Any]:
        return {
            "action": "GIFT",
            "gift_name": gift_name,
            "count": max(1, repeat_count)
        }
