"""Dublês de teste compartilhados entre os arquivos de teste.

O narrador de verdade gera áudio (edge-tts) e toca (MCI) — segundos por fala.
Nos testes, quem faz o papel dele é o `FakeNarrador`: anota o que o director
pediu para falar, sem internet e sem placa de som.
"""


class FakeNarrador:
    """Anota o que o director pediu para falar, sem gerar áudio."""

    def __init__(self):
        self.chamadas = []

    def anunciar_votacao(self, numero):
        self.chamadas.append(("votacao", numero))

    def anunciar_largada(self, numero):
        self.chamadas.append(("largada", numero))

    def anunciar_vencedor(self, numero, nome):
        self.chamadas.append(("vencedor", numero, nome))

    def anunciar_presente(self, nome, quantidade, presente, cavalo):
        self.chamadas.append(("presente", nome, quantidade, presente, cavalo))

    def anunciar_entrada(self, nome, fallback=""):
        self.chamadas.append(("entrada", nome))

    def anunciar_follow(self, nome, fallback=""):
        self.chamadas.append(("follow", nome))

    def anunciar_curtidas(self, nome, quantidade, fallback=""):
        self.chamadas.append(("curtidas", nome, quantidade))

    def anunciar_abertura(self, lider, segundo):
        self.chamadas.append(("abertura", lider, segundo))

    def anunciar_placar(self, lider, segundo, terceiro, nomes=None, cavalo=""):
        self.chamadas.append(("placar", lider, segundo, terceiro, nomes, cavalo))

    def anunciar_torcida(self, nomes, cavalo):
        self.chamadas.append(("torcida", nomes, cavalo))

    def anunciar_fidelidade(self):
        self.chamadas.append(("fidelidade",))

    def anunciar_xp_dobrado(self):
        self.chamadas.append(("xp_dobrado",))

    def anunciar_disputa(self, lider, segundo):
        self.chamadas.append(("disputa", lider, segundo))

    def anunciar_reta_final(self, lider, segundo):
        self.chamadas.append(("reta_final", lider, segundo))

    def anunciar_foto_finish(self, vencedor, segundo):
        self.chamadas.append(("foto_finish", vencedor, segundo))

    def anunciar_clima(self, clima, nomes):
        self.chamadas.append(("clima", clima, nomes))

    def anunciar_virada_do_clima(self, clima, nomes):
        self.chamadas.append(("virada_clima", clima, nomes))

    def descartar_locucao(self):
        self.chamadas.append(("descartar_locucao",))

    def interromper_locucao(self):
        self.chamadas.append(("interromper_locucao",))
