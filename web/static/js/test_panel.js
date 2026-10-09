let ws = null;
let eventLogs = [];
let activeFilter = "all";
let statsCounters = {
  gifts: 0,
  votes: 0,
  races: 0
};
let seenServerNotifications = new Set();

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
    el.innerHTML = `<span style="color: #64748b; font-size: 11px;">[${item.time}]</span> ${item.msg}`;
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
    alert("Histórico do console copiado com sucesso!");
  });
}

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

function updateLiveStats(data) {
  document.getElementById("statRaceNum").innerText = `#${data.race_number || 1}`;
  document.getElementById("statState").innerText = data.director_state || "READY";
  document.getElementById("statTimer").innerText = `${data.remaining_seconds || 0}s`;
  document.getElementById("statWeather").innerText = (data.engine && data.engine.weather) || "CLEAR";

  // Registra mudanças de fase no console
  if (data.director_state && data.director_state !== lastServerState) {
    appendLog(`🏁 FASE ALTERADA: ${data.director_state} (Corrida #${data.race_number})`, "#34d399", "race");
    lastServerState = data.director_state;
  }

  // Registra novos presentes e votos vindos do servidor
  if (data.notifications && Array.isArray(data.notifications)) {
    data.notifications.forEach((n) => {
      const key = `${n.text}_${n.horse_id}`;
      if (!seenServerNotifications.has(key)) {
        seenServerNotifications.add(key);
        if (n.type === "GIFT") {
          const isMythic = n.is_legendary;
          const col = isMythic ? "#fbbf24" : "#ec4899";
          appendLog(`🎁 ${n.text}`, col, "gift");
        } else if (n.type === "CHOICE") {
          appendLog(`🏇 ${n.text}`, "#38bdf8", "vote");
        }
      }
    });
  }
}

async function sendComment(customText = null) {
  const user = document.getElementById("commentUser").value.trim() || "Leonardo";
  const text = customText || document.getElementById("commentText").value.trim();
  
  if (!text) return;
  
  try {
    const res = await fetch("/api/test/inject_comment", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: user, display_name: user, text: text })
    });
    const result = await res.json();
    appendLog(`💬 Voto de @${user}: "${text}" -> ${result.status}`, "#38bdf8", "vote");
  } catch (err) {
    appendLog(`Erro ao enviar comentário: ${err}`, "#f87171", "all");
  }
}

async function simulateJoin() {
  const user = document.getElementById("commentUser").value.trim() || "Leonardo";
  try {
    const res = await fetch("/api/test/inject_join", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: user.toLowerCase(), display_name: user })
    });
    const result = await res.json();
    appendLog(`👤 @${user} entrou na LIVE!`, "#38bdf8", "vote");
  } catch (err) {
    appendLog(`Erro ao simular entrada: ${err}`, "#f87171", "all");
  }
}

async function simulateFollow() {
  const user = document.getElementById("commentUser").value.trim() || "Leonardo";
  try {
    const res = await fetch("/api/test/inject_follow", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: user.toLowerCase(), display_name: user })
    });
    const result = await res.json();
    appendLog(`➕ @${user} começou a seguir a LIVE!`, "#38bdf8", "vote");
  } catch (err) {
    appendLog(`Erro ao simular follow: ${err}`, "#f87171", "all");
  }
}

async function sendGift(customGift = null) {
  const user = document.getElementById("giftUser").value.trim() || "Leonardo";
  const gift = customGift || document.getElementById("giftSelect").value;
  const count = parseInt(document.getElementById("giftCount").value) || 1;
  
  try {
    const res = await fetch("/api/test/inject_gift", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: user, display_name: user, gift_name: gift, count: count })
    });
    const result = await res.json();
    const isRare = ["Lion", "Galaxy", "Dragon"].includes(gift);
    const col = isRare ? "#fbbf24" : "#f472b6";
    appendLog(`🎁 PRESENTE: @${user} enviou ${count}x ${gift}! -> ${result.status}`, col, "gift");
  } catch (err) {
    appendLog(`Erro ao enviar presente: ${err}`, "#f87171", "all");
  }
}

async function simulateBurst(count) {
  try {
    appendLog(`Simulando rajada de ${count} espectadores escolhendo cavalos...`, "#a855f7", "vote");
    const res = await fetch("/api/test/burst", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ count: count })
    });
    const result = await res.json();
    appendLog(`Sucesso: ${result.simulated_viewers} espectadores adicionados!`, "#34d399", "vote");
  } catch (err) {
    appendLog(`Erro na simulação de rajada: ${err}`, "#f87171", "all");
  }
}

async function setWeather(type) {
  try {
    const res = await fetch("/api/test/weather", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ weather: type })
    });
    const result = await res.json();
    appendLog(`Clima alterado para: ${result.weather}`, "#38bdf8", "race");
  } catch (err) {
    appendLog(`Erro ao trocar clima: ${err}`, "#f87171", "all");
  }
}

