# 📋 MELHORIAS — TikTok LIVE Horse

Anotações do que fazer no projeto. Ordem = impacto primeiro.

---

## 🔥 PARTE 1 — Prender atenção (retenção da live)

**Diagnóstico:** o voto leva 5s e o payoff demora 2min. O cara aposta e não tem motivo pra ficar olhando. Corrida de ~1m50 é eternidade pro ritmo do TikTok. O que prende gente é: **motivo pra ficar + motivo pra agir a cada 15s + motivo pra voltar**.

### 1. Bônus Fiel — XP dobrado pra quem fica até o pódio ⭐ prioridade máxima ✅ FEITO
- O que é: quem votou E viu o pódio ganha 2x XP. Quem saiu no meio ganha metade. Não pune, premia.
- Voz avisa: *"ficou até o fim? XP dobrado!"*
- Mexe em: `backend/progression.py` (ou onde distribui XP), `game/director.py` (detectar quem ficou até o pódio)
- Esforço: pequeno (1 mudança na distribuição de XP)
- **Feito:** `repository.distribute_race_xp(..., fieis, multiplicador_fiel=2.0)` — o XP base de
  todo mundo fica igual e quem ficou até o pódio leva ×2 (o "metade" do texto é a mesma conta
  vista do outro lado; ninguém é punido). Presença = quem apareceu (voto no meio da prova,
  comentário, presente, curtida, entrada, follow) com a prova rolando ou no pódio — o voto da
  votação NÃO conta, senão todo mundo seria fiel. Badge `🏅 FIEL 2x` na tela de XP + aviso da voz.

