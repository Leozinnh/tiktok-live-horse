"""Monte Carlo da matemática da corrida: distribuição de vitórias, pódios e tempos.

Uso:
    python tools/monte_carlo.py [n_corridas] [seed]

Serve para calibrar config.json + personalidades SEM abrir a live. Regra de
bolso: se um cavalo vence muito (ou nunca vence), mexa nos stats dele e rode
de novo; se a corrida termina em bloco (todos juntos), a diferença entre
personalidades está fraca.
"""
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Mesmo cuidado do main.py: console do Windows cai pra cp1252 e derruba nos acentos
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import load_config  # noqa: E402
from game.engine import RaceEngine  # noqa: E402


def rodar(n_corridas: int = 300, seed: int = 1234) -> None:
    random.seed(seed)
    config = load_config()
    engine = RaceEngine(config)

    vitorias = Counter()
    podios = Counter()
    terminaram = Counter()
    tempos = defaultdict(list)
    clima_vencedor = defaultdict(Counter)
    margens = []

    dt = 1.0 / 60.0
    for _ in range(n_corridas):
        engine.reset()
        clima = engine.weather_system.pick_random_weather()
        engine.start_race()
        for _ in range(4000):
            engine.update(dt)
            if engine.is_finished():
                break
        if not engine.is_finished():
            raise RuntimeError("corrida não terminou — investigar timeout")

        vencedor = engine.winner_horse_id
        vitorias[vencedor] += 1
        clima_vencedor[clima.value][vencedor] += 1
        for resultado in engine.final_results[:3]:
            podios[resultado["horse_id"]] += 1
        for h in engine.horses:
            if h.finished:
                terminaram[h.id] += 1
                tempos[h.id].append(h.finish_time_ms)

        # Margem do vencedor para o 2º colocado (emoção da chegada)
        dois_primeiros = engine.final_results[:2]
        margens.append(dois_primeiros[1]["finish_time_ms"] - dois_primeiros[0]["finish_time_ms"])

    nomes = {h.id: h.name for h in engine.horses}
    print(f"\n=== MONTE CARLO: {n_corridas} corridas | seed {seed} ===\n")
    print(f"{'#':>2} {'CAVALO':<10} {'VITÓRIAS':>9} {'PÓDIOS':>9} {'TERMINOU':>9} {'TEMPO MÉDIO':>12}")
    for i in range(1, 9):
        v = vitorias.get(i, 0)
        p = podios.get(i, 0)
        t = terminaram.get(i, 0)
        tempo = sum(tempos[i]) / len(tempos[i]) / 1000.0 if tempos[i] else 0.0
        print(f"{i:>2} {nomes[i]:<10} {v:>4} ({100*v/n_corridas:>4.1f}%) {p:>4} ({100*p/n_corridas:>4.1f}%) "
              f"{t:>4} ({100*t/n_corridas:>4.1f}%) {tempo:>10.2f}s")

    if margens:
        media = sum(margens) / len(margens)
        apertadas = sum(1 for m in margens if m <= 300)
        print(f"\nMargem média 1o/2o lugar: {media:>7.0f} ms | chegadas apertadas (<=300ms): {apertadas}/{len(margens)} "
              f"({100*apertadas/len(margens):.1f}%)")

    print("\nVencedor por clima:")
    for clima, contagem in sorted(clima_vencedor.items()):
        total = sum(contagem.values())
        detalhe = ", ".join(f"#{hid} x{c}" for hid, c in contagem.most_common())
        print(f"  {clima:<13} ({total:>3} corridas): {detalhe}")
    print()


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    s = int(sys.argv[2]) if len(sys.argv) > 2 else 1234
    rodar(n, s)
