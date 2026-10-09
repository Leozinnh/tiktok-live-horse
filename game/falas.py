"""As frases que o Narrador fala: presente, chegada e os momentos da corrida.

A live não pode soar repetitiva: se todo presente virasse sempre o mesmo
"obrigado pelo presente", o áudio viraria ruído de fundo. O Narrador SORTEIA
uma frase da lista certa a cada evento (ver `game/narrador.py`), então dezenas
de falas diferentes se alternam sozinhas sem ninguém escrever lógica de rodízio.

Os valores de cada lista:

- `FALAS` (presente): `{nome}` (quem mandou, sem o arroba), `{quantidade}`
  (já formatada — "5x " — e VAZIA quando é um presente só, porque "1x Rose"
  não existe na língua falada), `{presente}` (nome que o TikTok manda) e
  `{cavalo}` (o cavalo do apoiador).
- `BOAS_VINDAS` (chegada): só `{nome}` — a chegada não tem prêmio, tem a pessoa.
- `VOTACAO_ABERTA`, `LARGADA`: `{numero}` é o número da corrida.
- `VENCEDOR`: `{numero}` e `{nome}` do cavalo campeão.
- `CORRIDA_ABERTURA`, `CORRIDA_DISPUTA`, `RETA_FINAL` (a locução ao vivo):
  `{lider}` e `{segundo}` são os DOIS cavalos da frente naquele momento —
  quem puxa e quem vem na cola. Toda frase usa os dois: é a tensão da
  disputa que dá o clima, não um cavalo sozinho.
- `CORRIDA_PLACAR`: `{lider}`, `{segundo}` e `{terceiro}` — a chamada de
  POSIÇÕES (o "placar" do locutor de turfe), que preenche os vãos entre um
  marco e outro: a corrida fica narrada do começo ao fim, sem buracos.
- `FOTO_FINISH`: `{vencedor}` e `{segundo}` — só entra no ar quando a
  chegada foi decidida por menos de 50ms (ver `MARGEM_FOTO_FINISH_MS` no
  director); em corrida decidida com folga, a exclamação não faria sentido.
- `CLIMA` e `CLIMA_VIRADA`: `{clima}` (o rótulo já com a força — "chuva
  forte") e `{quem}` (a cláusula de quem o clima favorece, pronta para
  encostar no fim da frase: vem VAZIA quando o clima não favorece ninguém
  — céu limpo, por exemplo — e as frases precisam fechar sem ela).

Escreva pensando no texto FALADO: acento e pontuação importam (é o que faz a
voz do edge-tts ler certo), e evite frase longa demais — a fala entra no meio
da ação. A locução ao vivo é a que mais corre contra o relógio: durante a
corrida cada frase tem poucos segundos de janela antes do próximo marco.
Quem quiser trocar as frases sem mexer no código aponta `tts.falas`,
`tts.boas_vindas`, `tts.votacao`, `tts.largada`, `tts.vencedor`,
`tts.corrida_abertura`, `tts.corrida_disputa`, `tts.corrida_placar`,
`tts.reta_final`, `tts.foto_finish`, `tts.clima` e `tts.clima_virada` no
`config.json` para as próprias listas; as daqui são o padrão do jogo.
"""

