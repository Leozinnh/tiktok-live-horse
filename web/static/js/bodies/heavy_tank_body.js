// Modelo 5: Titã Blindado Pesado (Heavy Tank Juggernaut)
window.HorseBodyRegistry = window.HorseBodyRegistry || {};

window.HorseBodyRegistry["heavy_tank"] = function buildHeavyTankHorse(cfg, scene) {
  const group = new THREE.Group();
  const mats = HorseBodyUtils.createMaterials(cfg);

  // 1. Tronco COLOSSAL (2.3m de largura — 50% maior que um cavalo normal!)
  const body = new THREE.Mesh(new THREE.BoxGeometry(2.3, 1.8, 3.6), mats.coatMat);
  body.position.y = 2.6;
  body.castShadow = true;
  group.add(body);

  // Ombreiras de Aço Blindadas com Espinhos
  const shoulderGeo = new THREE.BoxGeometry(0.5, 1.4, 1.6);
  const shoulderL = new THREE.Mesh(shoulderGeo, mats.metalMat);
  shoulderL.position.set(1.3, 0.2, 0.8);
  shoulderL.castShadow = true;
  body.add(shoulderL);

  const spikeL = new THREE.Mesh(new THREE.ConeGeometry(0.2, 0.6, 6), mats.metalMat);
  spikeL.position.set(1.6, 0.6, 0.8);
  spikeL.rotation.z = -Math.PI / 3;
  body.add(spikeL);

  const shoulderR = new THREE.Mesh(shoulderGeo, mats.metalMat);
  shoulderR.position.set(-1.3, 0.2, 0.8);
  shoulderR.castShadow = true;
  body.add(shoulderR);

  const spikeR = new THREE.Mesh(new THREE.ConeGeometry(0.2, 0.6, 6), mats.metalMat);
  spikeR.position.set(-1.6, 0.6, 0.8);
  spikeR.rotation.z = Math.PI / 3;
  body.add(spikeR);

  // Manta de sela gigante
  const saddle = new THREE.Mesh(new THREE.BoxGeometry(2.35, 1.1, 2.0), mats.secondaryMat);
  saddle.position.set(0, 0.42, -0.1);
  saddle.castShadow = true;
  body.add(saddle);

  // 2. Pescoço Maciço
  const neck = new THREE.Mesh(new THREE.BoxGeometry(1.2, 2.0, 1.3), mats.coatMat);
  neck.position.set(0, 1.35, 1.55);
  neck.rotation.x = -Math.PI / 4.8;
  neck.castShadow = true;
  body.add(neck);

  // Crina Densa Espessa
  const mane = new THREE.Mesh(new THREE.BoxGeometry(0.5, 2.1, 0.7), mats.maneMat);
  mane.position.set(0, 0.08, -0.65);
  neck.add(mane);

  // 3. Cabeça Enorme e Pesada
  const head = new THREE.Mesh(new THREE.BoxGeometry(1.0, 1.1, 1.6), mats.coatMat);
  head.position.set(0, 1.05, 0.5);
  head.rotation.x = Math.PI / 3.8;
  head.castShadow = true;
  neck.add(head);

  const muzzle = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.85, 0.95), mats.darkMat);
  muzzle.position.set(0, -0.12, 1.0);
  head.add(muzzle);

  const earGeo = new THREE.ConeGeometry(0.22, 0.45, 4);
  const earL = new THREE.Mesh(earGeo, mats.coatMat);
  earL.position.set(0.4, 0.65, -0.3);
  head.add(earL);
  const earR = new THREE.Mesh(earGeo, mats.coatMat);
  earR.position.set(-0.4, 0.65, -0.3);
  head.add(earR);

  // 4. Jóquei
  HorseBodyUtils.createJockey(body, mats.silkMat, mats.helmMat, cfg.color_hex);

  // 5. Patas Maciças de Clydesdale com Cascos Gigantes
  const legs = HorseBodyUtils.createLegs(body, mats.coatMat, mats.hoofMat, 1.45, 1.05);

  // 6. Cauda Grossa
  const tail = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.1, 2.0, 8), mats.maneMat);
  tail.position.set(0, 0.2, -1.9);
  tail.rotation.x = -Math.PI / 3;
  body.add(tail);

  // 7. Auras, Badge e Emblema
  const auras = HorseBodyUtils.createAuras(group);
  const badgeObj = HorseBodyUtils.createBadgeAndEmblem(group, cfg);

  scene.add(group);

  return {
    id: cfg.id,
    number: cfg.number,
    name: cfg.name,
    bodyModel: "heavy_tank",
    group: group,
    body: body,
    neck: neck,
    legs: legs,
    tail: tail,
    aura: auras.aura,
    mythicAura: auras.mythicAura,
    emblem: badgeObj.emblem,
    setEmblem: badgeObj.setEmblem,
    badge: badgeObj.badge,
    phase: Math.random() * Math.PI * 2,
  };
};
