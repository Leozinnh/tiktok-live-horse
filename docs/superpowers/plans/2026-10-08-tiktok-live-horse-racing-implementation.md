# TikTok LIVE - Jogo de Corrida de Cavalos Interativo
## Plano de Implementação (Vertical Slice Completo)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar o jogo interativo de corrida de cavalos para TikTok LIVE com backend Python (FastAPI + WebSockets + SQLite), simulação física de 8 cavalos com personalidades únicas, loop autônomo contínuo (EventDirector), renderização 3D em Three.js para OBS (1080x1920), sistema de câmeras esportivas, efeitos sonoros sintetizados e painel de Test Mode completo.

**Architecture:** O backend Python executa a física da corrida a 60 ticks/s e orquestra a máquina de estados contínua. Os eventos do TikTok LIVE (e do Test Mode) passam por sanitização e rate limiting, alimentando um EventBus assíncrono. O estado completo é transmitido via WebSocket para o cliente web (OBS Browser Source / navegador), que renderiza o hipódromo 3D, cavalos animados, câmeras dinâmicas e HUD vertical profissional. O banco SQLite persiste viewers, escolhas, vitórias e rankings de XP.

**Tech Stack:** Python 3.14+, FastAPI, Uvicorn, WebSockets, aiosqlite, Pydantic, Three.js (r128+), Web Audio API, Vanilla CSS, pytest.

**Spec:** `docs/superpowers/specs/2026-10-08-tiktok-live-horse-racing-design.md`

## Global Constraints
- Sem dinheiro real, sem apostas, sem saques, sem menção a R$ ou valores monetários; progressão 100% virtual por XP e níveis.
- Resolução e proporção visual: 1080x1920 (9:16 vertical), com áreas seguras para overlays e comentários do TikTok.
- O sistema deve iniciar e rodar perfeitamente com comandos simples (`pip install -r requirements.txt` e `python main.py`).
- Não utilizar git para commits (conforme instrução explícita do usuário).

## Review Focus
1. **Conexões WebSocket Simultâneas:** O servidor não deve travar nem perder ticks caso múltiplos clientes conectem/desconectem (ex: OBS + Test Panel).
2. **Foto-Finish em Empate Próximo:** Se dois cavalos cruzarem a linha no mesmo tick, a ordenação deve resolver por milésimos de progresso real contínuo sem lançar exceções.
3. **Flood de Comentários / Presentes:** Rajadas de centenas de comandos por segundo no Test Mode ou no TikTok devem ser absorvidas pela fila e rate limiter sem degradar o framerate da física.
4. **Persistência Concorrente no SQLite:** Atualizações em lote de XP no fim da corrida para dezenas de espectadores devem ser atômicas e assíncronas sem bloquear o EventLoop.
5. **Autonomia do Loop Infinito:** O EventDirector deve recuperar graciosamente de qualquer estado e transicionar automaticamente mesmo se nenhum espectador interagir na corrida.

---

### Task 1: Estrutura de Configuração e Dependências