### 2. Torcida do meio da corrida VISÍVEL ✅ FEITO
- O jogo JÁ tem: empurrãozinho digitando o número na corrida + boost de curtida (+0.2 m/s). Ninguém sabe disso.
- O que fazer: texto grande na tela `DIGITE 7 PRA EMPURRAR A NEVASCA!` + barra coletiva de torcida por cavalo no HUD.
- Efeito: o cara sente que tá pilotando, não só apostando.
- Mexe em: `web/static/js/hud.js`, `game/falas.py`
- **Feito:** `#hudTorcidaCall` (texto grande, alterna a cada 14s entre o cavalo que precisa de
  empurrão (`DIGITE 7 PRA EMPURRAR A NEVASCA!` / genérica `DIGITE 1-8 PRA EMPURRAR!`) + barra
  âmbar/vermelha por cavalo na torre de posições com contador `🔥N`. O servidor manda
  `state.torcida` com torcedores, extra em m/s e % **do cavalo mais empurrado da pista** (o teto
  `TORCIDA_EXTRA_CAP` foi removido depois, a pedido: quem limita é a duração de cada empurrão).
  Cada pessoa conta UMA vez, mesmo spammando o número.

### 3. Narrador fala nome de GENTE, não só de cavalo ✅ FEITO
- Ninguém sai quando ouve o próprio nome.
- Hoje a voz fala presente e entrada, mas na corrida só narra posição.
- O que fazer: a cada placar (~300m), citar 2-3 nomes dos votos/torcida: *"e a torcida do Rafael tá empurrando o #4!"*
- Mexe em: `game/narrador.py`, `game/falas.py`
- **Feito:** o placar cita até 3 nomes de quem está empurrando aquele cavalo (`{nomes}` +
  `{cavalo}`), sem repetir o mesmo nome na mesma corrida (só reabre quando acaba a lista).
  Marco novo de locução em 675m ("torcida") e 1425m ("fidelidade", XP dobrado). A fala só cita
  quem está presente — sem nomes, sai a frase antiga, sem buraco.

### 4. Encurtar o ciclo
- Hoje: 30s votação + ~110s corrida (3000m) = 2m30 de loop. No TikTok isso é 2 vidas.
- Testar: votação 20s, pista 1800–2000m (~60–70s). Mais corridas/hora = mais apostas, mais pódios, mais dopamina.
- Alternativa sem mexer na física: "modo turbo" alternando com o normal.
- Mexe em: `config/config.json` (distância + tempos), validar com `python tools/monte_carlo.py`

### 5. Meta de curtidas na tela
- Barra fixa: *META 10K LIKES — libera boost geral*.
- Curtida é grátis e infinita, o sistema de boost de curtida já existe — só falta mostrar a barra e a voz comemorar quando bate.
- Ocupa quem não quer gastar presente.
- Mexe em: `web/static/js/hud.js`, `game/narrador.py`

### 6. Mostrar as odds na grade de votação ✅ FEITO
- O jogo já sabe os favoritos por clima (Titã na lama, Nevasca na chuva).
- Mostrar como odd na votação: `#6 TITÃ ⭐ favorito na lama`.
- Vira "informação de aposta" e dá assunto pro chat nos 20s de votação.
- Mexe em: tela de votação (frontend), `game/weather_events.py` + `game/horses.py` (fonte dos favoritos)
- **Feito:** `WeatherSystem.vantagem(personality)` é a MESMA conta que entra na velocidade (sem
  o empurrão global do vento, que vale para todos e não é vantagem de ninguém) — mostrar
  "favorito" e a corrida correr outra coisa seria mentir para quem aposta. A grade mostra
  `⭐ favorito na chuva +1,2%` / `⚠️ sofre na chuva -0,7%`; céu limpo não mostra etiqueta.

---

## 🌦️ Extra — a virada do clima não se via na pista
- **Problema relatado:** "quando muda o clima não vi impacto nenhum nos cavalos".
- **Medido:** a tabela do clima vale poucos % — a 28 m/s, 1% são 0,28 m/s, enquanto a diferença
  natural entre dois cavalos na mesma volta é de METROS por segundo. O efeito é real no
  agregado (com chuva, os dois favoritos levam ~84% das corridas) e invisível no instante.
  Subir a tabela para "dar para ver" deixaria a corrida decidida — pior para a live.
- **Feito:** a virada agora tem um evento visual próprio (`IMPULSO_DA_VIRADA = 1.06` por 7s em
  quem o tempo NOVO favorece), com o emblema do clima na garupa (`🌧️ O TEMPO VIROU`), toast
  `WEATHER_GAIN` e a pista reagindo junto com a voz. Quem PERDE não leva "tropeço" — o cavalo
  sairia com halo de turbo justo quando está perdendo velocidade.

### 7. Fixar o comentário da live
- Fixar: `"Digite 1-8 pra apostar! Fica até o pódio = XP dobrado"`.
- 80% de quem entra e sai é porque não entendeu o que fazer depois do voto.
- Esforço: zero código, fazer na hora de abrir a live.

**Ordem sugerida:** 1 + 7 hoje (só config e texto fixado) → 2 + 3 em seguida (onde a retenção dobra de verdade).

---

## 🛠️ PARTE 2 — Saúde do repo (não perder trabalho / live não cair)

### P0 — risco de perder trabalho
- [ ] **Decidir o `scene.js`:** 572 linhas não commitadas. Commitar (ou separar em 2 commits). Ver com `git diff web/static/js/scene.js`.
- [ ] **`processos.bat` solto na raiz (`??`):** mover pra `tools/processos.bat` + 3 linhas no README, ou por no `.gitignore` se for só uso local.

### P1 — risco de a live cair na hora
- [ ] **Auth mínima no `/test`:** hoje sem senha + `host 0.0.0.0` = qualquer um na rede controla a corrida (iniciar/finalizar/zerar TODOS). Botar um token simples no `config.json` e checar em `web/server.py` (~30 min).
- [ ] **Seção Troubleshooting no README:** os 3 problemas que vão morder: porta 8000 ocupada, OBS sem voz (Áudio do Desktop no `python.exe`), TTS mudo por 403 do `edge-tts`. Quebrar o parágrafo gigante do passo 4 do OBS em lista.
- [ ] **Reconexão do TikTok visível:** `TikTokLive` é lib não-oficial e quebra. Garantir log + backoff de reconexão visível no console do `/test`.

### P2 — dívida que vai cobrar
- [ ] **CI mínimo:** `.github/workflows/test.yml` com `pytest -q` (hoje só roda local, 34s).
- [ ] **Congelar `requirements.txt`:** `fastapi>=0.115`, `TikTokLive>=6.0` soltos — um `pip install` novo pode quebrar tudo na véspera da live. Travar com `pip freeze`.
- [ ] **README (15KB) x DOCUMENTACAO.md (76KB):** tem duplicação. README = 2 passos + OBS + painel; física/fórmulas ficam em `docs/`.
- [ ] **Frontend 920KB, `scene.js` com 2547 linhas:** conferir versão do `three.min.js` local; pensar em split do `scene.js`. Partícula/confete em loop 360º = clássico vazamento de memória em live de 3h.

---

*Criado em 2026-10-16. Estado da base: 106 testes passando.*
