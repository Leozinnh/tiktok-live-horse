// Utilitários compartilhados para construção de corpos de cavalos 3D
window.HorseBodyRegistry = window.HorseBodyRegistry || {};

window.HorseBodyUtils = {
  createMaterials(cfg) {
    const primaryColor = new THREE.Color(cfg.color_hex || "#f59e0b");
    const secondaryColor = new THREE.Color(cfg.secondary_color_hex || "#ffffff");
    const maneColor = new THREE.Color(cfg.mane_color_hex || "#1e293b");
    const hoofColor = new THREE.Color(cfg.hoof_color_hex || "#0f172a");
    const silkColor = new THREE.Color(cfg.jockey_silk_hex || cfg.secondary_color_hex || "#ffffff");
    const helmColor = new THREE.Color(cfg.jockey_helmet_hex || cfg.color_hex || "#f59e0b");

    return {
      coatMat: new THREE.MeshStandardMaterial({ color: primaryColor, roughness: 0.65, metalness: 0.1 }),
      secondaryMat: new THREE.MeshStandardMaterial({ color: secondaryColor, roughness: 0.4 }),
      maneMat: new THREE.MeshStandardMaterial({ color: maneColor, roughness: 0.8 }),
      hoofMat: new THREE.MeshStandardMaterial({ color: hoofColor, roughness: 0.9 }),
      silkMat: new THREE.MeshStandardMaterial({ color: silkColor, roughness: 0.3 }),
      helmMat: new THREE.MeshStandardMaterial({ color: helmColor, roughness: 0.2 }),
      darkMat: new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.7 }),
      metalMat: new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.85, roughness: 0.2 }),
      goldMat: new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.9, roughness: 0.15 }),
      neonMat: new THREE.MeshBasicMaterial({ color: primaryColor }),
    };
  },

  createLegs(body, coatMat, hoofMat, scaleX = 1.0, scaleY = 1.0) {
    const legGeo = new THREE.CylinderGeometry(0.18 * scaleX, 0.14 * scaleX, 1.4 * scaleY, 8);
    const lowerLegGeo = new THREE.CylinderGeometry(0.14 * scaleX, 0.11 * scaleX, 1.3 * scaleY, 8);
    const hoofGeo = new THREE.BoxGeometry(0.28 * scaleX, 0.25 * scaleY, 0.35 * scaleX);

    function createSingleLeg(x, z) {
      const upper = new THREE.Group();
      upper.position.set(x, -0.6 * scaleY, z);

      const upperMesh = new THREE.Mesh(legGeo, coatMat);
      upperMesh.position.y = -0.6 * scaleY;
      upperMesh.castShadow = true;
      upper.add(upperMesh);

      const lower = new THREE.Group();
      lower.position.y = -1.3 * scaleY;

      const lowerMesh = new THREE.Mesh(lowerLegGeo, coatMat);
      lowerMesh.position.y = -0.55 * scaleY;
      lowerMesh.castShadow = true;
      lower.add(lowerMesh);

      const hoof = new THREE.Mesh(hoofGeo, hoofMat);
      hoof.position.set(0, -1.2 * scaleY, 0.05);
      hoof.castShadow = true;
      lower.add(hoof);

      upper.add(lower);
      body.add(upper);
      return { upper, lower };
    }

    return {
      frontL: createSingleLeg(0.55 * scaleX, 1.1 * scaleX),
      frontR: createSingleLeg(-0.55 * scaleX, 1.1 * scaleX),
      backL: createSingleLeg(0.55 * scaleX, -1.1 * scaleX),
      backR: createSingleLeg(-0.55 * scaleX, -1.1 * scaleX),
    };
  },

  createJockey(body, silkMat, helmMat, primaryColor) {
    const jockeyGroup = new THREE.Group();
    jockeyGroup.position.set(0, 0.9, 0.0);

    const jBodyGeo = new THREE.BoxGeometry(0.75, 0.95, 0.65);
    const jBody = new THREE.Mesh(jBodyGeo, silkMat);
    jBody.position.y = 0.5;
    jBody.rotation.x = 0.35;
    jBody.castShadow = true;
    jockeyGroup.add(jBody);

    const helmGeo = new THREE.SphereGeometry(0.35, 12, 12);
    const helm = new THREE.Mesh(helmGeo, helmMat);
    helm.position.set(0, 1.15, 0.3);
    helm.castShadow = true;
    jockeyGroup.add(helm);

    body.add(jockeyGroup);
    return jockeyGroup;
  },

  // Textura do halo de energia: riscos radiais saindo de baixo do cavalo mais
  // um anel de choque na borda. Desenhada uma única vez e compartilhada por
  // todos os cavalos — quem carrega a cor é o material de cada um.
  auraTexture() {
    if (HorseBodyUtils._auraTex) return HorseBodyUtils._auraTex;

    const canvas = document.createElement("canvas");
    canvas.width = 256;
    canvas.height = 256;
    const ctx = canvas.getContext("2d");
    const cx = 128;
    const cy = 128;

    // Os riscos começam longe do centro (44% do raio): embaixo do cavalo o
    // halo fica limpo, senão o bicho vira um borrão branco no meio da luz.
    ctx.lineCap = "round";
    for (let i = 0; i < 56; i++) {
      const ang = (i / 56) * Math.PI * 2;
      const r0 = 46 + (i % 3) * 7;
      const r1 = 96 + (i % 5) * 12;
      const x0 = cx + Math.cos(ang) * r0;
      const y0 = cy + Math.sin(ang) * r0;
      const x1 = cx + Math.cos(ang) * r1;
      const y1 = cy + Math.sin(ang) * r1;
      const grad = ctx.createLinearGradient(x0, y0, x1, y1);
      grad.addColorStop(0, "rgba(255,255,255,0.95)");
      grad.addColorStop(1, "rgba(255,255,255,0)");
      ctx.strokeStyle = grad;
      ctx.lineWidth = i % 4 === 0 ? 3 : 1.6;
      ctx.beginPath();
      ctx.moveTo(x0, y0);
      ctx.lineTo(x1, y1);
      ctx.stroke();
    }

    // Anel de borda: em pista clara (areia) os riscos sozinhos somem.
    ctx.strokeStyle = "rgba(255,255,255,0.5)";
    ctx.lineWidth = 6;
    ctx.beginPath();
    ctx.arc(cx, cy, 105, 0, Math.PI * 2);
    ctx.stroke();

    const tex = new THREE.CanvasTexture(canvas);
    if (THREE.sRGBEncoding) tex.encoding = THREE.sRGBEncoding;
    HorseBodyUtils._auraTex = tex;
    return tex;
  },

  // Aura de boost: halo de energia girando no chão + fitas de velocidade
  // atrás do cavalo. Substituiu a esfera wireframe que envolvia o animal —
  // um balão que escondia o modelo e não dizia nada. O halo marca o
  // "empurrão no chão" em qualquer ângulo de câmera e as fitas dão o rastro
  // de velocidade no enquadramento de perseguição, que é o mais usado na live.
  createAuras(group, cfg) {
    const boostColor = new THREE.Color((cfg && cfg.color_hex) || "#38bdf8");

    const haloMat = new THREE.MeshBasicMaterial({
      map: HorseBodyUtils.auraTexture(),
      color: boostColor,
      transparent: true,
      opacity: 0.0,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      side: THREE.DoubleSide,
    });
    const halo = new THREE.Mesh(new THREE.PlaneGeometry(11, 11), haloMat);
    halo.rotation.x = -Math.PI / 2;
    halo.position.y = 0.09;
    halo.renderOrder = 3;
    group.add(halo);

    // Fitas de velocidade: caudas de luz na garupa (o modelo corre para +z,
    // então o rastro sai no -z). Nascem curtas e são esticadas em update().
    const bladeMat = new THREE.MeshBasicMaterial({
      color: boostColor,
      transparent: true,
      opacity: 0.0,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const blades = [];
    for (let i = 0; i < 7; i++) {
      const lateral = (i / 6) - 0.5; // leque de -1,1m a +1,1m
      const blade = new THREE.Mesh(new THREE.BoxGeometry(0.13, 0.13, 1.0), bladeMat);
      blade.position.set(lateral * 2.2, 1.25 + (i % 3) * 0.7, -2.3);
      blade.renderOrder = 3;
      group.add(blade);
      blades.push({ mesh: blade, phase: i * 0.9 });
    }

    const mythicAuraGeo = new THREE.TorusGeometry(3.2, 0.4, 8, 24);
    const mythicAuraMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b, wireframe: true, transparent: true, opacity: 0, side: THREE.DoubleSide });
    const mythicAura = new THREE.Mesh(mythicAuraGeo, mythicAuraMat);
    mythicAura.rotation.x = Math.PI / 2;
    mythicAura.position.y = 2.2;
    group.add(mythicAura);

    return {
      aura: halo,
      auraHaloMat: haloMat,
      auraBlades: blades,
      auraBladeMat: bladeMat,
      mythicAura: mythicAura,
    };
  },

  createBadgeAndEmblem(group, cfg) {
    // Emblema e badge em 2x (512 de largura em vez de 256): os dois sprites
    // têm 5,5m e 6m de largura, ou seja ~450px na tela em 1080p — com 256px
    // de origem o texto e o emoji chegavam esticados na transmissão.
    const emblemCanvas = document.createElement("canvas");
    emblemCanvas.width = 512; emblemCanvas.height = 256;
    const eCtx = emblemCanvas.getContext("2d");
    const emblemTex = new THREE.CanvasTexture(emblemCanvas);
    if (THREE.sRGBEncoding) emblemTex.encoding = THREE.sRGBEncoding;
    const emblemSprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: emblemTex, transparent: true, opacity: 0 }));
    emblemSprite.scale.set(5.5, 2.75, 1.0);
    emblemSprite.position.set(0, 8.5, 0);
    group.add(emblemSprite);

    const setEmblem = (emoji, donor) => {
      eCtx.clearRect(0, 0, 512, 256);
      eCtx.fillStyle = "rgba(15, 23, 42, 0.88)";
      eCtx.roundRect ? eCtx.roundRect(16, 16, 480, 224, 40) : eCtx.fillRect(16, 16, 480, 224);
      eCtx.fill();
      eCtx.strokeStyle = "#fbbf24";
      eCtx.lineWidth = 8;
      eCtx.stroke();

      eCtx.font = "104px 'Segoe UI Emoji', 'Apple Color Emoji', sans-serif";
      eCtx.textAlign = "center";
      eCtx.textBaseline = "middle";
      eCtx.fillText(emoji || "🎁", 256, 96);

      if (donor) {
        eCtx.fillStyle = "#ffffff";
        eCtx.font = "bold 40px sans-serif";
        eCtx.fillText(`@${donor.slice(0, 14)}`, 256, 190);
      }
      emblemTex.needsUpdate = true;
    };

    const badgeCanvas = document.createElement("canvas");
    badgeCanvas.width = 512; badgeCanvas.height = 128;
    const bCtx = badgeCanvas.getContext("2d");
    bCtx.fillStyle = "rgba(15, 23, 42, 0.85)";
    bCtx.roundRect ? bCtx.roundRect(8, 8, 496, 112, 24) : bCtx.fillRect(8, 8, 496, 112);
    bCtx.fill();
    bCtx.strokeStyle = cfg.color_hex || "#ffffff";
    bCtx.lineWidth = 8;
    bCtx.stroke();
    bCtx.fillStyle = "#ffffff";
    bCtx.font = "bold 52px sans-serif";
    bCtx.textAlign = "center";
    bCtx.fillText(`#${cfg.number} ${cfg.name}`, 256, 80);

    const badgeTexture = new THREE.CanvasTexture(badgeCanvas);
    if (THREE.sRGBEncoding) badgeTexture.encoding = THREE.sRGBEncoding;
    const badgeSprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: badgeTexture, transparent: true }));
    badgeSprite.scale.set(6.0, 1.5, 1.0);
    badgeSprite.position.set(0, 5.8, 0);
    group.add(badgeSprite);

    return { emblem: emblemSprite, setEmblem, badge: badgeSprite };
  }
};