FALAS = [
    # --- Originais ---
    "Olha o presente! {nome} mandou {quantidade}{presente}! Isso é turbo pro {cavalo}!",
    "Aeee! {nome} mandou {quantidade}{presente} pro {cavalo}! Valeu, família!",
    "Presente na área! {nome} mandou {quantidade}{presente}! O {cavalo} agradece!",
    "Uhuu! {nome} mandou {quantidade}{presente}! O {cavalo} vai voar na pista!",
    "Que jogada! {nome} mandou {quantidade}{presente} pro {cavalo}! Valeu demais!",
    "É presente! {nome} mandou {quantidade}{presente}! Acelera esse cavalo, família!",
    "{nome} mandou {quantidade}{presente}! O {cavalo} tá voando com essa força!",
    "Olha a força da torcida! {nome} mandou {quantidade}{presente} pro {cavalo}! Obrigado!",
    "Turbo liberado! {nome} mandou {quantidade}{presente}! O {cavalo} agradece!",
    "Família, olha isso! {nome} mandou {quantidade}{presente} pro {cavalo}!",
    "Gratidão, {nome}! {quantidade}{presente} pro {cavalo}! Que presenteza!",
    "É o {cavalo} na frente! {nome} mandou {quantidade}{presente}! Valeeeu!",
    "Forte! {nome} mandou {quantidade}{presente} pro {cavalo}! Muito obrigado!",
    "O {cavalo} ganhou asas! {nome} mandou {quantidade}{presente}!",
    "Chegou chegando! {nome} mandou {quantidade}{presente} pro {cavalo}!",
    "Uau! {nome} mandou {quantidade}{presente}! O {cavalo} disparou, família!",
    "Valeu, {nome}! {quantidade}{presente} recebido! O {cavalo} tá invocado!",
    "Que carinho! {nome} mandou {quantidade}{presente} pro {cavalo}! Gratidão!",

    # --- Turbo e velocidade ---
    "Pisa fundo! {nome} mandou {quantidade}{presente}! O {cavalo} ganhou fôlego!",
    "Segura, que lá vai o {cavalo}! {nome} mandou {quantidade}{presente}! Valeu!",
    "Combustível novo! {nome} mandou {quantidade}{presente} pro {cavalo}! Obrigado!",
    "Que arrancada! {nome} mandou {quantidade}{presente}! O {cavalo} saiu voando!",
    "Olha a poeira! {nome} mandou {quantidade}{presente}! O {cavalo} é um foguete!",
    "Sentiu o empurrão? {nome} mandou {quantidade}{presente} pro {cavalo}! Valeu!",
    "É o {cavalo} embalado! {nome} mandou {quantidade}{presente}! Muito obrigado!",
    "Vai, vai, vai! {nome} mandou {quantidade}{presente} pro {cavalo}! Valeu demais!",
    "Que vento a favor! {nome} mandou {quantidade}{presente}! O {cavalo} agradece!",
    "Acelerou! {nome} mandou {quantidade}{presente}! O {cavalo} não para mais!",

    # --- Torcida e emoção ---
    "A torcida tá com tudo! {nome} mandou {quantidade}{presente} pro {cavalo}!",
    "Pelo amor! {nome} mandou {quantidade}{presente}! O {cavalo} vai ganhar essa!",
    "Haja coração! {nome} mandou {quantidade}{presente} pro {cavalo}! Obrigadão!",
    "É emoção demais! {nome} mandou {quantidade}{presente}! Vai, {cavalo}!",
    "Explodiu a arquibancada! {nome} mandou {quantidade}{presente} pro {cavalo}!",
    "Que torcedor! {nome} mandou {quantidade}{presente}! O {cavalo} agradece!",
    "Isso é amor pelo {cavalo}! {nome} mandou {quantidade}{presente}! Valeu!",
    "Torcida fiel! {nome} mandou {quantidade}{presente} pro {cavalo}! Gratidão!",
    "O {cavalo} tem torcida! {nome} mandou {quantidade}{presente}! Muito obrigado!",
    "Grita aí, família! {nome} mandou {quantidade}{presente} pro {cavalo}!",

    # --- Carinhosas ---
    "Que coração bonito, {nome}! {quantidade}{presente} pro {cavalo}! Obrigado!",
    "Obrigado pelo carinho, {nome}! {quantidade}{presente} pro {cavalo}!",
    "Você é demais, {nome}! {quantidade}{presente} pro {cavalo}! Gratidão!",
    "O {cavalo} manda um relincho de agradecimento! {nome}, {quantidade}{presente}!",
    "Que gesto lindo! {nome} mandou {quantidade}{presente} pro {cavalo}! Valeu!",
    "Família linda! {nome} mandou {quantidade}{presente}! O {cavalo} agradece!",
    "Isso aquece o coração! {nome} mandou {quantidade}{presente} pro {cavalo}!",
    "De coração, {nome}! {quantidade}{presente} pro {cavalo}! Muito obrigado!",

    # --- Divertidas ---
    "Alô, alô! {nome} mandou {quantidade}{presente}! O {cavalo} tá de cabeça erguida!",
    "O {nome} não veio brincar! {quantidade}{presente} pro {cavalo}! Valeu!",
    "Tapete vermelho pro {nome}! Mandou {quantidade}{presente} pro {cavalo}!",
    "Esse {nome} entende de corrida! {quantidade}{presente} pro {cavalo}! Obrigado!",
    "O {cavalo} ganhou até massagem! {nome} mandou {quantidade}{presente}! Valeu!",
    "Tá chovendo presente! {nome} mandou {quantidade}{presente} pro {cavalo}!",
    "Dá-lhe, {nome}! {quantidade}{presente} e o {cavalo} sorrindo! Valeu demais!",
    "Cuidado, adversários! {nome} mandou {quantidade}{presente} pro {cavalo}!",
    "O {cavalo} foi pro spa! {nome} mandou {quantidade}{presente}! Obrigado!",
    "Aplausos pro {nome}! {quantidade}{presente} pro {cavalo}! Valeu, família!",

    # --- Curtas e diretas ---
    "Valeu, {nome}! {quantidade}{presente} pro {cavalo}!",
    "Obrigado, {nome}! {quantidade}{presente}! Vai, {cavalo}!",
    "Show, {nome}! {quantidade}{presente} pro {cavalo}!",
    "Gratidão, {nome}! {quantidade}{presente}! Voa, {cavalo}!",
    "Boa, {nome}! {quantidade}{presente} pro {cavalo}!",
    "Top, {nome}! {quantidade}{presente}! O {cavalo} agradece!",
    "Chegou {quantidade}{presente} do {nome}! Vai, {cavalo}!",
    "É isso, {nome}! {quantidade}{presente} pro {cavalo}! Valeu!",
]

