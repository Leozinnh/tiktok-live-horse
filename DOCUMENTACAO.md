# 📚 Documentação Técnica Completa - TikTok LIVE Corrida de Cavalos 3D

Bem-vindo à documentação oficial do projeto. Este documento foi elaborado para que qualquer desenvolvedor ou criador de conteúdo possa entender, manter, customizar e expandir qualquer parte do sistema com facilidade.

---

## 1. Visão Geral da Arquitetura

O sistema é dividido em duas metades perfeitamente desacopladas:
1. **Backend em Python (FastAPI + WebSockets + SQLite):** Executa a física matemática da corrida a 60 ticks/s, orquestra a máquina de estados contínua (`EventDirector`), sanitiza comandos do chat do TikTok e persiste XP, níveis e estatísticas em banco SQLite.
2. **Frontend 3D em Three.js (OBS Browser Source / WebGL):** Renderiza o hipódromo 3D, cavalos com rigging procedural de galope, iluminação dinâmica, partículas, diretor de câmeras de TV e interface esportiva vertical (1080x1920, 9:16).

```text
TikTok LIVE / Painel de Testes (/test)
           ↓
   TikTokEventAdapter / MockAdapter
           ↓ (Sanitização e Anti-Spam)
     EventBus (asyncio.Queue)
           ↓
   EventDirector (Loop Infinito)
    ├── Simulação Física (RaceEngine a 60 ticks/s)
    └── Banco SQLite (Viewers, XP, Rankings)
           ↓
    FastAPI WebSocket Broadcast (ws://localhost:8000/ws)
           ↓
   OBS Browser Source (Three.js 3D + Câmeras + HUD 9:16 + Web Audio)
```

---

## 2. Estrutura de Pastas e Arquivos

```text
tiktok_live_cavalo/
├── config/
│   ├── config.json              # Configurações gerais (tempos, XP, cavalos e regras)
│   └── settings.py              # Validação tipada via Pydantic dos dados do JSON
├── backend/
│   ├── database/
│   │   ├── connection.py        # Pool e conexão assíncrona ao SQLite com aiosqlite
│   │   ├── models.py            # DDL das tabelas (viewers, races, choices, results)
│   │   └── repository.py        # Métodos de consulta e gravação de XP e estatísticas
│   ├── event_bus.py             # Barramento pub/sub assíncrono interno
│   ├── security.py              # Rate limiting em janela de 1s e proteção contra spam
│   └── progression.py           # Fórmula matemática de curva de níveis e títulos
├── game/
│   ├── engine.py                # Loop principal da física da corrida e rankings
│   ├── director.py              # Máquina de estados autônoma (VOTING -> PODIUM -> etc)
│   ├── horses.py                # Estado dinâmico dos cavalos, fadiga e boosts
│   ├── physics.py               # Trajetória oval, derivadas tangenciais e raias
│   └── weather_events.py        # Sistema de clima (Sol, Chuva, Tempestade, Vento)
├── tiktok/
│   ├── adapter.py               # Conector TikTokLive com reconexão exponencial
│   ├── mock_adapter.py          # Emulador de eventos para o Modo de Teste
│   └── parser.py                # Parser semântico de comentários, nomes e presentes
├── web/
│   ├── server.py                # Servidor FastAPI, rotas REST e WebSocket
│   └── static/
│       ├── css/
│       │   ├── styles.css       # Estilos do HUD 9:16 do OBS (torre, placar, pódio)
│       │   └── test_panel.css   # Estilos do painel de controle do streamer (/test)
│       ├── js/
│       │   ├── three.min.js     # Engine Three.js r128 (local e offline)
│       │   ├── scene.js         # Cenário 3D (pista, gramado, arquibancadas, lago)
│       │   ├── horses_view.js   # Modelagem 3D procedural dos cavalos e galope
│       │   ├── particles.js     # Poeira, faíscas, ondas de choque, luz celeste
│       │   ├── camera.js        # Diretor de câmeras dinâmicas de transmissão
│       │   ├── audio.js         # Sintetizador procedural Web Audio (galope, torcida)
│       │   ├── hud.js           # Gerenciador dos elementos da interface na tela
│       │   ├── client.js        # Orquestrador do loop de renderização a 60 FPS
│       │   └── test_panel.js    # Lógica interativa do painel admin do streamer
│       ├── index.html           # Tela de transmissão capturada pelo OBS
│       └── test.html            # Painel do streamer aberto no navegador (/test)
├── tests/                       # 16 testes automatizados cobrindo todo o sistema
├── main.py                      # Ponto de partida único do projeto
├── requirements.txt             # Dependências Python
└── README.md                    # Guia rápido de inicialização
```

