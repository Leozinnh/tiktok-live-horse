// Modelo 3: Pégaso Alado Celestial (Pegasus Winged Steed)
window.HorseBodyRegistry = window.HorseBodyRegistry || {};

window.HorseBodyRegistry["pegasus"] = function buildPegasusHorse(cfg, scene) {
  const group = new THREE.Group();
  const mats = HorseBodyUtils.createMaterials(cfg);

  // 1. Tronco Nobre
  const body = new THREE.Mesh(new THREE.BoxGeometry(1.65, 1.4, 3.2), mats.coatMat);
  body.position.y = 2.4;
  body.castShadow = true;
  group.add(body);

  // Manta de sela celestial
  const saddle = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.9, 1.8), mats.secondaryMat);
  saddle.position.set(0, 0.3, -0.1);
  saddle.castShadow = true;
  body.add(saddle);

  // ASAS CELESTIAIS GRANDIOSAS (Envergadura Impressionante de ~5 Metros)
  const wingMat = new THREE.MeshStandardMaterial({
    color: 0xffffff,
    emissive: 0xe0f2fe,
    emissiveIntensity: 0.3,
    roughness: 0.2,
    metalness: 0.1,
    side: THREE.DoubleSide
  });

  const featherTipMat = new THREE.MeshBasicMaterial({
    color: mats.secondaryMat.color || 0x38bdf8,
    side: THREE.DoubleSide
  });

  function createWing(isLeft) {
    const wingGroup = new THREE.Group();
    const sign = isLeft ? 1 : -1;
    wingGroup.position.set(sign * 0.9, 0.65, 0.1);

    // 5 Grandes Penas Primárias em Leque
    for (let f = 0; f < 5; f++) {
      const fGroup = new THREE.Group();
      fGroup.position.set(sign * (0.6 + f * 0.55), 0.3 + f * 0.45, -f * 0.25);
      fGroup.rotation.z = sign * (0.35 + f * 0.14);

      // Corpo da pena
      const feather = new THREE.Mesh(
        new THREE.BoxGeometry(0.14, 0.6 + f * 0.45, 2.4 - f * 0.3),
        wingMat
      );
      feather.castShadow = true;
      fGroup.add(feather);

      // Ponta colorida brilhante da pena
      const tip = new THREE.Mesh(
        new THREE.BoxGeometry(0.16, 0.3, 0.8),
        featherTipMat
      );
      tip.position.set(0, (0.3 + f * 0.22), 0.7);
      fGroup.add(tip);

      wingGroup.add(fGroup);
    }
    body.add(wingGroup);
    return wingGroup;
  }

  const wingL = createWing(true);
  const wingR = createWing(false);

  // 2. Pescoço e Crina Esvoaçante
  const neck = new THREE.Mesh(new THREE.BoxGeometry(0.78, 1.8, 1.0), mats.coatMat);
  neck.position.set(0, 1.2, 1.4);
  neck.rotation.x = -Math.PI / 5;
  neck.castShadow = true;
  body.add(neck);

  const mane = new THREE.Mesh(new THREE.BoxGeometry(0.3, 2.0, 0.6), mats.maneMat);
  mane.position.set(0, 0.05, -0.55);
  neck.add(mane);

  // 3. Cabeça com Auréola Celestial Flutuante
  const head = new THREE.Mesh(new THREE.BoxGeometry(0.75, 0.85, 1.4), mats.coatMat);
  head.position.set(0, 0.9, 0.4);
  head.rotation.x = Math.PI / 4;
  head.castShadow = true;
  neck.add(head);

  // Auréola Dourada Flutuante acima da Cabeça
  const haloGeo = new THREE.TorusGeometry(0.65, 0.08, 8, 24);
  const haloMat = new THREE.MeshBasicMaterial({ color: 0xfef08a });
  const halo = new THREE.Mesh(haloGeo, haloMat);
  halo.rotation.x = Math.PI / 2;
  halo.position.set(0, 1.1, 0.1);
  head.add(halo);

  const muzzle = new THREE.Mesh(new THREE.BoxGeometry(0.65, 0.65, 0.8), mats.secondaryMat);
  muzzle.position.set(0, -0.1, 0.9);
  head.add(muzzle);

  const earGeo = new THREE.ConeGeometry(0.18, 0.5, 4);
  const earL = new THREE.Mesh(earGeo, mats.coatMat);
  earL.position.set(0.3, 0.55, -0.3);
  head.add(earL);
  const earR = new THREE.Mesh(earGeo, mats.coatMat);
  earR.position.set(-0.3, 0.55, -0.3);
  head.add(earR);

  // 4. Jóquei
  HorseBodyUtils.createJockey(body, mats.silkMat, mats.helmMat, cfg.color_hex);

  // 5. Patas com Cascos Dourados
  const legs = HorseBodyUtils.createLegs(body, mats.coatMat, mats.goldMat);

  // 6. Cauda Longa e Esvoaçante
  const tail = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.03, 2.2, 6), mats.maneMat);
  tail.position.set(0, 0.25, -1.8);
  tail.rotation.x = -Math.PI / 3.2;
  body.add(tail);

  // 7. Auras, Badge e Emblema
  const auras = HorseBodyUtils.createAuras(group);
  const badgeObj = HorseBodyUtils.createBadgeAndEmblem(group, cfg);

  scene.add(group);

  return {
    id: cfg.id,
    number: cfg.number,
    name: cfg.name,
    bodyModel: "pegasus",
    group: group,
    body: body,
    neck: neck,
    legs: legs,
    tail: tail,
    wings: { left: wingL, right: wingR },
    aura: auras.aura,
    mythicAura: auras.mythicAura,
    emblem: badgeObj.emblem,
    setEmblem: badgeObj.setEmblem,
    badge: badgeObj.badge,
    phase: Math.random() * Math.PI * 2,
  };
};
