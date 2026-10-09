// Modelo 2: Cavalo de Guerra Blindado (Armored Warhorse)
window.HorseBodyRegistry = window.HorseBodyRegistry || {};

window.HorseBodyRegistry["armored"] = function buildArmoredHorse(cfg, scene) {
  const group = new THREE.Group();
  const mats = HorseBodyUtils.createMaterials(cfg);

  // 1. Tronco Robusto
  const body = new THREE.Mesh(new THREE.BoxGeometry(1.7, 1.45, 3.3), mats.coatMat);
  body.position.y = 2.4;
  body.castShadow = true;
  group.add(body);

  // Placa de Armadura Peitoral (Gorget)
  const chestPlate = new THREE.Mesh(new THREE.BoxGeometry(1.76, 1.1, 1.2), mats.metalMat);
  chestPlate.position.set(0, 0.1, 1.1);
  chestPlate.castShadow = true;
  body.add(chestPlate);

  // Placa de Armadura na Garupa
  const rumpPlate = new THREE.Mesh(new THREE.BoxGeometry(1.74, 0.9, 1.3), mats.metalMat);
  rumpPlate.position.set(0, 0.25, -1.0);
  rumpPlate.castShadow = true;
  body.add(rumpPlate);

  // Manta de sela nobre
  const saddle = new THREE.Mesh(new THREE.BoxGeometry(1.75, 0.95, 1.4), mats.secondaryMat);
  saddle.position.set(0, 0.32, 0.0);
  saddle.castShadow = true;
  body.add(saddle);

  // 2. Pescoço com Cobre-pescoço (Crinet)
  const neck = new THREE.Mesh(new THREE.BoxGeometry(0.85, 1.8, 1.1), mats.coatMat);
  neck.position.set(0, 1.2, 1.4);
  neck.rotation.x = -Math.PI / 5;
  neck.castShadow = true;
  body.add(neck);

  const crinet = new THREE.Mesh(new THREE.BoxGeometry(0.9, 1.6, 0.45), mats.metalMat);
  crinet.position.set(0, 0.08, -0.45);
  neck.add(crinet);

  // 3. Cabeça com Chanfron de Aço
  const head = new THREE.Mesh(new THREE.BoxGeometry(0.78, 0.88, 1.4), mats.coatMat);
  head.position.set(0, 0.9, 0.4);
  head.rotation.x = Math.PI / 4;
  head.castShadow = true;
  neck.add(head);

  // Chanfron metálico na testa
  const chanfron = new THREE.Mesh(new THREE.BoxGeometry(0.82, 0.45, 1.1), mats.metalMat);
  chanfron.position.set(0, 0.25, 0.2);
  head.add(chanfron);

  const muzzle = new THREE.Mesh(new THREE.BoxGeometry(0.65, 0.65, 0.8), mats.darkMat);
  muzzle.position.set(0, -0.1, 0.9);
  head.add(muzzle);

  // Orelhas blindadas
  const earGeo = new THREE.ConeGeometry(0.18, 0.45, 4);
  const earL = new THREE.Mesh(earGeo, mats.metalMat);
  earL.position.set(0.3, 0.5, -0.3);
  head.add(earL);
  const earR = new THREE.Mesh(earGeo, mats.metalMat);
  earR.position.set(-0.3, 0.5, -0.3);
  head.add(earR);

  // Penacho de Cavaleiro Medieval no Topo da Cabeça
  const plumeMat = new THREE.MeshBasicMaterial({ color: 0xdc2626 });
  const plume = new THREE.Mesh(new THREE.ConeGeometry(0.2, 0.9, 6), plumeMat);
  plume.position.set(0, 0.85, 0.1);
  plume.rotation.x = -Math.PI / 6;
  head.add(plume);

  // 4. Jóquei de Armadura
  HorseBodyUtils.createJockey(body, mats.metalMat, mats.helmMat, cfg.color_hex);

  // 5. Patas com Caneleiras de Metal
  const legs = HorseBodyUtils.createLegs(body, mats.coatMat, mats.metalMat, 1.05, 1.0);

  // 6. Cauda
  const tail = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.05, 1.6, 6), mats.maneMat);
  tail.position.set(0, 0.2, -1.75);
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
    bodyModel: "armored",
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