**Files:**
- Create: `requirements.txt`
- Create: `config/config.json`
- Create: `config/settings.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `config.settings.Settings`, `config.settings.load_config()`

- [ ] **Step 1: Escrever teste de validação de configuração**
  Testar carregamento de `config.json`, tipos esperados (durações, lista dos 8 cavalos com atributos, taxas de XP).
- [ ] **Step 2: Executar teste e validar falha**
  `pytest tests/test_config.py`
- [ ] **Step 3: Implementar `requirements.txt`, `config/config.json` e `config/settings.py`**
  Definir modelos Pydantic para configurações e lista de 8 cavalos iniciais com seus atributos base.
- [ ] **Step 4: Executar teste e validar sucesso**
  `pytest tests/test_config.py`

---

### Task 2: Banco de Dados Assíncrono e Repositório de Progressão (SQLite)

**Files:**
- Create: `backend/database/connection.py`
- Create: `backend/database/models.py`
- Create: `backend/database/repository.py`
- Create: `backend/progression.py`
- Test: `tests/test_database.py`

**Interfaces:**
- Produces: `DatabaseRepository.init_db()`, `get_or_create_viewer()`, `record_choice()`, `save_race_results()`, `distribute_race_xp()`, `get_leaderboard()`

- [ ] **Step 1: Escrever testes para persistência e cálculos de nível**
  Testar criação de tabelas, registro de escolhas de cavalos, premiação de XP atômica e recuperação do TOP 10.
- [ ] **Step 2: Executar teste e validar falha**
  `pytest tests/test_database.py`
- [ ] **Step 3: Implementar conexão SQLite, schema DDL, repository e fórmula de progressão em `backend/`**
- [ ] **Step 4: Executar teste e validar sucesso**
  `pytest tests/test_database.py`

---

### Task 3: Segurança, Rate Limiting e Sanitização

**Files:**
- Create: `backend/security.py`
- Test: `tests/test_security.py`

**Interfaces:**
- Produces: `SecurityManager.validate_command()`, `SecurityManager.is_rate_limited()`

- [ ] **Step 1: Escrever testes de segurança contra flood e spam de comandos**
  Testar cooldown de troca de cavalo, limite de comandos por segundo por usuário e sanitização de nomes/strings.
- [ ] **Step 2: Executar teste e validar falha**
  `pytest tests/test_security.py`
- [ ] **Step 3: Implementar `backend/security.py`**
- [ ] **Step 4: Executar teste e validar sucesso**
  `pytest tests/test_security.py`

---

### Task 4: Simulação Física da Corrida e Personalidades dos Cavalos

**Files:**
- Create: `game/horses.py`
- Create: `game/physics.py`
- Create: `game/weather_events.py`
- Create: `game/engine.py`
- Test: `tests/test_engine.py`

**Interfaces:**
- Produces: `RaceEngine.reset()`, `RaceEngine.update(dt)`, `RaceEngine.apply_boost()`, `RaceEngine.get_snapshot()`

- [ ] **Step 1: Escrever testes unitários para a física da corrida**
  Testar cálculo de avanço na pista oval, aplicação das curvas de personalidade dos 8 cavalos, efeito de boosts e detecção de chegada.
- [ ] **Step 2: Executar teste e validar falha**
  `pytest tests/test_engine.py`
- [ ] **Step 3: Implementar `game/horses.py`, `physics.py`, `weather_events.py` e `engine.py`**
- [ ] **Step 4: Executar teste e validar sucesso**
  `pytest tests/test_engine.py`

---

### Task 5: EventDirector (Loop Contínuo Autônomo) e EventBus

**Files:**
- Create: `backend/event_bus.py`
- Create: `game/director.py`
- Test: `tests/test_director.py`

**Interfaces:**
- Produces: `EventBus.publish()`, `EventBus.subscribe()`, `EventDirector.start()`, `EventDirector.current_state`

- [ ] **Step 1: Escrever testes para transições de estados do EventDirector**
  Testar transições: VOTING -> COUNTDOWN -> RACING -> PODIUM -> XP -> LEADERBOARD -> VOTING.
- [ ] **Step 2: Executar teste e validar falha**
  `pytest tests/test_director.py`
- [ ] **Step 3: Implementar `backend/event_bus.py` e `game/director.py`**
- [ ] **Step 4: Executar teste e validar sucesso**
  `pytest tests/test_director.py`

---

### Task 6: Adaptador TikTok e Mock para Test Mode

**Files:**
- Create: `tiktok/parser.py`
- Create: `tiktok/mock_adapter.py`
- Create: `tiktok/adapter.py`
- Test: `tests/test_tiktok_parser.py`

**Interfaces:**
- Produces: `CommandParser.parse_comment()`, `CommandParser.parse_gift()`, `MockTikTokAdapter.inject_event()`, `TikTokLiveAdapter.connect()`

- [ ] **Step 1: Escrever testes de parsing de comentários e presentes**
  Testar comandos numéricos ("1", "2"), nomes ("relampago", "trovao"), presentes (rosa -> turbo), normalização sem acentos.
- [ ] **Step 2: Executar teste e validar falha**
  `pytest tests/test_tiktok_parser.py`
- [ ] **Step 3: Implementar `tiktok/parser.py`, `mock_adapter.py` e `adapter.py`**
- [ ] **Step 4: Executar teste e validar sucesso**
  `pytest tests/test_tiktok_parser.py`

---

### Task 7: Servidor FastAPI, WebSocket e Endpoints REST

**Files:**
- Create: `web/server.py`
- Modify: `main.py`
- Test: `tests/test_server.py`

**Interfaces:**
- Produces: `app` FastAPI, `/ws` endpoint de broadcast, `/api/test/inject` endpoint REST

- [ ] **Step 1: Escrever testes para endpoints FastAPI e broadcast WebSocket**
- [ ] **Step 2: Executar teste e validar falha**
  `pytest tests/test_server.py`
- [ ] **Step 3: Implementar `web/server.py` conectando Engine, Director, EventBus e SQLite**
- [ ] **Step 4: Executar teste e validar sucesso**
  `pytest tests/test_server.py`

---

### Task 8: Painel de Controle do Streamer (Test Mode)

**Files:**
- Create: `web/static/test.html`
- Create: `web/static/css/test_panel.css`
- Create: `web/static/js/test_panel.js`

**Interfaces:**
- Produces: Interface web em `http://localhost:8000/test` com injeção de comentários, presentes, likes, simulação de 50 espectadores e controle de clima.