# --------------------------------------------------------------------------
# Boas-vindas
# --------------------------------------------------------------------------

BOAS_VINDAS = [
    # --- Originais ---
    "Olha quem chegou! {nome}, seja bem-vindo à live!",
    "{nome} entrou na pista! Seja bem-vindo, família!",
    "Bem-vindo, {nome}! Comenta de um a oito e escolhe teu cavalo!",
    "Chegou mais um torcedor! Bem-vindo, {nome}!",
    "{nome} na área! Escolhe teu cavalo e bora torcer!",
    "Salve, {nome}! A corrida tá esperando você!",
    "Aeee! {nome} chegou! Bem-vindo à família das corridas!",
    "Família crescendo! {nome} chegou! Seja bem-vindo!",
    "Uhuu! Olha o {nome} aqui! Bem-vindo!",
    "E aí, {nome}! Bem-vindo! Escolhe teu cavalo e vem torcer!",
    "Que bom te ver, {nome}! Seja bem-vindo à live!",
    "Chegou o {nome}! Bem-vindo à pista, família!",
    "{nome} entrou na live! Bem-vindo! Bora pra corrida!",
    "A live ficou melhor! {nome} chegou! Bem-vindo!",
    "Bem-vindo, {nome}! Torce, comenta e vibra com a gente!",
    "É isso, {nome} na live! Escolhe teu cavalo e boa sorte!",

    # --- Empolgadas ---
    "Chegou chegando! {nome} entrou na pista! Bem-vindo!",
    "Mais um pra arquibancada! Bem-vindo, {nome}!",
    "Olha ele aí! {nome}, seja bem-vindo! Bora de corrida!",
    "A torcida cresceu! {nome} chegou! Bem-vindo, família!",
    "Boa! {nome} entrou! Escolhe teu cavalo e bora vibrar!",
    "Tá começando a festa! {nome} chegou! Bem-vindo!",
    "{nome} chegou na hora certa! A corrida vai ser boa! Bem-vindo!",
    "Eita, chegou gente boa! Bem-vindo, {nome}!",

    # --- Carinhosas ---
    "Que alegria te receber, {nome}! Fica à vontade, a arquibancada é sua!",
    "Bem-vindo, {nome}! Aqui todo mundo é família!",
    "Oi, {nome}! Que bom que você chegou! Bem-vindo!",
    "{nome}, a live ficou mais bonita com você! Bem-vindo!",
    "Obrigado por vir, {nome}! Fica com a gente e torce junto!",
    "Que presença boa, {nome}! Seja bem-vindo à nossa corrida!",
    "Bem-vindo, {nome}! Puxa uma cadeira e escolhe teu cavalo!",
    "Que bom ter você aqui, {nome}! Bem-vindo, de coração!",

    # --- Convidando a participar ---
    "Bem-vindo, {nome}! Comenta o número do teu cavalo, de um a oito!",
    "{nome}, escolhe teu cavalo de um a oito e vem torcer com a gente!",
    "Bem-vindo, {nome}! Já escolheu o cavalo da próxima corrida?",
    "Seja bem-vindo, {nome}! Manda teu palpite nos comentários!",
    "{nome}, chegou na hora boa! Comenta de um a oito e entra na corrida!",
    "Bem-vindo, {nome}! Cada comentário seu empurra o teu cavalo!",
    "Oi, {nome}! Qual cavalo é o seu favorito? Comenta aí!",
    "Bem-vindo, {nome}! Manda um presente e dá turbo no teu cavalo!",

    # --- Divertidas ---
    "Atenção, atenção! {nome} acaba de entrar na pista! Bem-vindo!",
    "Chama a banda! O {nome} chegou! Bem-vindo!",
    "Abram alas pro {nome}! Bem-vindo à live, família!",
    "O {nome} chegou e os cavalos já ficaram nervosos! Bem-vindo!",
    "Entrada triunfal do {nome}! Seja bem-vindo à live!",
    "Quem chegou? Foi o {nome}! Bem-vindo, bora torcer!",
    "Alô, alô! Olha o {nome} na arquibancada! Bem-vindo!",
    "Cuidado, torcedor profissional chegando! Bem-vindo, {nome}!",

    # --- Curtas e diretas ---
    "Oi, {nome}! Bem-vindo à live!",
    "Seja bem-vindo, {nome}!",
    "Fala, {nome}! Bem-vindo à pista!",
    "Salve, {nome}! Bem-vindo, família!",
    "{nome} na live! Bem-vindo!",
    "Boa, {nome}! Bem-vindo e boa sorte!",
]

