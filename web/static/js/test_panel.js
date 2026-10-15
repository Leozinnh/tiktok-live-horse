// Painel de controle e testes (/test).
//
// IDENTIDADE ÚNICA: o nome da barra de cima é o único do painel. Voto,
// torcida, presente, curtida, entrada e follow saem todos com ele. Antes
// havia "Nome do Espectador" e "Nome do Doador" separados, com valores
// diferentes de fábrica: quem votava como @leonardo e mandava presente
// aparecia na live como @joão_silva — dois espectadores para a mesma pessoa,
// e o teste de "o presente cai no cavalo em que votei" nunca fechava.
const NOME_PADRAO = "Leonardo";
const STORAGE_KEY = "tiktok-horse-espectador";

let ws = null;
let eventLogs = [];
let activeFilter = "all";
let statsCounters = {
  gifts: 0,
  votes: 0,
  races: 0
};
let seenServerNotifications = new Set();

// ----------------------------------------------------------------- identidade

function lerNomeSalvo() {
  try {
    return window.localStorage.getItem(STORAGE_KEY) || "";
  } catch (err) {
    return ""; // armazenamento bloqueado: o painel funciona, só não lembra o nome
  }
}

function salvarNome(nome) {
  try {
    window.localStorage.setItem(STORAGE_KEY, nome);
  } catch (err) {
    /* sem armazenamento: segue o jogo */
  }
}

function nomeDoEspectador() {
  const el = document.getElementById("viewerUser");
  return ((el && el.value) || "").trim() || NOME_PADRAO;
}

function identidade() {
  const nome = nomeDoEspectador();
  // O username vai normalizado como no banco (`strip().lower()` em
  // repository.py e no director.torcida_por_viewer): "Ana" e "ana" são a MESMA
  // pessoa. O display_name vai como digitado — é ele que aparece no HUD e na voz.
  return { username: nome.toLowerCase(), display_name: nome };
}

function atualizarEcho() {
  const username = nomeDoEspectador().toLowerCase();
  document.querySelectorAll(".who-echo").forEach((el) => {
    el.textContent = `@${username}`;
  });
}

function aoTrocarNome() {
  salvarNome(document.getElementById("viewerUser").value.trim());
  atualizarEcho();
}

// --------------------------------------------------------------------- console

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}

function appendLog(msg, color = "#38bdf8", category = "all") {
  const time = new Date().toLocaleTimeString();
  const entry = { time, msg, color, category };
  eventLogs.unshift(entry);

  if (category === "gift") {
    statsCounters.gifts++;
  } else if (category === "vote") {
    statsCounters.votes++;
  } else if (category === "race") {
    statsCounters.races++;
  }

  updateCounterUI();
  renderLogs();
}

function updateCounterUI() {
  const gEl = document.getElementById("logTotalGifts");
  if (gEl) gEl.innerText = statsCounters.gifts;
  const vEl = document.getElementById("logTotalVotes");
  if (vEl) vEl.innerText = statsCounters.votes;
}

function setLogFilter(filterName) {
  activeFilter = filterName;
  document.querySelectorAll(".log-filter-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.getAttribute("data-filter") === filterName);
  });
  renderLogs();
}

function renderLogs() {
  const container = document.getElementById("logContainer");
  if (!container) return;

  const filtered = activeFilter === "all"
    ? eventLogs
    : eventLogs.filter((item) => item.category === activeFilter);

  container.innerHTML = "";
  if (filtered.length === 0) {
    container.innerHTML = '<div class="log-entry" style="color: #64748b;">Nenhum evento registrado nesta categoria.</div>';
    return;
  }

  filtered.slice(0, 150).forEach((item) => {
    const el = document.createElement("div");
    el.className = "log-entry";
    el.style.color = item.color;
    // Os textos vêm do servidor (nomes digitados no chat da live entram aqui):
    // escapar antes de virar HTML evita que um nick com tag quebre o painel.
    el.innerHTML = `<span style="color: #64748b; font-size: 11px;">[${item.time}]</span> ${escapeHtml(item.msg)}`;
    container.appendChild(el);
  });
}

function clearLogs() {
  eventLogs = [];
  renderLogs();
}

