// O clima da pista vira chip no badge da corrida. É informação de APOSTA: o
// sorteio acontece antes da votação abrir, então quem escolhe o cavalo já
// sabe em que tempo a corrida vai ser (e cada cavalo tem seu clima favorito).
const WEATHER_INFO = {
  CLEAR: { icon: "☀️", label: "SOL" },
  SUNSET: { icon: "🌅", label: "PÔR DO SOL" },
  NIGHT_LIGHTS: { icon: "🌃", label: "NOTURNA" },
  RAIN: { icon: "🌧️", label: "CHUVA" },
  STORM: { icon: "⚡", label: "TEMPESTADE" },
  WIND: { icon: "💨", label: "VENTO" },
};

// A cor da pill de status por fase (as classes moram no styles.css).
const STATE_PILL_CLASS = {
  VOTING: "betting",
  COUNTDOWN: "countdown",
  RACING: "live",
  PODIUM: "podium",
  XP_REWARDS: "rewards",
  LEADERBOARD: "leaderboard",
};

// Nome de quem manda presente vem do chat: escapa antes de entrar no HTML.
function escaparHtml(valor) {
  return String(valor ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

class BroadcastHUD {
  constructor(audio) {
    this.audio = audio;
    this.lastState = null;
    this.lastRaceNumber = null;
    this.activeNotifications = new Set();
    this.seenNotificationIds = new Set();

    // Elementos DOM
    this.raceBadgeEl = document.getElementById("raceBadge");
    this.raceNumberEl = document.getElementById("hudRaceNumber");
    this.weatherEl = document.getElementById("hudWeather");
    this.statePillEl = document.getElementById("hudStatePill");
    this.stateTextEl = document.getElementById("hudStateText");
    this.timerEl = document.getElementById("hudTimer");
    this.timerUnitEl = document.getElementById("hudTimerUnit");
    this.timerBoxEl = document.getElementById("hudTimerBox");
    this.notificationContainer = document.getElementById("notification-container");
    this.centerModal = document.getElementById("center-modal");
    this.leaderboardEl = document.getElementById("hudLeaderboard");

    // Controle da cartela de votação: qual fase está montada no DOM e qual
    // número da contagem já foi exibido (evita remontar/piscar a cada update).
    this.votingPanelState = null;
    this.countdownShown = null;
  }

  applyConfig(config) {
    if (!config) return;
    if (this.leaderboardEl) {
      if (config.scale !== undefined) {
        this.leaderboardEl.style.transform = `scale(${config.scale})`;
        this.leaderboardEl.style.transformOrigin = "bottom center";
      }
      this.leaderboardEl.style.top = "auto";
      if (config.bottom !== undefined) {
        this.leaderboardEl.style.bottom = `${config.bottom}px`;
      }
    }
    const progressContainer = document.getElementById("trackProgressContainer");
    if (progressContainer && config.showProgress !== undefined) {
      this.hideProgressSetting = !config.showProgress;
    }
  }

  update(stateData) {
    if (!stateData) return;

    if (stateData.hud_config) {
      this.applyConfig(stateData.hud_config);
    }

    // 1. Atualizar Header
    const raceNumber = stateData.race_number || 1;
    if (this.raceNumberEl) {
      this.raceNumberEl.innerText = `#${raceNumber}`;
    }
    // Corrida nova: o número salta na tela (o primeiro payload também pulsa,
    // já que a página acabou de carregar e o olho precisa achar o lugar).
    if (this.raceBadgeEl && raceNumber !== this.lastRaceNumber) {
      this.raceBadgeEl.classList.remove("flash");
      void this.raceBadgeEl.offsetWidth; // força o reinício da animação
      this.raceBadgeEl.classList.add("flash");
      this.lastRaceNumber = raceNumber;
    }

    this.renderWeather(stateData);

    const state = stateData.director_state || "READY";
    if (this.stateTextEl) {
      this.stateTextEl.innerText = this.translateState(state);
    }
    if (this.statePillEl) {
      this.statePillEl.className = `status-pill ${STATE_PILL_CLASS[state] || ""}`.trim();
    }

    this.renderTimer(state, stateData);

    // 2. Notificações Flutuantes (Fila com IDs únicos: nunca bloqueia votos legítimos)
    if (stateData.notifications && Array.isArray(stateData.notifications)) {
      stateData.notifications.forEach((n) => {
        if (n.id !== undefined) {
          if (!this.seenNotificationIds.has(n.id)) {
            this.seenNotificationIds.add(n.id);
            if (this.seenNotificationIds.size > 200) {
              const arr = Array.from(this.seenNotificationIds);
              this.seenNotificationIds = new Set(arr.slice(-100));
            }
            this.showToast(n);
          }
        } else {
          const key = `${n.type}_${n.text}`;
          if (!this.activeNotifications.has(key)) {
            this.activeNotifications.add(key);
            setTimeout(() => this.activeNotifications.delete(key), 4000);
            this.showToast(n);
          }
        }
      });
    }

    // 3. Modais Centrais conforme a Fase
    this.renderCenterModal(state, stateData);

    // 4. Leaderboard Inferior (Durante a Corrida)
    this.renderBottomLeaderboard(state, stateData);

    this.lastState = state;
  }

  translateState(state) {
    switch (state) {
      case "VOTING": return "ESCOLHA SEU CAVALO";
      case "COUNTDOWN": return "LARGADA EM...";
      case "RACING": return "AO VIVO";
      case "PODIUM": return "VENCEDORES";
      case "XP_REWARDS": return "DISTRIBUIÇÃO DE XP";
      case "LEADERBOARD": return "TOP APOIADORES";
      default: return state;
    }
  }

  renderWeather(stateData) {
    if (!this.weatherEl) return;
    const weather = (stateData.engine && stateData.engine.weather) || "CLEAR";
    const info = WEATHER_INFO[weather];
    if (!info) {
      this.weatherEl.style.display = "none";
      return;
    }
    this.weatherEl.innerText = `${info.icon} ${info.label}`;
    this.weatherEl.className = `weather-chip weather-${weather.toLowerCase()}`;
    this.weatherEl.style.display = "flex";
  }

  renderTimer(state, stateData) {
    if (!this.timerBoxEl) return;

    // O relógio conta o que importa em cada fase: segundos até a largada na
    // votação/contagem e a DISTÂNCIA DO LÍDER na corrida — antes a prova
    // inteira exibia um "0s" parado, o pedaço mais morto do HUD.
    let valor = null;
    let unidade = "s";
    let urgente = false;

    if (state === "VOTING" || state === "COUNTDOWN") {
      const segundos = Math.ceil(stateData.remaining_seconds || 0);
      valor = segundos;
      urgente = segundos > 0 && segundos <= 5;
    } else if (state === "RACING") {
      const leaderboard = (stateData.engine && stateData.engine.leaderboard) || [];
      const trackLength = (stateData.engine && stateData.engine.track_length) || 3000;
      const metros = leaderboard.length ? Math.round(leaderboard[0].distance) : 0;
      valor = metros;
      unidade = "m";
      urgente = metros >= trackLength * 0.9; // reta final: o líder está chegando
    }

    if (valor === null) {
      this.timerBoxEl.style.display = "none";
      return;
    }

    this.timerBoxEl.style.display = "flex";
    this.timerBoxEl.classList.toggle("urgent", urgente);
    if (this.timerEl) this.timerEl.innerText = valor;
    if (this.timerUnitEl) this.timerUnitEl.innerText = unidade;
  }

  showToast(notification) {
    // Presente não é aviso comum: ganha o cartão caprichado (mostrarCartaoDePresente).
    if (notification.type === "GIFT") {
      if (notification.is_legendary) {
        this.showMythicAnnouncement(notification);
      } else {
        this.audio.playTurbo();
      }
      this.mostrarCartaoDePresente(notification);
      return;
    }

    let cleanText = notification.text || "";
    // Se o texto já começar com o mesmo emoji/badge, remove para evitar duplicação visual
    if (notification.badge && cleanText.startsWith(notification.badge)) {
      cleanText = cleanText.substring(notification.badge.length).trim();
    }

    const toast = document.createElement("div");
    toast.className = "toast";
    toast.innerHTML = `<span>${notification.badge || "🏇"}</span> <span>${escaparHtml(cleanText)}</span>`;
    this.notificationContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.transition = "opacity 0.4s ease, transform 0.4s ease";
      toast.style.opacity = "0";
      toast.style.transform = "translateX(-30px)";
      setTimeout(() => toast.remove(), 400);
    }, 4500);
  }

  // O "aviso" de presente da live: emoji enorme, quem mandou, quantos e o boost
  // que caiu no cavalo. A cor do brilho muda com o tier (rosa = turbo, boné/donut
  // = super boost, leão/dragão/galáxia = lendário dourado).
  mostrarCartaoDePresente(n) {
    const boost = (n.boost_label || "").toUpperCase();
    const classeTier = n.is_legendary
      ? "gift-lendario"
      : (boost.includes("SUPER") ? "gift-super" : "gift-turbo");

    const card = document.createElement("div");
    card.className = `toast gift-card ${classeTier}`;
    card.innerHTML = `
      <div class="gift-brilho"></div>
      <span class="gift-emoji">${n.gift_emoji || n.badge || "🎁"}</span>
      <div class="gift-info">
        <span class="gift-quem"><b>${escaparHtml(n.sender_name || "Apoiador")}</b> mandou ${escaparHtml(n.gift_name || "um presente")}${n.gift_count > 1 ? ` <i>x${n.gift_count}</i>` : ""}</span>
        <span class="gift-boost">⚡ ${escaparHtml(n.boost_label || "TURBO")} no ${escaparHtml(n.horse_name || "cavalo")}</span>
      </div>`;
    this.notificationContainer.appendChild(card);

    // O cartão de presente fica mais tempo na tela que um aviso comum.
    const duracao = n.is_legendary ? 7000 : 6000;
    setTimeout(() => {
      card.style.transition = "opacity 0.5s ease, transform 0.5s ease";
      card.style.opacity = "0";
      card.style.transform = "translateX(-40px) scale(0.94)";
      setTimeout(() => card.remove(), 500);
    }, duracao);
  }

  showMythicAnnouncement(n) {
    const isLion = n.legendary_kind === "LION";
    const kindClass = isLion ? "lion" : "galaxy";
    const icon = isLion ? "🦁" : "🌌";

    // 1. Som Épico Lendário
    this.audio.playLegendaryGiftAudio(n.legendary_kind);

    // 2. Dispara Efeitos no 3D (Pilar de Luz, Shockwave, Brasas e Screen Shake)
    if (window.gameClient && window.gameClient.horseManager) {
      const pos = window.gameClient.horseManager.getHorsePosition(n.horse_id);
      window.gameClient.particles.triggerLegendaryImpact(pos, n.legendary_kind);
    }

    // 3. Efeito de borda incandescente no Viewport
    const viewport = document.getElementById("viewport");
    if (viewport) {
      viewport.classList.add("viewport-mythic-glow");
      setTimeout(() => viewport.classList.remove("viewport-mythic-glow"), 5000);
    }

    // 4. Banner Colossal Central Superior
    const banner = document.createElement("div");
    banner.className = `mythic-gift-banner ${kindClass}`;
    banner.innerHTML = `
      <div class="mythic-header">
        <span>👑</span>
        <span>ACONTECIMENTO LENDÁRIO NA LIVE!</span>
        <span>👑</span>
      </div>
      <div class="mythic-sender">${icon} @${n.sender_name || "Apoiador"} ${icon}</div>
      <div class="mythic-gift-info">ENVIOU ${n.gift_name.toUpperCase()}!</div>
      <div class="mythic-boost-tag">⚡ ${n.boost_label || "OVERDRIVE MÍSTICO"} ATIVADO NO ${n.horse_name}! ⚡</div>
    `;

    const hudOverlay = document.getElementById("hud-overlay");
    if (hudOverlay) {
      hudOverlay.appendChild(banner);
      setTimeout(() => {
        banner.style.transition = "opacity 0.6s ease, transform 0.6s ease";
        banner.style.opacity = "0";
        banner.style.transform = "translateY(-40px) scale(0.9)";
        setTimeout(() => banner.remove(), 600);
      }, 5200);
    }
  }

  renderCenterModal(state, stateData) {
    // A cartela de votação fica na tela durante a votação E a contagem: antes
    // o número do countdown substituía a cartela inteira e ela sumia "do nada"
    // bem na hora em que o público quer conferir os números finais de cada
    // cavalo. Agora o número flutua POR CIMA (ver renderCountdownOverlay).
    if (state === "VOTING" || state === "COUNTDOWN") {
      this.renderVotingPanel(state, stateData);
      if (state === "COUNTDOWN") {
        this.renderCountdownOverlay(stateData);
      } else {
        this.countdownShown = null;
      }
      return;
    }

    // Saiu da votação: a próxima entrada remonta a cartela do zero.
    this.votingPanelState = null;
    this.countdownShown = null;

    if (state === "PODIUM") {
      const podium = stateData.podium || [];
      const first = podium[0] || {};
      const second = podium[1] || {};
      const third = podium[2] || {};

      this.centerModal.innerHTML = `
        <div class="podium-card">
          <div class="podium-title">🏆 PÓDIO DA CORRIDA 🏆</div>
          <div class="podium-stands">
            ${second.name ? `
              <div class="podium-place second">
                <div class="trophy-icon">🥈</div>
                <div class="horse-name" style="color: ${second.color_hex};">${second.name}</div>
                <div class="time">2º Lugar</div>
              </div>
            ` : ""}
            ${first.name ? `
              <div class="podium-place first">
                <div class="trophy-icon">🥇</div>
                <div class="horse-name" style="color: ${first.color_hex};">${first.name}</div>
                <div class="time">CAMPEÃO</div>
              </div>
            ` : ""}
            ${third.name ? `
              <div class="podium-place third">
                <div class="trophy-icon">🥉</div>
                <div class="horse-name" style="color: ${third.color_hex};">${third.name}</div>
                <div class="time">3º Lugar</div>
              </div>
            ` : ""}
          </div>
          <p style="color: var(--text-sub); font-size: 16px;">Parabéns a todos os apoiadores virtuais!</p>
        </div>
      `;
    } else if (state === "XP_REWARDS") {
      const rewards = stateData.rewards || [];
      let listHtml = "";

      if (rewards.length === 0) {
        listHtml = "<p style='color: var(--text-sub); padding: 12px;'>Nenhum espectador votou nesta rodada.</p>";
      } else {
        rewards.forEach((r) => {
          listHtml += `
            <div class="reward-item">
              <div class="user">
                <span>👤</span>
                <span>${r.display_name} (Lv. ${r.level})</span>
                ${r.level_up ? '<span style="color: #fbbf24; font-size: 13px;">⭐ LEVEL UP!</span>' : ""}
              </div>
              <div class="xp-gain">+${r.earned_xp} XP</div>
            </div>
          `;
        });
      }

      this.centerModal.innerHTML = `
        <div class="podium-card" style="border-color: var(--accent-green);">
          <div class="podium-title" style="color: var(--accent-green);">⭐ RECOMPENSAS DE XP ⭐</div>
          <p style="color: var(--text-sub); font-size: 15px;">Pontos 100% virtuais para progressão e níveis</p>
          <div class="rewards-list">
            ${listHtml}
          </div>
        </div>
      `;
    } else if (state === "LEADERBOARD") {
      const top = stateData.leaderboard || [];
      let topHtml = "";

      top.slice(0, 6).forEach((p, idx) => {
        topHtml += `
          <div class="reward-item">
            <div class="user">
              <span style="font-weight: 900; color: #fbbf24; width: 24px;">#${idx + 1}</span>
              <span>${p.display_name}</span>
              <span style="color: var(--text-sub); font-size: 13px;">(Lv. ${p.level})</span>
            </div>
            <div class="xp-gain" style="color: #38bdf8;">${p.xp} XP</div>
          </div>
        `;
      });

      this.centerModal.innerHTML = `
        <div class="podium-card" style="border-color: #38bdf8;">
          <div class="podium-title" style="color: #38bdf8;">👑 TOP JOGADORES DA LIVE</div>
          <div class="rewards-list">
            ${topHtml}
          </div>
        </div>
      `;
    } else {
      // RACING: limpa modal central para visão completa 3D
      if (this.centerModal.innerHTML !== "") this.centerModal.innerHTML = "";
    }
  }

  getContrastColor(hexColor) {
    if (!hexColor || typeof hexColor !== "string" || !hexColor.startsWith("#")) return "#ffffff";
    const hex = hexColor.replace("#", "");
    const r = parseInt(hex.slice(0, 2), 16) || 0;
    const g = parseInt(hex.slice(2, 4), 16) || 0;
    const b = parseInt(hex.slice(4, 6), 16) || 0;
    const yiq = (r * 299 + g * 587 + b * 114) / 1000;
    return yiq >= 165 ? "#0f172a" : "#ffffff";
  }

  renderVotingPanel(state, stateData) {
    const summary = stateData.voting_summary || {};
    const horses = Object.values(summary);

    if (this.votingPanelState !== state) {
      // Montagem única por fase. Remontar a cada update reiniciava a animação
      // de entrada e a cartela piscava a cada voto novo no chat.
      let cardsHtml = "";
      horses.forEach((h) => {
        const textColor = this.getContrastColor(h.color_hex);
        cardsHtml += `
          <div class="horse-vote-card" style="border-color: ${h.color_hex};">
            <div class="num-badge" style="background: ${h.color_hex}; color: ${textColor};">#${h.horse_id}</div>
            <div class="info">
              <div class="name">${h.horse_name}</div>
              <div class="supporters" data-horse="${h.horse_id}">👥 ${h.supporters_count} apoiadores</div>
            </div>
          </div>
        `;
      });

      const header = state === "COUNTDOWN"
        ? `<h2>VOTAÇÃO ENCERRADA!</h2>
           <p>Últimos números dos apoiadores — a prova começa em instantes!</p>`
        : `<h2>ESCOLHA SEU CAVALO!</h2>
           <p>Comente o número (1 a 8) ou o nome do cavalo no chat da LIVE!</p>`;

      this.centerModal.innerHTML = `
        <div class="voting-overlay">
          <div class="voting-header">
            ${header}
          </div>
          <div class="horses-vote-grid">
            ${cardsHtml}
          </div>
        </div>
      `;
      this.votingPanelState = state;
      return;
    }

    // Já montada: só os contadores mudam — troca o texto sem recriar o DOM.
    horses.forEach((h) => {
      const el = this.centerModal.querySelector(`.supporters[data-horse="${h.horse_id}"]`);
      const texto = `👥 ${h.supporters_count} apoiadores`;
      if (el && el.textContent !== texto) el.textContent = texto;
    });
  }

  renderCountdownOverlay(stateData) {
    const count = Math.ceil(stateData.remaining_seconds || 5);
    const texto = count > 0 ? String(count) : "LARGADA!";

    let wrap = this.centerModal.querySelector(".countdown-wrap");
    if (!wrap) {
      wrap = document.createElement("div");
      wrap.className = "countdown-wrap";
      wrap.innerHTML = `<div class="countdown-big"></div>`;
      this.centerModal.appendChild(wrap);
      this.countdownShown = null;
    }

    if (this.countdownShown !== texto) {
      const big = wrap.querySelector(".countdown-big");
      big.textContent = texto;
      // Trocar o texto não reinicia o CSS: força o replay do zoom a cada segundo.
      big.style.animation = "none";
      void big.offsetWidth;
      big.style.animation = "";
      this.countdownShown = texto;
    }
  }

  renderBottomLeaderboard(state, stateData) {
    if (!this.leaderboardEl) return;

    const progressContainer = document.getElementById("trackProgressContainer");
    const progressBar = document.getElementById("trackProgressBar");

    // O HUD de classificação só deve aparecer estritamente quando a corrida estiver rolando (RACING)!
    if (state !== "RACING") {
      this.leaderboardEl.style.display = "none";
      if (progressContainer) progressContainer.style.display = "none";
      return;
    }

    this.leaderboardEl.style.display = "block";
    if (progressContainer) progressContainer.style.display = "flex";

    const leaderboard = (stateData.engine && stateData.engine.leaderboard) || [];
    const horses = (stateData.engine && stateData.engine.horses) || [];
    const trackLength = (stateData.engine && stateData.engine.track_length) || 3000;

    // 1. Atualiza Torre Lateral Esquerda (Compacta estilo F1 - não tampa os cavalos)
    let rowsHtml = "";
    leaderboard.forEach((h) => {
      const isP1 = (h.position === 1);
      const textColor = this.getContrastColor(h.color_hex);
      rowsHtml += `
        <div class="tower-row ${isP1 ? 'p1' : ''}" style="border-left-color: ${h.color_hex};">
          <div class="left">
            <span class="tower-pos">${h.position}</span>
            <span class="tower-badge" style="background: ${h.color_hex}; color: ${textColor};">#${h.horse_id}</span>
            <span class="tower-name">${h.name}</span>
          </div>
          <div class="right">
            ${h.boost_active ? '<span class="tower-turbo-icon">⚡</span>' : ''}
            <span class="tower-dist">${Math.round(h.distance)}m</span>
          </div>
        </div>
      `;
    });

    this.leaderboardEl.innerHTML = `
      <div class="tower-header">
        <span>🏁 POSIÇÕES</span>
        <span>${trackLength}m</span>
      </div>
      <div class="tower-list">
        ${rowsHtml}
      </div>
    `;

    // 2. Atualiza Régua de Progresso Horizontal no Topo
    if (progressBar) {
      let dotsHtml = "";
      horses.forEach((h) => {
        const pct = Math.min(98, Math.max(1, (h.distance / trackLength) * 100));
        const dotTextColor = this.getContrastColor(h.color_hex);
        dotsHtml += `
          <div class="horse-progress-dot" style="left: ${pct}%; background: ${h.color_hex}; color: ${dotTextColor};" title="#${h.number} ${h.name}">
            ${h.number}
          </div>
        `;
      });
      progressBar.innerHTML = dotsHtml;
    }
  }
}

window.BroadcastHUD = BroadcastHUD;
