// Modelo 1: Cavalo Puro Sangue Clássico de Turfe
window.HorseBodyRegistry = window.HorseBodyRegistry || {};

window.HorseBodyRegistry["classic"] = function buildClassicHorse(cfg, scene) {
  const group = new THREE.Group();
  const mats = HorseBodyUtils.createMaterials(cfg);

  // 1. Tronco Atlético
  const bodyGeo = new THREE.BoxGeometry(1.6, 1.4, 3.2);
  const body = new THREE.Mesh(bodyGeo, mats.coatMat);
  body.position.y = 2.4;
  body.castShadow = true;
  group.add(body);

  // Manta de sela
  const saddle = new THREE.Mesh(new THREE.BoxGeometry(1.64, 0.9, 1.8), mats.secondaryMat);
  saddle.position.set(0, 0.3, -0.1);
  saddle.castShadow = true;
  body.add(saddle);

  // 2. Pescoço e Crina
  const neck = new THREE.Mesh(new THREE.BoxGeometry(0.8, 1.8, 1.0), mats.coatMat);
  neck.position.set(0, 1.2, 1.4);
  neck.rotation.x = -Math.PI / 5;
  neck.castShadow = true;
  body.add(neck);

  const mane = new THREE.Mesh(new THREE.BoxGeometry(0.25, 1.8, 0.4), mats.maneMat);
  mane.position.set(0, 0.05, -0.55);
  neck.add(mane);

  // 3. Cabeça e Orelhas
  const head = new THREE.Mesh(new THREE.BoxGeometry(0.75, 0.85, 1.4), mats.coatMat);
  head.position.set(0, 0.9, 0.4);
  head.rotation.x = Math.PI / 4;
  head.castShadow = true;
  neck.add(head);

  const muzzle = new THREE.Mesh(new THREE.BoxGeometry(0.65, 0.65, 0.8), mats.darkMat);
  muzzle.position.set(0, -0.1, 0.9);
  head.add(muzzle);

  const earGeo = new THREE.ConeGeometry(0.18, 0.45, 4);
  const earL = new THREE.Mesh(earGeo, mats.coatMat);
  earL.position.set(0.3, 0.5, -0.3);
  head.add(earL);
  const earR = new THREE.Mesh(earGeo, mats.coatMat);
  earR.position.set(-0.3, 0.5, -0.3);
  head.add(earR);

  // 4. Jóquei
  HorseBodyUtils.createJockey(body, mats.silkMat, mats.helmMat, cfg.color_hex);

  // 5. Patas
  const legs = HorseBodyUtils.createLegs(body, mats.coatMat, mats.hoofMat);

  // 6. Cauda
  const tail = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.04, 1.6, 6), mats.maneMat);
  tail.position.set(0, 0.2, -1.7);
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
    bodyModel: "classic",
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
