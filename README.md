# 🏇 TikTok LIVE - Jogo de Corrida de Cavalos Interativo (3D)

Jogo de corrida de cavalos interativo e autônomo desenvolvido especialmente para transmissões no **TikTok LIVE** e captura via **OBS Studio (1080x1920 vertical, 9:16)**.

---

## ⚠️ AVISO LEGAL E COMPLIANCE
- **100% Virtual:** Este jogo **NÃO** possui dinheiro real, apostas, saques, conversão de pontos em dinheiro, prêmios financeiros ou qualquer mecânica de azar.
- Os pontos são exclusivamente **XP e Níveis Virtuais** para engajamento, conquistas, distintivos (*badges*) e ranking da LIVE.
- Presentes do TikTok ativam turbos visuais na pista, exibem o nome do apoiador em 3D e concedem XP ao torcedor.

---

## 🚀 Como Iniciar em 2 Passos

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Iniciar o Jogo
```bash
python main.py
```

O servidor iniciará instantaneamente na porta **8000**.

---

## 📺 Configuração no OBS Studio

1. Abra o **OBS Studio**.
2. Na sua cena de transmissão vertical (9:16), adicione uma nova fonte: **Navegador (Browser Source)**.
3. Configure os parâmetros da fonte:
   - **URL:** `http://localhost:8000/`
   - **Largura:** `1080`
   - **Altura:** `1920`
   - **Taxa de Quadros (FPS):** `60`
   - **Controlar áudio via OBS:** Marque para monitorar e mixar o som direto pelo OBS.
