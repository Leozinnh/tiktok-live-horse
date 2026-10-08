class GameAudio {
  constructor() {
    this.ctx = null;
    this.isMuted = false;
    this.lastGallopTime = 0;
    this.crowdGain = null;
    this.crowdSource = null;
    this.initialized = false;
  }

  init() {
    if (this.initialized) return;
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AudioContext();
      this.initialized = true;
      this.setupCrowdNoise();
    } catch (e) {
      console.warn("Web Audio não suportado ou bloqueado:", e);
    }
  }

  resume() {
    if (this.ctx && this.ctx.state === "suspended") {
      this.ctx.resume();
    }
  }

  toggleMute() {
    this.isMuted = !this.isMuted;
    if (this.crowdGain) {
      this.crowdGain.gain.setValueAtTime(this.isMuted ? 0 : 0.05, this.ctx.currentTime);
    }
    return this.isMuted;
  }

  playBeep(freq = 440, duration = 0.12) {
    if (this.isMuted || !this.ctx) return;
    this.resume();
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = "sine";
    osc.frequency.setValueAtTime(freq, this.ctx.currentTime);

    gain.gain.setValueAtTime(0.2, this.ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);

    osc.connect(gain);
    gain.connect(this.ctx.destination);

    osc.start();
    osc.stop(this.ctx.currentTime + duration);
  }

  playStartHorn() {
    if (this.isMuted || !this.ctx) return;
    this.resume();
    // Trompete esportivo de largada
    const freqs = [523.25, 659.25, 783.99, 1046.5]; // C5, E5, G5, C6
    freqs.forEach((f, idx) => {
      setTimeout(() => {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = "sawtooth";
        osc.frequency.setValueAtTime(f, this.ctx.currentTime);
        gain.gain.setValueAtTime(0.18, this.ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.35);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start();
        osc.stop(this.ctx.currentTime + 0.35);
      }, idx * 90);
    });
  }

  playGallop(speed) {
    if (this.isMuted || !this.ctx || speed < 3.0) return;
    const now = Date.now();
    // Intervalo rítmico proporcional à velocidade
    const interval = Math.max(120, 420 - speed * 10);
    if (now - this.lastGallopTime > interval) {
      this.lastGallopTime = now;
      this.createHoofThud();
      setTimeout(() => this.createHoofThud(0.85), 65); // segundo toque do par de patas
    }
  }

  createHoofThud(volumeMult = 1.0) {
    if (!this.ctx) return;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    const filter = this.ctx.createBiquadFilter();

    osc.type = "triangle";
    osc.frequency.setValueAtTime(90, this.ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(35, this.ctx.currentTime + 0.08);

    filter.type = "lowpass";
    filter.frequency.setValueAtTime(220, this.ctx.currentTime);

    gain.gain.setValueAtTime(0.12 * volumeMult, this.ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.08);

    osc.connect(filter);
    filter.connect(gain);
    gain.connect(this.ctx.destination);

    osc.start();
    osc.stop(this.ctx.currentTime + 0.08);
  }

  playTurbo() {
    if (this.isMuted || !this.ctx) return;
    this.resume();
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = "sawtooth";
    osc.frequency.setValueAtTime(280, this.ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(1200, this.ctx.currentTime + 0.45);

    gain.gain.setValueAtTime(0.25, this.ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.45);

    osc.connect(gain);
    gain.connect(this.ctx.destination);

    osc.start();
    osc.stop(this.ctx.currentTime + 0.45);
  }

  playLegendaryGiftAudio(kind = "LION") {
    if (this.isMuted || !this.ctx) return;
    this.resume();

    // 1. Impacto Sub-Grave Ensurdecedor (Boom de Trovão)
    const subOsc = this.ctx.createOscillator();
    const subGain = this.ctx.createGain();
    subOsc.type = "sine";
    subOsc.frequency.setValueAtTime(140, this.ctx.currentTime);
    subOsc.frequency.exponentialRampToValueAtTime(25, this.ctx.currentTime + 1.2);

    subGain.gain.setValueAtTime(0.5, this.ctx.currentTime);
    subGain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 1.2);

    subOsc.connect(subGain);
    subGain.connect(this.ctx.destination);
    subOsc.start();
    subOsc.stop(this.ctx.currentTime + 1.2);

    // 2. Rugido do Leão / Sintetizador Cósmico
    const roarOsc = this.ctx.createOscillator();
    const roarGain = this.ctx.createGain();
    const roarFilter = this.ctx.createBiquadFilter();

    roarOsc.type = "sawtooth";
    roarOsc.frequency.setValueAtTime(kind === "LION" ? 180 : 320, this.ctx.currentTime);
    roarOsc.frequency.linearRampToValueAtTime(kind === "LION" ? 95 : 880, this.ctx.currentTime + 0.9);

    roarFilter.type = "lowpass";
    roarFilter.frequency.setValueAtTime(800, this.ctx.currentTime);
    roarFilter.frequency.linearRampToValueAtTime(2400, this.ctx.currentTime + 0.4);
    roarFilter.frequency.exponentialRampToValueAtTime(150, this.ctx.currentTime + 1.4);

    roarGain.gain.setValueAtTime(0.35, this.ctx.currentTime);
    roarGain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 1.4);

    roarOsc.connect(roarFilter);
    roarFilter.connect(roarGain);
    roarGain.connect(this.ctx.destination);
    roarOsc.start();
    roarOsc.stop(this.ctx.currentTime + 1.4);

    // 3. Erupção máxima da torcida do estádio por 3.5 segundos
    this.setCrowdIntensity(1.0);
    setTimeout(() => this.setCrowdIntensity(0.1), 3500);
  }

  playVictoryFanfare() {
    if (this.isMuted || !this.ctx) return;
    this.resume();
    const chord = [
      { f: 523.25, delay: 0 },
      { f: 659.25, delay: 150 },
      { f: 783.99, delay: 300 },
      { f: 1046.5, delay: 450, dur: 1.2 }
    ];

    chord.forEach((note) => {
      setTimeout(() => {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = "triangle";
        osc.frequency.setValueAtTime(note.f, this.ctx.currentTime);
        const dur = note.dur || 0.4;
        gain.gain.setValueAtTime(0.22, this.ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + dur);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start();
        osc.stop(this.ctx.currentTime + dur);
      }, note.delay);
    });
  }

  setupCrowdNoise() {
    if (!this.ctx) return;
    // Ruído contínuo rosa filtrado simulando murmúrio e torcida do hipódromo
    const bufferSize = this.ctx.sampleRate * 2;
    const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const data = buffer.getChannelData(0);
    let b0 = 0, b1 = 0, b2 = 0;
    for (let i = 0; i < bufferSize; i++) {
      const white = Math.random() * 2 - 1;
      b0 = 0.99 * b0 + white * 0.05;
      b1 = 0.95 * b1 + white * 0.1;
      b2 = 0.85 * b2 + white * 0.25;
      data[i] = (b0 + b1 + b2) * 0.3;
    }

    const noise = this.ctx.createBufferSource();
    noise.buffer = buffer;
    noise.loop = true;

    const filter = this.ctx.createBiquadFilter();
    filter.type = "bandpass";
    filter.frequency.setValueAtTime(600, this.ctx.currentTime);
    filter.Q.setValueAtTime(1.5, this.ctx.currentTime);

    this.crowdGain = this.ctx.createGain();
    this.crowdGain.gain.setValueAtTime(0.04, this.ctx.currentTime);

    noise.connect(filter);
    filter.connect(this.crowdGain);
    this.crowdGain.connect(this.ctx.destination);

    noise.start();
    this.crowdSource = noise;
  }

  setCrowdIntensity(intensity) {
    if (this.crowdGain && !this.isMuted) {
      // Intensidade de 0.0 (murmúrio leve) a 1.0 (clamor na reta final)
      const target = 0.03 + intensity * 0.12;
      this.crowdGain.gain.setValueAtTime(target, this.ctx.currentTime);
    }
  }
}
