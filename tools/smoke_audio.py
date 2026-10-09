"""Ouve a voz da corrida sem abrir live: um teste de ouvido.

Uso:
    python tools/smoke_audio.py              # fala uma de cada momento
    python tools/smoke_audio.py presente     # fala só o presente
    python tools/smoke_audio.py largada vencedor
    python tools/smoke_audio.py abertura reta_final   # a locução ao vivo

Usa o MESMO config e o MESMO motor do jogo (edge-tts gera, MCI toca), então
o que você ouvir aqui é exatamente o que a live vai falar. Precisa de
internet (a síntese acontece na nuvem da Microsoft) e de placa de som — a
voz sai pelo alto-falante padrão do Windows.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import load_config
from game.narrador import Narrador


def main() -> None:
    config = load_config()
    # O teste de ouvido fala mesmo que a voz esteja desligada no config.
    config.tts.active = True
    config.tts.anunciar_entrada = True

    narrador = Narrador(config.tts)
    narrador.ligar()
    print(f"🔊 Voz do config: {config.tts.voz} (rodízio: {narrador.vozes})")

    momentos = {
        "presente": lambda: narrador.anunciar_presente("ana", 5, "Rose", "RELÂMPAGO"),
        "entrada": lambda: narrador.anunciar_entrada("leo"),
        "votacao": lambda: narrador.anunciar_votacao(7),
        "largada": lambda: narrador.anunciar_largada(7),
        # A locução ao vivo, na ordem em que sai na corrida.
        "abertura": lambda: narrador.anunciar_abertura("RAIO", "TROVÃO"),
        "placar": lambda: narrador.anunciar_placar("RAIO", "TROVÃO", "NEVASCA"),
        "disputa": lambda: narrador.anunciar_disputa("RAIO", "TROVÃO"),
        "reta_final": lambda: narrador.anunciar_reta_final("RAIO", "TROVÃO"),
        "foto_finish": lambda: narrador.anunciar_foto_finish("RAIO", "TROVÃO"),
        "vencedor": lambda: narrador.anunciar_vencedor(3, "FURACÃO"),
    }
    escolhidos = [arg.lower() for arg in sys.argv[1:]] or list(momentos)
    desconhecidos = [nome for nome in escolhidos if nome not in momentos]
    if desconhecidos:
        print(f"Momento desconhecido: {', '.join(desconhecidos)}. Use: {', '.join(momentos)}")
        return

    try:
        for nome in escolhidos:
            print(f"  ▶️  {nome}: {momentos[nome]()}")
            # Espera a fila esvaziar e a fala terminar de tocar antes da próxima.
            while narrador.pendentes() > 0:
                time.sleep(0.2)
            time.sleep(4.0)
    except KeyboardInterrupt:
        pass
    finally:
        narrador.parar()
    print("✅ Fim. Ouviu tudo? Então a voz da live está pronta.")


if __name__ == "__main__":
    main()