function copyLogs() {
  const text = eventLogs.map((i) => `[${i.time}] ${i.msg}`).join("\n");
  navigator.clipboard.writeText(text).then(() => {
    appendLog("Histórico do console copiado para a área de transferência.", "#34d399", "all");
  }).catch((err) => {
    appendLog(`Não consegui copiar o histórico: ${err}`, "#f87171", "all");
  });
}

// ------------------------------------------------------------------ websocket

function connectWs() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    const badge = document.getElementById("connectionStatus");
    badge.className = "status-badge";
    badge.innerHTML = '<span class="status-indicator"></span> CONECTADO';
    appendLog("WebSocket conectado ao servidor.", "#34d399", "all");
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      updateLiveStats(data);
    } catch (e) {
      console.error("Erro no parse do JSON:", e);
    }
  };

  ws.onclose = () => {
    const badge = document.getElementById("connectionStatus");
    badge.className = "status-badge disconnected";
    badge.innerHTML = '<span class="status-indicator"></span> DESCONECTADO';
    appendLog("WebSocket desconectado. Tentando reconectar...", "#f87171", "all");
    setTimeout(connectWs, 2000);
  };
}

let lastServerState = null;

// Cada tipo de aviso que o servidor manda tem a sua cor e a sua aba.
// CHEER e LIKE entram aqui de propósito: a torcida do chat ("Ana torceu pelo
// #5") e a rajada de curtidas não apareciam no painel — só no terminal do
// Python, que é justamente onde o streamer não está olhando durante a live.
const NOTIF_ESTILO = {
  GIFT: { cor: "#ec4899", categoria: "gift" },
  LIKE: { cor: "#f472b6", categoria: "gift" },
  CHOICE: { cor: "#38bdf8", categoria: "vote" },
  CHEER: { cor: "#a855f7", categoria: "vote" },
  FOLLOW: { cor: "#34d399", categoria: "vote" },
  WEATHER: { cor: "#22d3ee", categoria: "race" },
  WEATHER_CHANGE: { cor: "#22d3ee", categoria: "race" }
};

function registrarAvisosDoServidor(notifications) {
  if (!Array.isArray(notifications)) return;

  notifications.forEach((n) => {
    // O id vem do director e é único na sessão inteira. Antes a chave era o
    // TEXTO do aviso: dois avisos iguais ("Ana torceu pelo #5" duas vezes, ou
    // dois presentes da mesma pessoa no mesmo cavalo) viravam um só no painel.
    if (n.id !== undefined) {
      if (seenServerNotifications.has(n.id)) return;
      seenServerNotifications.add(n.id);
      if (seenServerNotifications.size > 400) {
        seenServerNotifications = new Set(Array.from(seenServerNotifications).slice(-200));
      }
    }

    const estilo = NOTIF_ESTILO[n.type];
    if (!estilo) return;

    const cor = n.type === "GIFT" && n.is_legendary ? "#fbbf24" : estilo.cor;
    appendLog(`${n.badge ? n.badge + " " : ""}${n.text}`, cor, estilo.categoria);
  });
}

function updateLiveStats(data) {
  document.getElementById("statRaceNum").innerText = `#${data.race_number || 1}`;
  document.getElementById("statState").innerText = data.director_state || "READY";
  document.getElementById("statTimer").innerText = `${data.remaining_seconds || 0}s`;
  document.getElementById("statWeather").innerText = (data.engine && data.engine.weather) || "CLEAR";

  renderCorridaAoVivo(data);

  if (data.director_state && data.director_state !== lastServerState) {
    appendLog(`🏁 FASE ALTERADA: ${data.director_state} (Corrida #${data.race_number})`, "#34d399", "race");
    lastServerState = data.director_state;
    // Fim de corrida é quando o XP muda de mão: a lista se atualiza sozinha.
    if (data.director_state === "PODIUM" || data.director_state === "LEADERBOARD") {
      loadViewers();
    }
  }

  registrarAvisosDoServidor(data.notifications);
}

// ------------------------------------------------------------------- comandos