- [ ] **Step 1: Criar layout e CSS do painel de testes moderno**
- [ ] **Step 2: Implementar lógica JavaScript de disparo rápido de eventos para o backend via API/WS**
- [ ] **Step 3: Validar envio de eventos via script de teste automatizado**

---

### Task 9: Cenário 3D do Hipódromo, Pista e Iluminação (Three.js)

**Files:**
- Create: `web/static/js/scene.js`

**Interfaces:**
- Produces: `TrackScene.init(container)`, `TrackScene.update(time, weather)`, `TrackScene.getTrackPosition(distance_ratio, lane)`

- [ ] **Step 1: Implementar geometria precisa da pista oval, textura de areia, gramado central, cercas de contenção brancas, arquibancadas com torcedores estilizados e refletores esportivos**
- [ ] **Step 2: Implementar variações de iluminação e atmosfera climática (Dia, Pôr do Sol esportivo, Noite com refletores, Chuva)**

---

### Task 10: Modelagem 3D dos Cavalos, Rigging Procedural de Galope e Efeitos

**Files:**
- Create: `web/static/js/horses_view.js`
- Create: `web/static/js/particles.js`

**Interfaces:**
- Produces: `HorseVisualManager.update(horses_data)`, `ParticleSystem.emitDust()`, `ParticleSystem.emitTurbo()`, `ParticleSystem.emitConfetti()`

- [ ] **Step 1: Implementar modelos 3D estilizados com Three.js para os 8 cavalos com cores, arreios numerados (#1 a #8) e jockeys personalizados**
- [ ] **Step 2: Implementar animação procedural de galope sincronizada à velocidade real de cada cavalo**
- [ ] **Step 3: Implementar sistema de partículas (nuvens de poeira de casco, labaredas/faíscas de turbo e chuva de confetes no pódio)**

---

### Task 11: Diretor de Câmeras Cinematográficas e Áudio Sintetizado

**Files:**
- Create: `web/static/js/camera.js`
- Create: `web/static/js/audio.js`

**Interfaces:**
- Produces: `CinematicCameraDirector.setMode()`, `CinematicCameraDirector.update()`, `GameAudio.playGallop()`, `GameAudio.playFanfare()`, `GameAudio.playTurbo()`, `GameAudio.playCrowd()`

- [ ] **Step 1: Implementar os 6 ângulos de câmera (Start, Chase líderes, Overtake ação, Cerca TV rails, Foto-finish reta final e Pódio giratório 360º)**
- [ ] **Step 2: Implementar o sintetizador Web Audio com sons de galope dinâmico, clamor de torcida, sirene de largada, turbos e fanfarra de vitória**

---

### Task 12: HUD de Transmissão Esportiva Profissional 9:16 para OBS

**Files:**
- Create: `web/static/css/styles.css`
- Create: `web/static/js/hud.js`
- Create: `web/static/js/client.js`
- Create: `web/static/index.html`

**Interfaces:**
- Produces: Tela completa para Browser Source do OBS (1080x1920) integrando Scene, HorsesView, Particles, Camera, HUD e Audio.

- [ ] **Step 1: Desenvolver a interface esportiva de alta fidelidade: placar de posições em tempo real, cartela de escolha com contadores de torcida, barra de progresso vertical, pódio de vitória com troféu e tela de ranking da LIVE**
- [ ] **Step 2: Implementar fila inteligente de notificações na tela (ex: "@user escolheu RELÂMPAGO", "🎁 @user enviou TURBO!") com animações suaves e sem poluição visual**
- [ ] **Step 3: Conectar o cliente WebSocket ao `server.py` para sincronização a 60 FPS**

---

### Task 13: Ponto de Entrada `main.py` e Validação Completa Ponta a Ponta

**Files:**
- Create: `main.py`
- Create: `tests/test_e2e_flow.py`

**Interfaces:**
- Produces: Executável único que inicia servidor, banco, simulador e loop autônomo com `python main.py`

- [ ] **Step 1: Escrever teste de integração de ciclo completo (corrida simulada com votação, turbo, linha de chegada e gravação de XP no banco)**
- [ ] **Step 2: Implementar `main.py` com suporte a flags de linha de comando (`--test-mode`, `--tiktok-user`, `--port`) e inicialização limpa**
- [ ] **Step 3: Executar suíte completa de testes com `pytest -v` garantindo 100% de sucesso**
- [ ] **Step 4: Realizar execução de fumaça de 10 segundos com `python main.py` e verificar respostas HTTP e WebSocket**