# --------------------------------------------------------------------------
# Os momentos da corrida
# --------------------------------------------------------------------------

VOTACAO_ABERTA = [
    # --- Originais ---
    "Corrida {numero} no ar! Votação aberta: comenta de um a oito e escolhe teu cavalo!",
    "Atenção, família! Corrida {numero} começando! Comenta o número do teu cavalo!",
    "Corrida {numero}! Votação aberta agora! Escolhe teu cavalo comentando de um a oito!",
    "Prepare o palpite! Corrida {numero} valendo! Comenta de um a oito!",
    "A largada se aproxima! Corrida {numero}! Comenta o número do teu cavalo!",
    "Família, votação aberta! Corrida {numero}! De um a oito, escolhe teu cavalo!",
    "Corrida {numero} chegou! Comenta de um a oito e bora torcer!",
    "Bora de corrida {numero}! Escolhe teu cavalo nos comentários!",

    # --- Chamando o palpite ---
    "Hora do palpite! Corrida {numero}! Comenta de um a oito e escolhe teu cavalo!",
    "Quem vai ganhar a corrida {numero}? Comenta de um a oito e aposta no teu!",
    "Corrida {numero} abrindo! Manda o número do teu cavalo nos comentários!",
    "Votação da corrida {numero} aberta! De um a oito, quem é o teu favorito?",
    "Escolhe teu cavalo, família! Corrida {numero}! Comenta de um a oito!",
    "Corrida {numero} vem aí! Comenta o número e entra na disputa!",
    "Palpites abertos para a corrida {numero}! Comenta de um a oito!",
    "Chegou a hora de escolher! Corrida {numero}! Teu cavalo, de um a oito!",

    # --- Empolgadas ---
    "Atenção, atenção! Corrida {numero} no ar! Comenta de um a oito e bora!",
    "Vai começar a corrida {numero}! Escolhe teu cavalo antes que feche!",
    "Corra pro comentário! Corrida {numero}! De um a oito, escolhe teu cavalo!",
    "Tá aberta a votação da corrida {numero}! Comenta e vibra com a gente!",
    "É agora! Corrida {numero}! Comenta de um a oito e escolhe teu campeão!",
    "Segura que vem corrida {numero}! Comenta o número do teu cavalo!",
    "Família, correndo contra o tempo! Corrida {numero}! Comenta de um a oito!",
    "Olha a corrida {numero} chegando! Comenta de um a oito e bora torcer!",

    # --- Zoeira ---
    "Quem tem cavalo, comenta! Corrida {numero}! De um a oito!",
    "A pista tá pronta! Corrida {numero}! Falta só o teu palpite, de um a oito!",
    "Corrida {numero}! Quem não vota, não torce! Comenta de um a oito!",
    "Escolhe com carinho, que o cavalo não escolhe de volta! Corrida {numero}!",
    "Corrida {numero} abrindo! Aposta no cavalo certo, de um a oito!",
    "Chegou a hora da verdade! Corrida {numero}! Comenta de um a oito!",
]

LARGADA = [
    # --- Originais ---
    "Largada! E lá vão eles! Corrida {numero} começou!",
    "Valendo! A corrida {numero} começou! Olha eles disparando!",
    "Largada da corrida {numero}! Que comece a batalha!",
    "Eles partiram! Corrida {numero} rolando! Quem vai levar?",
    "Foi dada a largada da corrida {numero}! Olha a poeira!",
    "Corrida {numero} na pista! E lá vão eles!",
    "Partiu! Corrida {numero} começou! Segura a emoção!",
    "Largada! A corrida {numero} está nas mãos deles!",

    # --- Empolgadas ---
    "Foi dada a largada! Corrida {numero}! Que comece a disputa!",
    "Abriu o portão! Corrida {numero}! Lá vão eles!",
    "É agora! Corrida {numero} largou! Vai, vai, vai!",
    "Disparou! A corrida {numero} começou! Quem vai na frente?",
    "Saíram! Corrida {numero} valendo! Segura o coração!",
    "Largou a corrida {numero}! Olha a velocidade deles!",
    "E lá se vão os cavalos! Corrida {numero} em andamento!",
    "Começou! Corrida {numero}! Que arrancada, família!",

    # --- Narração de pista ---
    "Os cavalos estão na pista! Corrida {numero} largou!",
    "Tropel de cascos! A corrida {numero} começou!",
    "Poeira na pista! Corrida {numero} largou! Quem assume a ponta?",
    "A pista é deles! Corrida {numero} começou!",
    "Largada limpa! Corrida {numero} rolando! Segura firme!",
    "Corrida {numero} em disparada! Olha eles abrindo!",
    "Ouve o barulho dos cascos! Corrida {numero} começou!",
    "Todos largaram! Corrida {numero} na pista!",

    # --- Torcida ---
    "Torcida em pé! Corrida {numero} largou!",
    "Vibra, família! Corrida {numero} começou! Torce pelo teu cavalo!",
    "Grita aí! A corrida {numero} começou! Quem vai levar essa?",
    "Chegou a hora de torcer! Corrida {numero} largou!",
    "Valendo, valendo! Corrida {numero}! Que vença o melhor!",
    "Segura o grito! Corrida {numero} largou! Vai, teu cavalo!",
]

