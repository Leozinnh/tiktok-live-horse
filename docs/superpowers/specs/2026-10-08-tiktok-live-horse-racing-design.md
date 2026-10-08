# TikTok LIVE - Jogo de Corrida de Cavalos Interativo
## Documento de Especificação de Design e Arquitetura do Sistema

**Data:** 08/10/2026  
**Status:** Aprovado para Implementação  
**Alvo:** OBS Studio (1080x1920 vertical, 9:16) / Transmissão TikTok LIVE  

---

## 1. Visão Geral e Princípio de Compliance
O projeto é um simulador interativo de corrida de cavalos para transmissões ao vivo na plataforma TikTok LIVE, renderizado a 60 FPS com estética de transmissão esportiva televisiva de alta produção.

### REGRA INEGOCIÁVEL DE COMPLIANCE
- **Sem Dinheiro Real:** O sistema não possui apostas, saques, conversão de pontos em dinheiro, prêmios financeiros ou qualquer mecanismo de azar.
- **Pontos 100% Virtuais:** Toda pontuação é estritamente XP de engajamento, servindo para progressão de níveis de espectador, estatísticas, distintivos (badges), títulos honoríficos e ranking da LIVE.
- **Presentes:** Presentes enviados no TikTok funcionam exclusivamente como suporte moral / animações de torcida e boosts visuais temporários (ex: turbo de velocidade na corrida), jamais como moeda financeira ou aposta.

---

## 2. Arquitetura Geral do Sistema

```text
┌────────────────────────────────────────────────────────┐
│                      TikTok LIVE                       │
│    (Comentários, Presentes, Likes, Follows, Shares)    │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│             TikTokEventAdapter / TestMode              │
│       (Sanitização, Anti-Spam, Rate Limit, Fila)       │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                 EventBus Assíncrono                    │
│                  (asyncio.Queue)                       │
└─────────────┬───────────────────────────┬──────────────┘
              │                           │
              ▼                           ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│      EventDirector       │  │    SQLite Repository     │
│ (Máquina de Estados Loop)│  │ (Espectadores, XP, Stats)│
└─────────────┬────────────┘  └──────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────┐
│               Simulador Físico do Jogo                 │
│         (60 ticks/s: Posições, Velocidades, IA)        │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│            FastAPI + WebSocket Broadcast               │
│               (ws://localhost:8000/ws)                 │
└─────────────┬───────────────────────────┬──────────────┘
              │                           │
              ▼                           ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│   OBS Browser Source     │  │     Painel Streamer      │
│ Three.js 3D + HUD 9:16   │  │   Test Mode Simulator    │
│  (1080x1920 @ 60 FPS)    │  │  (/test no navegador)    │
└──────────────────────────┘  └──────────────────────────┘
```

---

## 3. Estrutura do Repositório