---

## 3. Como Customizar Regras do Jogo (`config/config.json`)

Toda a calibração de tempos, regras de pontuação e atributos dos cavalos fica centralizada em `config/config.json`:

```json
{
  "race_duration_seconds": 35.0,        // Duração máxima da corrida em segundos
  "voting_duration_seconds": 30.0,      // Tempo para o chat escolher os cavalos
  "countdown_duration_seconds": 5.0,    // Contagem regressiva antes da largada
  "podium_duration_seconds": 8.0,       // Duração da tela de pódio do vencedor
  "xp_duration_seconds": 6.0,           // Duração da tela de distribuição de XP
  "leaderboard_duration_seconds": 10.0, // Duração da tela de TOP jogadores da LIVE
  "track_length_meters": 1000.0,        // Metros virtuais da pista oval
  "tick_rate": 60,                      // Taxa de atualização da simulação por segundo
  "xp": {
    "participation": 20,                // XP ganho apenas por escolher um cavalo
    "cheer": 5,                         // XP ganho ao mandar mensagens de torcida
    "top_3": 50,                        // XP ganho se o cavalo terminar em 2º ou 3º
    "win": 150,                         // XP ganho se o cavalo for o campeão (1º)
    "gift_small": 100,                  // XP ganho por presentes pequenos (ex: Rosa)
    "gift_medium": 250,                 // XP ganho por presentes médios (ex: Donut)
    "gift_large": 500                   // XP ganho por presentes grandes (ex: Galáxia)
  }
}
```

---

## 4. Como Customizar os Cavalos e Personalidades

Cada cavalo tem seus atributos definidos dentro da lista `"horses"` em `config/config.json`:

```json
{
  "id": 1,
  "number": 1,
  "name": "RELÂMPAGO",
  "color_hex": "#F59E0B",               // Cor principal do corpo e farda
  "secondary_color_hex": "#FEF3C7",     // Cor da manta de sela
  "personality": "FRONT_RUNNER",        // Arquétipo comportamental
  "base_speed": 28.5,                   // Velocidade base em m/s (~100 km/h)
  "acceleration": 9.5,                  // Quão rápido alcança a velocidade máxima
  "stamina": 7.0,                       // Resistência à perda de fôlego no final
  "luck": 6.0,                          // Chance de picos orgânicos de aceleração
  "aggressiveness": 7.5,                // Bônus ao correr disputando liderança
  "description": "Larga em velocidade máxima, mas perde fôlego no final."
}
```

### Arquétipos de Personalidade Disponíveis (`game/horses.py`):
* `FRONT_RUNNER` (*Relâmpago*): Começa com +12% de velocidade até 40% da pista, mas cai para -10% na reta final por fadiga.
* `CLOSER` (*Trovão*): Economiza energia na primeira metade (-6%) e ganha um surto avassalador de +15% nos últimos 200m.
* `PACER` (*Furacão*): Mantém ritmo inabalável (+1%) do primeiro ao último metro sem sofrer com fadiga.
* `DRAFTER` (*Raio*): Ganha +7% de aceleração e vácuo quando corre atrás de qualquer outro cavalo.
* `CORNER_SPECIALIST` (*Pantera*): Ganha +8% de rendimento ao entrar nas curvas do hipódromo.
* `JUGGERNAUT` (*Titã*): Lento na arrancada inicial (-8%), mas velocidade constante e ganha vantagem quando a pista está molhada (chuva).
* `COLD_TACTICIAN` (*Nevasca*): Ganha bônus de eficiência máxima em climas adversos (chuva e vento).
* `WILDCARD` (*Fantasma*): Fator de sorte alto (até +18% de pico aleatório surpresa a qualquer momento).

---

## 5. Como Adicionar Novos Presentes do TikTok (`game/director.py`)

No arquivo `game/director.py`, dentro de `handle_viewer_gift()`, você pode mapear qualquer presente da plataforma para acionar turbos e efeitos visuais personalizados:

```python
gift_emoji_map = {
    "galaxy": "🌌",
    "lion": "🦁",
    "dragon": "🐉",
    "rose": "🌹",
    "donut": "🍩",
    "cap": "🧢",
    "coffee": "☕",
    "coracao": "💖",
    "whale": "🐋",      # Exemplo: Adicionar Baleia
    "fireworks": "🎆"   # Exemplo: Adicionar Fogos de Artifício
}
```

