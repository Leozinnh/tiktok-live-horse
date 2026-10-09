// Modelo 4: Cavalo Cibernético Mecha (Cyberpunk Mecha Steed)
window.HorseBodyRegistry = window.HorseBodyRegistry || {};

window.HorseBodyRegistry["cyber"] = function buildCyberHorse(cfg, scene) {
  const group = new THREE.Group();
  const mats = HorseBodyUtils.createMaterials(cfg);

  // Materiais Neon Cibernéticos com Emissive Alto
  const neonCyan = new THREE.MeshBasicMaterial({ color: 0x00f0ff });
  const neonThrusterFire = new THREE.MeshBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.85 });
  const cyberDarkMetal = new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.95, roughness: 0.15 });

  // 1. Tronco Mecha Angular Robótico
  const body = new THREE.Mesh(new THREE.BoxGeometry(1.7, 1.45, 3.3), cyberDarkMetal);
  body.position.y = 2.4;
  body.castShadow = true;
  group.add(body);

  // Turbinas a Jato Gigantes nos Flancos Traseiros
  const thrusterGeo = new THREE.CylinderGeometry(0.45, 0.55, 1.8, 12);
  
  // Turbina Esquerda
  const thrusterL = new THREE.Mesh(thrusterGeo, cyberDarkMetal);
  thrusterL.position.set(1.05, 0.35, -0.8);
  thrusterL.rotation.x = Math.PI / 2;
  body.add(thrusterL);

  const glowRingL = new THREE.Mesh(new THREE.TorusGeometry(0.48, 0.08, 8, 16), neonCyan);
  glowRingL.position.set(1.05, 0.35, -1.7);
  body.add(glowRingL);

  const flameL = new THREE.Mesh(new THREE.ConeGeometry(0.4, 1.4, 12), neonThrusterFire);
  flameL.position.set(1.05, 0.35, -2.4);
  flameL.rotation.x = -Math.PI / 2;
  body.add(flameL);

  // Turbina Direita
  const thrusterR = new THREE.Mesh(thrusterGeo, cyberDarkMetal);
  thrusterR.position.set(-1.05, 0.35, -0.8);
  thrusterR.rotation.x = Math.PI / 2;
  body.add(thrusterR);

  const glowRingR = new THREE.Mesh(new THREE.TorusGeometry(0.48, 0.08, 8, 16), neonCyan);
  glowRingR.position.set(-1.05, 0.35, -1.7);
  body.add(glowRingR);

  const flameR = new THREE.Mesh(new THREE.ConeGeometry(0.4, 1.4, 12), neonThrusterFire);
  flameR.position.set(-1.05, 0.35, -2.4);
  flameR.rotation.x = -Math.PI / 2;
  body.add(flameR);

  // Faixa de Circuito Neon no Dorso
  const spineLine = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.1, 3.2), neonCyan);
  spineLine.position.set(0, 0.74, 0);
  body.add(spineLine);

  // Manta de sela de fibra de carbono
  const saddle = new THREE.Mesh(new THREE.BoxGeometry(1.72, 0.9, 1.6), mats.coatMat);
  saddle.position.set(0, 0.3, -0.1);
  saddle.castShadow = true;
  body.add(saddle);

  // 2. Pescoço com Conduítes Cibernéticos
  const neck = new THREE.Mesh(new THREE.BoxGeometry(0.82, 1.8, 1.05), cyberDarkMetal);
  neck.position.set(0, 1.2, 1.4);
  neck.rotation.x = -Math.PI / 5;
  neck.castShadow = true;
  body.add(neck);

  // Crina de Feixe de LED Neon Ciano Brilhante
  const mane = new THREE.Mesh(new THREE.BoxGeometry(0.25, 2.0, 0.45), neonCyan);
  mane.position.set(0, 0.05, -0.55);
  neck.add(mane);

  // 3. Cabeça Mecha com Viseira Holográfica Iluminada
  const head = new THREE.Mesh(new THREE.BoxGeometry(0.78, 0.88, 1.45), cyberDarkMetal);
  head.position.set(0, 0.9, 0.4);
  head.rotation.x = Math.PI / 4;
  head.castShadow = true;
  neck.add(head);

  // Viseira Neon Grande e Chamativa
  const visor = new THREE.Mesh(new THREE.BoxGeometry(0.82, 0.35, 0.8), neonCyan);
  visor.position.set(0, 0.22, 0.3);
  head.add(visor);

  const muzzle = new THREE.Mesh(new THREE.BoxGeometry(0.68, 0.68, 0.82), mats.darkMat);
  muzzle.position.set(0, -0.1, 0.92);
  head.add(muzzle);

  // Antenas Laser Sensoriais
  const earGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.8, 8);
  const earL = new THREE.Mesh(earGeo, neonCyan);
  earL.position.set(0.3, 0.7, -0.3);
  head.add(earL);
  const earR = new THREE.Mesh(earGeo, neonCyan);
  earR.position.set(-0.3, 0.7, -0.3);
  head.add(earR);

  // 4. Piloto Cibernético
  HorseBodyUtils.createJockey(body, mats.darkMat, mats.helmMat, cfg.color_hex);

  // 5. Patas com Articulações Hidráulicas Neon
  const legs = HorseBodyUtils.createLegs(body, cyberDarkMetal, neonCyan);

  // 6. Cauda com Feixes de Fibra Óptica
  const tail = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.04, 1.8, 6), neonCyan);
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
    bodyModel: "cyber",
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