```text
tiktok_live_cavalo/
├── config/
│   ├── config.json              # Configurações de tempo, XP, cavalos e regras
│   └── settings.py              # Loader tipado de configuração
├── backend/
│   ├── database/
│   │   ├── connection.py        # Conexão SQLite assíncrona com aiosqlite
│   │   ├── models.py            # Esquemas de banco de dados
│   │   └── repository.py        # Queries de XP, viewers, escolhas e rankings
│   ├── event_bus.py             # Barramento assíncrono pub/sub
│   ├── security.py              # Rate limiting, sanitização e cooldowns
│   └── progression.py           # Sistema de XP, níveis e títulos
├── tiktok/
│   ├── adapter.py               # Conector TikTokLive com reconexão resiliente
│   ├── mock_adapter.py          # Simulador de eventos para Test Mode
│   └── parser.py                # Interpretação semântica de comentários e presentes
├── game/
│   ├── horses.py                # Definição dos 8 cavalos e arquétipos de personalidade
│   ├── physics.py               # Trajetória, física de velocidade, aceleração e fadiga
│   ├── weather_events.py        # Chuva, vento, tempestade, cavalo fantasma, etc.
│   ├── engine.py                # Loop principal de simulação matemática (60 ticks/s)
│   └── director.py              # EventDirector - orquestrador do loop autônomo
├── web/
│   ├── server.py                # Aplicação FastAPI, endpoints REST e WebSocket
│   ├── static/
│   │   ├── css/
│   │   │   ├── styles.css       # Estilos da transmissão 9:16 e HUD esportivo
│   │   │   └── test_panel.css   # Estilos do painel de controle do streamer
│   │   ├── js/
│   │   │   ├── scene.js         # Three.js: hipódromo 3D, pista, arquibancadas, iluminação
│   │   │   ├── horses_view.js   # Modelagem 3D dos cavalos, rigs de pata, crina, jockeys
│   │   │   ├── particles.js     # Poeira de casco, faíscas de turbo, chuva, confetes
│   │   │   ├── camera.js        # Câmeras cinematográficas dinâmicas de corrida
│   │   │   ├── hud.js           # Placar de posições, apoiadores, notificações animadas
│   │   │   ├── audio.js         # Web Audio API sintetizado (galope, torcida, vitória)
│   │   │   └── client.js        # WebSocket client e sincronizador de estados
│   │   ├── index.html           # Tela para captura OBS (1080x1920)
│   │   └── test.html            # Painel interativo de testes do streamer
├── tests/
│   ├── test_engine.py           # Testes unitários de física e simulação
│   ├── test_database.py         # Testes de persistência e cálculo de XP
│   └── test_security.py         # Testes de rate-limit e anti-spam
├── main.py                      # Ponto de partida único (`python main.py`)
└── requirements.txt             # Dependências Python (fastapi, uvicorn, aiosqlite, etc.)
```

---

## 4. Cavalos e Personalidades

O jogo inicializa com 8 cavalos icônicos, cada um com atributos calibrados e curva comportamental única:

1. **#1 RELÂMPAGO (Amarelo Ouro / Elétrico):**
   - *Arquétipo:* Velocista Nato (Front-runner).
   - *Comportamento:* Aceleração inicial explosiva. Assume a ponta rapidamente, mas sofre alta perda de stamina nos últimos 20% da pista.
2. **#2 TROVÃO (Azul Meia-Noite / Trovão):**
   - *Arquétipo:* Finalizador Brutal (Closer).
   - *Comportamento:* Mantém ritmo conservador na largada; nos últimos 200m ativa um surto constante de velocidade.
3. **#3 FURACÃO (Verde Esmeralda / Vento):**
   - *Arquétipo:* Maratonista Constante (Pacer).
   - *Comportamento:* Altíssima resistência; quase imune a cansaço e perda de velocidade em terrenos instáveis.
4. **#4 RAIO (Vermelho Escarlate / Fogo):**
   - *Arquétipo:* Agressivo & Vácuo (Drafting Hunter).
   - *Comportamento:* Ganha aceleração ao correr atrás de outro cavalo e busca ativamente brechas de ultrapassagem.
5. **#5 PANTERA (Preto Ônix / Sombra):**
   - *Arquétipo:* Tático de Curva (Corner Specialist).
   - *Comportamento:* Executa traçados perfeitos em curvas com mínimo atrito, ultrapassando concorrentes pelo lado interno.
6. **#6 TITÃ (Bronze Terroso / Rocha):**
   - *Arquétipo:* Tanque Pesado (Juggernaut).
   - *Comportamento:* Lento para acelerar, mas velocidade máxima inabalável; imune a penalidades climáticas (chuva/lama).
7. **#7 NEVASCA (Branco Gelo / Prata):**
   - *Arquétipo:* Mestre do Clima (Cold Tactician).
   - *Comportamento:* Desempenho equilibrado que se transforma em super-eficiência quando há eventos de chuva ou vento.
8. **#8 FANTASMA (Roxo Místico / Spectral):**
   - *Arquétipo:* O Joker (Wildcard).
   - *Comportamento:* Atributo de sorte elevado; chances de impulsos misteriosos repentinos e ultrapassagens inacreditáveis.

