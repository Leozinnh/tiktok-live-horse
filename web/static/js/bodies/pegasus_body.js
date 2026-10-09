// Modelo 3: Pégaso Alado Majestoso (Anatomical Feathered Pegasus)
window.HorseBodyRegistry = window.HorseBodyRegistry || {};

window.HorseBodyRegistry["pegasus"] = function buildPegasusHorse(cfg, scene) {
  const group = new THREE.Group();
  const mats = HorseBodyUtils.createMaterials(cfg);

  // 1. Tronco Nobre
  const body = new THREE.Mesh(new THREE.BoxGeometry(1.6, 1.4, 3.2), mats.coatMat);
  body.position.y = 2.4;
  body.castShadow = true;
  group.add(body);

  // Manta de sela celestial
  const saddle = new THREE.Mesh(new THREE.BoxGeometry(1.66, 0.9, 1.8), mats.secondaryMat);
  saddle.position.set(0, 0.3, -0.1);
  saddle.castShadow = true;
  body.add(saddle);

  // 2. CONSTRUÇÃO ANATÔMICA DAS ASAS DE PENAS (Realistas e Elegantes)
  const wingBaseColor = new THREE.Color(cfg.secondary_color_hex || "#ffffff");
  const wingTipColor = new THREE.Color(cfg.color_hex || "#f59e0b");

  const featherMat = new THREE.MeshStandardMaterial({
    color: wingBaseColor,
    roughness: 0.35,
    metalness: 0.1,
    side: THREE.DoubleSide
  });

  const featherTipMat = new THREE.MeshStandardMaterial({
    color: wingTipColor,
    roughness: 0.3,
    metalness: 0.2,
    side: THREE.DoubleSide
  });

  const boneMat = new THREE.MeshStandardMaterial({
    color: wingBaseColor,
    roughness: 0.5,
    metalness: 0.1
  });

  // Função auxiliar para criar uma pena afilada elegante
  function createFeatherMesh(length, width, mat) {
    const shape = new THREE.Shape();
    shape.moveTo(0, 0);
    shape.quadraticCurveTo(width * 0.8, length * 0.35, width * 0.5, length * 0.85);
    shape.quadraticCurveTo(0, length, -width * 0.1, length);
    shape.quadraticCurveTo(-width * 0.6, length * 0.65, -width * 0.4, length * 0.25);
    shape.closePath();

    const geo = new THREE.ShapeGeometry(shape);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.castShadow = true;
    return mesh;
  }

  function createWing(isLeft) {
    const wingPivot = new THREE.Group();
    const sign = isLeft ? 1 : -1;

    // Ponto de articulação anatômico no ombro do cavalo
    wingPivot.position.set(sign * 0.82, 0.72, 0.25);

    // Estrutura Óssea Principal (Bordo de Ataque Curvado)
    const boneUpper = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.08, 1.6, 8), boneMat);
    boneUpper.position.set(sign * 0.55, 0.65, 0.1);
    boneUpper.rotation.z = sign * 0.75;
    boneUpper.rotation.x = -0.25;
    boneUpper.castShadow = true;
    wingPivot.add(boneUpper);

    const boneFore = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.05, 1.8, 8), boneMat);
    boneFore.position.set(sign * 1.45, 1.15, -0.4);
    boneFore.rotation.z = sign * 0.25;
    boneFore.rotation.x = -0.55;
    boneFore.castShadow = true;
    wingPivot.add(boneFore);

    // 1ª Camada: Penas de Cobertura (Base do Ombro)
    for (let c = 0; c < 4; c++) {
      const f = createFeatherMesh(0.95 + c * 0.15, 0.38, featherMat);
      f.position.set(sign * (0.3 + c * 0.22), 0.35 + c * 0.18, -0.05 - c * 0.15);
      f.rotation.z = sign * (0.7 + c * 0.1);
      f.rotation.y = sign * 0.15;
      f.rotation.x = -0.35;
      wingPivot.add(f);
    }

    // 2ª Camada: Penas Secundárias (Meio da Asa)
    for (let s = 0; s < 5; s++) {
      const f = createFeatherMesh(1.5 + s * 0.18, 0.42, featherMat);
      f.position.set(sign * (0.6 + s * 0.25), 0.7 + s * 0.12, -0.2 - s * 0.22);
      f.rotation.z = sign * (0.55 + s * 0.08);
      f.rotation.y = sign * 0.18;
      f.rotation.x = -0.55;
      wingPivot.add(f);
    }

    // 3ª Camada: Penas Primárias Longas (Extremidade Externa)
    for (let p = 0; p < 6; p++) {
      const isTip = p >= 4;
      const f = createFeatherMesh(2.2 + p * 0.18, 0.45, isTip ? featherTipMat : featherMat);
      f.position.set(sign * (1.1 + p * 0.28), 1.05 + p * 0.08, -0.5 - p * 0.28);
      f.rotation.z = sign * (0.35 + p * 0.06);
      f.rotation.y = sign * 0.22;
      f.rotation.x = -0.75;
      wingPivot.add(f);
    }

    body.add(wingPivot);
    return wingPivot;
  }

  const wingL = createWing(true);
  const wingR = createWing(false);

  // 3. Pescoço e Crina Esvoaçante
  const neck = new THREE.Mesh(new THREE.BoxGeometry(0.78, 1.8, 1.0), mats.coatMat);
  neck.position.set(0, 1.2, 1.4);
  neck.rotation.x = -Math.PI / 5;
  neck.castShadow = true;
  body.add(neck);

  const mane = new THREE.Mesh(new THREE.BoxGeometry(0.28, 2.0, 0.55), mats.maneMat);
  mane.position.set(0, 0.05, -0.55);
  neck.add(mane);

  // 4. Cabeça Nobre com Auréola Dourada Flutuante
  const head = new THREE.Mesh(new THREE.BoxGeometry(0.75, 0.85, 1.4), mats.coatMat);
  head.position.set(0, 0.9, 0.4);
  head.rotation.x = Math.PI / 4;
  head.castShadow = true;
  neck.add(head);

  // Auréola Celestial
  const haloGeo = new THREE.TorusGeometry(0.55, 0.06, 8, 24);
  const haloMat = new THREE.MeshBasicMaterial({ color: 0xfef08a });
  const halo = new THREE.Mesh(haloGeo, haloMat);
  halo.rotation.x = Math.PI / 2;
  halo.position.set(0, 1.05, 0.1);
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

  // 5. Jóquei
  HorseBodyUtils.createJockey(body, mats.silkMat, mats.helmMat, cfg.color_hex);

  // 6. Patas com Cascos Dourados
  const legs = HorseBodyUtils.createLegs(body, mats.coatMat, mats.goldMat);

  // 7. Cauda Longa e Sedosa
  const tail = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.03, 2.2, 6), mats.maneMat);
  tail.position.set(0, 0.25, -1.8);
  tail.rotation.x = -Math.PI / 3.2;
  body.add(tail);

  // 8. Auras, Badge e Emblema
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
