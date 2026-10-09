# 📚 Documentação Técnica Completa - TikTok LIVE Corrida de Cavalos 3D

Bem-vindo à documentação técnica e de desenvolvimento do jogo **TikTok LIVE Corrida de Cavalos 3D**. Este manual foi elaborado com riqueza de detalhes para que você (ou qualquer desenvolvedor) possa entender a arquitetura completa, customizar atributos, adicionar novos cavalos, criar novos presentes e eventos climáticos, alterar a câmera, estilizar o HUD e operar transmissões profissionais no OBS Studio.

---

## 1. Visão Geral e Princípios Fundamentais

### 1.1 Compliance Rigoroso (100% Virtual)
- **Sem Dinheiro Real:** O sistema não possui apostas, saques, conversão de pontos para moeda fiduciária, prêmios em dinheiro ou qualquer mecânica de jogo de azar.
- **Pontuação e Progressão:** Todos os pontos distribuídos são estritamente **XP e Níveis Virtuais** para engajamento dos espectadores da LIVE, desbloqueio de títulos honoríficos, distintivos (*badges*) e ranking global.
- **Presentes:** Presentes enviados no TikTok LIVE funcionam exclusivamente como suporte de torcida, gerando efeitos visuais na tela (faíscas, ondas de choque, chamas nos cascos) e aceleradores temporários de velocidade (*boosts* de 2 a 6 segundos).

### 1.2 Fluxo de Dados Desacoplado
```text
           [ TikTok LIVE Real ]                   [ Painel Streamer (/test) ]
                    │                                          │
                    └───────────────────┬──────────────────────┘
                                        │
                                        ▼
                             [ TikTokEventAdapter ]
                      (Sanitização, Anti-Flood, Rate Limit)
                                        │
                                        ▼
                             [ EventBus Assíncrono ]
                               (asyncio.Queue)
                                        │
                                        ▼
                             [ EventDirector (Loop) ]
                ┌───────────────────────┴───────────────────────┐
                ▼                                               ▼
      [ RaceEngine (60 ticks/s) ]                     [ Banco SQLite Assíncrono ]
   - Física contínua em pista oval                 - Tabela viewers (XP, Níveis)
   - Personalidade dos 8 cavalos                   - Tabela races (Histórico de Provas)
   - Boosts, Fadiga e Clima                        - Tabela race_results (Pódios)
                │                                               │
                └───────────────────────┬───────────────────────┘
                                        │
                                        ▼
                          [ FastAPI WebSocket Broadcast ]
                             (ws://localhost:8000/ws)
                                        │
                                        ▼
                          [ OBS Studio (Browser Source) ]
                         Three.js 3D + HUD 9:16 + Web Audio
```

---

## 2. Mapa Completo de Arquivos do Projeto

```text
tiktok_live_cavalo/
├── config/
│   ├── config.json              # Configurações de tempo, XP, regras e os 8 cavalos
│   └── settings.py              # Validação de tipos e schema Pydantic
├── backend/
│   ├── database/
│   │   ├── connection.py        # Pool e conexão aiosqlite em modo WAL de alta performance
│   │   ├── models.py            # DDL SQL das tabelas (viewers, races, choices, results)
│   │   └── repository.py        # Queries assíncronas de gravação/leitura de XP e ranking
│   ├── event_bus.py             # Barramento assíncrono pub/sub
│   ├── security.py              # Rate limiting em janela de 1s e sanitização de texto
│   └── progression.py           # Fórmula matemática de curva de níveis (Lv 1 ao 100)
├── game/
│   ├── engine.py                # Motor físico a 60 ticks/s, foto-finish e líderes
│   ├── director.py              # Máquina de estados contínua (VOTING -> PODIUM -> LEADERBOARD)
│   ├── horses.py                # Modelagem do estado de cada cavalo, fadiga e boosts
│   ├── physics.py               # Trajetória oval, derivadas tangenciais e raias 3D
│   ├── weather_events.py        # Modificadores climáticos (Sol, Chuva, Tempestade, Vento)
│   ├── narrador.py              # Voz da live: fila + thread, edge-tts gera, MCI toca e apaga
│   └── falas.py                 # As frases faladas (presente, chegada, votação, largada, vencedor)
├── tiktok/
│   ├── adapter.py               # Conector TikTokLiveClient com auto-reconnect
│   ├── mock_adapter.py          # Emulador de eventos para o Modo de Teste
│   └── parser.py                # Parser de comentários ("1", "relampago", presentes, /turbo)
├── web/
│   ├── server.py                # Servidor FastAPI, rotas REST e WebSocket broadcast
│   └── static/
│       ├── css/
│       │   ├── styles.css       # Estilos da transmissão OBS (1080x1920 vertical 9:16)
│       │   └── test_panel.css   # Estilos do painel de controle do streamer (/test)
│       ├── js/
│       │   ├── three.min.js     # Three.js r128 local (independente de internet)
│       │   ├── scene.js         # Cenário 3D: pista, gramado, arquibancadas, árvores, lago
│       │   ├── horses_view.js   # Modelagem 3D procedural dos cavalos, galope e emblemas
│       │   ├── particles.js     # Poeira de cascos, faíscas, ondas de choque e confetes
│       │   ├── camera.js        # Diretor de câmeras dinâmicas de transmissão de TV
│       │   ├── audio.js         # Sintetizador procedural Web Audio API (galope, torcida)
│       │   ├── hud.js           # Gerenciador da interface, placar, régua e pódio
│       │   ├── client.js        # Loop principal de renderização a 60 FPS
│       │   └── test_panel.js    # Lógica interativa do painel admin com WebSocket
│       ├── index.html           # Página capturada pelo OBS Studio (Browser Source)
│       └── test.html            # Interface de controle do streamer no navegador (/test)
├── tools/
│   └── smoke_audio.py           # Teste de ouvido da voz, sem abrir live
├── tests/                       # 43 testes automatizados (pytest) com 100% de aprovação
├── main.py                      # Ponto de entrada do sistema (`python main.py`)
├── requirements.txt             # Dependências Python (fastapi, uvicorn, aiosqlite, etc.)
├── README.md                    # Guia rápido de inicialização
└── DOCUMENTACAO.md              # Este manual técnico completo
```

---

## 3. Configurações Globais (`config/config.json`)

Para calibrar o ritmo da transmissão sem encostar em código Python, edite `config/config.json`:

```json
{
  "race_duration_seconds": 35.0,        // Duração máxima da corrida (segundos)
  "voting_duration_seconds": 30.0,      // Tempo para os espectadores escolherem os cavalos
  "countdown_duration_seconds": 5.0,    // Contagem regressiva antes da largada (5.. 4.. 3..)
  "podium_duration_seconds": 8.0,       // Duração da tela de pódio dos vencedores
  "xp_duration_seconds": 6.0,           // Duração da tela de distribuição de XP
  "leaderboard_duration_seconds": 10.0, // Duração da tela de TOP jogadores da LIVE
  "track_length_meters": 1000.0,        // Comprimento da pista oval em metros virtuais
  "tick_rate": 60,                      // Taxa de atualização física por segundo (60 Hz)
  "tts": {
    "active": true,                     // Narração por voz ligada/desligada
    "voz": "pt-BR-FranciscaNeural",     // Voz padrão (e do rodízio, se "vozes" vazio)
    "vozes": [                          // Rodízio de vozes (lista vazia = sempre a "voz")
      "pt-BR-FranciscaNeural",
      "pt-BR-AntonioNeural",
      "pt-BR-ThalitaMultilingualNeural"
    ],
    "rate": "+8%",                      // Velocidade da fala (edge-tts)
    "pitch": "+3Hz",                    // Tom da fala (edge-tts)
    "anunciar_entrada": true,           // Oi falado para quem entra na live
    // Listas de frases próprias (opcionais): ausente/vazia = as do jogo
    // (game/falas.py); preenchida, substitui a lista inteira. Chaves:
    // "falas" (presentes), "boas_vindas", "votacao", "largada", "vencedor" e
    // as da locução ao vivo — "corrida_abertura", "corrida_disputa",
    // "corrida_placar", "reta_final", "foto_finish", "clima" (o tempo da
    // corrida na abertura) e "clima_virada" (o tempo virando na prova).
    "falas": null
  },
  "xp": {
    "participation": 20,                // XP ganho por escolher qualquer cavalo
    "cheer": 5,                         // XP ganho por mensagens de torcida
    "top_3": 50,                        // XP ganho se o cavalo escolhido for 2º ou 3º
    "win": 150,                         // XP ganho se o cavalo escolhido for o campeão (1º)
    "gift_small": 100,                  // XP virtual por presente pequeno (ex: Rosa)
    "gift_medium": 250,                 // XP virtual por presente médio (ex: Donut)
    "gift_large": 500                   // XP virtual por presente grande (ex: Galáxia)
  }
}
```