4. Clique em **OK**. A pista 3D alargada para 28m (raias com 3.2m de largura e muito espaço para ultrapassagens), cavalos animados com modelos customizados (Pégaso com asas de penas, Mecha, Blindado, Unicórnio com chifre arco-íris, Titã, Dragster, etc.), partidor profissional aberto ao céu (cavalos e nomes 100% visíveis e desobstruídos com cancelas mecânicas em V que abrem na largada), portal monumental com banner de chegada 4K ultra-nítido e iluminado, física com Dead Reckoning 60-144 FPS ultra-fluida, cercas de trilho duplo com flores, torre dos comissários, tendas VIP de paddock, câmeras de TV dinâmicas e HUD esportivo aparecerão imediatamente — céu com gradiente (estrelas à noite, relâmpago na tempestade), grama e areia texturizadas, luz que modela a cena, arquibancada com setores e torcida animada e vinheta de TV no enquadramento. A barra do topo mostra a **corrida atual** (com flash a cada prova nova), o **clima da pista** (informação de aposta!), a fase colorida (**AO VIVO** em vermelho) e o relógio contextual (segundos na votação, **distância do líder** na corrida), enquanto a **classificação ao vivo** fica elegantemente posicionada no rodapé (footer) em grid 4x2 sem obstruir nem 1 centímetro da pista de corrida. No pódio, o **cavalo campeão empina triunfante nas duas patas traseiras**, relincha vitoriosamente com áudio procedural e um show monumental de **fogos de artifício 3D e confetes** ilumina o céu da arena!
5. **Voz da corrida (TTS):** a narração falada sai pelo **alto-falante padrão do Windows** (fora do navegador). Adicione também **Áudio do Desktop** à cena — ou **Captura de Áudio do Aplicativo** apontando para o `python.exe` — senão a voz não chega em quem assiste. (Detalhes em [🔊 Narração por Voz](#-narração-por-voz-tts).)

---

## 🎮 Painel de Controle do Streamer (Admin / Test Mode)

Acesse em qualquer navegador em: **`http://localhost:8000/test`**

### 1. Controles Imediatos de Corrida:
- ⏩ **Iniciar Corrida Logo:** Pula o tempo de votação de 30s e inicia a contagem e largada na hora.
- 🏁 **Finalizar Corrida:** Força o encerramento da corrida e avança imediatamente para o pódio.
- 🔄 **Próxima Corrida:** Reinicia o ciclo e prepara a próxima prova com um clique.

### 2. Calibração do HUD no OBS em Tempo Real:
- **Tamanho do Placar (Escala):** Botões `➖ Menor (-10%)` | `🔄 Padrão (100%)` | `➕ Maior (+10%)` (calibra de 60% a 160%).
- **Posição Vertical:** Botões `▲ Subir (-25px)` e `▼ Descer (+25px)` para posicionar o placar com liberdade milimétrica.
- **Régua do Topo:** Botão para ocultar ou exibir a régua de progresso da pista.

### 3. Simulação de Eventos & Público:
- **Comentários & Votos:** Envie votos rápidos nos cavalos (#1 ao #8) ou comandos de torcida (`/turbo`, `bora torcida!`).
- **Simulação de Entrada na LIVE:** Botão `👤 Simular Entrada na LIVE (Oi da Voz)` para testar o anúncio sonoro imediato com áudio ducking e log no terminal.
- **Simulação de Seguidor & Curtidas:** Botões `➕ Simular Seguidor (Agradecimento)` e `💗 30 de uma vez` para testar o agradecimento na voz por novo seguidor e por rajadas de 20+ curtidas.
- **Presentes & Super Raros:** qualquer presente enviado é agradecido **NA HORA** pelo narrador com canal prioritário e áudio ducking (exatamente igual a novo seguidor ou chegada). Quanto mais valioso o presente, maior o bônus (velocidade e duração). Enviar em quantidade também amplia o bônus (cada unidade extra soma +10% do delta do presente, com teto).
  - 🌹 **Rosa** e ☕ **Café**: Turbo básico (`1.20`) e ágil.
  - 🧢 **Boné** e 🍩 **Donut**: Super Boost de velocidade (`1.35`).
  - 🌌 **Galáxia (+1500 XP)**: Overdrive cósmico (`1.60`) com vórtice estelar violeta e chamas nos cascos.
  - 🐉 **Dragão (+1800 XP)**: Impacto místico (`1.65`) com rastro de labaredas e rugido de torcida.
  - 🦁 **Leão (+2000 XP)**: Fúria dourada (`1.70`) com pilar de luz celeste de 90m, onda de choque e screen shake.
  - *Exemplo de quantidade:* 10 rosas (`1.30`) superam 1 rosa (`1.20`), mas continuam abaixo de 1 galáxia (`1.60`). O multiplicador final nunca passa de `1.80`.
  - *Presentes enviados durante a fase de votação já ficam acumulados para a largada!*
- **Curtidas em Rajada:** quando alguém manda **5 ou mais curtidas de uma vez**, o cavalo que a pessoa apoia — ou o **último colocado da pista**, quando o autor não é identificável — recebe **+0.2 m/s** de velocidade por 1,5 segundo. O empurrão **soma** (não multiplica) e toda a torcida leve fica travada em **+0.9 m/s**: por mais que o chat curta, o cavalo nunca acelera fora de controle. Curtida é gratuita e infinita: não rende XP nem compete com presentes.
- **Rajada em Massa:** Simule 20 ou 50 espectadores votando simultaneamente para testes de estresse.
- **Controle de Clima:** Sol Claro, Pôr do Sol, Noite com Refletores do Estádio, Chuva, Tempestade e Vento.

### 4. Gerenciamento de Usuários (Admin):
- **👥 Usuários Cadastrados:** lista todos os espectadores no banco com XP, nível, corridas e vitórias, ordenados por XP.
- **🧹 Zerar (por usuário):** zera XP, nível e estatísticas de um espectador específico, mantendo a identidade dele no banco.
- **🧨 Zerar TODOS:** zera XP, nível e estatísticas de todos os espectadores de uma vez. Útil para começar uma temporada nova.

### 5. Console com Histórico e Filtros:
- Abas de filtragem: `Todos`, `🎁 Presentes`, `💬 Votos`, `🏁 Fases`.
- Contadores em tempo real do total de presentes e votos na transmissão.
- Botões para `🗑️ Limpar` e `📋 Copiar Histórico`.

---

## 🐎 Os 8 Cavalos e Personalidades (Pasta `horses/`)

Cada cavalo possui seu arquivo de configuração próprio dentro da pasta **`horses/`** (`1_relampago.json` até `8_fantasma.json`), permitindo personalizar cores da pelagem, crina, cascos, farda e capacete do jóquei, estilo visual, nome e atributos:

1. **#1 RELÂMPAGO (Dourado):** Arrancada explosiva; lidera no início e perde fôlego na reta final.
2. **#2 TROVÃO (Azul):** Arrancada final avassaladora no último quarto da pista (750m finais na pista de 3000m).
3. **#3 FURACÃO (Verde):** Ritmo consistente e imune à fadiga.
4. **#4 RAIO (Vermelho):** Caçador no vácuo; acelera quando corre atrás dos líderes.
5. **#5 PANTERA (Preto):** Especialista em curvas e ultrapassagens pelo lado interno da pista.
6. **#6 TITÃ (Bronze):** Tanque inabalável; ganha vantagem em pistas molhadas/lama.
7. **#7 NEVASCA (Branco):** Frio e técnico; cresce de rendimento na chuva e no vento.
8. **#8 FANTASMA (Roxo):** Imprevisível; alto fator sorte com arrancadas repentinas.

**A briga é justa:** todo arquétipo é neutro no relógio — personalidade decide **quando** cada um é forte, nunca **se** é mais rápido. Em clima sorteado, cada cavalo vence ~12,5% das corridas (medido com `python tools/monte_carlo.py 1000` na pista de 3000m: todos entre 9,8% e 16,9%, margem média de chegada de ~488ms; travado pelos testes: nenhum cavalo fora de 6%–21% em 200 corridas). O **clima muda a cada corrida** (nunca repete o anterior), com intensidade sorteada que pesa de verdade, anúncio do locutor com os favoritos daquele tempo — e o tempo pode **virar no meio da prova**, com a cena transicionando suave e a voz avisando.

---

## 🔄 Ciclo Autônomo da Transmissão (EventDirector)

O jogo roda infinitamente sem necessidade de operador humano:
1. **ESCOLHA SEU CAVALO (30s):** Grade na tela com os 8 cavalos e contadores de torcida ao vivo. O chat comenta `1` a `8` ou o nome do cavalo.
2. **CONTAGEM REGRESSIVA (5s):** 5.. 4.. 3.. 2.. 1.. com bips sonoros e portões dos boxes se preparando.
3. **CORRIDA AO VIVO (~1min50, oval de 3000m):** Física a 60 ticks/s, **locução ao vivo** (abertura, disputa e reta final narradas pelo locutor; chegada apertada ganha foto-finish), clima anunciado na abertura e que pode **virar no meio da prova**, câmeras cinematográficas inteligentes, galope procedural sincronizado, poeira de cascos, cercas contínuas em 360º e turbos. **Digitar o número de um cavalo durante a prova dá um empurrãozinho de torcida** nele (só pela farra — não muda apuração nem XP).
4. **DISPUTA DE CHEGADA E PÓDIO (10s):** Ao cruzar a linha de chegada, a câmera acompanha a disputa pelo 2º e 3º lugares e 10,5s depois avança para o pódio com troféus, fanfarra orquestral e chuva de confetes em órbita 360º.
5. **XP E NÍVEIS (6s):** Distribuição de XP no banco de dados SQLite e aviso sonoro de "Level Up".
6. **TOP JOGADORES (10s):** Exibição do ranking geral dos maiores apoiadores da LIVE.
7. *Reinicia automaticamente para a próxima corrida com novo número de prova!*

---

## 🔌 Conectar ao TikTok LIVE Real

Quando for iniciar sua transmissão ao vivo no TikTok:
```bash
python main.py --tiktok-user SEU_USUARIO_TIKTOK --test-mode=False
```
*(Substitua `SEU_USUARIO_TIKTOK` pelo seu nome de usuário do TikTok sem o `@`).*

---

## 🔊 Narração por Voz (TTS)

A live ganha locução: presente, chegada, votação aberta, largada, vencedor **e a própria corrida** viram FALA — mesmo motor do `tiktok-live-pixel` (edge-tts gera o mp3 → MCI do Windows toca → arquivo apagado na hora). A voz sabe quem presenteou e qual o cavalo: *"Ana mandou 5x Rose pro Relâmpago!"*. Nome de cavalo em CAIXA ALTA é falado em caixa normal, senão soa grito (e nome curto sai letra por letra).

- **Locução ao vivo e Chegada Imediata com Fade-Out Suave:** durante a prova o locutor chama a **abertura** (150m), o **placar** (a cada ~300m, sempre citando o trio da frente), a **disputa** (a cada ~450m) e a **reta final** (2.880m) — 19 marcos cobrindo os 3000m a uma fala a cada ~5s. **No exato milissegundo em que o cavalo cruza a fita dos 3000m, a voz dispara o anúncio do vencedor sem atraso**, aplicando um **fade-out musical suave em ~240ms** na fala anterior (sem cortes secos no meio da frase) antes de chamar o campeão! Chegada decidida por menos de 150ms ganha foto-finish antes do anúncio do campeão.
- **Áudio Ducking para Boas-Vindas:** quando alguém entra na live durante uma fala, o narrador **reduz automaticamente o som atual em 50%**, reproduz o oi de boas-vindas com **destaque em volume máximo (100%)** e, ao terminar a saudação, **restaura suavemente o som para o volume original (100%)**!
- **Anti-Repetição Consecutiva (Shuffle Bag):** sistema de baralhos embaralhados que consome todas as dezenas de frases de cada momento antes de repetir, impedindo matematicamente que a mesma frase saia duas vezes seguidas mesmo com as vozes alternando.
- **Ligar/desligar:** `config/config.json` → `"tts": { "active": true }`. Vem ligada.
- **Vozes:** `tts.voz` (padrão `pt-BR-FranciscaNeural`) e `tts.vozes` — lista por onde as falas rodiziam; lista vazia = sempre a `tts.voz`. As três vozes pt-BR do serviço já vêm configuradas no rodízio.
- **Quem entra na live** ganha um oi falado. `tts.anunciar_entrada: false` cala só a chegada e mantém o resto (útil em live muito cheia).
- **Frases:** ficam em `game/falas.py` — ou troque por listas próprias em `tts.falas`, `tts.boas_vindas`, `tts.votacao`, `tts.largada`, `tts.vencedor` e nas da locução (`tts.corrida_abertura`, `tts.corrida_disputa`, `tts.corrida_placar`, `tts.reta_final`, `tts.foto_finish`) no config, sem tocar em código.
- **Teste de ouvido:** `python tools/smoke_audio.py` fala uma de cada momento, sem abrir live.
- **Não precisa da biblioteca de voz?** O jogo segue mudo e em frente: falha de áudio vira log, nunca derruba a corrida.

---

## 📖 Documentação Completa para Modificações

Para entender a fundo a física da pista oval, fórmulas de velocidade, adicionar novos cavalos, criar novos presentes ou customizar as câmeras e o 3D:
👉 Consulte o arquivo **`DOCUMENTACAO.md`** na raiz do projeto.
