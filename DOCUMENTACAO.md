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
│   └── weather_events.py        # Modificadores climáticos (Sol, Chuva, Tempestade, Vento)
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
├── tests/                       # 16 testes automatizados (pytest) com 100% de aprovação
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

## 4. Cavalos, Atributos e Arquétipos de Personalidade

Os 8 cavalos iniciais são configurados na lista `"horses"` em `config/config.json`:

| Nº | Nome | Cor Primária | Arquétipo de Personalidade | Comportamento Único na Pista |
|:---:|:---|:---:|:---|:---|
| **#1** | **RELÂMPAGO** | `#F59E0B` (Ouro) | `FRONT_RUNNER` | Arrancada inicial explosiva (+12% de velocidade até 40% da pista); cansaço acentuado no terço final (-10%). |
| **#2** | **TROVÃO** | `#2563EB` (Azul) | `CLOSER` | Ritmo cadenciado no início (-6%); surto avassalador de velocidade (+15%) nos últimos 200 metros. |
| **#3** | **FURACÃO** | `#10B981` (Verde) | `PACER` | Maratonista inabalável (+1% do início ao fim); quase imune à perda de stamina. |
| **#4** | **RAIO** | `#EF4444` (Vermelho) | `DRAFTER` | Caçador agressivo no vácuo; ganha +7% de aceleração sempre que corre atrás de outro cavalo. |
| **#5** | **PANTERA** | `#1E293B` (Preto) | `CORNER_SPECIALIST` | Mestre das curvas; ganha +8% de rendimento ao contornar as duas curvas ovais pelo lado interno. |
| **#6** | **TITÃ** | `#78350F` (Bronze) | `JUGGERNAUT` | Aceleração inicial pesada (-8%), porém velocidade inabalável e ganho de rendimento na chuva e lama. |
| **#7** | **NEVASCA** | `#06B6D4` (Ciano) | `COLD_TACTICIAN` | Frio e equilibrado; eficiência máxima quando ocorrem eventos de tempestade ou vento forte. |
| **#8** | **FANTASMA** | `#8B5CF6` (Roxo) | `WILDCARD` | Fator de sorte extremo (9.8/10); chances de impulsos surpresa de até +18% em qualquer trecho da prova. |

### Como Adicionar um Novo Cavalo (ex: #9 TITÂNIO):
1. Adicione um novo objeto na lista `"horses"` em `config/config.json` com `id: 9, number: 9, name: "TITÂNIO"`.
2. Adicione o nome no dicionário `HORSE_NAME_MAP` em `tiktok/parser.py`: `"titanio": 9`.
3. Pronto! O cavalo já terá seu box, farda 3D, placa numerada e participará automaticamente do ciclo.

---

## 5. Sistema de Presentes e Efeitos Especiais

### 5.1 Emojis Dinâmicos e Destaque ao Apoiador
Ao receber um presente, o cavalo correspondente exibe uma **pill 3D flutuante** acima da cabeça contendo:
1. O **Emoji oficial do presente** renderizado em alta definição (`Segoe UI Emoji`).
2. O **`@nome_do_apoiador`** em texto branco contrastante com fundo escuro translúcido.

### 5.2 Mapeamento de Presentes (`game/director.py`)
No arquivo `game/director.py`, dentro de `handle_viewer_gift()`, todos os presentes são normalizados:

```python
gift_emoji_map = {
    "galaxy": "🌌", "galaxia": "🌌",
    "lion": "🦁", "leao": "🦁", "leão": "🦁",
    "dragon": "🐉", "dragao": "🐉", "dragão": "🐉",
    "universe": "🪐", "universo": "🪐",
    "rose": "🌹", "rosa": "🌹",
    "donut": "🍩",
    "cap": "🧢", "bone": "🧢", "boné": "🧢",
    "coffee": "☕", "cafe": "☕", "café": "☕",
    "coracao": "💖", "coração": "💖", "heart": "💖",
    "fire": "🔥", "fogo": "🔥"
}
```

### 5.3 Presentes Míticos e Super Raros (Leão, Galáxia, Dragão)
Quando um presente raro é enviado, os seguintes efeitos são ativados simultaneamente:
* **Pilar de Luz Celestial de 90 Metros:** Um feixe vertical de energia translúcida desce do céu diretamente em cima do cavalo apoiado.
* **Onda de Choque Radial no Solo:** Anel luminoso expansivo que varre a areia da pista com raio de até 35 metros.
* **Tremor Sísmico de Câmera (*Screen Shake*):** A câmera de transmissão treme para transmitir o impacto e a potência do presente.
* **Aura Mítica Tórica e Rastro de Chamas:** Um anel energético brilhante gira em alta velocidade ao redor do cavalo, deixando brasas e labaredas no chão.
* **Banner Mítico no HUD:** Card monumental no topo da tela com borda dourada/violeta incandescente e pulsação em toda a moldura da live.
* **Áudio de Trovão e Sub-Grave:** Impacto estrondoso de 140 Hz descendo até 25 Hz com o clamor da multidão do estádio a 100% de volume por 4 segundos.
* **Turbo Massivo:** +35% de velocidade por 6.5 segundos e até +2.000 XP para o apoiador.

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
* A pista tem **22 metros de largura** (se estendendo de $z = 52.66\text{m}$ até $z = 74.66\text{m}$).
* As 8 raias foram distribuídas simetricamente a partir da base $R_{\text{base}} = \text{radius} - 8.4\text{m}$:
  $$\text{Raia}(i) = 55.26\text{m} + (i - 1) \times 2.4\text{m}$$
  * Raia 1 (Interna) = **$55.26\text{m}$** $\to$ perfeitamente alinhada com o Box #1.
  * Raia 8 (Externa) = **$72.06\text{m}$** $\to$ perfeitamente alinhada com o Box #8.