### Para definir a força do turbo e XP de um presente novo:
```python
if any(w in gift_lower for w in ["whale", "baleia"]):
    power = 1.30          # +30% de velocidade
    dur = 6.0            # Duração de 6 segundos
    xp = 1800            # 1.800 XP virtual concedido ao espectador
    b_label = "TSUNAMI DA BALEIA AZUL"
    is_legendary = True   # Dispara pilar de luz celeste, tremor e banner épico
    legendary_kind = "WHALE"
```

---

## 6. Mecânica Física e Coordenadas da Pista (`game/physics.py`)

A pista é uma oval de 1.000 metros dividida em 4 segmentos contínuos:
1. **Reta Principal (0 a 300m):** De $x = -150$ até $x = +150$ com $z = +63.66$.
2. **Curva 1 (300m a 500m):** Arco de 180º com raio $R = 63.66\text{m}$ em torno do centro $(+150, 0)$.
3. **Reta Oposta (500m a 800m):** De $x = +150$ até $x = -150$ com $z = -63.66$.
4. **Curva 2 (800m a 1000m):** Arco de 180º com raio $R = 63.66\text{m}$ em torno do centro $(-150, 0)$.

### Raias dos Cavalos:
* A pista tem **22 metros de largura**.
* O centro fica em $R = 63.66\text{m}$.
* As 8 raias são calculadas simetricamente com espaçamento de 2.4m:
  $$\text{Raia}(i) = (\text{radius} - 8.4) + (i - 1) \times 2.4$$
  * Raia 1 (Interna) = **$55.26\text{m}$** (alinhada exatamente com o Box 1).
  * Raia 8 (Externa) = **$72.06\text{m}$** (alinhada exatamente com o Box 8).
* Nenhuma raia encosta nas cercas (margem de segurança de ~2.6m de cada lado).

### Direção Tangencial de Rotação (`rot_y`):
A rotação dos cavalos em cada tick é calculada pela derivada tangencial forward contínua:
```python
dx = x_next - x
dz = z_next - z
rot_y = math.atan2(dx, dz)
```
Isso garante que os cavalos sempre olhem e galopem perfeitamente apontados para a frente da pista em qualquer ponto da curva, sem giros bruscos.

---

## 7. Sistema de Câmeras Cinematográficas (`web/static/js/camera.js`)

As câmeras funcionam como uma mesa de corte de transmissão de TV esportiva profissional:
* **`CAM_START`:** Visão aberta frontal e elevada $(-210, 36, 140)$ dos boxes de largada e arquibancadas (ativa em `VOTING` e `COUNTDOWN`).
* **`CAM_CHASE`:** Câmera aérea/guindaste esportivo recuada a **44m de distância** e **24m de altura** do cavalo líder. Enquadra com folga todo o pelotão de 8 cavalos sem sensação de aperto no celular.
* **`CAM_SIDE`:** Câmera lateral aberta de helicóptero a **46m de distância lateral** e **28m de altura**, exibindo as ultrapassagens nas curvas em perspectiva ampla.
* **`CAM_FINISH`:** Câmera angular posicionada logo após a linha de chegada $(186, 15, 87)$ focando os cavalos cruzando o portal.
* **`CAM_PODIUM`:** Órbita contínua de 360 graus a 22m de raio ao redor do cavalo vencedor com chuva de confetes.

### Transição Suave Pós-Chegada:
Quando o líder cruza a linha de chegada (1000m), o arquivo `camera.js` **não congela**: ele passa a seguir imediatamente o líder da disputa restante (2º e 3º lugares) até a transição automática para o pódio 3.5 segundos depois.

---

## 8. Interface, HUD e OBS (`styles.css` e `hud.js`)

A interface foi projetada para proporção **9:16 vertical (1080x1920)** com safe-area para transmissões no TikTok (evitando sobreposição com botões do aplicativo).

### Componentes do HUD:
1. **Top Bar:** Placa dourada com número da corrida (`CORRIDA #42`), status pulsante (`AO VIVO`), relógio regressivo e botão de mudo.
2. **Régua de Progresso da Pista (Topo):** Linha sutil de 6px com os 8 cavalos representados por círculos coloridos numerados avançando em direção à bandeira quadriculada 🏁 (1000m).
3. **Torre Lateral Esquerda (Posições):** Inspirada na Fórmula 1 e MotoGP, mede apenas **235px de largura** ancorada no lado esquerdo (`top: 195px; left: 28px;`), deixando mais de **85% da tela 100% livre** para a visão 3D da pista e dos cavalos.
4. **Fila de Notificações:** Toasts animados no canto superior direito (`top: 195px; right: 28px;`) informando votos e presentes sem invadir o centro da tela.
5. **Ajuste em Tempo Real:** No painel do streamer (`http://localhost:8000/test`), é possível calibrar o tamanho do placar (60% a 160%), subir ou descer a posição vertical e ocultar/mostrar elementos ao vivo via WebSocket.

