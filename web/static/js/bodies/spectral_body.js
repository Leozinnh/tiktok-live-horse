// Modelo 7: Fantasma Espectral Etéreo (Spectral Phantom Steed)
window.HorseBodyRegistry = window.HorseBodyRegistry || {};

window.HorseBodyRegistry["spectral"] = function buildSpectralHorse(cfg, scene) {
  const group = new THREE.Group();
  const primaryColor = new THREE.Color(cfg.color_hex || "#8b5cf6");

  // Materiais Espectrais com Transparência e Brilho Próprio
  const spectralMat = new THREE.MeshStandardMaterial({
    color: primaryColor,
    emissive: primaryColor,
    emissiveIntensity: 0.5,
    transparent: true,
    opacity: 0.65,
    roughness: 0.2,
    metalness: 0.4
  });

  const ghostRibMat = new THREE.MeshBasicMaterial({
    color: 0xc084fc,
    transparent: true,
    opacity: 0.85
  });

  const glowEyeMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff });

  // 1. Tronco Etéreo Translúcido
  const body = new THREE.Mesh(new THREE.BoxGeometry(1.6, 1.38, 3.2), spectralMat);
  body.position.y = 2.45;
  group.add(body);

  // Arcos das Costelas Espectrais
  for (let r = -1.0; r <= 1.0; r += 0.45) {
    const rib = new THREE.Mesh(new THREE.BoxGeometry(1.72, 1.0, 0.16), ghostRibMat);
    rib.position.set(0, 0.1, r);
    body.add(rib);
  }

  // 2. Pescoço Espectral
  const neck = new THREE.Mesh(new THREE.BoxGeometry(0.78, 1.8, 1.0), spectralMat);
  neck.position.set(0, 1.2, 1.4);
  neck.rotation.x = -Math.PI / 5;
  body.add(neck);

  const mane = new THREE.Mesh(new THREE.BoxGeometry(0.28, 2.1, 0.6), ghostRibMat);
  mane.position.set(0, 0.05, -0.55);
  neck.add(mane);

  // 3. Cabeça Fantasmagórica com Olhos Cyan Incandescentes
  const head = new THREE.Mesh(new THREE.BoxGeometry(0.75, 0.85, 1.4), spectralMat);
  head.position.set(0, 0.9, 0.4);
  head.rotation.x = Math.PI / 4;
  neck.add(head);

  // Olhos Espectrais Grandes
  const eyeL = new THREE.Mesh(new THREE.SphereGeometry(0.18, 12, 12), glowEyeMat);
  eyeL.position.set(0.4, 0.25, 0.45);
  head.add(eyeL);

  const eyeR = new THREE.Mesh(new THREE.SphereGeometry(0.18, 12, 12), glowEyeMat);
  eyeR.position.set(-0.4, 0.25, 0.45);
  head.add(eyeR);

  // 4. Cavaleiro Fantasma
  HorseBodyUtils.createJockey(body, spectralMat, ghostRibMat, cfg.color_hex);

  // 5. Patas com Cascos Etéreos
  const legs = HorseBodyUtils.createLegs(body, spectralMat, glowEyeMat);

  // 6. Cauda Fluida de Ectoplasma
  const tail = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.02, 2.2, 6), ghostRibMat);
  tail.position.set(0, 0.2, -1.8);
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
    bodyModel: "spectral",
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