---

## 5. Simulação da Corrida e Física

- **Geometria:** Pista oval de 1.000 metros virtuais demarcados em coordenadas 3D paramétricas.
- **Tickrate:** 60 Hz no backend. O estado enviado via WebSocket contém `x, y, z`, velocidade, distância percorrida, posição no ranking, boosts ativos e animação.
- **Equação de Velocidade:**
  $$V(t) = (V_{\text{base}} \times \text{CurvaPersonalidade}(d)) + \text{BonusApoiadores} + \text{BoostPresente} - \text{Fadiga}(t) + \text{VariaçãoAleatória}$$
- **Boosts:**
  - *Comentário/Like coletivo:* Cada 20 interações do cavalo aumentam o "Ímpeto" em +1% (acumulável até +5%).
  - *Presentes (ex: Rosa, Café, Donut, etc.):* Disparam turbos imediatos de 2 a 5 segundos com rastro de partículas luminosas.

---

## 6. O EventDirector: Máquina de Estados de Transmissão Contínua

O `EventDirector` executa um loop de estados autônomo, sem intervenção do operador:

| Estado | Duração | Ações Visuais e Lógicas |
|---|---|---|
| **VOTING** | 30s | Exibe cartela com os 8 cavalos, contadores de torcida em tempo real, instruções de comentário e trilha sonora pré-corrida. |
| **COUNTDOWN** | 5s | Portões se fecham; contagem regressiva 5, 4, 3, 2, 1 no centro da tela; efeitos sonoros de bips. |
| **RACING** | ~35s-40s | Disparo da largada; simulação física em 60 FPS; câmeras automáticas; narração visual de eventos e ultrapassagens. |
| **PHOTO_FINISH** | 4s | Cruzamento da linha de chegada com câmera lenta nos líderes e verificação milimétrica. |
| **PODIUM** | 8s | Telão com Pódio (1º, 2º e 3º), chuva de confetes, troféu dourado e destaque ao "Maior Apoiador". |
| **XP_REWARDS** | 6s | Processamento no SQLite; animação de barras de XP subindo e destaque para quem subiu de nível. |
| **LEADERBOARD** | 10s | Placar com os maiores pontuadores da LIVE e maiores vencedores da temporada. Reinicia ciclo no VOTING com nova corrida. |

---

## 7. Sistema Visual 3D e Transmissão 9:16 (Three.js)

- **Resolução Nativa:** 1080x1920 (aspect ratio 9:16) com área segura para exibição no TikTok mobile (evitando sobreposição com botões nativos da live no canto superior direito e rodapé de comentários).
- **Cenário 3D:**
  - Hipódromo com gramado texturizado, pista de terra/areia com marcações de raias e cerca de madeira branca.
  - Arquibancadas laterais com público animado, postes de iluminação noturna/tardinha esportiva.
  - Céu dinâmico com sol, nuvens volumétricas ou iluminação dramática de refletores.