---

## 4. Cavalos, Atributos e Arquétipos de Personalidade (Pasta `horses/`)

Cada cavalo agora possui seu **próprio arquivo JSON de configuração independente** dentro da pasta dedicada **`horses/`** na raiz do projeto. Isso permite customizar individualmente o visual completo de cada animal (corpo, crina, cascos, farda e capacete do jóquei, estilo visual, nome, número e atributos):

```text
horses/
├── 1_relampago.json
├── 2_trovao.json
├── 3_furacao.json
├── 4_raio.json
├── 5_pantera.json
├── 6_tita.json
├── 7_nevasca.json
└── 8_fantasma.json
```

### Exemplo de Arquivo de Configuração (`horses/1_relampago.json`):
```json
{
  "id": 1,
  "number": 1,
  "name": "RELÂMPAGO",
  "body_model": "slender_racer",        // Modelo 3D ("classic", "armored", "pegasus", "cyber", "heavy_tank", "unicorn", "spectral", "slender_racer")
  "visual_style": "solar",              // Estilo temático ("solar", "storm", "fire", "nature", "shadow", "earth", "ice", "spectral")
  "color_hex": "#F59E0B",               // Cor principal da pelagem do cavalo
  "secondary_color_hex": "#FEF3C7",     // Cor da manta de sela
  "mane_color_hex": "#D97706",          // Cor da crina e da cauda do cavalo
  "hoof_color_hex": "#1E293B",          // Cor dos 4 cascos
  "jockey_silk_hex": "#F59E0B",         // Cor da jaqueta do jóquei
  "jockey_helmet_hex": "#FFFFFF",       // Cor do capacete do jóquei
  "personality": "FRONT_RUNNER",        // Arquétipo comportamental
  "base_speed": 28.08,                  // Velocidade base em m/s (~101 km/h)
  "acceleration": 10.5,                 // Aceleração nos primeiros metros
  "stamina": 8.0,                       // Resistência à fadiga
  "luck": 6.0,                          // Chance de picos orgânicos
  "aggressiveness": 7.5,                // Bônus em disputa direta
  "description": "Larga em velocidade máxima, mas perde fôlego no final."
}
```

### 4.1 Catálogo de Corpos 3D Disponíveis (`web/static/js/bodies/`)
Cada modelo 3D é um arquivo JavaScript independente na pasta `web/static/js/bodies/`. Você escolhe qual corpo o cavalo vai ter simplesmente mudando o campo `"body_model"` no JSON dele:

| Modelo (`body_model`) | Arquivo JS | Descrição Visual e Características 3D |
|:---|:---|:---|
| **`classic`** | `classic_body.js` | **Puro Sangue de Turfe:** Proporções atléticas clássicas, manta elegante, pescoço arqueado e jóquei padrão. |
| **`armored`** | `armored_body.js` | **Cavalo de Guerra Blindado:** Peitoral de aço chanfrado (*gorget*), proteção na garupa, caneleiras de metal nas 4 patas e chanfron reforçado na cabeça. |
| **`pegasus`** | `pegasus_body.js` | **Pégaso Alado:** Asas celestiais de penas articuladas nas laterais que **batem no ritmo do galope**, cascos dourados e cauda longa sedosa. |
| **`cyber`** | `cyber_body.js` | **Mecha Cyberpunk:** Painéis metálicos angulares, turbinas propulsoras nos flancos com luzes neon ciano, crina de feixe de LED e viseira holográfica na cabeça. |
| **`heavy_tank`** | `heavy_tank_body.js` | **Titã Juggernaut:** Tronco maciço e musculatura colossal (1.95m de largura), pescoço grosso, crina densa e patas pesadas estilo *Clydesdale*. |
| **`unicorn`** | `unicorn_body.js` | **Unicórnio Místico Radiante:** Chifre espiral arco-íris monumental de 1.85m iluminado com gradiente em 6 cores (magenta, violeta, ciano, esmeralda, dourado e diamante), gemas espiraladas, estrela de diamante no topo, crina em 4 mechas multicoloridas pastel e cauda mágica tricolor. |
| **`spectral`** | `spectral_body.js` | **Fantasma Espectral:** Materiais translúcidos com brilho etéreo próprio, costelas fantasmagóricas visíveis, cauda fluida e olhos azuis brilhantes. |
| **`slender_racer`** | `slender_racer_body.js` | **Velocista Aerodinâmico:** Corpo afilado e rebaixado (3.5m), pescoço esticado em cunha e jóquei deitado em postura ultra-aerodinâmica de dragster. |

### 4.2 Como Criar um Novo Modelo de Corpo 3D
1. Crie um arquivo em `web/static/js/bodies/meu_modelo.js`.
2. Registre seu modelo no catálogo global:
   ```javascript
   window.HorseBodyRegistry["meu_modelo"] = function buildMeuModelo(cfg, scene, particles) {
     const group = new THREE.Group();
     const mats = HorseBodyUtils.createMaterials(cfg);
     // ... monte suas geometrias Three.js aqui ...
     return {
       id: cfg.id, number: cfg.number, name: cfg.name, group: group,
       body: body, neck: neck, legs: legs, tail: tail,
       aura: auras.aura, mythicAura: auras.mythicAura,
       emblem: badgeObj.emblem, setEmblem: badgeObj.setEmblem,
       badge: badgeObj.badge, phase: Math.random() * Math.PI * 2,
     };
   };
   ```
3. Adicione a tag `<script src="/static/js/bodies/meu_modelo.js"></script>` em `web/static/index.html`.
4. Defina `"body_model": "meu_modelo"` no JSON do cavalo que desejar!

---

### 4.3 Tabela Oficial de Cavalos e Configurações Iniciais

| Nº | Nome | Arquivo JSON | Modelo 3D (`body_model`) | Cor / Crina | Arquétipo |
|:---:|:---|:---:|:---:|:---:|:---|
| **#1** | **RELÂMPAGO** | `1_relampago.json` | `slender_racer` | Ouro / Âmbar | `FRONT_RUNNER` |
| **#2** | **TROVÃO** | `2_trovao.json` | `cyber` | Azul / Meia-noite | `CLOSER` |
| **#3** | **FURACÃO** | `3_furacao.json` | `classic` | Verde / Floresta | `PACER` |
| **#4** | **RAIO** | `4_raio.json` | `pegasus` | Vermelho / Bordô | `DRAFTER` |
| **#5** | **PANTERA** | `5_pantera.json` | `armored` | Preto / Carvão | `CORNER_SPECIALIST` |
| **#6** | **TITÃ** | `6_tita.json` | `heavy_tank` | Bronze / Castanho | `JUGGERNAUT` |
| **#7** | **NEVASCA** | `7_nevasca.json` | `unicorn` | Prata / Cinza | `COLD_TACTICIAN` |
| **#8** | **FANTASMA** | `8_fantasma.json` | `spectral` | Roxo / Índigo | `WILDCARD` |