VENCEDOR = [
    # --- Originais ---
    "Chegou! O cavalo {numero} {nome} venceu a corrida!",
    "É dele! O {nome}, cavalo {numero}, cruzou primeiro! Que corrida!",
    "Temos um vencedor! O cavalo {numero} {nome} levou a melhor!",
    "Que virada! O {nome}, número {numero}, venceu a corrida!",
    "Vitória! O cavalo {numero} {nome} chegou na frente!",
    "O {nome} não deu chance! Cavalo {numero}, campeão da corrida!",
    "E o grande campeão é o {nome}! O cavalo {numero} venceu!",
    "Fim de corrida! O {nome}, número {numero}, levou o troféu!",

    # --- Emoção ---
    "Cruzou a linha! O cavalo {numero} {nome} é o campeão! Que corrida, família!",
    "Que final! O {nome}, número {numero}, venceu! Gente, que emoção!",
    "É campeão! O cavalo {numero} {nome} fez história nessa corrida!",
    "Não acredito! O {nome}, cavalo {numero}, ganhou! Que reta final!",
    "Uhuu! O cavalo {numero} {nome} levou a taça! Parabéns, torcida!",
    "Venceu o {nome}! Cavalo {numero}! Que disparada espetacular!",
    "Fotografia final! O cavalo {numero} {nome} é o vencedor!",
    "Que reta final! O {nome}, número {numero}, cruzou na frente!",

    # --- Elogiando o campeão ---
    "O {nome} mostrou o porquê é craque! Cavalo {numero}, campeão!",
    "Que raça! O cavalo {numero} {nome} venceu com folga!",
    "Domínio total! O {nome}, número {numero}, levou a corrida!",
    "Parabéns ao {nome}! O cavalo {numero} é o grande campeão!",
    "Um show de velocidade! O cavalo {numero} {nome} venceu!",
    "O {nome} voou na pista! Cavalo {numero}, campeão desta corrida!",
    "Que cavalo! O {nome}, número {numero}, é o rei da pista!",
    "Aplausos pro {nome}! O cavalo {numero} cruzou primeiro!",

    # --- Torcida e festa ---
    "Festa na arquibancada! O cavalo {numero} {nome} é o campeão!",
    "A torcida do {nome} vai à loucura! Cavalo {numero} venceu!",
    "Parabéns, torcedores do {nome}! Cavalo {numero}, campeão!",
    "Quem apostou no {nome} comemora! O cavalo {numero} venceu!",
    "É do {nome}! Cavalo {numero}! Comemora, torcida!",
    "Soltem os fogos! O cavalo {numero} {nome} venceu a corrida!",
]

# ---------------------------------------------------------------------------
# Locução ao vivo: as chamadas DURANTE a corrida (o narrador fala enquanto os
# cavalos correm). Diferente das listas acima — que marcam um momento — estas
# são disparadas por MARCO DE DISTÂNCIA (ver MARCOS_LOCUCAO no director) e
# sempre citam a dupla da frente: quem lidera e quem vem na cola. Toda frase
# precisa dos dois placeholders, senão a chamada perde a tensão da disputa.
# ---------------------------------------------------------------------------

CORRIDA_ABERTURA = [
    # --- Originais ---
    "{lider} puxa o ritmo! E olha o {segundo} vindo colado logo atrás!",
    "Na ponta é o {lider}! Mas o {segundo} não desgruda, família!",
    "{lider} assume a liderança! {segundo} vem na caçada, atento!",
    "Quem abre é o {lider}! O {segundo} vem logo atrás, na cola!",
    "{lider} na frente! E o {segundo} vem no vácuo, esperando o momento!",
    "Olha o {lider} disparando! O {segundo} não deixa abrir!",
    "{lider} puxa a fila! {segundo} coladinho, sem perder contato!",
    "A ponta é do {lider}! Mas olha o {segundo} vindo por dentro!",
    "{lider} na liderança! {segundo} vem junto, é corrida de dupla!",
    "Abre o {lider}! {segundo} logo atrás, a corrida tá pegada!",

    # --- Largada rápida ---
    "{lider} saiu na frente! {segundo} vem rente, sem dar folga!",
    "Que arrancada do {lider}! {segundo} tenta acompanhar!",
    "{lider} larga firme na ponta! {segundo} vem no encalço!",
    "Primeiros metros! {lider} na frente e {segundo} bem colado!",
    "{lider} dispara cedo! {segundo} não perde de vista!",
    "A corrida começou quente! {lider} na ponta, {segundo} atrás!",
    "{lider} ganhou a primeira posição! {segundo} vem de perto!",
    "Olha a saída! {lider} na frente e {segundo} logo ali!",

    # --- Tensão desde o início ---
    "Ainda é cedo, mas {lider} já manda! {segundo} espera a hora!",
    "{lider} na liderança! {segundo} vem escondido no vácuo!",
    "Começou a briga! {lider} na ponta, {segundo} pressionando!",
    "{lider} abre uma vantagenzinha! {segundo} vem fechando!",
    "Calma que é só o começo! {lider} lidera, {segundo} vigia!",
    "{lider} e {segundo} já saíram na frente do resto!",
    "Dupla na dianteira! {lider} lidera e {segundo} vem colado!",
    "{lider} comanda a corrida! {segundo} vem no pé dele!",
]

