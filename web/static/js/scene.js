class TrackScene {
  constructor(containerElement) {
    this.container = containerElement;
    this.scene = null;
    this.camera = null;
    this.renderer = null;

    // Iluminação
    this.ambientLight = null;
    this.sunLight = null;
    this.floodlights = [];

    // Parâmetros da pista (compatíveis com game/physics.py)
    this.straightLen = 300.0;
    this.curveLen = 200.0;
    this.radius = 200.0 / Math.PI; // ~63.66m
    this.trackWidth = 22.0;

    // Objetos animados
    this.flags = [];
    this.crowdMeshes = [];
    this.clouds = [];
    this.fountains = [];
    this.finishGate = null;
    this.startGate = null;

    this.currentWeather = "CLEAR";
    this.init();
  }

  init() {
    const width = this.container.clientWidth || 1080;
    const height = this.container.clientHeight || 1920;

    // 1. Cena e Fog Atmosférico
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x7dd3fc);
    this.scene.fog = new THREE.FogExp2(0xbae6fd, 0.0014);

    // 2. Câmera
    this.camera = new THREE.PerspectiveCamera(48, width / height, 1.0, 1800.0);
    this.camera.position.set(-210, 36, 140);
    this.camera.lookAt(new THREE.Vector3(-145, 4, 75));

    // 3. Renderer com Suporte a Sombras Suaves
    this.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.05;
    this.container.appendChild(this.renderer.domElement);

    // 4. Configuração de Iluminação
    this.setupLighting();

    // 5. Construção do Hipódromo Monumental
    this.buildGroundAndInfield();
    this.buildTrack();
    this.buildLaneMarkings();
    this.buildFencesAndHedges();
    this.buildDistanceMarkers();
    this.buildJumbotron();
    this.buildGrandstands();
    this.buildTreesAndNature();
    this.buildClouds();
    this.buildStartAndFinishGates();
    this.buildStadiumTowers();

    window.addEventListener("resize", () => this.onResize());
  }

  setupLighting() {
    this.ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    this.scene.add(this.ambientLight);

    this.sunLight = new THREE.DirectionalLight(0xfffaed, 1.3);
    this.sunLight.position.set(-160, 240, 190);
    this.sunLight.castShadow = true;
    this.sunLight.shadow.mapSize.width = 2048;
    this.sunLight.shadow.mapSize.height = 2048;
    this.sunLight.shadow.camera.near = 10;
    this.sunLight.shadow.camera.far = 700;
    const d = 260;
    this.sunLight.shadow.camera.left = -d;
    this.sunLight.shadow.camera.right = d;
    this.sunLight.shadow.camera.top = d;
    this.sunLight.shadow.camera.bottom = -d;
    this.sunLight.shadow.bias = -0.0004;
    this.scene.add(this.sunLight);

    // 4 Refletores esportivos nos cantos do estádio
    const towerPositions = [
      [-180, 65, 130],
      [180, 65, 130],
      [180, 65, -130],
      [-180, 65, -130],
    ];

    towerPositions.forEach((pos) => {
      const spot = new THREE.SpotLight(0xffffff, 0.0);
      spot.position.set(pos[0], pos[1], pos[2]);
      spot.target.position.set(pos[0] * 0.45, 0, pos[2] * 0.45);
      spot.angle = Math.PI / 4;
      spot.penumbra = 0.5;
      spot.distance = 400;
      this.scene.add(spot);
      this.scene.add(spot.target);
      this.floodlights.push(spot);
    });
  }

  buildGroundAndInfield() {
    // 1. Gramado Base Gigante
    const grassGeo = new THREE.PlaneGeometry(1600, 1400, 32, 32);
    const grassMat = new THREE.MeshLambertMaterial({ color: 0x226926, side: THREE.DoubleSide });
    const grass = new THREE.Mesh(grassGeo, grassMat);
    grass.rotation.x = -Math.PI / 2;
    grass.position.y = -0.15;
    grass.receiveShadow = true;
    this.scene.add(grass);

    // 2. Gramado Infield Central Texturizado com Faixas de Corte
    for (let strip = -120; strip <= 120; strip += 20) {
      const stripGeo = new THREE.PlaneGeometry(280, 18);
      const col = (Math.abs(strip) % 40 === 0) ? 0x2e7d32 : 0x256e29;
      const stripMat = new THREE.MeshLambertMaterial({ color: col, side: THREE.DoubleSide });
      const stripMesh = new THREE.Mesh(stripGeo, stripMat);
      stripMesh.rotation.x = -Math.PI / 2;
      stripMesh.position.set(0, -0.08, strip * 0.4);
      stripMesh.receiveShadow = true;
      this.scene.add(stripMesh);
    }

    // 3. Lago Ornamental no Infield
    const lakeGeo = new THREE.RingGeometry(18, 42, 36);
    const lakeMat = new THREE.MeshStandardMaterial({
      color: 0x0284c7,
      roughness: 0.08,
      metalness: 0.85
    });
    const lake = new THREE.Mesh(lakeGeo, lakeMat);
    lake.rotation.x = -Math.PI / 2;
    lake.position.set(-20, 0.05, 0);
    this.scene.add(lake);

    // Ilha central do lago com fonte
    const islandGeo = new THREE.CylinderGeometry(16, 17, 0.4, 24);
    const islandMat = new THREE.MeshLambertMaterial({ color: 0x166534 });
    const island = new THREE.Mesh(islandGeo, islandMat);
    island.position.set(-20, 0.15, 0);
    this.scene.add(island);

    // Fonte de água central decorativa
    const fountainBase = new THREE.Mesh(
      new THREE.CylinderGeometry(3, 3.5, 1.2, 16),
      new THREE.MeshStandardMaterial({ color: 0xe2e8f0, roughness: 0.3 })
    );
    fountainBase.position.set(-20, 0.8, 0);
    this.scene.add(fountainBase);

    // Jatos de água da fonte
    for (let j = 0; j < 6; j++) {
      const jet = new THREE.Mesh(
        new THREE.CylinderGeometry(0.12, 0.2, 3.5, 8),
        new THREE.MeshBasicMaterial({ color: 0xbae6fd, transparent: true, opacity: 0.75 })
      );
      const angle = (j / 6) * Math.PI * 2;
      jet.position.set(-20 + Math.cos(angle) * 1.8, 2.2, Math.sin(angle) * 1.8);
      jet.rotation.x = 0.2 * Math.sin(angle);
      jet.rotation.z = 0.2 * Math.cos(angle);
      this.scene.add(jet);
      this.fountains.push(jet);
    }
  }

  buildTrack() {
    const pointsInner = [];
    const pointsOuter = [];
    const segments = 180;
    const halfStraight = this.straightLen / 2.0;

    for (let i = 0; i <= segments; i++) {
      const t = i / segments;
      const dist = t * (2 * this.straightLen + 2 * this.curveLen);
      let x = 0, z = 0, nx = 0, nz = 0;

      if (dist <= this.straightLen) {
        const u = dist / this.straightLen;
        x = -halfStraight + u * this.straightLen;
        z = this.radius;
        nx = 0; nz = 1;
      } else if (dist <= this.straightLen + this.curveLen) {
        const u = (dist - this.straightLen) / this.curveLen;
        const angle = Math.PI / 2 - u * Math.PI;
        x = halfStraight + this.radius * Math.cos(angle);
        z = this.radius * Math.sin(angle);
        nx = Math.cos(angle); nz = Math.sin(angle);
      } else if (dist <= 2 * this.straightLen + this.curveLen) {
        const u = (dist - (this.straightLen + this.curveLen)) / this.straightLen;
        x = halfStraight - u * this.straightLen;
        z = -this.radius;
        nx = 0; nz = -1;
      } else {
        const u = (dist - (2 * this.straightLen + this.curveLen)) / this.curveLen;
        const angle = -Math.PI / 2 - u * Math.PI;
        x = -halfStraight + this.radius * Math.cos(angle);
        z = this.radius * Math.sin(angle);
        nx = Math.cos(angle); nz = Math.sin(angle);
      }

      const pIn = new THREE.Vector3(x - nx * (this.trackWidth * 0.5), 0.06, z - nz * (this.trackWidth * 0.5));
      const pOut = new THREE.Vector3(x + nx * (this.trackWidth * 0.5), 0.06, z + nz * (this.trackWidth * 0.5));
      pointsInner.push(pIn);
      pointsOuter.push(pOut);
    }

    const trackGeo = new THREE.BufferGeometry();
    const vertices = [];
    const uvs = [];

    for (let i = 0; i < segments; i++) {
      const p1 = pointsInner[i];
      const p2 = pointsOuter[i];
      const p3 = pointsInner[i + 1];
      const p4 = pointsOuter[i + 1];

      vertices.push(p1.x, p1.y, p1.z, p2.x, p2.y, p2.z, p3.x, p3.y, p3.z);
      uvs.push(0, i / segments, 1, i / segments, 0, (i + 1) / segments);

      vertices.push(p2.x, p2.y, p2.z, p4.x, p4.y, p4.z, p3.x, p3.y, p3.z);
      uvs.push(1, i / segments, 1, (i + 1) / segments, 0, (i + 1) / segments);
    }

    trackGeo.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
    trackGeo.setAttribute("uv", new THREE.Float32BufferAttribute(uvs, 2));
    trackGeo.computeVertexNormals();

    const trackMat = new THREE.MeshStandardMaterial({
      color: 0xca9868, // Areia batida dourada esportiva
      roughness: 0.88,
      metalness: 0.05,
      side: THREE.DoubleSide
    });

    const trackMesh = new THREE.Mesh(trackGeo, trackMat);
    trackMesh.receiveShadow = true;
    this.scene.add(trackMesh);
  }

  buildLaneMarkings() {
    // Linhas sutis brancas demarcando as raias dos 8 cavalos
    const halfStraight = this.straightLen / 2.0;
    const lineMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.35 });

    // 7 divisórias entre as 8 raias (centradas perfeitamente entre cada raia)
    for (let line = 1; line <= 7; line++) {
      const lineOffset = (this.radius - 8.4) + line * 2.4;
      const straightLineGeo = new THREE.PlaneGeometry(this.straightLen, 0.12);
      
      // Reta principal
      const lineMesh = new THREE.Mesh(straightLineGeo, lineMat);
      lineMesh.rotation.x = -Math.PI / 2;
      lineMesh.position.set(0, 0.08, lineOffset);
      this.scene.add(lineMesh);

      // Reta oposta
      const lineMeshOpp = new THREE.Mesh(straightLineGeo, lineMat);
      lineMeshOpp.rotation.x = -Math.PI / 2;
      lineMeshOpp.position.set(0, 0.08, -lineOffset);
      this.scene.add(lineMeshOpp);
    }

    // Linha de chegada quadriculada no chão
    const finishLineGeo = new THREE.PlaneGeometry(3.0, this.trackWidth);
    const canvas = document.createElement("canvas");
    canvas.width = 64; canvas.height = 256;
    const ctx = canvas.getContext("2d");
    for (let y = 0; y < 16; y++) {
      for (let x = 0; x < 4; x++) {
        ctx.fillStyle = (x + y) % 2 === 0 ? "#ffffff" : "#111827";
        ctx.fillRect(x * 16, y * 16, 16, 16);
      }
    }
    const checkerTex = new THREE.CanvasTexture(canvas);
    checkerTex.wrapS = THREE.RepeatWrapping;
    checkerTex.wrapT = THREE.RepeatWrapping;
    const finishMat = new THREE.MeshBasicMaterial({ map: checkerTex });
    const finishMesh = new THREE.Mesh(finishLineGeo, finishMat);
    finishMesh.rotation.x = -Math.PI / 2;
    finishMesh.position.set(halfStraight, 0.09, this.radius);
    this.scene.add(finishMesh);
  }

  buildFencesAndHedges() {
    const fenceMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.3 });
    const hedgeMat = new THREE.MeshLambertMaterial({ color: 0x15803d });
    const postGeo = new THREE.CylinderGeometry(0.12, 0.12, 1.8, 8);
    const railMat = fenceMat;

    const halfStraight = this.straightLen / 2.0; // 150m
    const rIn = this.radius - this.trackWidth * 0.5 - 0.5; // ~52.16m
    const rOut = this.radius + this.trackWidth * 0.5 + 0.5; // ~75.16m

    // Função auxiliar para gerar pontos ovais ao longo de um raio
    const generatePerimeterPoints = (radiusVal, stepDist = 5.0) => {
      const points = [];
      // 1. Reta Principal (-150 a +150 em +Z)
      for (let x = -halfStraight; x <= halfStraight; x += stepDist) {
        points.push(new THREE.Vector3(x, 0.9, radiusVal));
      }
      // 2. Curva 1 (ao redor de 150, 0) de pi/2 a -pi/2
      const curveSegments = Math.round((Math.PI * radiusVal) / stepDist);
      for (let i = 1; i < curveSegments; i++) {
        const theta = (Math.PI / 2.0) - (i / curveSegments) * Math.PI;
        points.push(new THREE.Vector3(150.0 + radiusVal * Math.cos(theta), 0.9, radiusVal * Math.sin(theta)));
      }
      // 3. Reta Oposta (+150 a -150 em -Z)
      for (let x = halfStraight; x >= -halfStraight; x -= stepDist) {
        points.push(new THREE.Vector3(x, 0.9, -radiusVal));
      }
      // 4. Curva 2 (ao redor de -150, 0) de -pi/2 a -3pi/2
      for (let i = 1; i < curveSegments; i++) {
        const theta = -(Math.PI / 2.0) - (i / curveSegments) * Math.PI;
        points.push(new THREE.Vector3(-150.0 + radiusVal * Math.cos(theta), 0.9, radiusVal * Math.sin(theta)));
      }
      return points;
    };

    const innerPoints = generatePerimeterPoints(rIn, 4.5);
    const outerPoints = generatePerimeterPoints(rOut, 4.5);

    const placeFenceLoop = (pts, isInner = false) => {
      for (let i = 0; i < pts.length; i++) {
        const p1 = pts[i];
        const p2 = pts[(i + 1) % pts.length];

        // Poste vertical
        const post = new THREE.Mesh(postGeo, fenceMat);
        post.position.copy(p1);
        post.castShadow = true;
        this.scene.add(post);

        // Barra horizontal da cerca
        const dist = p1.distanceTo(p2);
        const rail = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.16, dist), railMat);
        const mid = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
        rail.position.set(mid.x, 1.3, mid.z);
        rail.lookAt(p2);
        this.scene.add(rail);

        // Sebe viva contornando a cerca interna
        if (isInner && i % 2 === 0) {
          const hedge = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.9, dist * 2.0), hedgeMat);
          hedge.position.set(mid.x, 0.45, mid.z);
          hedge.lookAt(p2);
          hedge.castShadow = true;
          this.scene.add(hedge);
        }
      }
    };

    placeFenceLoop(innerPoints, true);
    placeFenceLoop(outerPoints, false);
  }

  buildDistanceMarkers() {
    // Marcadores clássicos de turfe ao longo da raia (800m, 600m, 400m, 200m, 100m)
    const markers = [
      { text: "800m", x: -150, z: -this.radius - 12 },
      { text: "600m", x: 50, z: -this.radius - 12 },
      { text: "400m", x: 150, z: -10 },
      { text: "200m", x: 50, z: this.radius + 13 },
      { text: "100m", x: 100, z: this.radius + 13 },
      { text: "FINAL", x: 148, z: this.radius + 13 }
    ];

    markers.forEach((m) => {
      const post = new THREE.Mesh(
        new THREE.CylinderGeometry(0.18, 0.22, 4.0, 8),
        new THREE.MeshStandardMaterial({ color: 0x1e293b })
      );
      post.position.set(m.x, 2.0, m.z);
      post.castShadow = true;
      this.scene.add(post);

      const boardCanvas = document.createElement("canvas");
      boardCanvas.width = 128; boardCanvas.height = 64;
      const ctx = boardCanvas.getContext("2d");
      ctx.fillStyle = "#f59e0b";
      ctx.fillRect(0, 0, 128, 64);
      ctx.fillStyle = "#0f172a";
      ctx.font = "bold 26px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(m.text, 64, 42);

      const tex = new THREE.CanvasTexture(boardCanvas);
      const board = new THREE.Mesh(
        new THREE.BoxGeometry(2.4, 1.4, 0.2),
        new THREE.MeshStandardMaterial({ map: tex })
      );
      board.position.set(m.x, 4.2, m.z);
      board.castShadow = true;
      this.scene.add(board);
    });
  }

  buildJumbotron() {
    // Telão gigante de LED no centro do Infield voltado para o estádio
    const jumbotronGroup = new THREE.Group();
    const frameMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.8 });
    
    // Pilares de suporte treliçado
    const p1 = new THREE.Mesh(new THREE.BoxGeometry(1.5, 18, 1.5), frameMat);
    p1.position.set(40, 9, 2);
    jumbotronGroup.add(p1);

    const p2 = new THREE.Mesh(new THREE.BoxGeometry(1.5, 18, 1.5), frameMat);
    p2.position.set(70, 9, 2);
    jumbotronGroup.add(p2);

    // Moldura do telão
    const frame = new THREE.Mesh(new THREE.BoxGeometry(34, 16, 2.0), frameMat);
    frame.position.set(55, 20, 2);
    frame.castShadow = true;
    jumbotronGroup.add(frame);

    // Tela de LED acesa
    const canvas = document.createElement("canvas");
    canvas.width = 512; canvas.height = 256;
    const ctx = canvas.getContext("2d");
    const grad = ctx.createLinearGradient(0, 0, 512, 256);
    grad.addColorStop(0, "#0f172a");
    grad.addColorStop(1, "#1e3a8a");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 512, 256);
    ctx.strokeStyle = "#fbbf24";
    ctx.lineWidth = 12;
    ctx.strokeRect(6, 6, 500, 244);
    ctx.fillStyle = "#fbbf24";
    ctx.font = "bold 44px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("🏇 TIKTOK LIVE DERBY 🏇", 256, 110);
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 26px sans-serif";
    ctx.fillText("APÓIE SEU CAVALO NO CHAT!", 256, 170);

    const screenTex = new THREE.CanvasTexture(canvas);
    const screenMat = new THREE.MeshBasicMaterial({ map: screenTex });
    const screen = new THREE.Mesh(new THREE.PlaneGeometry(31, 13.5), screenMat);
    screen.position.set(55, 20, 3.05);
    jumbotronGroup.add(screen);

    this.scene.add(jumbotronGroup);
  }

  buildGrandstands() {
    const standGroup = new THREE.Group();
    const concreteMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, roughness: 0.8 });
    const roofMat = new THREE.MeshStandardMaterial({ color: 0x1e3a8a, roughness: 0.4 });
    const seatColors = [0xef4444, 0x3b82f6, 0xf59e0b, 0x10b981, 0xffffff];

    // Degraus da arquibancada principal
    for (let tier = 0; tier < 10; tier++) {
      const stepGeo = new THREE.BoxGeometry(250, 1.5, 3.2);
      const step = new THREE.Mesh(stepGeo, concreteMat);
      step.position.set(0, tier * 1.5 + 0.75, this.radius + 18 + tier * 3.0);
      step.castShadow = true;
      step.receiveShadow = true;
      standGroup.add(step);

      // Torcedores vibrando
      const crowdCount = 80;
      for (let c = 0; c < crowdCount; c++) {
        const crowdGeo = new THREE.CylinderGeometry(0.35, 0.35, 1.2, 8);
        const col = seatColors[Math.floor(Math.random() * seatColors.length)];
        const crowdMat = new THREE.MeshLambertMaterial({ color: col });
        const fan = new THREE.Mesh(crowdGeo, crowdMat);
        const xOffset = -120 + (c / crowdCount) * 240 + (Math.random() - 0.5) * 1.8;
        fan.position.set(xOffset, tier * 1.5 + 1.8, this.radius + 18 + tier * 3.0);
        standGroup.add(fan);
        this.crowdMeshes.push({ mesh: fan, baseHeight: fan.position.y, phase: Math.random() * Math.PI * 2 });
      }
    }

    // Camarote VIP com vidro espelhado no topo
    const vipGeo = new THREE.BoxGeometry(250, 6, 8);
    const glassMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, roughness: 0.1, metalness: 0.9 });
    const vip = new THREE.Mesh(vipGeo, glassMat);
    vip.position.set(0, 18.5, this.radius + 48);
    vip.castShadow = true;
    standGroup.add(vip);

    // Teto / Cobertura monumental curvada
    const roofGeo = new THREE.BoxGeometry(260, 2.0, 38);
    const roof = new THREE.Mesh(roofGeo, roofMat);
    roof.position.set(0, 26, this.radius + 32);
    roof.rotation.x = 0.14;
    roof.castShadow = true;
    standGroup.add(roof);

    // Mastros e Bandeiras Coloridas no Teto
    const flagColors = [0xef4444, 0xf59e0b, 0x10b981, 0x3b82f6, 0x8b5cf6];
    for (let f = -120; f <= 120; f += 24) {
      const pole = new THREE.Mesh(
        new THREE.CylinderGeometry(0.1, 0.12, 6.0, 6),
        new THREE.MeshStandardMaterial({ color: 0xffffff })
      );
      pole.position.set(f, 29, this.radius + 15);
      standGroup.add(pole);

      const flag = new THREE.Mesh(
        new THREE.PlaneGeometry(3.5, 2.0),
        new THREE.MeshBasicMaterial({ color: flagColors[Math.abs(f) % flagColors.length], side: THREE.DoubleSide })
      );
      flag.position.set(f + 1.75, 30.5, this.radius + 15);
      standGroup.add(flag);
      this.flags.push(flag);
    }

    this.scene.add(standGroup);
  }

  buildTreesAndNature() {
    // Função para criar uma árvore conífera/pinheiro 3D detalhada
    const createPineTree = (x, z, scale = 1.0) => {
      const treeGroup = new THREE.Group();
      const trunkMat = new THREE.MeshLambertMaterial({ color: 0x5c3a21 });
      const foliageMat = new THREE.MeshLambertMaterial({ color: 0x14532d });

      // Tronco
      const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.4 * scale, 0.6 * scale, 4 * scale, 8), trunkMat);
      trunk.position.y = 2 * scale;
      trunk.castShadow = true;
      treeGroup.add(trunk);

      // 3 Camadas de folhagem cônica
      for (let layer = 0; layer < 3; layer++) {
        const cone = new THREE.Mesh(
          new THREE.ConeGeometry((3.5 - layer * 0.8) * scale, 3.8 * scale, 8),
          foliageMat
        );
        cone.position.y = (3.5 + layer * 2.2) * scale;
        cone.castShadow = true;
        treeGroup.add(cone);
      }

      treeGroup.position.set(x, 0, z);
      return treeGroup;
    };

    // Árvores no entorno externo do estádio e das curvas (todas fora da pista e das cercas)
    // A pista ocupa raios de 52m a 75m. As árvores externas ficam com raio >= 90m das curvas ou z <= -95m na reta oposta.
    const treeCoords = [
      // Curva 1 Externa (raio >= 92m de (150, 0))
      [245, 0], [240, 35], [225, 65], [198, 90], [240, -35], [225, -65], [198, -90],
      [258, 20], [258, -20],
      // Curva 2 Externa (raio >= 92m de (-150, 0))
      [-245, 0], [-240, 35], [-225, 65], [-198, 90], [-240, -35], [-225, -65], [-198, -90],
      [-258, 20], [-258, -20],
      // Reta Oposta (Atrás da cerca externa em z <= -96m)
      [-140, -96], [-105, -96], [-70, -96], [-35, -96], [0, -96], [35, -96], [70, -96], [105, -96], [140, -96],
      [-120, -112], [-80, -112], [-40, -112], [0, -112], [40, -112], [80, -112], [120, -112],
      [-140, -128], [-90, -128], [-40, -128], [10, -128], [60, -128], [110, -128],
      // Infield Central Seguro (Dentro do gramado seguro |z| <= 22m e longe do lago)
      [-95, 18], [-80, -20], [55, 22], [85, -18], [105, 15], [-105, -10]
    ];

    treeCoords.forEach(([x, z]) => {
      const scale = 0.85 + Math.random() * 0.45;
      const tree = createPineTree(x, z, scale);
      this.scene.add(tree);
    });
  }

  buildClouds() {
    const cloudMat = new THREE.MeshLambertMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.82
    });

    for (let i = 0; i < 18; i++) {
      const cloudGroup = new THREE.Group();
      const numPuffs = 4 + Math.floor(Math.random() * 3);
      for (let p = 0; p < numPuffs; p++) {
        const puff = new THREE.Mesh(new THREE.DodecahedronGeometry(8 + Math.random() * 6, 1), cloudMat);
        puff.position.set(p * 7 + (Math.random() - 0.5) * 4, (Math.random() - 0.5) * 3, (Math.random() - 0.5) * 4);
        cloudGroup.add(puff);
      }
      cloudGroup.position.set(
        (Math.random() - 0.5) * 800,
        90 + Math.random() * 40,
        (Math.random() - 0.5) * 600
      );
      this.scene.add(cloudGroup);
      this.clouds.push(cloudGroup);
    }
  }

  buildStartAndFinishGates() {
    const halfStraight = this.straightLen / 2.0;

    // 1. Portão de Largada (Boxes / Stalls Profissionais)
    const stallGroup = new THREE.Group();
    const metalMat = new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.7, roughness: 0.3 });
    const canopyMat = new THREE.MeshStandardMaterial({ color: 0xb45309, roughness: 0.4 });
    const stallColors = [0xf59e0b, 0x2563eb, 0x10b981, 0xef4444, 0x1e293b, 0x78350f, 0x06b6d4, 0x8b5cf6];

    for (let lane = 1; lane <= 8; lane++) {
      const zOffset = (this.radius - 8.4) + (lane - 1) * 2.4;
      
      // Postes do box
      const post = new THREE.Mesh(new THREE.BoxGeometry(0.35, 4.5, 2.4), metalMat);
      post.position.set(-halfStraight, 2.25, zOffset);
      post.castShadow = true;
      stallGroup.add(post);

      // Placa numerada frontal do box
      const numPlate = new THREE.Mesh(
        new THREE.BoxGeometry(0.5, 0.8, 1.2),
        new THREE.MeshLambertMaterial({ color: stallColors[lane - 1] })
      );
      numPlate.position.set(-halfStraight + 0.3, 4.2, zOffset);
      stallGroup.add(numPlate);
    }

    // Cobertura do portão de largada
    const canopy = new THREE.Mesh(new THREE.BoxGeometry(2.0, 0.4, this.trackWidth + 1.5), canopyMat);
    canopy.position.set(-halfStraight, 4.7, this.radius);
    stallGroup.add(canopy);

    this.startGate = stallGroup;
    this.scene.add(stallGroup);

    // 2. Portal Monumental de Chegada (Golden Horse Arches)
    const finishGroup = new THREE.Group();
    const pillarMat = new THREE.MeshStandardMaterial({ color: 0xd97706, metalness: 0.8, roughness: 0.2 });
    
    // Torres laterais com detalhes dourados
    const t1 = new THREE.Mesh(new THREE.CylinderGeometry(0.7, 0.9, 13, 16), pillarMat);
    t1.position.set(halfStraight, 6.5, this.radius - this.trackWidth * 0.5 - 1.5);
    t1.castShadow = true;
    finishGroup.add(t1);

    const t2 = new THREE.Mesh(new THREE.CylinderGeometry(0.7, 0.9, 13, 16), pillarMat);
    t2.position.set(halfStraight, 6.5, this.radius + this.trackWidth * 0.5 + 1.5);
    t2.castShadow = true;
    finishGroup.add(t2);

    // Banner Superior da Linha de Chegada
    const bannerCanvas = document.createElement("canvas");
    bannerCanvas.width = 512; bannerCanvas.height = 128;
    const bCtx = bannerCanvas.getContext("2d");
    bCtx.fillStyle = "#111827";
    bCtx.fillRect(0, 0, 512, 128);
    bCtx.strokeStyle = "#fbbf24";
    bCtx.lineWidth = 8;
    bCtx.strokeRect(4, 4, 504, 120);
    bCtx.fillStyle = "#fbbf24";
    bCtx.font = "bold 38px sans-serif";
    bCtx.textAlign = "center";
    bCtx.fillText("🏁 LINHA DE CHEGADA 🏁", 256, 80);

    const bannerTex = new THREE.CanvasTexture(bannerCanvas);
    const banner = new THREE.Mesh(
      new THREE.BoxGeometry(0.8, 3.2, this.trackWidth + 3.0),
      new THREE.MeshStandardMaterial({ map: bannerTex })
    );
    banner.position.set(halfStraight, 12.0, this.radius);
    banner.castShadow = true;
    finishGroup.add(banner);

    this.finishGate = finishGroup;
    this.scene.add(finishGroup);
  }

  buildStadiumTowers() {
    const towerGeo = new THREE.CylinderGeometry(1.2, 2.2, 60, 8);
    const towerMat = new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.85 });
    const positions = [
      [-180, 30, 130],
      [180, 30, 130],
      [180, 30, -130],
      [-180, 30, -130],
    ];
    positions.forEach((p) => {
      const tower = new THREE.Mesh(towerGeo, towerMat);
      tower.position.set(p[0], p[1], p[2]);
      tower.castShadow = true;
      this.scene.add(tower);

      // Caixa de refletores no topo da torre
      const head = new THREE.Mesh(
        new THREE.BoxGeometry(6, 4, 3),
        new THREE.MeshStandardMaterial({ color: 0x0f172a })
      );
      head.position.set(p[0], 60, p[2]);
      this.scene.add(head);
    });
  }

  setWeather(weatherType) {
    this.currentWeather = weatherType;
    if (weatherType === "NIGHT_LIGHTS") {
      this.scene.background.setHex(0x050814);
      this.scene.fog.color.setHex(0x050814);
      this.ambientLight.intensity = 0.28;
      this.sunLight.intensity = 0.12;
      this.floodlights.forEach((f) => (f.intensity = 2.4));
    } else if (weatherType === "SUNSET") {
      this.scene.background.setHex(0xf97316);
      this.scene.fog.color.setHex(0xf97316);
      this.ambientLight.intensity = 0.55;
      this.sunLight.color.setHex(0xffaa55);
      this.sunLight.intensity = 1.35;
      this.floodlights.forEach((f) => (f.intensity = 0.9));
    } else if (weatherType === "RAIN" || weatherType === "STORM") {
      this.scene.background.setHex(0x475569);
      this.scene.fog.color.setHex(0x475569);
      this.ambientLight.intensity = 0.42;
      this.sunLight.intensity = 0.32;
      this.floodlights.forEach((f) => (f.intensity = 1.4));
    } else {
      // CLEAR
      this.scene.background.setHex(0x7dd3fc);
      this.scene.fog.color.setHex(0xbae6fd);
      this.ambientLight.intensity = 0.7;
      this.sunLight.color.setHex(0xfffaed);
      this.sunLight.intensity = 1.3;
      this.floodlights.forEach((f) => (f.intensity = 0.0));
    }
  }

  update(timeSeconds) {
    // 1. Torcida pulando e vibrando
    for (let i = 0; i < this.crowdMeshes.length; i++) {
      const c = this.crowdMeshes[i];
      c.mesh.position.y = c.baseHeight + Math.sin(timeSeconds * 6.0 + c.phase) * 0.28;
    }

    // 2. Nuvens flutuando no horizonte
    for (let i = 0; i < this.clouds.length; i++) {
      const cl = this.clouds[i];
      cl.position.x += 0.8 * 0.016;
      if (cl.position.x > 450) {
        cl.position.x = -450;
      }
    }

    // 3. Bandeiras balançando no vento
    for (let i = 0; i < this.flags.length; i++) {
      const fl = this.flags[i];
      fl.rotation.y = Math.sin(timeSeconds * 4.0 + i) * 0.22;
    }
  }

  render() {
    this.renderer.render(this.scene, this.camera);
  }

  onResize() {
    const width = this.container.clientWidth || 1080;
    const height = this.container.clientHeight || 1920;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }
}
