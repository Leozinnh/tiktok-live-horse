// Modelo 9: Corcel do Trovão (Lightning Racer) — o RELÂMPAGO
// Velocista dourado carregado de eletricidade: raios cravados nos flancos,
// crina de espinhos incandescentes, cauda em ziguezague e arcos elétricos
// vivos correndo pelo corpo (animados em horses_view.js).
window.HorseBodyRegistry = window.HorseBodyRegistry || {};

window.HorseBodyRegistry["lightning_racer"] = function buildLightningRacerHorse(cfg, scene) {
  const group = new THREE.Group();
  const mats = HorseBodyUtils.createMaterials(cfg);

  // Pelagem dourada que devolve luz própria: o cavalo nunca fica "apagado",
  // nem na sombra da arquibancada.
  mats.coatMat.emissive = new THREE.Color(cfg.color_hex || "#f59e0b").lerp(new THREE.Color(0xffffff), 0.25);
  mats.coatMat.emissiveIntensity = 0.28;

  // Materiais de energia: brilham por conta própria (não dependem do sol)
  const boltMat = new THREE.MeshBasicMaterial({ color: 0xfde68a });        // raios cravados
  const sparkMat = new THREE.MeshBasicMaterial({ color: 0xfff7cc });       // crina/olhos
  const shoeMat = new THREE.MeshBasicMaterial({ color: 0xfcd34d });        // cascos incandescentes
  // Azul-gelo, não creme: sobre a pelagem dourada o arc elétrico creme
  // desaparecia (era quase a mesma cor do pano de fundo). O ciano é
  // complementar do dourado, então o raio lê à distância — inclusive na
  // câmera de perseguição, que é a mais usada na live.
  const arcoMat = new THREE.MeshBasicMaterial({
    color: 0xd6f0ff,
    transparent: true,
    opacity: 0.0,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });

  // 1. Tronco baixo, longo e afilado (mesma proporção de velocista do
  // slender_racer, para o cavalo manter a leitura de dragster na pista)
  const body = new THREE.Mesh(new THREE.BoxGeometry(1.4, 1.25, 3.9), mats.coatMat);
  body.position.y = 2.25;
  body.castShadow = true;
  group.add(body);

  // 1.1 Raios cravados nos flancos (3 por lado, em ziguezague)
  for (let lado = -1; lado <= 1; lado += 2) {
    for (let r = 0; r < 3; r++) {
      const z0 = 0.55 - r * 1.05;
      const raio = new THREE.Group();
      raio.position.set(lado * 0.72, 0.05, z0);

      const alta = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.62, 0.12), boltMat);
      alta.position.set(0, 0.22, 0);
      alta.rotation.z = lado * 0.55;
      raio.add(alta);

      const baixa = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.55, 0.12), boltMat);
      baixa.position.set(lado * 0.16, -0.28, 0);
      baixa.rotation.z = -lado * 0.55;
      raio.add(baixa);

      body.add(raio);
    }
  }

  // 1.2 Aerofólio de dragster na garupa
  const spoiler = new THREE.Group();
  spoiler.position.set(0, 0.85, -1.55);
  const spoilerWing = new THREE.Mesh(new THREE.BoxGeometry(1.85, 0.08, 0.45), mats.darkMat);
  spoilerWing.castShadow = true;
  spoiler.add(spoilerWing);
  for (let lado = -1; lado <= 1; lado += 2) {
    const endPlate = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.42, 0.5), boltMat);
    endPlate.position.set(lado * 0.92, 0.05, 0);
    spoiler.add(endPlate);
  }
  body.add(spoiler);

  // 1.3 Manta de sela
  const saddle = new THREE.Mesh(new THREE.BoxGeometry(1.42, 0.8, 2.2), mats.secondaryMat);
  saddle.position.set(0, 0.3, -0.1);
  saddle.castShadow = true;
  body.add(saddle);

  // 2. Pescoço esticado em cunha
  const neck = new THREE.Mesh(new THREE.BoxGeometry(0.7, 1.95, 0.95), mats.coatMat);
  neck.position.set(0, 1.05, 1.7);
  neck.rotation.x = -Math.PI / 4;
  neck.castShadow = true;
  body.add(neck);

  // 2.1 Crina de espinhos energéticos (guarda de energia subindo o pescoço)
  for (let i = 0; i < 7; i++) {
    const espinho = new THREE.Mesh(new THREE.ConeGeometry(0.11, 0.72 - i * 0.04, 4), boltMat);
    espinho.position.set(0, 0.62 - i * 0.22, -0.5 - i * 0.02);
    espinho.rotation.x = -0.75 - i * 0.07;
    neck.add(espinho);
  }

  // 3. Cabeça afilada + focinho + olhos incandescentes
  const head = new THREE.Mesh(new THREE.BoxGeometry(0.68, 0.72, 1.5), mats.coatMat);
  head.position.set(0, 0.82, 0.45);
  head.rotation.x = Math.PI / 4.8;
  head.castShadow = true;
  neck.add(head);

  const muzzle = new THREE.Mesh(new THREE.BoxGeometry(0.58, 0.55, 0.85), mats.darkMat);
  muzzle.position.set(0, -0.08, 0.95);
  head.add(muzzle);

  for (let lado = -1; lado <= 1; lado += 2) {
    const olho = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.12, 0.28), sparkMat);
    olho.position.set(lado * 0.3, 0.2, 0.42);
    head.add(olho);
  }

  const earGeo = new THREE.ConeGeometry(0.12, 0.5, 4);
  const earL = new THREE.Mesh(earGeo, boltMat);
  earL.position.set(0.25, 0.52, -0.3);
  head.add(earL);
  const earR = new THREE.Mesh(earGeo, boltMat);
  earR.position.set(-0.25, 0.52, -0.3);
  head.add(earR);

  // 4. Jóquei deitado + para-raios no capacete
  const jockeyGroup = new THREE.Group();
  jockeyGroup.position.set(0, 0.62, -0.2);

  const jBody = new THREE.Mesh(new THREE.BoxGeometry(0.66, 0.78, 0.7), mats.silkMat);
  jBody.position.y = 0.35;
  jBody.rotation.x = 0.65;
  jBody.castShadow = true;
  jockeyGroup.add(jBody);

  const helm = new THREE.Mesh(new THREE.SphereGeometry(0.31, 12, 12), mats.helmMat);
  helm.position.set(0, 0.86, 0.4);
  helm.castShadow = true;
  jockeyGroup.add(helm);

  const haste = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.5, 6), boltMat);
  haste.position.set(0, 1.2, 0.4);
  jockeyGroup.add(haste);

  const ponta = new THREE.Mesh(new THREE.ConeGeometry(0.13, 0.34, 4), sparkMat);
  ponta.position.set(0, 1.6, 0.4);
  jockeyGroup.add(ponta);
  body.add(jockeyGroup);

  // 5. Patas longas de velocista + caneleiras incandescentes
  const legs = HorseBodyUtils.createLegs(body, mats.coatMat, shoeMat, 0.86, 1.1);
  const patas = [legs.frontL, legs.frontR, legs.backL, legs.backR];
  for (let i = 0; i < patas.length; i++) {
    const caneleira = new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.3, 0.36), boltMat);
    caneleira.position.set(0, -0.62, 0.02);
    patas[i].lower.add(caneleira);
  }

  // 6. Cauda em ziguezague (raio descendo)
  const cauda = new THREE.Group();
  cauda.position.set(0, 0.2, -1.95);
  for (let i = 0; i < 4; i++) {
    const elo = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.16, 0.6), i === 3 ? boltMat : mats.maneMat);
    elo.position.set((i % 2 === 0 ? 1 : -1) * 0.16, -0.18 - i * 0.34, -i * 0.14);
    elo.rotation.y = (i % 2 === 0 ? 1 : -1) * 0.42;
    elo.rotation.x = -0.35;
    cauda.add(elo);
  }
  body.add(cauda);

  // 7. Arcos elétricos: feixes de faíscas que saltam de um lado ao outro do
  // corpo. As posições base são sorteadas por frame em horses_view.js, então
  // o desenho do raio nunca se repete.
  const arcos = [];
  const arcoGeo = new THREE.BoxGeometry(0.22, 0.22, 0.55);
  for (let a = 0; a < 3; a++) {
    const arcoGrupo = new THREE.Group();
    const segmentos = [];
    for (let i = 0; i < 6; i++) {
      const seg = new THREE.Mesh(arcoGeo, arcoMat);
      const base = new THREE.Vector3(
        (i % 2 === 0 ? 1 : -1) * (0.62 + (i % 3) * 0.2 + a * 0.14),
        2.0 + Math.sin(i * 1.9 + a * 2.1) * 0.95,
        1.7 - i * 0.68
      );
      seg.position.copy(base);
      seg.visible = false;
      arcoGrupo.add(seg);
      segmentos.push({ mesh: seg, base: base });
    }
    group.add(arcoGrupo);
    arcos.push({ grupo: arcoGrupo, segmentos: segmentos, timer: 0 });
  }

  // 8. Auras, Badge e Emblema
  const auras = HorseBodyUtils.createAuras(group, cfg);
  const badgeObj = HorseBodyUtils.createBadgeAndEmblem(group, cfg);

  scene.add(group);

  return {
    id: cfg.id,
    number: cfg.number,
    name: cfg.name,
    bodyModel: "lightning_racer",
    group: group,
    body: body,
    neck: neck,
    legs: legs,
    tail: cauda,
    aura: auras.aura,
    auraHaloMat: auras.auraHaloMat,
    auraBlades: auras.auraBlades,
    auraBladeMat: auras.auraBladeMat,
    mythicAura: auras.mythicAura,
    arcos: arcos,
    arcoMat: arcoMat,
    emblem: badgeObj.emblem,
    setEmblem: badgeObj.setEmblem,
    badge: badgeObj.badge,
    phase: Math.random() * Math.PI * 2,
  };
};
