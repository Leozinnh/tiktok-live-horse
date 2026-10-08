# 🏇 TikTok LIVE - Jogo de Corrida de Cavalos Interativo (3D)

Jogo de corrida de cavalos interativo e autônomo desenvolvido especialmente para transmissões no **TikTok LIVE** e captura via **OBS Studio (1080x1920 vertical, 9:16)**.

---

## ⚠️ AVISO LEGAL E COMPLIANCE
- **100% Virtual:** Este jogo **NÃO** possui dinheiro real, apostas, saques, conversão de pontos em dinheiro, prêmios financeiros ou qualquer mecânica de azar.
- Os pontos são exclusivamente **XP e Níveis Virtuais** para engajamento, conquistas, badges e ranking da LIVE.
- Presentes do TikTok ativam turbos cosméticos/visuais e concedem XP ao apoiador.

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
   - **Controlar áudio via OBS:** Marque se quiser monitorar o som direto pelo mixer do OBS.
4. Clique em **OK**. A pista 3D, cavalos animados e HUD esportivo aparecerão imediatamente.

---

## 🎮 Painel de Testes do Streamer (Test Mode)

Você pode simular e testar todas as interações sem precisar estar ao vivo no TikTok:

1. Abra seu navegador em: **`http://localhost:8000/test`**
2. Recursos disponíveis com 1 clique:
   - **Simular Comentários:** Envie votos rápidos nos cavalos (#1 ao #8) ou comandos de torcida (`/turbo`, `bora torcida!`).
   - **Simular Presentes:** Dispare Rosa, Café, Donut, Boné, Leão ou Galáxia e veja o cavalo correspondente acelerar em chamas com boost de velocidade.
   - **Rajada de Público:** Simule 20 ou 50 espectadores escolhendo cavalos simultaneamente para teste de estresse.
   - **Controle de Clima:** Alterne entre Sol Claro, Pôr do Sol Dourado, Noite com Refletores do Estádio, Chuva, Tempestade e Vento.

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

O jogo roda infinitamente sem necessidade de operador:
1. **ESCOLHA SEU CAVALO (30s):** Cartela na tela com os 8 cavalos e contadores de torcida em tempo real. O chat comenta `1` a `8` ou o nome do cavalo.
2. **CONTAGEM REGRESSIVA (5s):** 5.. 4.. 3.. 2.. 1.. com bips sonoros e portões dos boxes se preparando.
3. **CORRIDA AO VIVO (~35s):** Física a 60 ticks/s, câmeras cinematográficas inteligentes (perseguição, ação e cerca), galope procedural, poeira de cascos e turbos.
4. **PÓDIO (8s):** Câmera 360º no vencedor, troféus de 1º, 2º e 3º lugares, e chuva de confetes.
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