**Todos os arquétipos são neutros no relógio.** O que decide corrida é o **tempo** ($tempo = distância/velocidade$), então o contrato de cada personalidade é $\sum (fração\ da\ pista / fator) = 1.00$ — média harmônica, não a média dos fatores; é o teste `test_personalidade_decide_quando_vence_nao_se_vence` que trava essa conta. O efeito prático, medido com `python tools/monte_carlo.py 1000`: em clima sorteado, **cada cavalo vence ~12,5%** (todos entre 10% e 15%, margem média de chegada de ~180ms), e o guardião `test_nenhum_cavalo_fica_para_tras` reprova qualquer cavalo fora de **8%–17% em 200 corridas**. Personalidade define **quando** cada um é forte — nunca **se** é mais rápido.

### Como Adicionar um Novo Cavalo (ex: #9 TITÂNIO):
1. Crie um novo arquivo JSON dentro da pasta `horses/`, por exemplo: `horses/9_titanio.json`.
2. Preencha com os dados desejados (`id: 9`, `number: 9`, `name: "TITÂNIO"`, cores, jockey, etc.).
3. Adicione o nome no dicionário `HORSE_NAME_MAP` em `tiktok/parser.py`: `"titanio": 9`.
4. Pronto! O sistema carrega dinamicamente qualquer quantidade de cavalos da pasta `horses/`.

---

## 5. Sistema de Presentes e Efeitos Especiais

### 5.1 Emojis Dinâmicos e Destaque ao Apoiador
Ao receber um presente, o cavalo correspondente exibe uma **pill 3D flutuante** acima da cabeça contendo:
1. O **Emoji oficial do presente** renderizado em alta definição (`Segoe UI Emoji`).
2. O **`@nome_do_apoiador`** em texto branco contrastante com fundo escuro translúcido.

### 5.2 Tabela de Presentes e Escala de Valor (`game/director.py`)
No topo de `game/director.py` existe a tabela `GIFT_TIERS`, que casa o nome do presente por substring (inglês e português) e define bônus, duração, XP, emoji e o tipo lendário:

| Presente | Multiplicador | Duração | XP |
|---|---|---|---|
| 🦁 Leão (`lion`, `leao`) | `1.70` | 9.0s | 2000 |
| 🐉 Dragão (`dragon`, `dragao`) | `1.65` | 8.5s | 1800 |
| 🌌 Galáxia (`galaxy`, `galaxia`, `universe`) | `1.60` | 8.0s | 1500 |
| 🧢 Boné (`cap`, `bone`) | `1.35` | 5.5s | 250 (config) |
| 🍩 Donut (`donut`) | `1.35` | 5.5s | 250 (config) |
| ☕ Café (`coffee`, `cafe`) | `1.20` | 4.5s | 100 (config) |
| 🌹 Rosa (`rose`, `rosa`, `heart`, `coracao`) | `1.20` | 4.0s | 100 (config) |
| 🎁 Qualquer outro (padrão) | `1.12` | 3.0s | 100 (config) |

**Quantidade enviada de uma vez** amplia o bônus: cada unidade extra soma `+10%` do delta do presente (máximo de 5 extras) e o multiplicador final nunca passa do teto `1.80`.
Exemplo: 10 rosas = `1.30` — mais forte que 1 rosa (`1.20`), porém mais fraco que 1 galáxia (`1.60`).

**Presente sem escolha vai para um cavalo SORTEADO.** Se o presente chega de quem nunca digitou o número de nenhum cavalo, o empurrão cai num cavalo sorteado — e não mais no líder da pista. Sortear mata dois vícios de uma vez: o líder parava de ganhar combustível de graça (era ele que vencia quase sempre) e quem doa sem escolher espalha emoção pelo páreo inteiro.

Para **adicionar um presente novo**, basta inserir uma linha em `GIFT_TIERS` (sem tocar em nenhuma lógica) e, se ele tiver efeitos visuais próprios no 3D, mapear o `legendary` correspondente no front-end.

### 5.2.1 Curtidas em Rajada (Boost de Torcida)
Quando alguém manda **5 ou mais curtidas de uma vez** (`LIKE_BURST_MIN`), o cavalo que a pessoa apoia — ou um cavalo **sorteado**, quando o TikTok não informa o autor — recebe um boost `GALERA CURTIU` de `1.02` a `1.05` por 3 segundos.
Curtida é gratuita e infinita: o empurrão é de propósito **bem leve**, não rende XP e não grava nada no banco, para nunca competir com os presentes.

### 5.2.2 Torcida no Chat (número digitado com a corrida rolando)
Quando alguém digita o **número de um cavalo durante a corrida** (fase `RACING`), o cavalo leva um empurrão de torcida `TORCIDA NO CHAT` (`+3%` por 2,5s — `TORCIDA_POWER`/`TORCIDA_DURATION_SECONDS` em `game/director.py`) e o telão anuncia *"{nome} torce pelo {cavalo}!"*.
É um carinho, não um voto: não vale na apuração, não mexe na lista de apoiadores do cavalo, não rende XP e não fala nada na voz — o chat pode incentivar a cada mensagem sem virar bagunça na fila da narração.

### 5.3 Presentes Míticos e Super Raros (Leão, Galáxia, Dragão)
Quando um presente raro é enviado, os seguintes efeitos são ativados simultaneamente:
* **Pilar de Luz Celestial de 90 Metros:** Um feixe vertical de energia translúcida desce do céu diretamente em cima do cavalo apoiado.
* **Onda de Choque Radial no Solo:** Anel luminoso expansivo que varre a areia da pista com raio de até 35 metros.
* **Tremor Sísmico de Câmera (*Screen Shake*):** A câmera de transmissão treme para transmitir o impacto e a potência do presente.
* **Aura Mítica Tórica e Rastro de Chamas:** Um anel energético brilhante gira em alta velocidade ao redor do cavalo, deixando brasas e labaredas no chão.
* **Banner Mítico no HUD:** Card monumental no topo da tela com borda dourada/violeta incandescente e pulsação em toda a moldura da live.
* **Áudio de Trovão e Sub-Grave:** Impacto estrondoso de 140 Hz descendo até 25 Hz com o clamor da multidão do estádio a 100% de volume por 4 segundos.
* **Turbo Massivo:** até +70% de velocidade por 9 segundos (Leão; ver tabela `GIFT_TIERS` em 5.2) e até +2.000 XP para o apoiador.

### 5.4 Retenção de Presentes Pré-Largada
Se um espectador enviar presentes durante a fase de **Votação (`VOTING`)** ou **Contagem Regressiva (`COUNTDOWN`)**:
* O cavalo já recebe o turbo nos boxes e já exibe o emoji e o `@nome_do_apoiador` antes mesmo da largada!
* O bônus de velocidade entra em ação assim que os portões se abrem, garantindo que nenhum presente enviado seja desperdiçado.

---

## 6. Mecânica Física, Pista Oval e Raias (`game/physics.py`)

A pista é modelada como uma oval clássica de hipódromo com 1.000 metros de comprimento percorrível:

```text
               Curva 2 [800m - 1000m]          Curva 1 [300m - 500m]
                   (Raio: 63.66m)                  (Raio: 63.66m)
                  ┌───────────────┐               ┌───────────────┐
                  │               │               │               │
                  │   Reta Oposta │               │               │
                  │   [500m - 800m, z = -63.66m]  │               │
                  │                               │               │
                  │   Infield (Lago, Telão LED,   │               │
                  │   Gramado, Árvores)           │               │
                  │                               │               │
                  │   Reta Principal              │               │
                  │   [0m - 300m, z = +63.66m]    │               │
                  │   Largada: x=-150             │               │
                  │   Chegada: x=+150             │               │
                  └───────────────┘               └───────────────┘
```

### 6.1 Distribuição Exata das Raias
* A pista tem **28 metros de largura** (se estendendo de $z = 49.66\text{m}$ até $z = 77.66\text{m}$).
* As 8 raias foram distribuídas com **3.2 metros de largura por raia** a partir da base $R_{\text{base}} = \text{radius} - 11.2\text{m}$:
  $$\text{Raia}(i) = 52.46\text{m} + (i - 1) \times 3.2\text{m}$$
  * Raia 1 (Interna) = **$52.46\text{m}$** $\to$ perfeitamente alinhada com o Box #1.
  * Raia 8 (Externa) = **$74.86\text{m}$** $\to$ perfeitamente alinhada com o Box #8.
* Margem de segurança de ~2.8m de cada lado em relação às cercas interna e externa: **zero cavalos escapam da pista ou atravessam cercas**, com muito mais espaço lateral para ultrapassagens e exibição dos modelos 3D.
* **Cabines dos Boxes:** Cada box de espera tem **6.6 metros de comprimento** por **3.2 metros de largura** e **3.2 metros de altura**, acomodando perfeitamente qualquer modelo de corpo (inclusive Titã Juggernaut e Dragster) com folga na frente e atrás.

### 6.2 Rotação Tangencial Contínua em Curvas (`rot_y`)
Em vez de ângulos estáticos que causavam giros bruscos, a orientação do cavalo é calculada através da derivada tangencial contínua da trajetória:
```python
x, z = self._compute_point(dist_mod, r)
x_next, z_next = self._compute_point((dist_mod + 0.25) % self.track_length, r)
rot_y = math.atan2(x_next - x, z_next - z)
```
No cliente Three.js (`horses_view.js`), a interpolação angular normaliza as diferenças entre $-\pi$ e $+\pi$:
```javascript
let diffRot = targetRotY - horseObj.group.rotation.y;
while (diffRot < -Math.PI) diffRot += Math.PI * 2;
while (diffRot > Math.PI) diffRot -= Math.PI * 2;
horseObj.group.rotation.y += diffRot * 0.45;
```
Isso faz com que os cavalos se inclinem e façam as duas curvas com naturalidade, sempre galopando para a frente da pista.

---

## 7. Cenário 3D e Cercas Paramétricas (`web/static/js/scene.js`)

### 7.1 Portão de Largada Móvel Tubular Aberto (Céu Aberto e Visibilidade 100%)
O partidor foi desenhado com arquitetura **tubular aberta de alta tecnologia (*open roll-cage*)**, inspirada nos maiores hipódromos do mundo (Churchill Downs e Ascot), garantindo que os cavalos e seus nomes fiquem **completamente visíveis e desobstruídos sob o céu**:
* **Sem Teto Obstrutivo:** A antiga viga superior que cortava a visão dos cavalos e tapava as placas de nome flutuantes foi **completamente removida**. Os boxes são abertos ao céu, permitindo ver perfeitamente as cabeças, orelhas, chifres, jóqueis e os crachás holográficos (`#1 RELÂMPAGO`, etc.) de qualquer ângulo superior.
* **Divisórias Tubulares Vazadas:** Em vez de paredes opacas que escondiam os cavalos, cada box conta com **3 postes verticais esguios de aço escovado** e **3 longarinas horizontais abertas**, permitindo enxergar através dos boxes de qualquer ângulo.
* **Bumpers de Flanco Baixos (Cintura Baixa):** O acolchoamento verde turfe escuro (`#14532d`) com frisos cromados fica restrito à altura dos flancos ($y = 1.35\text{m}$, apenas 0.85m de altura). Abaixo dele (patas e cascos) e acima dele (dorso, asas, crina, cabeça e jóquei) **tudo é 100% aberto e visível**!
* **Cancelas Dianteiras Vazadas em V (*V-Doors*):** Portas articuladas com hastes de aço e almofadas baixas na cor de cada cavalo. A cabeça, os olhos e o pescoço do cavalo ficam totalmente visíveis olhando para a frente da pista. No início da prova (`RACING`), abrem 85º para a frente em um movimento mecânico fluido.
* **Placas Numeradas na Altura dos Olhos:** As placas 3D com as cores e números de cada cavalo ficam montadas no poste frontal a 2.3m de altura, sem cobrir o focinho nem os crachás flutuantes.
* **Semáforo de Partida em Mastro Lateral:** Os 3 holofotes sincronizados ficam montados em um mastro estilizado na lateral do partidor ($z = zMin - 1.2$), visíveis pela câmera e sem sobrecarregar a visão dos boxes.

### 7.2 Cercas de Turfe de Trilho Duplo com Flores
* **Cercas de Trilho Duplo (360 Graus):** Malha paramétrica contínua com **trilho superior a 1.35m** e **trilho intermediário a 0.75m**, além de tampas arredondadas no topo de cada poste vertical em PVC branco puro.
* **Canteiros de Flores na Sebe Viva Interna:** A sebe viva que contorna o perímetro interno da pista agora conta com **canteiros floridos multicoloridos** (petúnias vermelhas, flores amarelas, brancas e lilases).

### 7.3 Portal Monumental e Banner Ultra-HD 4K da Linha de Chegada
* **Banner de Chegada Ultra-HD (2048 x 512):** O banner foi construído como uma caixa suspensa 3D independente com iluminação própria em `MeshBasicMaterial`, **filtragem anisotrópica máxima (16x)** e mipmapping ativado, permanecendo **nítido, luminoso e legível tanto de dia quanto à noite**:
  * Face dianteira (+X) e traseira (-X) texturizadas em altíssima resolução sem distorções de geometria.
  * Fundo esportivo em fibra de carbono e vidro azul marinho escuro.
  * Moldura dupla dourada com cantos decorativos e luzes LED esportivas em toda a extensão.
  * Faixas laterais com bandeiras quadriculadas de turfe (*checkered flags*).
  * Subtítulo em dourado: `"★ TIKTOK LIVE GRAND PRIX DERBY ★"`.
  * Título monumental em branco incandescente com sombra 3D: `"🏁 LINHA DE CHEGADA 🏁"`.
  * Indicação métrica: `"FINISH LINE • 1000 METROS"`.

### 7.4 Movimento Cinético Contínuo e Fluidez 60-144 FPS (Dead Reckoning)
Para eliminar qualquer sensação de travamento (*stuttering*) ou engasgos decorrentes de variações naturais de latência nos pacotes de rede WebSocket:
* **Previsão Cinemática Contínua por Frame:** Em cada quadro do `requestAnimationFrame`, a posição do cavalo avança no espaço 3D usando seu vetor velocidade instantâneo:
  $$x_{\text{novo}} = x + v \cdot \sin(\text{rot}_y) \cdot dt$$
  $$z_{\text{novo}} = z + v \cdot \cos(\text{rot}_y) \cdot dt$$
* **Amortecimento Ponderado por Tempo Real:** As coordenadas do servidor são integradas suavemente com fator $\min(1.0, dt \times 9.0)$, absorvendo imperceptivelmente qualquer atraso ou jitter de rede sem desacelerações repentinas.
* **Resultado:** Animação de corrida sedosa e ultra-fluida a 60 FPS estáveis (e até 120/144 FPS em monitores de alta taxa de atualização).

