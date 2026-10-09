class ParticleSystem {
  constructor(scene) {
    this.scene = scene;
    
    // 1. Partículas de Poeira de Casco
    this.dustParticles = [];
    this.dustPoolSize = 120;
    this.initDust();
    
    // 2. Partículas de Turbo / Faíscas
    this.sparks = [];
    this.sparkPoolSize = 160;
    this.initSparks();

    // 3. Efeitos Míticos Lendários (Leão, Galáxia)
    this.shockwaves = [];
    this.lightBeams = [];
    this.mythicEmbers = [];
    this.initMythicEffects();
    
    // 4. Sistema de Chuva
    this.rainMesh = null;
    this.rainCount = 1200;
    this.initRain();
    
    // 5. Confetes de Pódio
    this.confettiParticles = [];
    this.initConfetti();

    // Screen Shake Trigger
    this.screenShakeIntensity = 0.0;
  }

  initDust() {
    const geo = new THREE.DodecahedronGeometry(0.35, 0);
    const mat = new THREE.MeshLambertMaterial({
      color: 0xc49a6c,
      transparent: true,
      opacity: 0.0,
      depthWrite: false,
    });

    for (let i = 0; i < this.dustPoolSize; i++) {
      const p = new THREE.Mesh(geo, mat.clone());
      p.visible = false;
      this.scene.add(p);
      this.dustParticles.push({
        mesh: p,
        life: 0,
        maxLife: 0.6,
        vx: 0, vy: 0, vz: 0,
        scale: 1.0,
      });
    }
  }

  emitDust(pos, horseSpeed) {
    if (horseSpeed < 5.0) return;
    const p = this.dustParticles.find((item) => !item.mesh.visible);
    if (!p) return;

    p.mesh.position.set(
      pos.x + (Math.random() - 0.5) * 0.6,
      0.2,
      pos.z + (Math.random() - 0.5) * 0.6
    );
    p.mesh.visible = true;
    p.life = 0.5;
    p.maxLife = 0.5;
    p.vx = (Math.random() - 0.5) * 0.8;
    p.vy = 0.8 + Math.random() * 0.6;
    p.vz = (Math.random() - 0.5) * 0.8;
    p.scale = 0.4 + Math.random() * 0.4;
    p.mesh.scale.set(p.scale, p.scale, p.scale);
    p.mesh.material.opacity = 0.65;
  }

  initSparks() {
    const geo = new THREE.BoxGeometry(0.22, 0.22, 0.22);
    const colors = [0xf59e0b, 0xef4444, 0x38bdf8, 0xa855f7];

    for (let i = 0; i < this.sparkPoolSize; i++) {
      const col = colors[i % colors.length];
      const mat = new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.0 });
      const m = new THREE.Mesh(geo, mat);
      m.visible = false;
      this.scene.add(m);
      this.sparks.push({
        mesh: m,
        life: 0,
        vx: 0, vy: 0, vz: 0
      });
    }
  }

  emitTurboSparks(pos) {
    for (let k = 0; k < 3; k++) {
      const s = this.sparks.find((item) => !item.mesh.visible);
      if (!s) break;
      s.mesh.position.set(
        pos.x + (Math.random() - 0.5) * 1.0,
        pos.y + 1.2 + (Math.random() - 0.5) * 0.8,
        pos.z + (Math.random() - 0.5) * 1.0
      );
      s.mesh.visible = true;
      s.life = 0.45;
      s.vx = (Math.random() - 0.5) * 4.0;
      s.vy = 2.0 + Math.random() * 3.0;
      s.vz = (Math.random() - 0.5) * 4.0;
      s.mesh.material.opacity = 0.95;
    }
  }

  initMythicEffects() {
    // 1. Pilares de Luz Celestial
    for (let i = 0; i < 4; i++) {
      const beamGeo = new THREE.CylinderGeometry(4.0, 5.0, 90, 16, 1, true);
      const beamMat = new THREE.MeshBasicMaterial({
        color: 0xfbbf24,
        transparent: true,
        opacity: 0.0,
        side: THREE.DoubleSide
      });
      const beam = new THREE.Mesh(beamGeo, beamMat);
      beam.visible = false;
      this.scene.add(beam);
      this.lightBeams.push({ mesh: beam, life: 0, maxLife: 1.5, scale: 1.0 });
    }

    // 2. Ondas de Choque no Chão
    for (let i = 0; i < 6; i++) {
      const ringGeo = new THREE.RingGeometry(0.5, 2.2, 32);
      const ringMat = new THREE.MeshBasicMaterial({
        color: 0xf59e0b,
        transparent: true,
        opacity: 0.0,
        side: THREE.DoubleSide
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.rotation.x = -Math.PI / 2;
      ring.visible = false;
      this.scene.add(ring);
      this.shockwaves.push({ mesh: ring, life: 0, maxLife: 1.2, radius: 1.0 });
    }

    // 3. Brasas Cósmicas / Fogo de Dragão
    const emberGeo = new THREE.SphereGeometry(0.3, 8, 8);
    for (let i = 0; i < 80; i++) {
      const mat = new THREE.MeshBasicMaterial({ color: 0xfbbf24, transparent: true, opacity: 0 });
      const m = new THREE.Mesh(emberGeo, mat);
      m.visible = false;
      this.scene.add(m);
      this.mythicEmbers.push({ mesh: m, life: 0, vx: 0, vy: 0, vz: 0 });
    }
  }

  triggerLegendaryImpact(pos, kind = "LION") {
    const isLion = kind === "LION";
    const primaryHex = isLion ? 0xf59e0b : 0xa855f7; // Dourado ou Roxo Galáctico

    // 1. Ativa Pilar de Luz Celestial
    const beam = this.lightBeams.find((b) => !b.mesh.visible);
    if (beam) {
      beam.mesh.position.set(pos.x, 45, pos.z);
      beam.mesh.material.color.setHex(primaryHex);
      beam.mesh.material.opacity = 0.85;
      beam.mesh.visible = true;
      beam.life = 1.4;
      beam.maxLife = 1.4;
      beam.scale = 1.0;
    }

    // 2. Dispara Onda de Choque no Solo
    const shock = this.shockwaves.find((s) => !s.mesh.visible);
    if (shock) {
      shock.mesh.position.set(pos.x, 0.25, pos.z);
      shock.mesh.material.color.setHex(isLion ? 0xfef08a : 0x38bdf8);
      shock.mesh.material.opacity = 0.95;
      shock.mesh.visible = true;
      shock.life = 1.1;
      shock.maxLife = 1.1;
      shock.radius = 1.0;
      shock.mesh.scale.set(1, 1, 1);
    }

    // 3. Erupção de Brasas Cósmicas / Chamas Místicas
    for (let i = 0; i < 24; i++) {
      const ember = this.mythicEmbers.find((e) => !e.mesh.visible);
      if (!ember) break;
      ember.mesh.position.set(
        pos.x + (Math.random() - 0.5) * 2.0,
        pos.y + 1.0,
        pos.z + (Math.random() - 0.5) * 2.0
      );
      ember.mesh.material.color.setHex(isLion ? (Math.random() > 0.5 ? 0xf59e0b : 0xef4444) : (Math.random() > 0.5 ? 0xa855f7 : 0x06b6d4));
      ember.mesh.visible = true;
      ember.life = 1.2;
      ember.vx = (Math.random() - 0.5) * 14.0;
      ember.vy = 6.0 + Math.random() * 12.0;
      ember.vz = (Math.random() - 0.5) * 14.0;
      ember.mesh.material.opacity = 1.0;
    }

    // 4. Tremor de tela dramático
    this.screenShakeIntensity = 1.0;
  }

  emitLegendaryAuraTrail(pos, kind = "LION") {
    // Efeito contínuo enquanto o cavalo estiver sob boost lendário
    const isLion = kind === "LION";
    for (let k = 0; k < 4; k++) {
      const ember = this.mythicEmbers.find((e) => !e.mesh.visible);
      if (!ember) break;
      ember.mesh.position.set(
        pos.x + (Math.random() - 0.5) * 1.5,
        pos.y + 0.4 + Math.random() * 1.8,
        pos.z + (Math.random() - 0.5) * 1.5
      );
      ember.mesh.material.color.setHex(isLion ? 0xf59e0b : 0x38bdf8);
      ember.mesh.visible = true;
      ember.life = 0.5;
      ember.vx = (Math.random() - 0.5) * 4.0;
      ember.vy = 2.0 + Math.random() * 4.0;
      ember.vz = (Math.random() - 0.5) * 4.0;
      ember.mesh.material.opacity = 0.9;
    }
  }

  initRain() {
    const rainGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(this.rainCount * 3);

    for (let i = 0; i < this.rainCount * 3; i += 3) {
      positions[i] = (Math.random() - 0.5) * 400;
      positions[i + 1] = Math.random() * 70;
      positions[i + 2] = (Math.random() - 0.5) * 400;
    }

    rainGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    const rainMat = new THREE.PointsMaterial({
      color: 0x93c5fd,
      size: 0.7,
      transparent: true,
      opacity: 0.0,
    });

    this.rainMesh = new THREE.Points(rainGeo, rainMat);
    this.scene.add(this.rainMesh);
  }

  initConfetti() {
    const colors = [0xf59e0b, 0xef4444, 0x10b981, 0x3b82f6, 0xec4899, 0xffffff];
    const geo = new THREE.PlaneGeometry(0.35, 0.35);

    for (let i = 0; i < 180; i++) {
      const col = colors[i % colors.length];
      const mat = new THREE.MeshBasicMaterial({ color: col, side: THREE.DoubleSide, transparent: true, opacity: 0 });
      const m = new THREE.Mesh(geo, mat);
      m.visible = false;
      this.scene.add(m);
      this.confettiParticles.push({
        mesh: m,
        vx: 0, vy: 0, vz: 0,
        rotSpeed: (Math.random() - 0.5) * 8.0,
        life: 0
      });
    }
  }

  triggerConfetti(originPos) {
    this.confettiParticles.forEach((c) => {
      c.mesh.position.set(
        originPos.x + (Math.random() - 0.5) * 15,
        originPos.y + 12 + Math.random() * 8,
        originPos.z + (Math.random() - 0.5) * 15
      );
      c.mesh.visible = true;
      c.mesh.material.opacity = 1.0;
      c.life = 4.0;
      c.vx = (Math.random() - 0.5) * 6;
      c.vy = -1.5 - Math.random() * 2.0;
      c.vz = (Math.random() - 0.5) * 6;
    });
  }

  update(dt, weatherType) {
    // Decaimento suave do screen shake
    if (this.screenShakeIntensity > 0) {
      this.screenShakeIntensity = Math.max(0, this.screenShakeIntensity - dt * 2.5);
    }

    // 1. Atualizar Pilares de Luz Míticos
    for (let i = 0; i < this.lightBeams.length; i++) {
      const b = this.lightBeams[i];
      if (b.mesh.visible) {
        b.life -= dt;
        if (b.life <= 0) {
          b.mesh.visible = false;
        } else {
          b.mesh.rotation.y += dt * 3.0;
          const prog = 1.0 - (b.life / b.maxLife);
          b.mesh.scale.set(1.0 + prog * 1.5, 1.0, 1.0 + prog * 1.5);
          b.mesh.material.opacity = Math.max(0, 0.85 * (1.0 - prog));
        }
      }
    }

    // 2. Atualizar Ondas de Choque
    for (let i = 0; i < this.shockwaves.length; i++) {
      const s = this.shockwaves[i];
      if (s.mesh.visible) {
        s.life -= dt;
        if (s.life <= 0) {
          s.mesh.visible = false;
        } else {
          const prog = 1.0 - (s.life / s.maxLife);
          const currentScale = 1.0 + prog * 16.0;
          s.mesh.scale.set(currentScale, currentScale, 1.0);
          s.mesh.material.opacity = Math.max(0, 0.95 * (1.0 - prog));
        }
      }
    }

    // 3. Atualizar Brasas Míticas
    for (let i = 0; i < this.mythicEmbers.length; i++) {
      const e = this.mythicEmbers[i];
      if (e.mesh.visible) {
        e.life -= dt;
        if (e.life <= 0) {
          e.mesh.visible = false;
        } else {
          e.mesh.position.x += e.vx * dt;
          e.mesh.position.y += e.vy * dt;
          e.mesh.position.z += e.vz * dt;
          e.mesh.material.opacity = Math.max(0, e.life / 1.2);
        }
      }
    }

    // 4. Atualizar Poeira
    for (let i = 0; i < this.dustParticles.length; i++) {
      const p = this.dustParticles[i];
      if (p.mesh.visible) {
        p.life -= dt;
        if (p.life <= 0) {
          p.mesh.visible = false;
        } else {
          p.mesh.position.x += p.vx * dt;
          p.mesh.position.y += p.vy * dt;
          p.mesh.position.z += p.vz * dt;
          const progress = 1.0 - (p.life / p.maxLife);
          p.mesh.scale.setScalar(p.scale * (1.0 + progress * 2.0));
          p.mesh.material.opacity = Math.max(0, 0.65 * (1.0 - progress));
        }
      }
    }

    // 5. Atualizar Faíscas
    for (let i = 0; i < this.sparks.length; i++) {
      const s = this.sparks[i];
      if (s.mesh.visible) {
        s.life -= dt;
        if (s.life <= 0) {
          s.mesh.visible = false;
        } else {
          s.mesh.position.x += s.vx * dt;
          s.mesh.position.y += s.vy * dt;
          s.mesh.position.z += s.vz * dt;
          s.mesh.material.opacity = Math.max(0, s.life / 0.45);
        }
      }
    }

    // 6. Atualizar Chuva
    if (this.rainMesh) {
      if (weatherType === "RAIN" || weatherType === "STORM") {
        this.rainMesh.material.opacity = weatherType === "STORM" ? 0.75 : 0.45;
        const pos = this.rainMesh.geometry.attributes.position.array;
        for (let i = 1; i < pos.length; i += 3) {
          pos[i] -= 85 * dt;
          if (pos[i] < 0) pos[i] = 70;
        }
        this.rainMesh.geometry.attributes.position.needsUpdate = true;
      } else {
        this.rainMesh.material.opacity = 0.0;
      }
    }

    // 7. Atualizar Confetes
    for (let i = 0; i < this.confettiParticles.length; i++) {
      const c = this.confettiParticles[i];
      if (c.mesh.visible) {
        c.life -= dt;
        if (c.life <= 0 || c.mesh.position.y <= 0.1) {
          c.mesh.visible = false;
        } else {
          c.mesh.position.x += c.vx * dt;
          c.mesh.position.y += c.vy * dt;
          c.mesh.position.z += c.vz * dt;
          c.mesh.rotation.x += c.rotSpeed * dt;
          c.mesh.rotation.y += c.rotSpeed * dt;
          c.mesh.material.opacity = Math.min(1.0, c.life / 1.5);
        }
      }
    }
  }
}

window.ParticleSystem = ParticleSystem;