---

## 9. Áudio Procedural Sintetizado (`web/static/js/audio.js`)

O áudio não depende de arquivos externos pesados de MP3: ele é gerado proceduralmente em tempo real via **Web Audio API**:
* **Galope dos Cavalos (`playGallop(speed)`):** Oscilador triangular com filtro passa-baixas gerando batidas de cascos rítmicas com frequência proporcional à velocidade instantânea dos líderes.
* **Clamor da Torcida (`setCrowdIntensity(intensity)`):** Ruído contínuo filtrado em passa-banda que sobe de intensidade automaticamente na reta final e explode em 100% quando presentes raros são enviados.
* **Sirene e Bips de Largada:** Osciladores senoidais clássicos de largada de turfe.
* **Efeitos de Presentes Raros:** Impacto sub-grave descendente (140 Hz $\to$ 25 Hz) simulando estrondo de trovão, sweep cósmico e fanfarra triunfal no pódio.

---

## 10. Banco de Dados SQLite e Progressão (`backend/database/`)

O banco SQLite é salvo no arquivo local `race_game.db` com modo WAL habilitado para suportar alta concorrência assíncrona.

### Tabelas Principais:
* **`viewers`:** Registro persistente de cada espectador do TikTok (`tiktok_username`, `display_name`, `xp`, `level`, `races_count`, `wins_count`).
* **`races`:** Histórico de cada corrida (`race_number`, `status`, `winner_horse_id`, `started_at`, `finished_at`).
* **`race_choices`:** Registro da escolha de cavalo de cada usuário por corrida.
* **`race_results`:** Ordem final de chegada e tempos em milissegundos de cada cavalo.

### Fórmula de Níveis Virtuais (`backend/progression.py`):
$$\text{Nível}(XP) = \left\lfloor \left(\frac{XP}{100}\right)^{\frac{1}{1.35}} \right\rfloor + 1$$
* Nível 1: 0 XP
* Nível 2: 100 XP
* Nível 5: 649 XP
* Nível 10: 1.958 XP
* Nível 25: 7.781 XP
* Títulos honoríficos são concedidos automaticamente (ex: *Iniciante das Pistas*, *Torcedor Fervoroso*, *Lenda do Turfe*, *Campeão Supremo*).

---

## 11. Painel de Controle do Streamer / Admin (`/test`)

Acessível em qualquer navegador em:
👉 **`http://localhost:8000/test`**

### Recursos Disponíveis:
* **Controles Diretos de Corrida:**
  * ⏩ **Iniciar Corrida Logo:** Pula o timer de 30s de votação e inicia a contagem regressiva de largada imediatamente.
  * 🏁 **Finalizar Corrida:** Força o cruzamento imediato da linha de chegada e abre o pódio.
  * 🔄 **Próxima Corrida:** Reinicia o ciclo e cria a próxima corrida limpa com um clique.
* **Simulação de Comentários & Votos:** Digite ou clique nos botões rápidos (#1 ao #8, `/turbo`, etc.).
* **Simulação de Presentes:** Dispare Rosa, Café, Donut, Boné, Leão (+2000 XP), Galáxia (+1500 XP) ou Dragão (+1800 XP).
* **Rajada de Público:** Simule 20 ou 50 espectadores comentando e escolhendo cavalos simultaneamente.
* **Controles de Clima:** Sol Claro, Pôr do Sol, Noite com Refletores, Chuva, Tempestade e Vento.
* **Ajuste Visual do HUD:** Redimensione o placar (60% a 160%) e suba/desça a altura com sincronização imediata no OBS.
* **Console com Filtros:** Histórico permanente com abas para `Todos`, `🎁 Presentes`, `💬 Votos`, `🏁 Fases`, além de botões para `Limpar` e `Copiar`.

---

## 12. Como Executar e Validar

### Iniciar o Jogo em Modo de Teste:
```bash
python main.py
```

### Iniciar Conectado à LIVE Real do TikTok:
```bash
python main.py --tiktok-user SEU_USUARIO_TIKTOK --test-mode=False
```

### Executar a Suíte de Testes Automatizados:
```bash
python -m pytest -v
```
*(Todos os 16 testes de física, banco de dados, máquina de estados, segurança e API devem passar com 100% de sucesso).*
