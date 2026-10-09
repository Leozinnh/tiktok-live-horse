class GameClient {
  constructor() {
    this.container = document.getElementById("canvas-container");
    this.audio = new GameAudio();
    this.hud = new BroadcastHUD(this.audio);

    this.scene = new TrackScene(this.container);
    this.particles = new ParticleSystem(this.scene.scene);
    this.horseManager = new HorseVisualManager(this.scene.scene, this.particles);
    this.cameraDirector = new CinematicCameraDirector(this.scene.camera, this.scene, this.horseManager);

    this.latestServerState = null;
    this.lastTime = performance.now();
    this.lastState = null;
    this.lastCountdownBeep = -1;
    this._ultimoClima = undefined;

    this.initWebSocket();
    this.startRenderLoop();
  }

  initWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log("[GameClient] WebSocket conectado com sucesso!");
    };

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "HUD_CONFIG_UPDATE" && msg.config) {
          this.hud.applyConfig(msg.config);
          return;
        }
        this.onStateUpdate(msg);
      } catch (err) {
        console.error("[GameClient] Erro no JSON do WebSocket:", err);
      }
    };

    this.ws.onclose = () => {
      console.warn("[GameClient] Conexão WebSocket perdida. Reconectando em 2s...");
      setTimeout(() => this.initWebSocket(), 2000);
    };
  }

  onStateUpdate(state) {
    this.latestServerState = state;
    this.hud.update(state);

    // Transição de Clima: a primeira leitura aplica direto (a página abriu
    // no clima que estiver rolando); daí em diante o clima VIRA com transição.
    const weather = (state.engine && state.engine.weather) || "CLEAR";
    if (this._ultimoClima !== weather) {
      const primeiraLeitura = this._ultimoClima === undefined;
      this.scene.setWeather(weather, primeiraLeitura ? { instantaneo: true } : undefined);
      this._ultimoClima = weather;
    }

    // Gatilhos de Áudio e Efeitos de Transição de Estado
    const curState = state.director_state;
    if (this.lastState !== curState) {
      if (curState === "COUNTDOWN") {
        this.audio.playBeep(440, 0.2);
        this.lastCountdownBeep = Math.ceil(state.remaining_seconds || 5);
      } else if (curState === "RACING") {
        this.audio.playStartHorn();
      } else if (curState === "PODIUM") {
        this.audio.playVictoryFanfare();
        this.audio.playHorseNeigh();
        const winnerId = (state.engine && state.engine.winner_horse_id) || 1;
        const winPos = this.horseManager.getHorsePosition(winnerId);
        this.particles.triggerVictoryFireworks(winPos);
      } else if (curState === "VOTING") {
        this.particles.stopVictoryFireworks();
      }
      this.lastState = curState;
    }

    // Bip a cada segundo do Countdown
    if (curState === "COUNTDOWN") {
      const sec = Math.ceil(state.remaining_seconds || 0);
      if (sec !== this.lastCountdownBeep && sec > 0) {
        this.lastCountdownBeep = sec;
        this.audio.playBeep(sec === 1 ? 880 : 440, 0.15);
      }
    }
  }

  startRenderLoop() {
    const loop = (now) => {
      const dt = Math.min(0.1, (now - this.lastTime) / 1000.0);
      this.lastTime = now;

      if (this.latestServerState) {
        const engineData = this.latestServerState.engine || {};
        const horses = engineData.horses || [];
        const directorState = this.latestServerState.director_state || "READY";

        // 1. Atualizar cavalos e animação de galope / empinar do campeão
        this.horseManager.update(horses, dt, directorState, engineData.winner_horse_id);

        // 2. Atualizar partículas (poeira, faíscas, chuva, confetes, fogos)
        this.particles.update(dt, engineData.weather || "CLEAR");

        // 3. Atualizar cena, arquibancadas e portão de largada
        this.scene.update(now / 1000.0, directorState);

        // 4. Atualizar câmera cinematográfica
        this.cameraDirector.update(dt, directorState, engineData);

        // 5. Atualizar áudio dinâmico durante a corrida
        if (directorState === "RACING" && horses.length > 0) {
          const leaderId = engineData.leader_horse_id || 1;
          const leader = horses.find((h) => h.id === leaderId) || horses[0];
          this.audio.playGallop(leader.speed || 0);

          // Intensidade da torcida cresce na reta final (> 700m)
          const dist = leader.distance || 0;
          const intensity = Math.max(0.0, (dist - 400.0) / 600.0);
          this.audio.setCrowdIntensity(intensity);
        } else {
          this.audio.setCrowdIntensity(0.0);
        }
      } else {
        this.scene.update(now / 1000.0);
      }

      // Renderizar frame Three.js
      this.scene.render();
      requestAnimationFrame(loop);
    };

    requestAnimationFrame(loop);
  }
}

window.addEventListener("DOMContentLoaded", () => {
  window.gameClient = new GameClient();
});