CORRIDA_DISPUTA = [
    # --- Originais ---
    "A corrida tá pegada! {lider} e {segundo} lado a lado!",
    "É disputa de gigantes! {lider} e {segundo} trocando posição!",
    "Olha isso, família! {lider} e {segundo} ombro a ombro!",
    "Que corrida! {lider} na frente, mas o {segundo} não larga!",
    "No meio do caminho é o {lider}! E o {segundo} pressiona forte!",
    "{lider} e {segundo} na briga pela ponta! Que espetáculo!",
    "Ninguém solta! {lider} e {segundo} na disputa direta!",
    "{lider} segura a ponta por um fio! {segundo} vem voando!",
    "Corrida aberta! {lider} e {segundo} decidindo palmo a palmo!",
    "Tá pegando fogo! {lider} e {segundo} na liderança disputada!",

    # --- Troca de posição ---
    "Trocou a ponta! {lider} agora manda e {segundo} reage!",
    "Olha a ultrapassagem! {lider} na frente e {segundo} vem de volta!",
    "{lider} passa e assume! {segundo} não aceita e vem junto!",
    "Mudou tudo! {lider} lidera e {segundo} tenta retomar!",
    "A ponta muda de dono! {lider} na frente, {segundo} atrás!",
    "{lider} por fora! {segundo} responde e a briga continua!",
    "Que ultrapassagem! {lider} na frente e {segundo} colado!",
    "Quem manda agora? {lider}! Mas {segundo} está respirando no pescoço!",

    # --- Pressão ---
    "{segundo} pressiona! {lider} sente e segura a liderança!",
    "{lider} resiste! {segundo} aperta cada vez mais!",
    "Pressão total! {segundo} cola no {lider} e a ponta treme!",
    "{lider} não pode vacilar! {segundo} está logo atrás!",
    "{segundo} encosta! {lider} acelera para não perder a ponta!",
    "A diferença diminui! {segundo} chega perto do {lider}!",
    "{lider} luta pela ponta! {segundo} não dá trégua!",
    "O fôlego é curto! {lider} e {segundo} dando tudo!",

    # --- Emoção ---
    "É emocionante, família! {lider} e {segundo} na frente do pelotão!",
    "Que duelo! {lider} e {segundo} esquentando a pista!",
    "Quem leva essa? {lider} e {segundo} na briga!",
    "A pista é só deles! {lider} e {segundo} em disputa!",
    "Segura a emoção! {lider} e {segundo} se alternando na frente!",
    "Que briga bonita! {lider} e {segundo} sem se largar!",
    "Que tensão! {lider} e {segundo} na ponta, nada definido!",
]