### 7.5 Celebração Triunfal do Campeão (Cavalo Empinando, Relincho e Fogos 3D)
Ao término da prova, a tela de Pódio ganha um espetáculo visual cinematográfico:
* **Cavalo Campeão Empinando nas 2 Patas Traseiras (*Rearing Horse*):**
  * O tronco do vencedor ergue-se no ar a **~35º de inclinação**, elevando o corpo para **3.65m de altura**.
  * As duas patas dianteiras **pedalam vitoriosamente no ar** com joelhos articulados em movimentos orgânicos alternados.
  * As patas traseiras ficam **firmemente plantadas no solo do hipódromo**, suportando o peso do corpo empinado.
  * Se o campeão for o Pégaso, suas **três camadas de asas de penas se abrem majestosamente** para o céu.
* **Relincho Triunfal Procedural:** O sintetizador de áudio sintetiza em tempo real um relincho realista com varredura harmônica (650Hz a 1.450Hz) e vibrato laríngeo a 8Hz com formante passa-faixa.
* **Show de Fogos de Artifício 3D (*Victory Fireworks*):**
  * Foguetes pirotécnicos são disparados continuamente a cada 0.7s - 1.1s no entorno do vencedor.
  * Explodem em alturas de **22m a 40m** no céu da arena em esferas radiantes de 30+ partículas em 6 cores esportivas (dourado `#fbbf24`, esmeralda `#10b981`, ciano `#06b6d4`, magenta `#f43f5e`, roxo `#a855f7` e escarlate).
  * Físicas de gravidade parabólica, resistência aerodinâmica e decaimento luminoso, acompanhados de som de estouro e chuva de confetes.
* **Câmera Heroica em Contra-Plongée:** O diretor de câmeras aproxima a tomada para **14.5m** em órbita suave de 360º, apontando de baixo para cima para realçar a magnitude e a glória do animal campeão.
* **Torre dos Comissários e Cabine de Transmissão (*Stewards Tower*):** Edifício de observação envidraçado de 2 andares perto da linha de chegada, com base de madeira nobre, janelões panorâmicos em vidro azul espelhado, telhado colonial pontudo e mastro de antena esportiva.
* **Tendas Brancas de Paddock VIP & Hospitality:** 3 gazebos brancos de evento com cúpulas cônicas, colunas brancas e mesas redondas posicionadas na área de hospitalidade à beira da reta.
* **Cais de Madeira no Lago Ornamental:** Deck rústico de madeira com postes de amarração náuticos avançando sobre a água límpida do lago central.
* **Jumbotron LED de 34 Metros:** Telão no centro do Infield com suporte metálico treliçado exibindo o logotipo esportivo e avisos ao vivo.
* **Arquibancada Monumental:** 10 degraus de concreto com faixas de assentos, escadas entre os setores e fachada com faixa de publicidade; **~900 torcedores instanciados** (corpo + cabeça, cores e alturas variadas, pulando em fases próprias), camarote VIP de vidro espelhado com montantes, colunas, parede de fundo e 12 bandeiras no telhado que balançam com o vento.
* **Floresta Periférica:** Pinheiros e carvalhos 3D posicionados exclusivamente fora da pista (raio $\ge 92\text{m}$ nas curvas e $z \le -96\text{m}$ na reta oposta).
* **Placas de Distância Oficiais:** Marcadores verticais de turfe ao longo da pista: `800m`, `600m`, `400m`, `200m`, `100m` e `FINAL`.

### 7.4 Céu, Luz e Clima (o passe visual)

O fundo liso de cor única e a luz chapada eram o maior "cheiro de protótipo" da cena. Agora:

* **Céu com gradiente:** domo com shader próprio (cor do topo → cor do horizonte) + **sol em sprite** com brilho radial desenhado em canvas + **estrelas** que aparecem à noite. Cada clima tem a sua paleta (o pôr do sol tem céu roxo com horizonte laranja; a tempestade, chumbo).
* **Luz que modela:** luz **hemisférica** (céu azulado por cima, gramado esverdeado por baixo) + sol direcional com sombras + **preenchimento frio** do lado oposto (nenhuma sombra fica preta). Refletores do estádio acendem só no clima noturno.
* **Texturas procedurais:** grama com manchas tonais e areia com grãos e estrias longitudinais, geradas em canvas — **nenhum asset externo** para baixar ou versionar.
* **Clima mexe na pista:** chuva/tempestade **molham a areia** (escurece e ganha espelho); a neblina fecha o horizonte; a **tempestade dispara relâmpagos** — um clarão curto que acende o céu e o ambiente (e a fonte do lago pulsa de verdade).
* **O clima VIRA com transição:** trocar de clima (inclusive a **virada no meio da prova**) não é um corte seco: a cena caminha da paleta atual para a nova em **1,8s** (`DURACAO_TRANSICAO_CLIMA`), com suavização de entrada e saída — céu, neblina, luzes, nuvens e pista interpolam juntos, e o sol acende/apaga no meio do caminho. Trocar de clima de novo no meio de uma transição parte de onde a cena está (nada de piscar de volta).
* **Pipeline de cor sRGB:** `outputEncoding` do renderer + texturas de canvas marcadas como sRGB — sem isso o ACES escurece a cena inteira e as cores saem lavadas.
* **Contraste sob controle:** a exposição do tone mapping fica em **0.92** e ambiente/hemisfério são enxutos (0.33/0.42 no claro) contra um sol forte (1.5). Com a exposição antiga (1.05) os realces — areia, camisas brancas, céu — estouravam e a cena achatava; menos luz de preenchimento devolve sombra de verdade sem perder cor. Cada clima mantém a proporção na sua própria paleta (tabela `PALETAS_CLIMA`, ao lado da classe em `scene.js`).
* **Arquibancada de estádio:** degraus de concreto com **faixa azul de assentos** no espelho, **escadas** dividindo os setores, fachada frontal com **faixa de publicidade iluminada**, camarote VIP de vidro com montantes, colunas, parede de fundo e teto com testa. A torcida é **instanciada** (`InstancedMesh`: corpo + cabeça, 2 draw calls no lugar de ~900) com altura, camisa e tom de pele variados, pulando por fase própria — e cada fã respeita os corredores das escadas.
* **Vinheta de transmissão (CSS):** escurecimento suave nos cantos e na base, entre o canvas e o HUD — a imagem ganha cara de TV sem escurecer texto ou painel. O degrau do campeão no pódio tem um brilho varrendo, e o líder da torre de posições ganha glow.

---

## 8. Câmeras Cinematográficas (`web/static/js/camera.js`)

A câmera alterna de modo automaticamente conforme os acontecimentos da corrida:

1. **`CAM_START`:** Visão aberta panorâmica e elevada $(-210, 36, 140)$ focando os boxes de largada durante a votação e contagem.
2. **`CAM_CHASE`:** Câmera aérea esportiva recuada a **44m de distância** e **24m de altura** do cavalo líder, enquadrando os 8 cavalos sem aperto no formato vertical do celular.
3. **`CAM_SIDE`:** Câmera lateral aberta de helicóptero a **46m de distância lateral** e **28m de altura**, perfeita para acompanhar ultrapassagens nas curvas.
4. **`CAM_FINISH`:** Câmera angular na reta final $(186, 15, 87)$ focando a aproximação em alta velocidade para cruzar a linha quadriculada.
5. **`CAM_PODIUM`:** Órbita circular de 360 graus a 22m de raio ao redor do vencedor durante a celebração com chuva de confetes.