- **Modelagem 3D dos Cavalos:**
  - Cavalos estilizados de alto impacto visual, com musculatura, arreios com a numeração do cavalo (#1 a #8), jockeys com cores da farda correspondente.
  - Sistema de animação procedural de galope sincronizado com a velocidade instantânea (frequência de passos, subida/descida do dorso, movimento de cauda e crina).
  - Emissores de partículas: poeira de terra nos cascos, rastros luminosos em turbos, faíscas elétricas e chuva.
- **Diretor de Câmeras Cinematográficas:**
  - `CAM_START`: Visão aberta frontal dos boxes com os 8 cavalos perfilados.
  - `CAM_CHASE`: Acompanha a lateral e diagonal do pelotão de frente, mantendo os 3 líderes sempre em enquadramento dramático.
  - `CAM_OVERTAKE`: Acionada dinamicamente quando há troca de liderança, focando o cavalo ultrapassador em plano fechado.
  - `CAM_RAILS`: Câmera fixa rente à cerca que os cavalos passam em alta velocidade (efeito de transmissão de TV).
  - `CAM_FINISH`: Posicionada exatamente na linha de chegada em ângulo lateral.
  - `CAM_PODIUM`: Foca o cavalo vencedor girando em torno dele na celebração.

---

## 8. HUD de Transmissão Esportiva e Notificações

- **Topo:** Indicador de Corrida Atual (`CORRIDA #042`), fase do ciclo e relógio regressivo.
- **Barra Lateral / Inferior:**
  - Mini-mapa vertical do progresso dos cavalos ao longo dos 1000m.
  - Leaderboard instantâneo ordenado por posição (#1 a #8) com nome do cavalo, cor, distância do líder e contagem de apoiadores.
- **Fila de Notificações (Broadcast Ticker):**
  - Toast animado: *"@leandro apoiou RELÂMPAGO!"*
  - Toast dourado: *"🎁 @marcos enviou ROSA! TURBO ATIVADO no TROVÃO!"*
  - Anti-flood: Notificações agrupadas e exibidas a no máximo 2 por segundo para legibilidade perfeita no celular.

---

## 9. Áudio Dinâmico (Web Audio API)

- **Música e Ambiência:** Trilha orquestral esportiva enérgica durante a corrida e trilha de suspense na contagem regressiva.
- **Efeitos Sonoros Procedurais / Sintetizados:**
  - Galope rítmico proporcional à velocidade dos cavalos.
  - Bips de largada e sirene de partida clássica de turfe.
  - Clamor e gritos da multidão que aumentam quando os cavalos entram na reta final.
  - Som de turbo espacial e faíscas ao receber presentes.
  - Fanfarra triunfal na vitória.

---

## 10. Persistência de Dados e Progressão (SQLite)

### Tabelas Principais
- `viewers`: `id, tiktok_username, display_name, xp, level, races_count, wins_count, favorite_horse, created_at, updated_at`
- `races`: `id, race_number, status, winner_horse_id, total_participants, total_gifts, started_at, finished_at`
- `race_choices`: `id, race_id, viewer_id, horse_id, created_at`
- `race_results`: `id, race_id, horse_id, final_position, finish_time_ms`
- `leaderboard_season`: `id, viewer_id, season_number, season_xp, season_wins`

### Fórmulas de XP
- Escolher cavalo participante: **+20 XP**
- Torcer / enviar comandos de incentivo: **+5 XP** (máx 3x por corrida)
- Cavalo escolhido no Top 3: **+50 XP**
- Cavalo escolhido Vencedor (1º lugar): **+150 XP**
- Envio de presente de apoio: **+100 a +500 XP** (proporcional ao apoio, sem recompensa financeira)
- Progressão de Nível: $\text{XP}(Lv) = 100 \times Lv^{1.35}$

---

## 11. Painel de Testes (Test Mode)

Interface web dedicada (`/test`) que se conecta ao backend e permite ao operador:
- Injetar comentários de texto simulando diferentes usuários e cavalos escolhidos.
- Disparar presentes com 1 clique (Rosa, Donut, Foguete, Leão).
- Simular rajadas de 50 espectadores escolhendo cavalos simultaneamente para teste de estresse.
- Forçar ativação de eventos climáticos (Chuva, Tempestade, Vento).
- Pausar, pular etapas ou acelerar o tempo do `EventDirector`.

---

## 12. Estratégia de Verificação e Testes Automatizados

1. **Testes Unitários:**
   - Física da corrida (distância, desaceleração, tempos válidos e sem NaN).
   - Máquina de estados do `EventDirector` e transições de tempo.
   - Segurança: rate limiter e sanitizador de comandos.
   - Persistência e cálculos de nível de XP no banco SQLite.
2. **Teste de Integração:**
   - Comunicação WebSocket cliente-servidor a 60 ticks/s.
   - Injeção de eventos via Test Mode e confirmação de resposta no HUD.
3. **Validação Visual no Navegador:**
   - Renderização correta em 1080x1920 a 60 FPS estáveis.
   - Funcionamento de áudio, câmeras e efeitos de partículas.
