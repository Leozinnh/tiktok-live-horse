// Modelo 8: Velocista Aerodinâmico Dragster (Slender Aero Racer)
window.HorseBodyRegistry = window.HorseBodyRegistry || {};

window.HorseBodyRegistry["slender_racer"] = function buildSlenderRacerHorse(cfg, scene) {
  const group = new THREE.Group();
  const mats = HorseBodyUtils.createMaterials(cfg);

  // 1. Tronco Baixo, Longo e Aerodinâmico (3.8m de Comprimento!)
  const body = new THREE.Mesh(new THREE.BoxGeometry(1.35, 1.2, 3.8), mats.coatMat);
  body.position.y = 2.25;
  body.castShadow = true;
  group.add(body);

  // AEROFÓLIO / SPOILER DE CORRIDA NA GARUPA (Estilo F1 / Dragster)
  const spoilerGroup = new THREE.Group();
  spoilerGroup.position.set(0, 0.85, -1.5);

  // Asa principal
  const spoilerWing = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.08, 0.45), mats.darkMat);
  spoilerWing.castShadow = true;
  spoilerGroup.add(spoilerWing);

  // Aletas laterais
  const endPlateL = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.35, 0.5), mats.secondaryMat);
  endPlateL.position.set(0.9, 0, 0);
  spoilerGroup.add(endPlateL);

  const endPlateR = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.35, 0.5), mats.secondaryMat);
  endPlateR.position.set(-0.9, 0, 0);
  spoilerGroup.add(endPlateR);

  // Suportes verticais
  const strutL = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.5, 0.15), mats.darkMat);
  strutL.position.set(0.45, -0.25, 0);
  spoilerGroup.add(strutL);

  const strutR = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.5, 0.15), mats.darkMat);
  strutR.position.set(-0.45, -0.25, 0);
  spoilerGroup.add(strutR);

  body.add(spoilerGroup);

  // Manta de sela aerodinâmica afilada
  const saddle = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.75, 2.2), mats.secondaryMat);
  saddle.position.set(0, 0.28, -0.1);
  saddle.castShadow = true;
  body.add(saddle);

  // 2. Pescoço Inclinado em Cunha (Aerodinâmica Agressiva)
  const neck = new THREE.Mesh(new THREE.BoxGeometry(0.68, 1.9, 0.9), mats.coatMat);
  neck.position.set(0, 1.05, 1.65);
  neck.rotation.x = -Math.PI / 3.9;
  neck.castShadow = true;
  body.add(neck);

  // Crina aerodinâmica rente
  const mane = new THREE.Mesh(new THREE.BoxGeometry(0.2, 1.9, 0.35), mats.maneMat);
  mane.position.set(0, 0.05, -0.5);
  neck.add(mane);

  // 3. Cabeça Fina e Afilada em Ponta de Flecha
  const head = new THREE.Mesh(new THREE.BoxGeometry(0.65, 0.72, 1.5), mats.coatMat);
  head.position.set(0, 0.8, 0.45);
  head.rotation.x = Math.PI / 4.8;
  head.castShadow = true;
  neck.add(head);

  const muzzle = new THREE.Mesh(new THREE.BoxGeometry(0.55, 0.55, 0.85), mats.darkMat);
  muzzle.position.set(0, -0.08, 0.95);
  head.add(muzzle);

  const earGeo = new THREE.ConeGeometry(0.12, 0.45, 4);
  const earL = new THREE.Mesh(earGeo, mats.coatMat);
  earL.position.set(0.25, 0.5, -0.3);
  head.add(earL);
  const earR = new THREE.Mesh(earGeo, mats.coatMat);
  earR.position.set(-0.25, 0.5, -0.3);
  head.add(earR);

  // 4. Jóquei Totalmente Deitado no Dorso
  const jockeyGroup = new THREE.Group();
  jockeyGroup.position.set(0, 0.65, -0.2);

  const jBody = new THREE.Mesh(new THREE.BoxGeometry(0.65, 0.75, 0.7), mats.silkMat);
  jBody.position.y = 0.35;
  jBody.rotation.x = 0.65;
  jBody.castShadow = true;
  jockeyGroup.add(jBody);

  const helm = new THREE.Mesh(new THREE.SphereGeometry(0.3, 12, 12), mats.helmMat);
  helm.position.set(0, 0.85, 0.4);
  helm.castShadow = true;
  jockeyGroup.add(helm);
  body.add(jockeyGroup);

  // 5. Patas Longas de Velocista
  const legs = HorseBodyUtils.createLegs(body, mats.coatMat, mats.hoofMat, 0.88, 1.12);

  // 6. Cauda Rente
  const tail = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.02, 1.5, 6), mats.maneMat);
  tail.position.set(0, 0.15, -1.95);
  tail.rotation.x = -Math.PI / 3.8;
  body.add(tail);

  // 7. Auras, Badge e Emblema
  const auras = HorseBodyUtils.createAuras(group);
  const badgeObj = HorseBodyUtils.createBadgeAndEmblem(group, cfg);

  scene.add(group);

  return {
    id: cfg.id,
    number: cfg.number,
    name: cfg.name,
    bodyModel: "slender_racer",
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
