// Modelo 6: Unicórnio Místico Radiante (Rainbow Prism Unicorn)
window.HorseBodyRegistry = window.HorseBodyRegistry || {};

window.HorseBodyRegistry["unicorn"] = function buildUnicornHorse(cfg, scene) {
  const group = new THREE.Group();
  const mats = HorseBodyUtils.createMaterials(cfg);

  // Paleta de Cores do Arco-Íris Mágico
  const rainbowColors = [
    0xf43f5e, // Rosa Magenta
    0xa855f7, // Roxo Violeta
    0x06b6d4, // Ciano Elétrico
    0x10b981, // Verde Esmeralda
    0xfacc15, // Amarelo Dourado
    0xffffff  // Cristal Diamante
  ];

  // 1. TEXTURA PROCEDURAL DO CHIFRE ARCO-ÍRIS ESPIRAL
  function createRainbowHornTexture() {
    const canvas = document.createElement("canvas");
    canvas.width = 256;
    canvas.height = 512;
    const ctx = canvas.getContext("2d");

    // Gradiente Vertical Arco-Íris Iluminado
    const grad = ctx.createLinearGradient(0, 512, 0, 0);
    grad.addColorStop(0.00, "#f43f5e"); // Rosa Magenta base
    grad.addColorStop(0.20, "#ec4899"); // Rosa choque
    grad.addColorStop(0.40, "#a855f7"); // Roxo Violeta
    grad.addColorStop(0.60, "#06b6d4"); // Ciano celestial
    grad.addColorStop(0.80, "#10b981"); // Verde esmeralda
    grad.addColorStop(0.92, "#facc15"); // Ouro radiante
    grad.addColorStop(1.00, "#ffffff"); // Ponta de diamante

    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 256, 512);

    // Faixas Diagonais Brilhantes Espirais (Efeito de brocado perolado)
    ctx.strokeStyle = "rgba(255, 255, 255, 0.75)";
    ctx.lineWidth = 18;
    for (let y = -256; y < 768; y += 48) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(256, y + 128);
      ctx.stroke();
    }

    const tex = new THREE.CanvasTexture(canvas);
    if (THREE.sRGBEncoding) tex.encoding = THREE.sRGBEncoding;
    return tex;
  }

  const rainbowHornTex = createRainbowHornTexture();

  const rainbowHornMat = new THREE.MeshStandardMaterial({
    map: rainbowHornTex,
    emissive: new THREE.Color(0xffffff),
    emissiveMap: rainbowHornTex,
    emissiveIntensity: 0.95, // Brilho próprio bem intenso!
    metalness: 0.85,
    roughness: 0.15
  });

  // 1. Tronco Nobre com Manta de Sela Mágica
  const body = new THREE.Mesh(new THREE.BoxGeometry(1.55, 1.38, 3.15), mats.coatMat);
  body.position.y = 2.4;
  body.castShadow = true;
  group.add(body);

  // Manta de sela com borda dourada e degradê
  const saddle = new THREE.Mesh(new THREE.BoxGeometry(1.64, 0.9, 1.75), mats.secondaryMat);
  saddle.position.set(0, 0.3, -0.1);
  saddle.castShadow = true;
  body.add(saddle);

  // 2. Pescoço com Crina em Mechas Coloridas (Arco-Íris)
  const neck = new THREE.Mesh(new THREE.BoxGeometry(0.75, 1.85, 0.95), mats.coatMat);
  neck.position.set(0, 1.25, 1.4);
  neck.rotation.x = -Math.PI / 5.2;
  neck.castShadow = true;
  body.add(neck);

  // CRINA ARCO-ÍRIS MULTICOLORIDA EM 4 MECHAS
  const maneColors = [0xf472b6, 0xc084fc, 0x38bdf8, 0x4ade80];
  for (let m = 0; m < 4; m++) {
    const strandMat = new THREE.MeshStandardMaterial({
      color: maneColors[m],
      roughness: 0.4,
      metalness: 0.2
    });
    const strand = new THREE.Mesh(
      new THREE.BoxGeometry(0.32, 0.52, 0.55),
      strandMat
    );
    strand.position.set(0, 0.75 - m * 0.48, -0.55);
    strand.castShadow = true;
    neck.add(strand);
  }

  // 3. Cabeça do Unicórnio
  const head = new THREE.Mesh(new THREE.BoxGeometry(0.72, 0.82, 1.38), mats.coatMat);
  head.position.set(0, 0.95, 0.4);
  head.rotation.x = Math.PI / 4.2;
  head.castShadow = true;
  neck.add(head);

  // CHIFRE ARCO-ÍRIS ESPIRAL MONUMENTAL (1.85 METROS DE PURO BRILHO)
  const hornGroup = new THREE.Group();
  hornGroup.position.set(0, 0.85, 0.55);
  hornGroup.rotation.x = Math.PI / 4.2;

  // Cone Principal do Chifre com textura Arco-Íris
  const hornGeo = new THREE.ConeGeometry(0.2, 1.85, 16);
  const hornMesh = new THREE.Mesh(hornGeo, rainbowHornMat);
  hornMesh.position.y = 0.92;
  hornMesh.castShadow = true;
  hornGroup.add(hornMesh);

  // Contas / Gemas Coloridas Espiralando ao Longo do Chifre
  const numGems = 9;
  for (let g = 0; g < numGems; g++) {
    const t = g / (numGems - 1); // 0 a 1 da base ao topo
    const angle = t * Math.PI * 4.5; // Espiral de mais de 2 voltas completas
    const radius = 0.22 * (1.0 - t * 0.7);
    const gemY = 0.15 + t * 1.6;

    const gemMat = new THREE.MeshBasicMaterial({
      color: rainbowColors[g % rainbowColors.length]
    });
    const gem = new THREE.Mesh(new THREE.SphereGeometry(0.065, 8, 8), gemMat);
    gem.position.set(
      Math.cos(angle) * radius,
      gemY,
      Math.sin(angle) * radius
    );
    hornGroup.add(gem);
  }

  // Estrela / Prisma Cristalino Radiante na Ponta do Chifre
  const starTipMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
  const starTip = new THREE.Mesh(new THREE.OctahedronGeometry(0.22), starTipMat);
  starTip.position.y = 1.95;
  hornGroup.add(starTip);

  // Pequeno anel de luz mágica pulsante no topo
  const tipRingMat = new THREE.MeshBasicMaterial({ color: 0xfacc15, wireframe: true });
  const tipRing = new THREE.Mesh(new THREE.TorusGeometry(0.28, 0.04, 6, 16), tipRingMat);
  tipRing.rotation.x = Math.PI / 2;
  tipRing.position.y = 1.95;
  hornGroup.add(tipRing);

  head.add(hornGroup);

  // Focinho Suave
  const muzzle = new THREE.Mesh(new THREE.BoxGeometry(0.62, 0.62, 0.78), mats.secondaryMat);
  muzzle.position.set(0, -0.1, 0.9);
  head.add(muzzle);

  // Orelhas Nobres
  const earGeo = new THREE.ConeGeometry(0.16, 0.52, 4);
  const earL = new THREE.Mesh(earGeo, mats.coatMat);
  earL.position.set(0.28, 0.55, -0.3);
  head.add(earL);
  const earR = new THREE.Mesh(earGeo, mats.coatMat);
  earR.position.set(-0.28, 0.55, -0.3);
  head.add(earR);

  // 4. Jóquei Místico Encantado
  HorseBodyUtils.createJockey(body, mats.silkMat, mats.helmMat, cfg.color_hex);

  // 5. Patas com Cascos Místicos Dourados-Cristalinos
  const hoofCrystalMat = new THREE.MeshStandardMaterial({
    color: 0xfde047,
    emissive: 0xf59e0b,
    emissiveIntensity: 0.5,
    metalness: 0.9,
    roughness: 0.1
  });
  const legs = HorseBodyUtils.createLegs(body, mats.coatMat, hoofCrystalMat, 0.98, 1.02);

  // 6. CAUDA EM MECHAS ARCO-ÍRIS
  const tailGroup = new THREE.Group();
  tailGroup.position.set(0, 0.25, -1.75);
  tailGroup.rotation.x = -Math.PI / 3.4;

  const tailColors = [0xf472b6, 0xa855f7, 0x38bdf8];
  for (let tc = 0; tc < 3; tc++) {
    const tMat = new THREE.MeshStandardMaterial({
      color: tailColors[tc],
      roughness: 0.35,
      metalness: 0.2
    });
    const tailStrand = new THREE.Mesh(
      new THREE.CylinderGeometry(0.09, 0.02, 2.1, 6),
      tMat
    );
    tailStrand.position.set((tc - 1) * 0.14, 0, (tc - 1) * 0.05);
    tailGroup.add(tailStrand);
  }
  body.add(tailGroup);

  // 7. Auras, Badge e Emblema
  const auras = HorseBodyUtils.createAuras(group);
  const badgeObj = HorseBodyUtils.createBadgeAndEmblem(group, cfg);

  scene.add(group);

  return {
    id: cfg.id,
    number: cfg.number,
    name: cfg.name,
    bodyModel: "unicorn",
    group: group,
    body: body,
    neck: neck,
    legs: legs,
    tail: tailGroup,
    aura: auras.aura,
    mythicAura: auras.mythicAura,
    emblem: badgeObj.emblem,
    setEmblem: badgeObj.setEmblem,
    badge: badgeObj.badge,
    phase: Math.random() * Math.PI * 2,
  };
};
