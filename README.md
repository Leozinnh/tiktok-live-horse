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
4. Clique em **OK**. A pista 3D, cavalos animados, câmeras de TV e HUD esportivo aparecerão imediatamente.

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
- **Presentes & Super Raros:**
  - 🌹 **Rosa** e ☕ **Café**: Turbo básico e ágil.
  - 🧢 **Boné** e 🍩 **Donut**: Super Boost de velocidade.
  - 🦁 **Leão (+2000 XP)**: Fúria dourada com pilar de luz celeste de 90m, onda de choque e screen shake.
  - 🌌 **Galáxia (+1500 XP)**: Overdrive cósmico com vórtice estelar violeta e chamas nos cascos.
  - 🐉 **Dragão (+1800 XP)**: Impacto místico com rastro de labaredas e rugido de torcida.
  - *Presentes enviados durante a fase de votação já ficam acumulados para a largada!*
- **Rajada em Massa:** Simule 20 ou 50 espectadores votando simultaneamente para testes de estresse.
- **Controle de Clima:** Sol Claro, Pôr do Sol, Noite com Refletores do Estádio, Chuva, Tempestade e Vento.

### 4. Console com Histórico e Filtros:
- Abas de filtragem: `Todos`, `🎁 Presentes`, `💬 Votos`, `🏁 Fases`.
- Contadores em tempo real do total de presentes e votos na transmissão.
- Botões para `🗑️ Limpar` e `📋 Copiar Histórico`.

---

## 🐎 Os 8 Cavalos e Personalidades

1. **#1 RELÂMPAGO (Dourado):** Arrancada explosiva; lidera no início e perde fôlego na reta final.
2. **#2 TROVÃO (Azul):** Arrancada final avassaladora nos últimos 150 metros.
3. **#3 FURACÃO (Verde):** Ritmo consistente e imune à fadiga.
4. **#4 RAIO (Vermelho):** Caçador no vácuo; acelera quando corre atrás dos líderes.
5. **#5 PANTERA (Preto):** Especialista em curvas e ultrapassagens pelo lado interno da pista.
6. **#6 TITÃ (Bronze):** Tanque inabalável; ganha vantagem em pistas molhadas/lama.
7. **#7 NEVASCA (Branco):** Frio e técnico; cresce de rendimento na chuva e no vento.
8. **#8 FANTASMA (Roxo):** Imprevisível; alto fator sorte com arrancadas repentinas.

---

## 🔄 Ciclo Autônomo da Transmissão (EventDirector)

O jogo roda infinitamente sem necessidade de operador humano:
1. **ESCOLHA SEU CAVALO (30s):** Grade na tela com os 8 cavalos e contadores de torcida ao vivo. O chat comenta `1` a `8` ou o nome do cavalo.
2. **CONTAGEM REGRESSIVA (5s):** 5.. 4.. 3.. 2.. 1.. com bips sonoros e portões dos boxes se preparando.
3. **CORRIDA AO VIVO (~35s):** Física a 60 ticks/s, câmeras cinematográficas inteligentes, galope procedural sincronizado, poeira de cascos, cercas contínuas em 360º e turbos.
4. **DISPUTA DE CHEGADA E PÓDIO (8s):** Ao cruzar a linha de chegada, a câmera acompanha a disputa pelo 2º e 3º lugares e 3.5s depois avança para o pódio com troféus, fanfarra orquestral e chuva de confetes em órbita 360º.
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

## 📖 Documentação Completa para Modificações

Para entender a fundo a física da pista oval, fórmulas de velocidade, adicionar novos cavalos, criar novos presentes ou customizar as câmeras e o 3D:
👉 Consulte o arquivo **`DOCUMENTACAO.md`** na raiz do projeto.
