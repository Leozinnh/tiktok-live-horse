class HorseVisualManager {
  constructor(scene, particleSystem) {
    this.scene = scene;
    this.particles = particleSystem;
    this.horsesMap = new Map(); // id -> horseVisualObject
  }

  createHorseMesh(horseConfig) {
    const modelKey = (horseConfig.body_model || horseConfig.visual_style || "classic").toLowerCase();
    const builder = (window.HorseBodyRegistry && window.HorseBodyRegistry[modelKey])
      || (window.HorseBodyRegistry && window.HorseBodyRegistry["classic"]);

    if (builder) {
      const obj = builder(horseConfig, this.scene, this.particles);
      obj.bodyModel = modelKey;
      return obj;
    }

    const group = new THREE.Group();
    const primaryColor = new THREE.Color(horseConfig.color_hex || "#f59e0b");
    const secondaryColor = new THREE.Color(horseConfig.secondary_color_hex || "#ffffff");
    const maneColor = new THREE.Color(horseConfig.mane_color_hex || "#1e293b");
    const hoofColor = new THREE.Color(horseConfig.hoof_color_hex || "#0f172a");
    const silkColor = new THREE.Color(horseConfig.jockey_silk_hex || horseConfig.secondary_color_hex || "#ffffff");
    const helmColor = new THREE.Color(horseConfig.jockey_helmet_hex || horseConfig.color_hex || "#f59e0b");

    // Materiais
    const coatMat = new THREE.MeshStandardMaterial({
      color: primaryColor,
      roughness: 0.65,
      metalness: 0.1,
    });
    const darkMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.7 });
    const maneMat = new THREE.MeshStandardMaterial({ color: maneColor, roughness: 0.8 });
    const silkMat = new THREE.MeshStandardMaterial({ color: silkColor, roughness: 0.3 });
    const hoofMat = new THREE.MeshStandardMaterial({ color: hoofColor, roughness: 0.9 });
    const helmMat = new THREE.MeshStandardMaterial({ color: helmColor, roughness: 0.2 });

    // 1. Tronco / Corpo do Cavalo
    const bodyGeo = new THREE.BoxGeometry(1.6, 1.4, 3.2);
    const body = new THREE.Mesh(bodyGeo, coatMat);
    body.position.y = 2.4;
    body.castShadow = true;
    group.add(body);

    // Manta de sela com a cor secundária e número
    const saddleGeo = new THREE.BoxGeometry(1.64, 0.9, 1.8);
    const saddle = new THREE.Mesh(saddleGeo, silkMat);
    saddle.position.set(0, 0.3, -0.1);
    saddle.castShadow = true;
    body.add(saddle);

    // 2. Pescoço e Cabeça
    const neckGeo = new THREE.BoxGeometry(0.8, 1.8, 1.0);
    const neck = new THREE.Mesh(neckGeo, coatMat);
    neck.position.set(0, 1.2, 1.4);
    neck.rotation.x = -Math.PI / 5;
    neck.castShadow = true;
    body.add(neck);

    // Crina estilizada no dorso do pescoço
    const maneGeo = new THREE.BoxGeometry(0.25, 1.8, 0.4);
    const mane = new THREE.Mesh(maneGeo, maneMat);
    mane.position.set(0, 0.05, -0.55);
    neck.add(mane);

    const headGeo = new THREE.BoxGeometry(0.75, 0.85, 1.4);
    const head = new THREE.Mesh(headGeo, coatMat);
    head.position.set(0, 0.9, 0.4);
    head.rotation.x = Math.PI / 4;
    head.castShadow = true;
    neck.add(head);

    // Focinho
    const muzzleGeo = new THREE.BoxGeometry(0.65, 0.65, 0.8);
    const muzzle = new THREE.Mesh(muzzleGeo, darkMat);
    muzzle.position.set(0, -0.1, 0.9);
    head.add(muzzle);

    // Orelhas
    const earGeo = new THREE.ConeGeometry(0.18, 0.45, 4);
    const earL = new THREE.Mesh(earGeo, coatMat);
    earL.position.set(0.3, 0.5, -0.3);
    head.add(earL);
    const earR = new THREE.Mesh(earGeo, coatMat);
    earR.position.set(-0.3, 0.5, -0.3);
    head.add(earR);

    // 3. Jockey (Cavaleiro Esportivo)
    const jockeyGroup = new THREE.Group();
    jockeyGroup.position.set(0, 0.9, 0.0);

    // Tronco do Jockey (farda de corrida)
    const jBodyGeo = new THREE.BoxGeometry(0.75, 0.95, 0.65);
    const jBody = new THREE.Mesh(jBodyGeo, silkMat);
    jBody.position.y = 0.5;
    jBody.rotation.x = 0.35; // inclinado aerodinamicamente
    jBody.castShadow = true;
    jockeyGroup.add(jBody);

    // Capacete do Jockey
    const helmGeo = new THREE.SphereGeometry(0.35, 12, 12);
    const helm = new THREE.Mesh(helmGeo, helmMat);
    helm.position.set(0, 1.15, 0.3);
    helm.castShadow = true;
    jockeyGroup.add(helm);
    body.add(jockeyGroup);

    // 4. Quatro Patas Articuladas
    const legGeo = new THREE.CylinderGeometry(0.18, 0.14, 1.4, 8);
    const lowerLegGeo = new THREE.CylinderGeometry(0.14, 0.11, 1.3, 8);
    const hoofGeo = new THREE.BoxGeometry(0.28, 0.25, 0.35);

    function createLeg(x, z) {
      const upper = new THREE.Group();
      upper.position.set(x, -0.6, z);

      const upperMesh = new THREE.Mesh(legGeo, coatMat);
      upperMesh.position.y = -0.6;
      upperMesh.castShadow = true;
      upper.add(upperMesh);

      const lower = new THREE.Group();
      lower.position.y = -1.3;

      const lowerMesh = new THREE.Mesh(lowerLegGeo, coatMat);
      lowerMesh.position.y = -0.55;
      lowerMesh.castShadow = true;
      lower.add(lowerMesh);

      const hoof = new THREE.Mesh(hoofGeo, hoofMat);
      hoof.position.set(0, -1.2, 0.05);
      hoof.castShadow = true;
      lower.add(hoof);

      upper.add(lower);
      body.add(upper);
      return { upper, lower };
    }

    const frontL = createLeg(0.55, 1.1);
    const frontR = createLeg(-0.55, 1.1);
    const backL = createLeg(0.55, -1.1);
    const backR = createLeg(-0.55, -1.1);

    // 5. Cauda
    const tailGeo = new THREE.CylinderGeometry(0.12, 0.04, 1.6, 6);
    const tail = new THREE.Mesh(tailGeo, maneMat);
    tail.position.set(0, 0.2, -1.7);
    tail.rotation.x = -Math.PI / 3;
    body.add(tail);

    // 6. Aura de Turbo / Boost
    const auraGeo = new THREE.SphereGeometry(2.4, 16, 16);
    const auraMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      wireframe: true,
      transparent: true,
      opacity: 0.0,
    });
    const auraMesh = new THREE.Mesh(auraGeo, auraMat);
    auraMesh.position.y = 2.0;
    group.add(auraMesh);

    // 6.1 Aura Mítica Lendária (Leão / Galáxia)
    const mythicAuraGeo = new THREE.TorusGeometry(3.2, 0.4, 8, 24);
    const mythicAuraMat = new THREE.MeshBasicMaterial({
      color: 0xf59e0b,
      wireframe: true,
      transparent: true,
      opacity: 0.0,
      side: THREE.DoubleSide
    });
    const mythicAura = new THREE.Mesh(mythicAuraGeo, mythicAuraMat);
    mythicAura.rotation.x = Math.PI / 2;
    mythicAura.position.y = 2.2;
    group.add(mythicAura);

    // 6.2 Emblema Holográfico Flutuante (Leão / Galáxia / Dragão / Rosa / etc)
    const emblemCanvas = document.createElement("canvas");
    emblemCanvas.width = 256; emblemCanvas.height = 128;
    const eCtx = emblemCanvas.getContext("2d");
    const emblemTex = new THREE.CanvasTexture(emblemCanvas);
    emblemTex.encoding = THREE.sRGBEncoding;
    const emblemSprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: emblemTex, transparent: true, opacity: 0 }));
    emblemSprite.scale.set(5.5, 2.75, 1.0);
    emblemSprite.position.set(0, 8.5, 0);
    group.add(emblemSprite);

    const setEmblem = (emoji, donor) => {
      eCtx.clearRect(0, 0, 256, 128);
      eCtx.fillStyle = "rgba(15, 23, 42, 0.88)";
      eCtx.roundRect ? eCtx.roundRect(8, 8, 240, 112, 20) : eCtx.fillRect(8, 8, 240, 112);
      eCtx.fill();
      eCtx.strokeStyle = "#fbbf24";
      eCtx.lineWidth = 4;
      eCtx.stroke();

      eCtx.font = "52px 'Segoe UI Emoji', 'Apple Color Emoji', sans-serif";
      eCtx.textAlign = "center";
      eCtx.textBaseline = "middle";
      eCtx.fillText(emoji || "🎁", 128, 48);

      if (donor) {
        eCtx.fillStyle = "#ffffff";
        eCtx.font = "bold 20px sans-serif";
        eCtx.fillText(`@${donor.slice(0, 14)}`, 128, 95);
      }
      emblemTex.needsUpdate = true;
    };

    // 7. Badge de Nome Flutuante (Canvas Textura)
    const badgeCanvas = document.createElement("canvas");
    badgeCanvas.width = 256;
    badgeCanvas.height = 64;
    const ctx = badgeCanvas.getContext("2d");
    ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
    ctx.roundRect ? ctx.roundRect(4, 4, 248, 56, 12) : ctx.fillRect(4, 4, 248, 56);
    ctx.fill();
    ctx.strokeStyle = horseConfig.color_hex || "#ffffff";
    ctx.lineWidth = 4;
    ctx.stroke();
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 26px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(`#${horseConfig.number} ${horseConfig.name}`, 128, 40);

    const badgeTexture = new THREE.CanvasTexture(badgeCanvas);
    badgeTexture.encoding = THREE.sRGBEncoding;
    const badgeMat = new THREE.SpriteMaterial({ map: badgeTexture, transparent: true });
    const badgeSprite = new THREE.Sprite(badgeMat);
    badgeSprite.scale.set(6.0, 1.5, 1.0);
    badgeSprite.position.set(0, 5.8, 0);
    group.add(badgeSprite);

    this.scene.add(group);

    return {
      id: horseConfig.id,
      number: horseConfig.number,
      name: horseConfig.name,
      group: group,
      body: body,
      neck: neck,
      legs: { frontL, frontR, backL, backR },
      tail: tail,
      aura: auraMesh,
      mythicAura: mythicAura,
      emblem: emblemSprite,
      setEmblem: setEmblem,
      currentEmblemKind: "LION",
      badge: badgeSprite,
      phase: Math.random() * Math.PI * 2,
    };
  }

  update(horsesData, dt) {
    if (!horsesData || !Array.isArray(horsesData)) return;

    for (let i = 0; i < horsesData.length; i++) {
      const hData = horsesData[i];
      let horseObj = this.horsesMap.get(hData.id);
      const modelKey = (hData.body_model || hData.visual_style || "classic").toLowerCase();

      if (!horseObj || horseObj.bodyModel !== modelKey) {
        if (horseObj && horseObj.group) {
          this.scene.remove(horseObj.group);
        }
        horseObj = this.createHorseMesh(hData);
        this.horsesMap.set(hData.id, horseObj);
      }

      // Atualiza coordenadas no mundo
      const targetX = hData.x || 0;
      const targetY = (hData.y || 0) + 0.1;
      const targetZ = hData.z || 0;
      const targetRotY = hData.rotation_y || 0;

      // Interpolação angular contínua em curvas sem descontinuidade
      let diffRot = targetRotY - horseObj.group.rotation.y;
      while (diffRot < -Math.PI) diffRot += Math.PI * 2;
      while (diffRot > Math.PI) diffRot -= Math.PI * 2;
      const rotLerp = Math.min(1.0, dt * 14.0);
      horseObj.group.rotation.y += diffRot * rotLerp;

      // Avanço cinemático contínuo por frame (Dead Reckoning com velocidade vetorial):
      // Garante movimento 60-144 FPS liso e sedoso, sem engasgos de rede
      const speed = hData.finished ? 0.0 : (hData.speed || 0.0);
      if (speed > 0.5) {
        const vx = speed * Math.sin(horseObj.group.rotation.y);
        const vz = speed * Math.cos(horseObj.group.rotation.y);
        horseObj.group.position.x += vx * dt;
        horseObj.group.position.z += vz * dt;
      }

      // Amortecimento suave com taxa proporcional a dt (elimina micro-stuttering)
      const corr = Math.min(1.0, dt * 9.0);
      horseObj.group.position.x += (targetX - horseObj.group.position.x) * corr;
      horseObj.group.position.y = targetY;
      horseObj.group.position.z += (targetZ - horseObj.group.position.z) * corr;

      // Animação Procedural de Galope sincronizada à velocidade (interrompe quando cruzar a chegada)
      if (!hData.finished && speed > 1.0) {
        horseObj.phase += speed * dt * 0.72;

        // Movimento do tronco (sobe e desce + pitch)
        horseObj.body.position.y = 2.4 + Math.sin(horseObj.phase * 2.0) * 0.22;
        horseObj.body.rotation.x = Math.sin(horseObj.phase) * 0.12;
        horseObj.neck.rotation.x = -Math.PI / 5 + Math.cos(horseObj.phase) * 0.08;

        // Patas dianteiras e traseiras alternando
        const fSwing = Math.sin(horseObj.phase) * 0.75;
        const bSwing = Math.cos(horseObj.phase) * 0.85;

        horseObj.legs.frontL.upper.rotation.x = fSwing;
        horseObj.legs.frontL.lower.rotation.x = Math.max(0, -fSwing * 1.1);

        horseObj.legs.frontR.upper.rotation.x = -fSwing;
        horseObj.legs.frontR.lower.rotation.x = Math.max(0, fSwing * 1.1);

        horseObj.legs.backL.upper.rotation.x = -bSwing;
        horseObj.legs.backL.lower.rotation.x = Math.max(0, bSwing * 1.2);

        horseObj.legs.backR.upper.rotation.x = bSwing;
        horseObj.legs.backR.lower.rotation.x = Math.max(0, -bSwing * 1.2);

        // Emissão de poeira nos cascos
        if (Math.sin(horseObj.phase) > 0.8) {
          this.particles.emitDust(horseObj.group.position, speed);
        }

        // Animação de asas graciosa e fluida (Pégaso)
        if (horseObj.wings) {
          const t = horseObj.phase * 2.2;
          const flap = Math.sin(t);
          const flapCos = Math.cos(t);

          // Batimento tridimensional: abre e varre para trás na descida, recolhe suave na subida
          horseObj.wings.left.rotation.z = 0.22 + flap * 0.45;
          horseObj.wings.left.rotation.y = 0.12 + flapCos * 0.18;
          horseObj.wings.left.rotation.x = -0.15 + flap * 0.1;

          horseObj.wings.right.rotation.z = -(0.22 + flap * 0.45);
          horseObj.wings.right.rotation.y = -(0.12 + flapCos * 0.18);
          horseObj.wings.right.rotation.x = -0.15 + flap * 0.1;
        }
      } else {
        // Em repouso nos boxes ou parado na linha de chegada (parado naturalmente com as 4 patas no chão)
        horseObj.body.position.y = 2.4 + Math.sin(Date.now() * 0.003 + horseObj.id) * 0.04;
        horseObj.body.rotation.x = 0;
        horseObj.neck.rotation.x = -Math.PI / 5;
        horseObj.legs.frontL.upper.rotation.x = 0;
        horseObj.legs.frontL.lower.rotation.x = 0;
        horseObj.legs.frontR.upper.rotation.x = 0;
        horseObj.legs.frontR.lower.rotation.x = 0;
        horseObj.legs.backL.upper.rotation.x = 0;
        horseObj.legs.backL.lower.rotation.x = 0;
        horseObj.legs.backR.upper.rotation.x = 0;
        horseObj.legs.backR.lower.rotation.x = 0;

        // Asas elegantemente recolhidas e dobradas para trás contra o dorso
        if (horseObj.wings) {
          horseObj.wings.left.rotation.z = -0.2;
          horseObj.wings.left.rotation.y = -0.35;
          horseObj.wings.left.rotation.x = 0.12;

          horseObj.wings.right.rotation.z = 0.2;
          horseObj.wings.right.rotation.y = 0.35;
          horseObj.wings.right.rotation.x = 0.12;
        }
      }

      // Emblema holográfico flutuante para QUALQUER presente recebido (Leão 🦁, Galáxia 🌌, Dragão 🐉, Rosa 🌹, Donut 🍩, etc)
      const activeEmoji = hData.gift_emoji || (hData.is_legendary_boost ? (hData.legendary_kind === "GALAXY" ? "🌌" : (hData.legendary_kind === "DRAGON" ? "🐉" : "🦁")) : null);
      if (activeEmoji) {
        if (horseObj.currentEmblemEmoji !== activeEmoji || horseObj.currentDonor !== hData.donor_name) {
          horseObj.setEmblem(activeEmoji, hData.donor_name);
          horseObj.currentEmblemEmoji = activeEmoji;
          horseObj.currentDonor = hData.donor_name;
        }
        horseObj.emblem.material.opacity = 1.0;
        horseObj.emblem.position.y = 8.4 + Math.sin(Date.now() * 0.006) * 0.4;
      } else {
        horseObj.emblem.material.opacity = 0.0;
        horseObj.currentEmblemEmoji = null;
        horseObj.currentDonor = null;
      }

      // Efeito de Boost Lendário (Aura Mítica e Chamas Cósmicas)
      if (hData.is_legendary_boost) {
        const isLion = hData.legendary_kind === "LION";
        const primaryHex = isLion ? 0xf59e0b : (hData.legendary_kind === "GALAXY" ? 0xa855f7 : 0xef4444);
        
        // Aura Mítica em rotação rápida
        horseObj.mythicAura.material.color.setHex(primaryHex);
        horseObj.mythicAura.material.opacity = 0.85 + Math.sin(Date.now() * 0.02) * 0.15;
        horseObj.mythicAura.rotation.z += dt * 8.0;

        // Rastro de fogo e brasas
        this.particles.emitLegendaryAuraTrail(horseObj.group.position, hData.legendary_kind);
      } else {
        horseObj.mythicAura.material.opacity = 0.0;
      }

      // Efeito de Boost / Turbo Comum
      if (hData.boost_active) {
        horseObj.aura.material.opacity = 0.55 + Math.sin(Date.now() * 0.015) * 0.25;
        horseObj.aura.rotation.y += dt * 4.0;
        this.particles.emitTurboSparks(horseObj.group.position);
      } else {
        horseObj.aura.material.opacity = 0.0;
      }
    }
  }

  getHorsePosition(horseId) {
    const h = this.horsesMap.get(horseId);
    return h ? h.group.position : new THREE.Vector3(0, 0, 0);
  }

  getHorseRotationY(horseId) {
    const h = this.horsesMap.get(horseId);
    return h ? h.group.rotation.y : (Math.PI / 2.0);
  }
}

window.HorseVisualManager = HorseVisualManager;