* Margem de segurança de ~2.6m de cada lado em relação às cercas interna e externa: **zero cavalos escapam da pista ou atravessam cercas**.

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

### 7.1 Cercas Ovais em 360 Graus
As cercas brancas de turfe e as sebes vivas verdes (*hedges*) são geradas através de uma malha paramétrica contínua que contorna as duas retas e os dois arcos circulares das curvas:
* Cerca Interna: raio fixo em **$52.16\text{m}$** (rente à borda interna da pista).
* Cerca Externa: raio fixo em **$75.16\text{m}$** (rente à borda externa da pista).
* As cercas acompanham o hipódromo em um circuito fechado contínuo: **nenhuma grade entra na pista**.

### 7.2 Elementos do Cenário
* **Jumbotron LED de 34 Metros:** Telão no centro do Infield com suporte metálico treliçado exibindo o logotipo esportivo e avisos ao vivo.
* **Lago Ornamental & Fonte:** Espelho d'água azul reflexivo com ilha central e chafariz de 6 jatos de água.
* **Arquibancada Monumental:** 10 degraus de concreto com centenas de torcedores coloridos animados, camarotes VIP com vidros espelhados e 12 bandeiras no telhado que balançam com o vento.
* **Floresta Periférica:** Pinheiros e carvalhos 3D posicionados exclusivamente fora da pista (raio $\ge 92\text{m}$ nas curvas e $z \le -96\text{m}$ na reta oposta).
* **Placas de Distância Oficiais:** Marcadores verticais de turfe ao longo da pista: `800m`, `600m`, `400m`, `200m`, `100m` e `FINAL`.

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
│ [🏇 CORRIDA #42]      [🔴 AO VIVO]       [⏳ 28s] [🔊] │  ← Top Bar
├────────────────────────────────────────────────────────┤
│ [───1───2──────3─────────4──5──────6──7────8────────🏁] │  ← Régua de Progresso
├────────────────────────────────────────────────────────┤
│                                                        │
│ ┌───────────────┐                                      │
│ │ 🏁 POSIÇÕES   │                                      │
│ │ 1. #1 RELÂM.  │                                      │
│ │ 2. #2 TROVÃO  │                                      │
│ │ 3. #4 RAIO ⚡ │           ÁREA 3D LIVRE              │
│ │ 4. #3 FURACÃO │         (Mais de 85% da tela         │
│ │ 5. #5 PANTERA │            desobstruída)             │
│ │ 6. #7 NEVASCA │                                      │
│ │ 7. #6 TITÃ    │                                      │
│ │ 8. #8 FANTAS. │                                      │
│ └───────────────┘                                      │
│  (Torre Lateral                                        │
│   Compacta F1)                                         │
│                                                        │
│                                                        │
│                                                        │
│                     [ CENTRO / MODAIS ]                │
│             (Votação, Contagem, Pódio, XP)             │
└────────────────────────────────────────────────────────┘
```

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
3. **Simulação de Presentes:** Dispare Rosa, Café, Donut, Boné, Leão (+2000 XP), Galáxia (+1500 XP) ou Dragão (+1800 XP).
4. **Rajada de Público:** Simule 20 ou 50 espectadores comentando e votando de uma vez só.
5. **Controles de Clima:** Sol, Pôr do Sol, Noite com Refletores, Chuva, Tempestade e Vento.
6. **Console de Eventos Avançado:**
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
5. Para conectar à sua live real do TikTok quando abrir transmissão:
   ```bash
   python main.py --tiktok-user SEU_USUARIO_TIKTOK --test-mode=False
   ```

---

## 13. Testes Automatizados e Garantia de Qualidade

O projeto possui **16 testes automatizados** cobrindo todos os módulos vitais. Para executar:

```bash
python -m pytest -v
```

Os testes verificam:
* Carregamento e validação de `config.json` e atributos dos 8 cavalos.
* Ciclo de vida completo do banco SQLite e cálculos atômicos de XP e níveis.
* Rate limiting por usuário em janela de 1s e sanitização de strings contra ataques.
* Simulação matemática da corrida, boosts, curvas de personalidade e linha de chegada.
* Máquina de estados do `EventDirector` (VOTING $\to$ COUNTDOWN $\to$ RACING $\to$ PODIUM $\to$ XP $\to$ LEADERBOARD).
* Parser semântico de comandos do TikTok (números, nomes, presentes e comandos de torcida).
* Endpoints REST do servidor FastAPI e sincronização WebSocket.
* Teste de integração ponta a ponta (E2E) simulando uma prova completa com espectadores reais.