async function skipToRace() {
  try {
    const res = await fetch("/api/test/skip_to_race", { method: "POST" });
    const result = await res.json();
    appendLog("⏩ Votação pulada! Contagem e largada iniciadas!", "#f59e0b", "race");
  } catch (err) {
    appendLog(`Erro ao pular votação: ${err}`, "#f87171", "all");
  }
}

async function forceFinish() {
  try {
    const res = await fetch("/api/test/force_finish", { method: "POST" });
    const result = await res.json();
    appendLog("🏁 Corrida finalizada manualmente! Avançando para o pódio!", "#34d399", "race");
  } catch (err) {
    appendLog(`Erro ao finalizar corrida: ${err}`, "#f87171", "all");
  }
}

async function nextRace() {
  try {
    const res = await fetch("/api/test/next_race", { method: "POST" });
    const result = await res.json();
    appendLog(`🔄 Ciclo reiniciado! Nova Corrida #${result.race_number}`, "#38bdf8", "race");
  } catch (err) {
    appendLog(`Erro ao reiniciar corrida: ${err}`, "#f87171", "all");
  }
}

async function boostHorse(horseId) {
  try {
    const res = await fetch(`/api/test/boost_horse?horse_id=${horseId}`, { method: "POST" });
    appendLog(`⚡ Turbo manual aplicado no Cavalo #${horseId}!`, "#f59e0b", "gift");
  } catch (err) {
    appendLog(`Erro ao aplicar boost: ${err}`, "#f87171", "all");
  }
}

let currentHudConfig = {
  scale: 1.0,
  top: 195,
  left: 28,
  showProgress: true
};

function changeHudScale(delta) {
  currentHudConfig.scale = Math.max(0.6, Math.min(1.6, Math.round((currentHudConfig.scale + delta) * 10) / 10));
  updateHudSetting();
}

function resetHudScale() {
  currentHudConfig.scale = 1.0;
  currentHudConfig.top = 195;
  updateHudSetting();
}

function changeHudTop(delta) {
  currentHudConfig.top = Math.max(80, Math.min(450, currentHudConfig.top + delta));
  updateHudSetting();
}

function toggleProgressHud() {
  currentHudConfig.showProgress = !currentHudConfig.showProgress;
  updateHudSetting();
}

async function updateHudSetting() {
  const scaleEl = document.getElementById("hudScaleVal");
  if (scaleEl) scaleEl.innerText = `${Math.round(currentHudConfig.scale * 100)}%`;
  const topEl = document.getElementById("hudTopVal");
  if (topEl) topEl.innerText = `${currentHudConfig.top}px`;
  
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: "SET_HUD_CONFIG",
      config: currentHudConfig
    }));
  } else {
    await fetch("/api/test/hud_config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(currentHudConfig)
    });
  }
  appendLog(`📐 HUD ajustado: Escala ${Math.round(currentHudConfig.scale * 100)}% | Posição Top: ${currentHudConfig.top}px`, "#38bdf8", "race");
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}

async function simulateLikes(count) {
  const user = document.getElementById("giftUser").value.trim() || "Torcida";
  try {
    const res = await fetch("/api/test/inject_like", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: user, display_name: user, count: count })
    });
    const result = await res.json();
    appendLog(`💗 @${escapeHtml(user)} mandou ${count} curtidas de uma vez! -> boost leve no cavalo apoiado`, "#f472b6", "gift");
  } catch (err) {
    appendLog(`Erro ao simular curtidas: ${err}`, "#f87171", "all");
  }
}

let lastViewers = [];

async function loadViewers() {
  try {
    const res = await fetch("/api/test/viewers");
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
    const res = await fetch("/api/test/reset_viewer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ viewer_id: viewerId })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    appendLog(`🧹 Usuário ${escapeHtml(label)} foi zerado (XP, nível e estatísticas).`, "#fbbf24", "race");
    loadViewers();
  } catch (err) {
    appendLog(`Erro ao zerar usuário: ${err}`, "#f87171", "all");
  }
}

async function resetAllViewers() {
  if (!confirm("Zerar TODOS os usuários? XP, níveis e estatísticas de todo mundo.\nEssa ação NÃO pode ser desfeita.")) return;

  try {
    const res = await fetch("/api/test/reset_all_viewers", { method: "POST" });
    const result = await res.json();
    appendLog(`🧨 ${result.reset_count} usuário(s) zerado(s)!`, "#ef4444", "race");
    loadViewers();
  } catch (err) {
    appendLog(`Erro ao zerar todos: ${err}`, "#f87171", "all");
  }
}

window.addEventListener("DOMContentLoaded", () => {
  connectWs();
  loadViewers();
});