async function postJson(url, corpo = null) {
  const opcoes = { method: "POST" };
  if (corpo) {
    opcoes.headers = { "Content-Type": "application/json" };
    opcoes.body = JSON.stringify(corpo);
  }
  const res = await fetch(url, opcoes);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function sendComment(customText = null) {
  const texto = (customText || document.getElementById("commentText").value || "").trim();
  if (!texto) return;

  const quem = identidade();
  try {
    const result = await postJson("/api/test/inject_comment", { ...quem, text: texto });
    // Comentário aceito não vira linha local: o servidor manda o aviso
    // ("escolheu o #N" ou "torceu pelo #N") e é ele que conta a história —
    // era esse aviso que faltava para o painel explicar o voto do chat.
    if (result.status !== "ok") {
      appendLog(`⚠️ @${quem.username} "${texto}" → ${result.message || result.status}`, "#fbbf24", "vote");
    } else if (result.action === "CHEER") {
      appendLog(`📣 @${quem.username} puxou a torcida do cavalo apoiado!`, "#a855f7", "vote");
    }
  } catch (err) {
    appendLog(`Erro ao enviar comentário: ${err}`, "#f87171", "all");
  }
}

async function simulateJoin() {
  const quem = identidade();
  try {
    // Entrada não gera aviso no servidor (é presença, não voto): a linha do
    // painel é o único registro dela.
    await postJson("/api/test/inject_join", quem);
    appendLog(`👤 @${quem.username} entrou na LIVE (oi da voz)!`, "#38bdf8", "vote");
  } catch (err) {
    appendLog(`Erro ao simular entrada: ${err}`, "#f87171", "all");
  }
}

async function simulateFollow() {
  const quem = identidade();
  try {
    await postJson("/api/test/inject_follow", quem); // o aviso vem do servidor
  } catch (err) {
    appendLog(`Erro ao simular follow: ${err}`, "#f87171", "all");
  }
}

async function sendGift(customGift = null) {
  const gift = customGift || document.getElementById("giftSelect").value;
  const count = Math.max(1, parseInt(document.getElementById("giftCount").value) || 1);
  const quem = identidade();

  try {
    await postJson("/api/test/inject_gift", { ...quem, gift_name: gift, count });
    // Sem eco local: a linha do presente vem do servidor e diz em qual cavalo
    // o boost caiu e com que força — a mesma frase que a live está vendo.
  } catch (err) {
    appendLog(`Erro ao enviar presente: ${err}`, "#f87171", "all");
  }
}

async function simulateLikes(count) {
  const quem = identidade();
  try {
    await postJson("/api/test/inject_like", { ...quem, count });
    // Rajada de 20+ ganha linha do servidor; abaixo disso (e o empurrão de
    // 5+) o painel explica o que a curtida fez, senão o botão parece morto.
    if (count < 20) {
      appendLog(
        count >= 5
          ? `💗 @${quem.username} mandou ${count} curtidas → empurrão leve no cavalo apoiado`
          : `💗 @${quem.username} mandou ${count} curtidas → abaixo de 5, sem empurrão`,
        "#f472b6",
        "gift"
      );
    }
  } catch (err) {
    appendLog(`Erro ao simular curtidas: ${err}`, "#f87171", "all");
  }
}

async function simulateBurst(count) {
  appendLog(`Simulando rajada de ${count} espectadores escolhendo cavalos...`, "#a855f7", "vote");
  try {
    const result = await postJson("/api/test/burst", { count });
    appendLog(`Sucesso: ${result.simulated_viewers} espectadores adicionados!`, "#34d399", "vote");
  } catch (err) {
    appendLog(`Erro na simulação de rajada: ${err}`, "#f87171", "all");
  }
}

async function setWeather(type) {
  try {
    const result = await postJson("/api/test/weather", { weather: type });
    appendLog(`Clima alterado para: ${result.weather}`, "#38bdf8", "race");
  } catch (err) {
    appendLog(`Erro ao trocar clima: ${err}`, "#f87171", "all");
  }
}

// Controles de corrida: a linha do console diz o que o servidor RESPONDEU
// (a fase em que ficou), não o que o botão prometia — antes um erro do
// servidor aparecia no painel como sucesso.
async function acaoDeCorrida(url, montarMensagem) {
  try {
    const result = await postJson(url);
    appendLog(montarMensagem(result), "#34d399", "race");
  } catch (err) {
    appendLog(`❌ Falhou (${url}): ${err}`, "#f87171", "all");
  }
}

function skipToRace() {
  return acaoDeCorrida("/api/test/skip_to_race", (r) => `⏩ Votação pulada! Fase agora: ${r.state}`);
}

function forceFinish() {
  return acaoDeCorrida("/api/test/force_finish", (r) => `🏁 Corrida finalizada na mão! Fase agora: ${r.state}`);
}

function nextRace() {
  return acaoDeCorrida("/api/test/next_race", (r) => `🔄 Ciclo reiniciado! Nova Corrida #${r.race_number}`);
}

async function boostHorse(horseId) {
  try {
    const res = await fetch(`/api/test/boost_horse?horse_id=${horseId}`, { method: "POST" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const r = await res.json();
    appendLog(
      `⚡ Turbo manual no #${r.horse_id} ${r.horse_name || ""}: ${r.power.toFixed(2)}x por ${Math.round(r.duration)}s`,
      "#f59e0b",
      "gift"
    );
  } catch (err) {
    appendLog(`Erro ao aplicar boost: ${err}`, "#f87171", "all");
  }
}

// ------------------------------------------------------------- corrida ao vivo

let assinaturaCorrida = "";

function renderCorridaAoVivo(data) {
  const container = document.getElementById("corridaAoVivo");
  if (!container || !data.engine) return;

  const pista = data.engine.track_length || 3000;
  const placar = data.engine.leaderboard || [];
  const porId = {};
  (data.engine.horses || []).forEach((h) => { porId[h.id] = h; });

  // Assinatura: redesenha quando algo MUDA de verdade (10m de pista, ~3x por
  // segundo a 28 m/s) em vez de a cada um dos 60 ticks do servidor.
  const assinatura = `${data.director_state}|${placar
    .map((l) => `${l.position}-${l.horse_id}-${Math.round(l.distance / 10)}-${l.supporter_count}-${l.boost_active ? 1 : 0}`)
    .join("|")}`;
  if (assinatura === assinaturaCorrida) return;
  assinaturaCorrida = assinatura;

  const resumo = document.getElementById("corridaResumo");
  if (resumo) {
    const lider = placar[0];
    resumo.innerText = (lider && lider.distance > 0)
      ? `${data.director_state} • ${lider.name} na frente com ${Math.round(lider.distance)}m de ${Math.round(pista)}m`
      : `${data.director_state || "—"} • prova de ${Math.round(pista)}m`;
  }

  const linhas = placar.map((l) => {
    const h = porId[l.horse_id] || {};
    const boosts = h.boosts || [];
    const boost = boosts[boosts.length - 1]; // o mais recente é o que está puxando
    // Torcida e curtida SOMAM velocidade (m/s); presente MULTIPLICA. Mostrar
    // as duas como "1.35x" contava a história errada: o empurrão da torcida
    // aparecia como se fosse um turbo de 40% quando é +0,4 m/s.
    const boostTxt = boost
      ? `<span style="color: #fbbf24;">${boost.emoji || "⚡"}</span> ` +
        `<strong>${Number(boost.power).toFixed(2)}${boost.additive ? " m/s" : "x"}</strong>` +
        (h.donor_name
          ? `<div style="color: #94a3b8; font-size: 9px; max-width: 64px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(h.donor_name)}">${escapeHtml(h.donor_name)}</div>`
          : "")
      : '<span style="color: #475569;">—</span>';
    const pct = Math.max(0, Math.min(100, (l.distance / pista) * 100));

    return `
      <tr style="border-top: 1px solid rgba(148, 163, 184, 0.15);">
        <td style="padding: 4px 2px; color: #94a3b8; text-align: right; width: 14px;">${l.position}</td>
        <td style="padding: 4px 4px; white-space: nowrap;">
          <span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: ${l.color_hex}; margin-right: 5px;"></span>
          <span style="color: #e2e8f0; font-weight: 700;">#${l.horse_id}</span>
          <span style="color: #cbd5e1;">${escapeHtml(l.name)}</span>${h.finished ? " 🏁" : ""}
        </td>
        <td style="padding: 4px 4px; min-width: 56px;">
          <div style="background: rgba(148, 163, 184, 0.25); border-radius: 4px; height: 6px; overflow: hidden;">
            <div style="width: ${pct}%; height: 100%; background: ${l.color_hex};"></div>
          </div>
          <div style="font-size: 10px; color: #94a3b8; margin-top: 2px;">${Math.round(l.distance)}m</div>
        </td>
        <td style="padding: 4px 2px; text-align: center; color: #38bdf8; font-weight: 700;">${l.supporter_count}</td>
        <td style="padding: 4px 2px; font-size: 11px; white-space: nowrap;">${boostTxt}</td>
      </tr>`;
  }).join("");

  container.innerHTML = `
    <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
      <thead>
        <tr style="color: #94a3b8; font-size: 10px; text-transform: uppercase;">
          <th></th>
          <th style="text-align: left; padding: 3px 4px; white-space: nowrap;">Cavalo</th>
          <th style="text-align: left; white-space: nowrap;">Prova</th>
          <th style="text-align: center;" title="Apoios (votos) do cavalo">👥</th>
          <th style="text-align: left; white-space: nowrap;">Boost ⚡</th>
        </tr>
      </thead>
      <tbody>${linhas}</tbody>
    </table>`;
}

// -------------------------------------------------------------- usuários/XP

let lastViewers = [];

async function loadViewers() {
  try {
    const res = await fetch("/api/test/viewers");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    lastViewers = data.viewers || [];
    renderViewers(lastViewers, data.total || lastViewers.length);
  } catch (err) {
    appendLog(`Erro ao carregar usuários: ${err}`, "#f87171", "all");
  }
}

function renderViewers(viewers, total) {
  const totalEl = document.getElementById("viewersTotal");
  if (totalEl) totalEl.innerText = total;

  const container = document.getElementById("viewersList");
  if (!container) return;

  if (!viewers.length) {
    container.innerHTML = '<div style="color: #64748b; font-size: 13px;">Nenhum usuário cadastrado ainda.</div>';
    return;
  }

  const rows = viewers.map((v) => `
    <tr style="border-top: 1px solid rgba(148, 163, 184, 0.15);">
      <td style="padding: 5px 6px; color: #e2e8f0;">${escapeHtml(v.display_name)} <span style="color: #64748b; font-size: 11px;">@${escapeHtml(v.tiktok_username)}</span></td>
      <td style="color: #fbbf24; font-weight: 700; text-align: right;">${v.xp}</td>
      <td style="text-align: center;">${v.level}</td>
      <td style="text-align: center;">${v.races_count}</td>
      <td style="text-align: center;">${v.wins_count}</td>
      <td style="text-align: right;">
        <button class="quick-btn" style="padding: 3px 10px; font-size: 11px; background: #7f1d1d; border-color: #ef4444;" onclick="resetViewer(${v.id})">🧹 Zerar</button>
      </td>
    </tr>`).join("");

  container.innerHTML = `
    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
      <thead>
        <tr style="color: #94a3b8; font-size: 11px; text-transform: uppercase;">
          <th style="text-align: left; padding: 4px 6px;">Usuário</th>
          <th style="text-align: right;">XP</th>
          <th style="text-align: center;">Nv</th>
          <th style="text-align: center;">🏁</th>
          <th style="text-align: center;">🏆</th>
          <th></th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>`;
}

async function resetViewer(viewerId) {
  const v = lastViewers.find((x) => x.id === viewerId);
  const label = v ? `${v.display_name} (@${v.tiktok_username})` : `#${viewerId}`;
  if (!confirm(`Zerar XP, nível e estatísticas de ${label}?`)) return;

  try {
    await postJson("/api/test/reset_viewer", { viewer_id: viewerId });
    appendLog(`🧹 Usuário ${label} foi zerado (XP, nível e estatísticas).`, "#fbbf24", "race");
    loadViewers();
  } catch (err) {
    appendLog(`Erro ao zerar usuário: ${err}`, "#f87171", "all");
  }
}

async function resetAllViewers() {
  if (!confirm("Zerar TODOS os usuários? XP, níveis e estatísticas de todo mundo.\nEssa ação NÃO pode ser desfeita.")) return;

  try {
    const result = await postJson("/api/test/reset_all_viewers");
    appendLog(`🧨 ${result.reset_count} usuário(s) zerado(s)!`, "#ef4444", "race");
    loadViewers();
  } catch (err) {
    appendLog(`Erro ao zerar todos: ${err}`, "#f87171", "all");
  }
}

window.addEventListener("DOMContentLoaded", () => {
  const salvo = lerNomeSalvo();
  const campo = document.getElementById("viewerUser");
  if (campo && salvo) campo.value = salvo;
  atualizarEcho();
  connectWs();
  loadViewers();
});