# O "placar" do locutor de turfe: as posições do TRIO da frente, chamadas
# entre um marco e outro. São estas que fazem a corrida ficar narrada do
# começo ao fim — sem elas, sobravam buracos de ~10s de silêncio na prova.
CORRIDA_PLACAR = [
    # --- Originais ---
    "Olha o placar! {lider} na frente, {segundo} em segundo e {terceiro} fechando o trio!",
    "Posições! {lider} lidera, {segundo} vem colado e {terceiro} na espreita!",
    "Como está a corrida? {lider}, {segundo} e {terceiro} nos três primeiros!",
    "Placar da prova: {lider} puxa, {segundo} persegue e {terceiro} vem junto!",
    "Trio da frente: {lider}, {segundo} e {terceiro}! Que corrida equilibrada!",
    "Nada definido! {lider} na ponta, {segundo} em segundo e {terceiro} logo atrás!",
    "Olha a fila! {lider} primeiro, {segundo} segundo e {terceiro} terceiro!",
    "{lider} mantém a ponta, mas {segundo} e {terceiro} não deixam escapar!",
    "É disputa de trio! {lider}, {segundo} e {terceiro} separados por pouco!",
    "No placar: {lider} primeiro, com {segundo} e {terceiro} vindo forte atrás!",

    # --- Chamada de posições ---
    "Atualizando as posições! {lider} em primeiro, {segundo} em segundo, {terceiro} em terceiro!",
    "O pódio provisório! {lider}, {segundo} e {terceiro}!",
    "Quem está na frente? {lider}! Depois {segundo} e {terceiro}!",
    "Vamos às posições! {lider} lidera, seguido de {segundo} e {terceiro}!",
    "Primeiro {lider}, segundo {segundo}, terceiro {terceiro}! Segue a briga!",
    "Hora do placar! {lider} na liderança, {segundo} e {terceiro} atrás!",
    "Conferindo a pista! {lider}, {segundo} e {terceiro} no pódio por enquanto!",
    "Placar atualizado! {lider} na ponta, depois {segundo} e {terceiro}!",

    # --- Tensão no trio ---
    "{lider} lidera, mas {segundo} e {terceiro} estão no cangote!",
    "O trio está embolado! {lider}, {segundo} e {terceiro} quase juntos!",
    "Três cavalos na briga! {lider}, {segundo} e {terceiro}!",
    "{terceiro} também quer! {lider} e {segundo} na frente, mas o trio aperta!",
    "Cuidado, {lider}! {segundo} e {terceiro} vêm juntos atrás!",
    "Ninguém escapou! {lider}, {segundo} e {terceiro} na briga!",
    "A diferença é mínima! {lider}, {segundo} e {terceiro} no mesmo bolo!",
    "É um trio de ferro! {lider}, {segundo} e {terceiro} na frente!",

    # --- Narração de turfe ---
    "Na dianteira, {lider}! Em seguida {segundo}, e {terceiro} completa o trio!",
    "Atenção ao placar! {lider}, {segundo} e {terceiro} em ordem!",
    "Pela ordem de chegada atual: {lider}, {segundo} e {terceiro}!",
    "Na contagem de posições, {lider} lidera! {segundo} e {terceiro} vêm atrás!",
    "O quadro de posições! {lider} primeiro, {segundo} segundo, {terceiro} terceiro!",
    "Seguimos com {lider} na frente! {segundo} e {terceiro} perseguindo!",
]

RETA_FINAL = [
    # --- Originais ---
    "Reta final! {lider} na frente e {segundo} vem voando!",
    "É agora! {lider} puxa, mas olha o {segundo} chegando!",
    "Últimos metros! {lider} e {segundo} na briga pelo título!",
    "Reta final, família! {lider} segura a ponta contra o {segundo}!",
    "Vem chegando o {segundo}! {lider} resiste na liderança!",
    "Tudo se decide agora! {lider} contra {segundo}!",
    "Reta! {lider} na frente, {segundo} colado no vácuo!",
    "Segura o coração! {lider} e {segundo} na decisão!",
    "É puro fogo! {lider} tenta segurar o {segundo}!",
    "Reta final! {lider} e {segundo} a poucos metros da linha!",

    # --- Decisão ---
    "É agora ou nunca! {lider} e {segundo} na disputa final!",
    "Última chance! {segundo} vai atrás do {lider} na reta!",
    "A linha de chegada está ali! {lider} e {segundo} na briga!",
    "Quem leva? {lider} na frente, mas {segundo} está voando!",
    "Tudo ou nada! {lider} e {segundo} a metros da vitória!",
    "É a hora da verdade! {lider} e {segundo} na reta!",
    "{lider} quer o título! {segundo} também, e vai pra cima!",
    "Falta pouco! {lider} na frente e {segundo} tentando a virada!",

    # --- Emoção ---
    "Gente, que reta! {lider} e {segundo} dando tudo!",
    "Prende a respiração! {lider} e {segundo} lado a lado!",
    "Que emoção! {lider} segura e {segundo} ataca!",
    "Não pisca! {lider} e {segundo} brigando pela vitória!",
    "O coração vai sair pela boca! {lider} e {segundo} na reta!",
    "A torcida vai à loucura! {lider} e {segundo} na final da pista!",
    "Vai, vai, vai! {lider} e {segundo} na reta final!",
    "Que fogo! {lider} e {segundo} sem ceder nada!",

    # --- Virada no ar ---
    "{segundo} tenta a virada! {lider} não vai entregar fácil!",
    "{segundo} encosta! {lider} responde no limite!",
    "Olha o {segundo} chegando por fora! {lider} resiste!",
    "{lider} tenta fechar a porta! {segundo} quer passar!",
    "A virada é possível! {segundo} está colado no {lider}!",
    "{lider} está no limite! {segundo} vem forte demais!",
]