### Transição Contínua Pós-Chegada:
* Quando o cavalo vencedor cruza a linha de chegada (1000m), a câmera **não congela**: ela foca automaticamente no próximo cavalo ativo disputando o 2º e 3º lugares!
* A engine fecha a prova 3.5 segundos após a vitória e dispara imediatamente a tela de **PÓDIO** com órbita 360º.

---

## 9. HUD Esportivo Vertical (1080x1920) e Ajuste em Tempo Real

A interface do usuário foi desenhada no padrão das transmissões da **Fórmula 1 e turfe internacional**:

```text
┌────────────────────────────────────────────────────────┐
│ [🏇 CORRIDA #42 ⚡TEMPESTADE]  [🔴 AO VIVO]  [847m] [🔊] │  ← Top Bar
├────────────────────────────────────────────────────────┤
│ [───1───2──────3─────────4──5──────6──7────8────────🏁] │  ← Régua de Progresso
├────────────────────────────────────────────────────────┤
│                                                        │
│                                                        │
│                     ÁREA 3D LIVRE                      │
│             (Toda a pista, cavalos e cenário           │
│                 100% desobstruídos!)                   │
│                                                        │
│                                                        │
├────────────────────────────────────────────────────────┤
│ 🏁 CLASSIFICAÇÃO AO VIVO (Grid 4x2 no Rodapé)          │
│ [1º #1 RELÂMP. 450m] [2º #2 TROVÃO 442m] ... [8º #8]   │  ← Footer Ticker
└────────────────────────────────────────────────────────┘
```

* **Classificação no Rodapé (Footer):** Em vez de uma torre lateral vertical cobrindo a pista onde os cavalos correm, a classificação ao vivo foi reposicionada no **rodapé da tela** (`bottom: 24px`) em um grid de **2 colunas amplas por 4 linhas**.
  * **Exibição Estritamente em Corrida (`RACING`):** O HUD de posições fica **completamente oculto durante a votação (`VOTING`), contagem (`COUNTDOWN`), pódio e ranking**, evitando qualquer sobreposição sobre a cartela de escolha de cavalos. Ele surge automaticamente no momento da largada e desaparece ao cruzar a chegada.
  * **Nomes 100% Visíveis:** As colunas amplas com ~500px cada garantem que todos os nomes dos animais (`RELÂMPAGO`, `FANTASMA`, `FURACÃO`) sejam exibidos por inteiro sem cortes nem reticências.
* **Parser Inteligente e Flexível do Chat do TikTok (`tiktok/parser.py`):**
  * Aceita dígitos simples (`1`, `2`...), dígitos com hashtag (`#1`, `# 2`), dígitos repetidos em spam (`111`, `888`), prefixos comuns (`cavalo 3`, `no 4`, `num 5`) e números inseridos no meio de frases (`vai 1`, `bora 3!`, `eu vou de 7`).
  * Reconhece nomes de cavalos mesmo com letras e vogais repetidas pelo público empolgado da live (ex: `relampagooo`, `trovaooo`, `furacaooo`).
* **Notificações Toast Sem Emojis Duplicados:** As notificações de clima exibem exatamente 1 emoji no distintivo lateral, eliminando o emoji repetido no corpo do texto.
* **Agradecimento por Seguir e Rajada de 20+ Curtidas:**
  * **Novo Seguidor (`FollowEvent`):** O narrador agradece imediatamente na voz com áudio ducking e exibe um toast com distintivo `➕` na tela.
  * **20+ Curtidas (`LikeEvent`):** Ao atingir uma rajada de 20 ou mais curtidas seguidas, o narrador agradece o esforço do espectador na voz e exibe toast `❤️` na tela.
* **Prioridade Imediata para Presentes (Zero Delay):** Quando um apoiador envia uma Rosa ou outro presente, o narrador corta instantaneamente qualquer locução antiga de pista que estiver tocando e reproduz o agradecimento em **2 a 3 segundos** (em vez de esperar 1 minuto na fila).
* **Purga Automática de Áudio de Prova Anterior:** Ao término da corrida e no início da nova prova, todas as frases de corrida pendentes são descartadas e o áudio da prova anterior é interrompido via MCI, impedindo qualquer vazamento de áudio atrasado.

### A Top Bar ("CORRIDA #N") em detalhe:
* **Badge da corrida:** troféu em chip dourado + rótulo `CORRIDA` + número `#N` com gradiente. Quando uma corrida NOVA abre, o número salta na tela (flash) — o olho do espectador acha o marcador sozinho.
* **Chip de clima:** ☀️ SOL, 🌅 PÔR DO SOL, 🌃 NOTURNA, 🌧️ CHUVA, ⚡ TEMPESTADE ou 💨 VENTO — cada um com a sua cor. É **informação de aposta**: o clima da pista é sorteado ANTES da votação abrir, e cada cavalo tem o seu clima favorito (ver seção 8) — quem escolhe o cavalo já sabe em que tempo a prova vai ser.
* **Pill de status por fase:** votação é dourada, **AO VIVO é vermelha** (com pulso mais rápido), pódio dourado, XP verde e ranking azul — a fase se lê de longe, sem precisar ler o texto.
* **Relógio contextual:** na votação/contagem conta os segundos (fica vermelho e pisca nos últimos 5s); **na corrida vira a distância do líder** (ex.: `847m`, vermelho ao passar dos 900m — reta final); nas telas de resultado some (não há o que contar).

### Os modais centrais (votação, contagem, pódio, XP):

* **Cartela de votação:** grade 4×2 com o número, o nome e os **apoiadores ao vivo** de cada cavalo. Ela **fica na tela também durante a contagem regressiva** (o cabeçalho vira "VOTAÇÃO ENCERRADA!") — o número do countdown flutua **por cima** da cena, em vez de substituir o painel. Antes, a virada para a contagem trocava o modal inteiro e a cartela sumia de uma vez, bem na hora em que o público quer conferir os números finais.
* **Atualização sem piscar:** a cartela é montada uma vez por fase e só o texto dos contadores muda a cada voto (sem remontar o DOM). Remontar a cada update reiniciava a animação de entrada — o painel piscava a cada voto novo no chat.

### Controles de Calibração do HUD no Painel Admin (`/test`):
No **Card 4** de `http://localhost:8000/test`, você ajusta a interface do OBS ao vivo:
* **Tamanho do Placar (Escala):** Botões `➖ Menor (-10%)` e `➕ Maior (+10%)` (calibra de 60% a 160%).
* **Posição Vertical (Altura):** Botões `▲ Subir (-25px)` e `▼ Descer (+25px)` (posicionamento milimétrico).
* **Régua do Topo:** Botão para ocultar ou exibir a régua de progresso com um clique.

---

## 10. Painel do Streamer e Modo de Teste (`/test`)

Acesse em qualquer navegador em:
👉 **`http://localhost:8000/test`**

### Recursos Disponíveis:
1. **Controles Diretos de Corrida:**
   * ⏩ **Iniciar Corrida Logo:** Pula os 30s de votação e inicia a contagem e largada na hora.
   * 🏁 **Finalizar Corrida:** Força o encerramento da corrida e avança para o pódio imediatamente.
   * 🔄 **Próxima Corrida:** Reinicia o ciclo e prepara a próxima prova.
