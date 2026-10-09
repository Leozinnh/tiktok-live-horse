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

  createAuras(group) {
    const auraGeo = new THREE.SphereGeometry(2.4, 16, 16);
    const auraMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8, wireframe: true, transparent: true, opacity: 0 });
    const auraMesh = new THREE.Mesh(auraGeo, auraMat);
    auraMesh.position.y = 2.0;
    group.add(auraMesh);

    const mythicAuraGeo = new THREE.TorusGeometry(3.2, 0.4, 8, 24);
    const mythicAuraMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b, wireframe: true, transparent: true, opacity: 0, side: THREE.DoubleSide });
    const mythicAura = new THREE.Mesh(mythicAuraGeo, mythicAuraMat);
    mythicAura.rotation.x = Math.PI / 2;
    mythicAura.position.y = 2.2;
    group.add(mythicAura);

    return { aura: auraMesh, mythicAura: mythicAura };
  },

  createBadgeAndEmblem(group, cfg) {
    const emblemCanvas = document.createElement("canvas");
    emblemCanvas.width = 256; emblemCanvas.height = 128;
    const eCtx = emblemCanvas.getContext("2d");
    const emblemTex = new THREE.CanvasTexture(emblemCanvas);
    if (THREE.sRGBEncoding) emblemTex.encoding = THREE.sRGBEncoding;
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

    const badgeCanvas = document.createElement("canvas");
    badgeCanvas.width = 256; badgeCanvas.height = 64;
    const bCtx = badgeCanvas.getContext("2d");
    bCtx.fillStyle = "rgba(15, 23, 42, 0.85)";
    bCtx.roundRect ? bCtx.roundRect(4, 4, 248, 56, 12) : bCtx.fillRect(4, 4, 248, 56);
    bCtx.fill();
    bCtx.strokeStyle = cfg.color_hex || "#ffffff";
    bCtx.lineWidth = 4;
    bCtx.stroke();
    bCtx.fillStyle = "#ffffff";
    bCtx.font = "bold 26px sans-serif";
    bCtx.textAlign = "center";
    bCtx.fillText(`#${cfg.number} ${cfg.name}`, 128, 40);

    const badgeTexture = new THREE.CanvasTexture(badgeCanvas);
    if (THREE.sRGBEncoding) badgeTexture.encoding = THREE.sRGBEncoding;
    const badgeSprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: badgeTexture, transparent: true }));
    badgeSprite.scale.set(6.0, 1.5, 1.0);
    badgeSprite.position.set(0, 5.8, 0);
    group.add(badgeSprite);

    return { emblem: emblemSprite, setEmblem, badge: badgeSprite };
  }
};