FOTO_FINISH = [
    # --- Originais ---
    "Que chegada! {vencedor} levou no fio do bigode na frente do {segundo}!",
    "Foto finish! {vencedor} bateu o {segundo} por um nariz!",
    "Gente, que aperto! {vencedor} e {segundo} cruzaram quase juntos!",
    "No peito! {vencedor} ganhou do {segundo} na última patada!",
    "Impossível piscar! {vencedor} venceu o {segundo} por milímetros!",
    "Que duelo! {vencedor} levou a melhor sobre o {segundo} no grito!",
    "Chegada de tirar o fôlego! {vencedor} na frente do {segundo}!",
    "Apertadíssimo! {vencedor} bateu o {segundo} no sufoco!",
    "Olha o replay pra crer! {vencedor} venceu o {segundo} no detalhe!",
    "Uma patada de diferença! {vencedor} sobre o {segundo}!",

    # --- Por um triz ---
    "Por um triz! {vencedor} ganhou e {segundo} ficou a um passo!",
    "Quase empate! {vencedor} venceu e {segundo} chegou colado!",
    "Foi por um fio! {vencedor} na frente do {segundo}!",
    "Uma respiração de diferença! {vencedor} bateu o {segundo}!",
    "Que sufoco! {vencedor} venceu e {segundo} quase leva!",
    "Que chegada impossível! {vencedor} levou, {segundo} chegou junto!",
    "No limite! {vencedor} cruzou primeiro por muito pouco, {segundo} quase!",
    "A diferença é minúscula! {vencedor} ganhou do {segundo}!",

    # --- Emoção ---
    "Não acredito! {vencedor} ganhou do {segundo} na foto!",
    "Que loucura! {vencedor} e {segundo} chegaram juntos, mas {vencedor} venceu!",
    "Meu Deus, que final! {vencedor} bateu o {segundo}!",
    "Coração na mão! {vencedor} levou, {segundo} ficou pertinho!",
    "Isso é corrida! {vencedor} venceu o {segundo} no último segundo!",
    "Que emoção, gente! {vencedor} levou no detalhe sobre {segundo}!",
    "Final de cinema! {vencedor} bateu {segundo} por pouquíssimo!",
    "Tá todo mundo de boca aberta! {vencedor} venceu o {segundo}!",

    # --- Narração de foto ---
    "A foto decide! {vencedor} cruzou antes do {segundo}!",
    "Foto finish confirmado! {vencedor} na frente do {segundo}!",
    "Na análise da imagem, {vencedor} venceu e {segundo} ficou em segundo!",
    "Decidido na foto! {vencedor} ganhou e {segundo} chegou logo depois!",
    "Os juízes confirmam! {vencedor} bateu o {segundo} por um nariz!",
    "Resultado por foto! {vencedor} campeão, {segundo} vice colado!",
]

# ---------------------------------------------------------------------------
# O clima: anunciado na abertura da votação (CLIMA) e quando o tempo VIRA no
# meio da prova (CLIMA_VIRADA, ver `_talvez_virar_o_clima` no director).
# `{clima}` já vem com a força ("chuva forte"); `{quem}` é a cláusula de quem
# o clima favorece — pronta para encostar no FIM da frase, e vazia quando o
# clima não favorece ninguém. Por isso toda frase termina em `{quem}`.
# ---------------------------------------------------------------------------

CLIMA = [
    # --- Originais ---
    "Atenção à pista! A corrida de agora é com {clima}!{quem}",
    "Olha o tempo, família! {clima} na pista pra corrida de hoje!{quem}",
    "Boletim do tempo! A prova vai ser com {clima}!{quem}",
    "A pista tá com {clima} hoje! Isso pode mudar tudo!{quem}",
    "De olho no tempo! {clima} na pista da corrida de agora!{quem}",
    "Prepara o palpite com {clima} na pista! A corrida vai ser boa!{quem}",
    "O tempo deu a cara dele: {clima} na pista hoje!{quem}",
    "Corrida de hoje é com {clima}! Escolhe bem o teu cavalo!{quem}",

    # --- Climões ---
    "Eita, {clima} na pista! A corrida promete!{quem}",
    "A pista pediu {clima} hoje! E a corrida agradece!{quem}",
    "Vem aí uma corrida com {clima}! Segura a emoção!{quem}",
    "O tempo caprichou: {clima} pra corrida de agora!{quem}",
]

CLIMA_VIRADA = [
    # --- Originais ---
    "Olha o tempo virando! Agora é {clima} na pista!{quem}",
    "A prova virou! Agora é {clima} na pista!{quem}",
    "Mudou tudo, família! O tempo virou pra {clima}!{quem}",
    "Eita! {clima} na pista no meio da corrida!{quem}",
    "O tempo não perdoou! Vira pra {clima} e a prova muda!{quem}",
    "Vira, vira! A pista agora é com {clima}!{quem}",
    "Atualizando o tempo! Agora é {clima}! A corrida continua!{quem}",
    "Isso muda a corrida! O tempo virou pra {clima}!{quem}",
]