2. **Simulação de Comentários & Votos:** Digite ou clique nos botões rápidos (#1 ao #8, `/turbo`, etc.).
   * **Simulação de Entrada de Espectador:** Botão `👤 Simular Entrada na LIVE (Oi da Voz)` (`POST /api/test/inject_join`) para testar o anúncio sonoro de boas-vindas com ducking de áudio e log no terminal.
3. **Simulação de Presentes:** Dispare Rosa, Café, Donut, Boné, Leão (+2000 XP), Galáxia (+1500 XP) ou Dragão (+1800 XP).
4. **Simulação de Curtidas:** Rajadas de 5, 10 ou 30 curtidas de uma vez (`POST /api/test/inject_like`) para ver o empurrão leve da torcida.
5. **Rajada de Público:** Simule 20 ou 50 espectadores comentando e votando de uma vez só.
6. **Controles de Clima:** Sol, Pôr do Sol, Noite com Refletores, Chuva, Tempestade e Vento.
7. **👥 Gerenciamento de Usuários (Admin):** lista todos os espectadores cadastrados (XP, nível, corridas, vitórias) com botão **🧹 Zerar** por usuário e **🧨 Zerar TODOS** — zera XP, nível e estatísticas sem apagar as contas (`GET /api/test/viewers`, `POST /api/test/reset_viewer`, `POST /api/test/reset_all_viewers`).
8. **Console de Eventos Avançado:**
   * Abas de filtro: `[Todos]`, `[🎁 Presentes]`, `[💬 Votos]`, `[🏁 Fases]`.
   * Contadores em tempo real de presentes e votos acumulados.
   * Botões para `🗑️ Limpar` e `📋 Copiar Histórico`.

---

## 11. Banco de Dados SQLite e Progressão (`race_game.db`)

O banco SQLite roda de forma assíncrona com `aiosqlite` e journal mode WAL para máxima velocidade.

### Estrutura das Tabelas:
* **`viewers`:** `id`, `tiktok_username`, `display_name`, `xp`, `level`, `races_count`, `wins_count`, `favorite_horse_id`, `created_at`, `updated_at`.
* **`races`:** `id`, `race_number`, `status`, `winner_horse_id`, `total_participants`, `total_gifts`, `started_at`, `finished_at`.
* **`race_choices`:** `id`, `race_id`, `viewer_id`, `horse_id`, `created_at`.
* **`race_results`:** `id`, `race_id`, `horse_id`, `final_position`, `finish_time_ms`.

### Curva de Níveis:
$$\text{Nível}(XP) = \left\lfloor \left(\frac{XP}{100}\right)^{\frac{1}{1.35}} \right\rfloor + 1$$
Cada subida de nível gera uma notificação animada na tela com estrela dourada (**⭐ LEVEL UP!**).

---

## 12. Como Configurar e Transmitir no OBS Studio

1. Abra o **OBS Studio**.
2. No menu de Cenas, adicione uma nova fonte: **Navegador (Browser Source)**.
3. Defina os parâmetros:
   * **URL:** `http://localhost:8000/`
   * **Largura:** `1080`
   * **Altura:** `1920`
   * **Taxa de Quadros:** `60 FPS`
   * **Controlar áudio via OBS:** Marque para ouvir o áudio das corridas no mixer do OBS.
4. Abra o painel de testes em um segundo monitor: `http://localhost:8000/test`.
5. **Voz da corrida (TTS):** a narração falada sai pelo **alto-falante padrão do Windows** (fora do navegador). Adicione à cena uma fonte **Áudio do Desktop** — ou **Captura de Áudio do Aplicativo** apontando para o `python.exe` — para a voz entrar na transmissão. O som 3D do jogo continua vindo pelo Browser Source.
6. Para conectar à sua live real do TikTok quando abrir transmissão:
   ```bash
   python main.py --tiktok-user SEU_USUARIO_TIKTOK --test-mode=False
   ```

---

## 13. Testes Automatizados e Garantia de Qualidade

O projeto possui **68 testes automatizados** cobrindo todos os módulos vitais. Para executar:

```bash
python -m pytest -v
```

Os testes verificam:
* Carregamento e validação de `config.json` e atributos dos 8 cavalos em arquivos individuais na pasta `horses/`.
* Ciclo de vida completo do banco SQLite e cálculos atômicos de XP e níveis.
* Rate limiting por usuário em janela de 1s e sanitização de strings contra ataques.
* Simulação matemática da corrida, boosts, curvas de personalidade e linha de chegada.
* **Balanceamento**: todo arquétipo é neutro no relógio ($\sum fração/fator = 1.00$) e, em 200 corridas com clima sorteado, cada cavalo vence entre 8% e 17% — ninguém domina nem fica escanteado.
* **Clima**: sorteio que nunca repete o clima da corrida anterior, intensidade que escala o efeito de verdade, rótulo falado ("chuva forte"), anúncio na abertura com os favoritos e a virada do tempo no meio da prova (agendada na largada, uma vez por corrida).
* Máquina de estados do `EventDirector` (VOTING $\to$ COUNTDOWN $\to$ RACING $\to$ PODIUM $\to$ XP $\to$ LEADERBOARD).
* Parser semântico de comandos do TikTok (números, nomes, presentes e comandos de torcida).
* Torcida no chat: número digitado com a corrida rolando empurra o cavalo de leve (e nada acontece fora da corrida); presente e curtida de quem não escolheu cavalo caem em **cavalo sorteado**.
* Endpoints REST do servidor FastAPI e sincronização WebSocket.
* Voz da live: frases e fila do Narrador com gerador/tocador injetados (sem internet e sem placa de som), incluindo o descarte da fala mais antiga com a fila cheia e o **descarte da locução de corrida quando a chegada decide** (vencedor e foto-finish nunca são descartados).
* **Anúncio Imediato na Chegada (Zero Atraso):** assim que o primeiro cavalo cruza a marca de 1000m, a voz dispara o anúncio do campeão na hora (sem aguardar o timeout pós-chegada da física), cortando falas de meio de prova pendentes via `interromper_locucao()`.
* **Áudio Ducking para Boas-Vindas:** canal prioritário de saudações com reprodução simultânea no MCI que reduz o volume da fala atual em 50% (`volume 500`), reproduz o oi em volume máximo (`volume 1000`) e restaura suavemente o som principal ao término da saudação.
* Locução ao vivo: frases da dupla da frente, queda na frase padrão com placeholder quebrado e todas as frases do jogo formatando sem erro.
* Fiação da voz no `EventDirector`: votação (com lembrete a cada 12s), largada, vencedor, presente, entrada e clima falados nos momentos certos — e a locução disparando abertura, disputa, reta final e os três placares UMA vez cada, na ordem da prova.
* Margem da foto-finish: a exclamação só entra quando a chegada foi decidida no detalhe.
* Teste de integração ponta a ponta (E2E) simulando uma prova completa com espectadores reais.

---

## 14. Narração por Voz (`game/narrador.py` + `game/falas.py`)

Mesmo motor do `tiktok-live-pixel`, portado inteiro e ampliado: uma **thread com fila**, pelo mesmo motivo da thread do TikTok — gerar a voz leva segundos, e o loop de eventos do jogo não pode esperar por isso. Quem presenteia ganha o crédito no telão NA HORA; a fala entra na fila e sai quando der. O ciclo é o pedido original: **gera → toca → apaga**.

1. O `EventDirector` (ou o adapter, no caso da chegada) chama `narrador.anunciar_*` e segue em frente — nunca bloqueia.
2. A thread da fila sintetiza o mp3 com o **edge-tts** (nuvem da Microsoft, sem chave de API) num arquivo temporário.
3. A reprodução usa o **MCI do Windows** via `ctypes` (biblioteca padrão): nenhum binário externo nem pacote de áudio para instalar.
4. Terminou de tocar, o arquivo é apagado.

### 14.1 Anúncio Imediato do Vencedor com Fade-Out Suave (Zero Corte Seco)
Antes, o anúncio do vencedor aguardava os 3.5 segundos da desaceleração da engine pós-chegada para só então sintetizar a voz, acumulando até 8 segundos de espera, e um corte abrupto podia acontecer no meio da palavra.
Agora:
* **Disparo no Milissegundo do Cruzamento:** No exato instante em que o cavalo cruza a linha de 1000m (`winner_horse_id` detectado em `RACING`), o narrador entra em ação imediatamente.
* **Fade-Out Suave da Locução Anterior (`interromper_locucao()`):** Se alguma locução da corrida estiver sendo falada nos alto-falantes (ex: *"Olha o placar..."*), o narrador **não corta o som do nada**. Ele executa um **fade-out musical e suave de ~240ms** (reduzindo o volume de forma exponencial em 6 etapas: 70% $\to$ 45% $\to$ 25% $\to$ 10% $\to$ 2% $\to$ 0%), silenciando a fala anterior com extrema elegância antes de abrir o veredito do campeão.
* O veredito do campeão e foto-finish são sintetizados instantaneamente, entrando com volume pleno e clareza total na virada para o pódio!

### 14.2 Áudio Ducking nas Boas-Vindas
Quando alguém entra na live durante a narração:
* O sistema ativa um **canal simultâneo de áudio no MCI**.
* O som atual que estiver tocando (seja narração da corrida ou agradecimento de presente) tem seu volume **reduzido pela metade (50%, volume 500)**.
* A voz de boas-vindas toca em **volume máximo (100%, volume 1000)** com destaque sonoro imediato.
* Assim que a saudação termina, o volume do áudio principal é **automaticamente restaurado para o volume original (1000)**.

### 14.3 Higienização Fonética de Nomes e Remoção de Emojis na Fala
Usuários do TikTok frequentemente possuem emojis em seus nomes de exibição (ex.: `caioba🇧🇷✋🏽😛🤚🏽`). Sem higienização, sintetizadores neurais leem literalmente o nome descritivo de cada emoji em português (*"caioba bandeira do brasil mão levantada rosto com língua..."*).
* **Filtro Fonético de Nomes (`_limpar_nome_para_fala`):** Remove todos os emojis, símbolos e caracteres pictográficos, mantendo exclusivamente letras (com acentos), números e espaços (`caioba🇧🇷✋🏽😛🤚🏽` $\to$ `caioba`).
* **Fallback Inteligente:** Se o nome de exibição do usuário for composto exclusivamente por emojis (ex.: `🔥💎👑`), o sistema utiliza automaticamente o seu `@username` limpo (ex.: `pedro_gamer` $\to$ `pedrogamer`), evitando saudações vazias ou genéricas.
* **Filtro Geral de Síntese:** No método `_normalizar_para_fala`, qualquer resquício de emoji ou símbolo que chegue ao texto final é eliminado antes de chamar o `edge-tts`, garantindo uma locução 100% natural e humana.

### A locução ao vivo (o locutor da corrida)

A corrida era o único trecho silencioso da transmissão: saía a largada e depois só o vencedor — ~35s de vazio. Agora o narrador acompanha a prova inteira, disparado por **marco de distância do líder** (`MARCOS_LOCUCAO` no `EventDirector`); cada marco fala **uma vez por corrida** (o placar são três marcos distintos, um por distância). O ritmo ficou de **~1 fala a cada 5s** — medido a 60Hz, o maior buraco entre falas caiu de 10-12s para ~6s:

| Momento | Marco | Frase (exemplo) |
|---|---|---|
| **Abertura** | 120m | *"{lider} puxa o ritmo! E olha o {segundo} vindo colado logo atrás!"* |
| **Placar** | 320m, 620m e 760m | *"Olha o placar! {lider} na frente, {segundo} em segundo e {terceiro} fechando o trio!"* — o placar do turfe: cita o **trio** da frente |
| **Disputa** | 480m | *"A corrida tá pegada! {lider} e {segundo} lado a lado!"* |
| **Reta final** | 880m | *"Reta final! {lider} na frente e {segundo} vem voando!"* — cai a ~4s da linha: o tempo de gerar o áudio e a voz entrar no ar antes do cruzamento |
| **Foto-finish** | chegada | *"Que chegada! {vencedor} levou no fio do bigode na frente do {segundo}!"* — só quando a chegada foi decidida por **menos de 50ms** (`MARGEM_FOTO_FINISH_MS`; acontece em ~1/3 das corridas). Entra na fila ANTES do anúncio do campeão: primeiro o susto, depois o veredito |

E a **votação** (30s parados) não fica muda: a voz lembra a galera de votar a cada **12s** (`CHAMADA_VOTACAO_INTERVALO`) até a largada.

E o **clima** também fala: a votação abre com o tempo da corrida anunciado **junto com quem se dá bem nele** (*"Atenção à pista! A corrida de agora é com chuva forte! Quem se dá bem nisso: Nevasca e Titã!"*), e quando o tempo **vira com a prova rolando** o locutor avisa na hora (*"Olha o tempo virando! Agora é vento forte! ..."*) — listas `clima` e `clima_virada` em `game/falas.py`, trocáveis pelo config (`tts.clima`, `tts.clima_virada`).

Toda frase da locução cita a **dupla da frente** (ou o trio, no placar) — a tensão da fala está no duelo, não num cavalo sozinho.

Detalhes de projeto:

* **Fila máxima de 20 falas:** cheia, a mais antiga sai — narrar o que está acontecendo agora vale mais do que narrar o atrasado.
* **Locução de corrida descartada quando a chegada decide:** no instante em que o líder cruza a linha (ou a corrida é encerrada no meio, ou um novo ciclo começa), as falas de meio de prova que ainda estavam na fila são jogadas fora — antes o locutor seguia narrando a corrida como se ninguém tivesse chegado. `descartar_locucao()` no `game/narrador.py` limpa só o que é de corrida: chegada, vencedor, votação e presentes **nunca** são descartados.
* **Anti-Repetição Consecutiva (Sistema Shuffle Bag):** o sorteio de frases opera com baralhos embaralhados independentes por categoria (`_baralhos_frases`). Todas as frases de cada lista são faladas antes de qualquer repetição, e a virada do baralho impede matematicamente que a última frase sorteada seja escolhida como a primeira do próximo ciclo. Isso elimina completamente o efeito de repetição da mesma frase com vozes diferentes.
* **Frases sorteadas** de `game/falas.py` (dezenas por momento): a voz nunca vira disco riscado. Um `{placeholder}` inválido numa frase editada cai na frase padrão com aviso no log — nunca deixa a live muda. As listas da locução aceitam troca pelo config (`tts.corrida_abertura`, `tts.corrida_disputa`, `tts.corrida_placar`, `tts.reta_final`, `tts.foto_finish`, `tts.clima`, `tts.clima_virada`).
* **Rodízio de vozes** (`tts.vozes`): uma live inteira numa voz só soa como robô lendo avisos; a lista vazia volta para a `tts.voz` de sempre.
* **Nome de cavalo em CAIXA ALTA** (RELÂMPAGO) é falado em caixa normal (Relâmpago): caixa alta na fala soa como grito, e nome curto todo em maiúsculas corre o risco de sair letra por letra.
* **Chegada de espectador** (`JoinEvent` do TikTok): oi falado com cooldown de 60s por pessoa (o TikTok repete a entrada de quem sai e volta). Entrada não grava no banco nem rende XP — é presença, não voto. `tts.anunciar_entrada: false` cala só a chegada.
* **Falha de áudio nunca derruba o jogo:** sem internet, sem biblioteca ou sem placa de som, o que acontece é um aviso no log (`Não consegui falar ...`) e a corrida segue em frente.
* **Teste de ouvido:** `python tools/smoke_audio.py presente` (ou `entrada`, `votacao`, `largada`, `vencedor`; sem argumento, fala uma de cada).
