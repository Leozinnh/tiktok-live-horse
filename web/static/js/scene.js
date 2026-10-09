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
    this.clouds = [];
    this.fountains = [];
    this.finishGate = null;
    this.startGate = null;

    // Torcida instanciada (montada em buildGrandstands)
    this.crowdData = [];
    this.crowdCorpo = null;
    this.crowdCabeca = null;
    this._instPos = new THREE.Vector3();
    this._instEscala = new THREE.Vector3();
    this._instQuat = new THREE.Quaternion();
    this._instMatriz = new THREE.Matrix4();

    // Visual: céu com gradiente, sol, estrelas e luzes de modelagem
    this.skyUniforms = null;
    this.sunSprite = null;
    this.stars = null;
    this.hemiLight = null;
    this.fillLight = null;
    this.cloudMat = null;
    this.trackMat = null;

    // Relâmpago da tempestade (e o relógio interno do update)
    this.lightningTimer = 4.0;
    this.flashIntensity = 0.0;
    this._ultimoTempo = 0.0;
    this._corHorizonteBase = new THREE.Color(0xc9ecff);
    this._ambienteBase = 0.33;
    this._corBranca = new THREE.Color(0xffffff);

    // Posição da linha de chegada REAL da pista (distância 1000 = fim da
    // curva 4, em x=-150). É a mesma âncora usada pela física — a câmera de
    // chegada e o HUD dependem dela, então fica definida já no construtor.
    this.finishLinePosition = new THREE.Vector3(-this.straightLen / 2.0, 0, this.radius);

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
    // Exposição abaixo de 1: com 1.05 os realces (areia, camisas brancas, céu)
    // estouravam e a cena achatava. Menos exposição + ambiente mais baixo
    // (em setupLighting/PALETAS) devolve o contraste sem perder cor.
    this.renderer.toneMappingExposure = 0.92;
    // Pipeline de cor correto: sem o output em sRGB o ACES escurece a cena e
    // as cores saem lavadas — céu, gramado e areia perdem a vida.
    this.renderer.outputEncoding = THREE.sRGBEncoding;
    this.container.appendChild(this.renderer.domElement);

    // 4. Configuração de Iluminação
    this.setupLighting();

    // 5. Construção do Hipódromo Monumental
    this.buildSky();
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
    // Ambiente/hemisfério enxutos: eles preenchem a sombra, mas em excesso
    // lavam a imagem inteira (o "estourado" some quando a sombra é sombra).
    this.ambientLight = new THREE.AmbientLight(0xffffff, 0.33);
    this.scene.add(this.ambientLight);

    // Luz do céu (azulada, por cima) contra a luz do gramado (esverdeada, por
    // baixo): dá volume a cavalos e estádio — luz ambiente chapada não dá.
    this.hemiLight = new THREE.HemisphereLight(0xbfd9ff, 0x3f6b2e, 0.42);
    this.scene.add(this.hemiLight);

    this.sunLight = new THREE.DirectionalLight(0xfffaed, 1.35);
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

    // Preenchimento frio vindo do lado oposto ao sol: nenhuma sombra fica
    // preta — o cavalo que corre na sombra continua legível.
    this.fillLight = new THREE.DirectionalLight(0xcfe8ff, 0.28);
    this.fillLight.position.set(220, 130, -260);
    this.scene.add(this.fillLight);

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

  // Céu de verdade: um domo com gradiente (topo → horizonte), o disco do sol
  // e as estrelas da noite. Fundo liso de cor única era o maior "cheiro de
  // protótipo" da cena — todo plano de câmera pegava o mesmo azul chapado.
  buildSky() {
    const skyGeo = new THREE.SphereGeometry(1100, 32, 16);
    this.skyUniforms = {
      topColor: { value: new THREE.Color(0x2f7ddb) },
      horizonColor: { value: new THREE.Color(0xc9ecff) },
      offset: { value: 140.0 },
      exponent: { value: 0.75 },
    };
    const skyMat = new THREE.ShaderMaterial({
      uniforms: this.skyUniforms,
      vertexShader: `
        varying vec3 vWorldPosition;
        void main() {
          vec4 worldPosition = modelMatrix * vec4(position, 1.0);
          vWorldPosition = worldPosition.xyz;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform vec3 topColor;
        uniform vec3 horizonColor;
        uniform float offset;
        uniform float exponent;
        varying vec3 vWorldPosition;
        void main() {
          float h = normalize(vWorldPosition + vec3(0.0, offset, 0.0)).y;
          float f = pow(max(h, 0.0), exponent);
          gl_FragColor = vec4(mix(horizonColor, topColor, f), 1.0);
        }
      `,
      side: THREE.BackSide,
      depthWrite: false,
      fog: false,
    });
    this.scene.add(new THREE.Mesh(skyGeo, skyMat));

    // Sol: sprite com brilho radial desenhado em canvas (sem asset externo).
    const sunCanvas = document.createElement("canvas");
    sunCanvas.width = sunCanvas.height = 256;
    const sCtx = sunCanvas.getContext("2d");
    const sunGrad = sCtx.createRadialGradient(128, 128, 0, 128, 128, 128);
    sunGrad.addColorStop(0.0, "rgba(255, 255, 240, 1.0)");
    sunGrad.addColorStop(0.22, "rgba(255, 238, 180, 0.9)");
    sunGrad.addColorStop(0.5, "rgba(255, 210, 120, 0.28)");
    sunGrad.addColorStop(1.0, "rgba(255, 190, 90, 0.0)");
    sCtx.fillStyle = sunGrad;
    sCtx.fillRect(0, 0, 256, 256);

    this.sunSprite = new THREE.Sprite(
      new THREE.SpriteMaterial({
        map: new THREE.CanvasTexture(sunCanvas),
        transparent: true,
        depthWrite: false,
        fog: false,
      })
    );
    // Alinhado com a direção da luz do sol (-160, 240, 190) — o brilho nasce
    // de onde a sombra aponta.
    this.sunSprite.position.set(-330, 430, 390);
    this.sunSprite.scale.set(260, 260, 1);
    this.scene.add(this.sunSprite);

    // Estrelas: pontos fixos no domo, invisíveis de dia (o clima acende).
    const starCount = 420;
    const positions = new Float32Array(starCount * 3);
    for (let i = 0; i < starCount; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.random() * Math.PI * 0.42; // só o hemisfério de cima
      const r = 950;
      positions[i * 3] = Math.cos(theta) * Math.sin(phi + 0.12) * r;
      positions[i * 3 + 1] = Math.cos(phi) * r * 0.9 + 60;
      positions[i * 3 + 2] = Math.sin(theta) * Math.sin(phi + 0.12) * r;
    }
    const starGeo = new THREE.BufferGeometry();
    starGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    this.stars = new THREE.Points(
      starGeo,
      new THREE.PointsMaterial({
        color: 0xffffff,
        size: 2.2,
        sizeAttenuation: false,
        transparent: true,
        opacity: 0.0,
        fog: false,
        depthWrite: false,
      })
    );
    this.scene.add(this.stars);
  }

  // Textura procedural de grama (canvas): manchas tonais que quebram o
  // "verde plástico" do fundo liso, sem baixar nenhum asset.
  criarTexturaGrama(repeatX, repeatY, base) {
    const canvas = document.createElement("canvas");
    canvas.width = canvas.height = 256;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = base;
    ctx.fillRect(0, 0, 256, 256);
    for (let i = 0; i < 2600; i++) {
      ctx.fillStyle =
        Math.random() < 0.55 ? "rgba(20, 83, 45, 0.45)" : "rgba(134, 239, 172, 0.10)";
      ctx.fillRect(
        Math.random() * 256,
        Math.random() * 256,
        1 + Math.random() * 3,
        1 + Math.random() * 3
      );
    }
    const tex = new THREE.CanvasTexture(canvas);
    tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
    tex.repeat.set(repeatX, repeatY);
    tex.encoding = THREE.sRGBEncoding;
    tex.anisotropy = this.renderer ? this.renderer.capabilities.getMaxAnisotropy() : 4;
    return tex;
  }

  // Textura procedural da areia da pista: grãos, mosqueados e estrias
  // longitudinais (o casco bate sempre na mesma direção).
  criarTexturaAreia() {
    const canvas = document.createElement("canvas");
    canvas.width = canvas.height = 256;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#ca9868"; // areia batida dourada esportiva
    ctx.fillRect(0, 0, 256, 256);
    for (let i = 0; i < 3200; i++) {
      const r = Math.random();
      ctx.fillStyle =
        r < 0.5
          ? "rgba(169, 123, 79, 0.5)"
          : r < 0.85
          ? "rgba(224, 185, 136, 0.45)"
          : "rgba(120, 84, 48, 0.4)";
      ctx.fillRect(
        Math.random() * 256,
        Math.random() * 256,
        1 + Math.random() * 2.5,
        1 + Math.random() * 2.5
      );
    }
    for (let i = 0; i < 26; i++) {
      ctx.strokeStyle = `rgba(140, 100, 60, ${0.05 + Math.random() * 0.09})`;
      ctx.lineWidth = 1 + Math.random() * 2.5;
      const x = Math.random() * 256;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x + (Math.random() - 0.5) * 14, 256);
      ctx.stroke();
    }
    const tex = new THREE.CanvasTexture(canvas);
    tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
    tex.repeat.set(1, 64); // 1 fita de 22m de largura × ~15m por tile na volta
    tex.encoding = THREE.sRGBEncoding;
    tex.anisotropy = this.renderer ? this.renderer.capabilities.getMaxAnisotropy() : 4;
    return tex;
  }

  buildGroundAndInfield() {
    // 1. Gramado Base Gigante (com textura procedural de grama)
    const grassGeo = new THREE.PlaneGeometry(1600, 1400, 32, 32);
    const grassMat = new THREE.MeshLambertMaterial({
      map: this.criarTexturaGrama(48, 42, "#226926"),
      side: THREE.DoubleSide,
    });
    const grass = new THREE.Mesh(grassGeo, grassMat);
    grass.rotation.x = -Math.PI / 2;
    grass.position.y = -0.15;
    grass.receiveShadow = true;
    this.scene.add(grass);

    // 2. Gramado Infield Central Texturizado com Faixas de Corte
    // (duas texturas — uma por tom do corte — reaproveitadas nas faixas)
    const texturaCorteClaro = this.criarTexturaGrama(12, 1.6, "#2e7d32");
    const texturaCorteEscuro = this.criarTexturaGrama(12, 1.6, "#256e29");
    for (let strip = -120; strip <= 120; strip += 20) {
      const stripGeo = new THREE.PlaneGeometry(280, 18);
      const stripMat = new THREE.MeshLambertMaterial({
        map: Math.abs(strip) % 40 === 0 ? texturaCorteClaro : texturaCorteEscuro,
        side: THREE.DoubleSide,
      });
      const stripMesh = new THREE.Mesh(stripGeo, stripMat);
      stripMesh.rotation.x = -Math.PI / 2;
      stripMesh.position.set(0, -0.08, strip * 0.4);
      stripMesh.receiveShadow = true;
      this.scene.add(stripMesh);
    }

    // 3. Lago Ornamental no Infield
    const lakeGeo = new THREE.RingGeometry(18, 42, 36);
    const lakeMat = new THREE.MeshStandardMaterial({
      color: 0x0ea5e9,
      roughness: 0.12,
      // Sem mapa de ambiente, metalness alta deixa a água PRETA (metal só
      // reflete o que existe em volta) — baixa ela vira água com brilho.
      metalness: 0.3
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

    // A cor mora na textura; o material começa branco (= textura pura) e o
    // clima molha/tinge a pista mexendo só no color de multiplicação.
    this.trackMat = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      map: this.criarTexturaAreia(),
      roughness: 0.92,
      metalness: 0.04,
      side: THREE.DoubleSide
    });

    const trackMesh = new THREE.Mesh(trackGeo, this.trackMat);
    trackMesh.receiveShadow = true;
    this.scene.add(trackMesh);
  }

  buildLaneMarkings() {
    // Linhas sutis brancas demarcando as raias dos 8 cavalos
    const halfStraight = this.straightLen / 2.0;
    const lineMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.26 });

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
    checkerTex.encoding = THREE.sRGBEncoding;
    const finishMat = new THREE.MeshBasicMaterial({ map: checkerTex });
    const finishMesh = new THREE.Mesh(finishLineGeo, finishMat);
    finishMesh.rotation.x = -Math.PI / 2;
    // A corrida cruza a linha em x=-150 (distância 1000 na física), não em
    // +150: com a linha desenhada do outro lado a câmera de chegada
    // enquadrava um trecho vazio da reta.
    finishMesh.position.set(-halfStraight, 0.09, this.radius);
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
      { text: "100m", x: -50, z: this.radius + 13 },
      { text: "FINAL", x: -170, z: this.radius + 13 }
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
      tex.encoding = THREE.sRGBEncoding;
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
    screenTex.encoding = THREE.sRGBEncoding;
    const screenMat = new THREE.MeshBasicMaterial({ map: screenTex });
    const screen = new THREE.Mesh(new THREE.PlaneGeometry(31, 13.5), screenMat);
    screen.position.set(55, 20, 3.05);
    jumbotronGroup.add(screen);

    this.scene.add(jumbotronGroup);
  }

  buildGrandstands() {
    const standGroup = new THREE.Group();
    const concreteMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, roughness: 0.8 });
    const escadaMat = new THREE.MeshStandardMaterial({ color: 0xb6c2cf, roughness: 0.7 });
    const assentoMat = new THREE.MeshStandardMaterial({ color: 0x1e40af, roughness: 0.55 });
    const roofMat = new THREE.MeshStandardMaterial({ color: 0x1e3a8a, roughness: 0.4 });
    const mullionMat = new THREE.MeshStandardMaterial({ color: 0xdbeafe, roughness: 0.35, metalness: 0.4 });
    const seatColors = [0xef4444, 0x3b82f6, 0xf59e0b, 0x10b981, 0xffffff];
    const peleCores = [0xffdbac, 0xe8b98f, 0xc68642, 0x8d5524];

    const LARGURA = 250;
    const NIVEIS = 10;
    const zBase = this.radius + 18;
    const corredores = [-94, -32, 32, 94]; // escadas que dividem os setores
    const emCorredor = (x) => corredores.some((cx) => Math.abs(x - cx) < 2.6);

    // 1. Degraus de concreto + faixa azul no espelho (lê como fileira de assentos)
    for (let tier = 0; tier < NIVEIS; tier++) {
      const z = zBase + tier * 3.0;

      const step = new THREE.Mesh(new THREE.BoxGeometry(LARGURA, 1.5, 3.2), concreteMat);
      step.position.set(0, tier * 1.5 + 0.75, z);
      step.castShadow = true;
      step.receiveShadow = true;
      standGroup.add(step);

      const faixa = new THREE.Mesh(new THREE.BoxGeometry(LARGURA, 0.5, 0.5), assentoMat);
      faixa.position.set(0, tier * 1.5 + 1.72, z - 1.3);
      standGroup.add(faixa);
    }

    // 2. Escadas entre setores: painel inclinado acompanhando a rampa dos degraus
    const inclinacao = -Math.atan2(1.5, 3.0);
    corredores.forEach((cx) => {
      const escada = new THREE.Mesh(new THREE.BoxGeometry(4.6, 0.7, 33.6), escadaMat);
      escada.position.set(cx, 8.3, zBase + 13.5);
      escada.rotation.x = inclinacao;
      escada.receiveShadow = true;
      standGroup.add(escada);
    });

    // 3. Fachada frontal + faixa de publicidade iluminada (a arquibancada
    // ganha base sólida em vez de degraus flutuando sobre a grama)
    const fachada = new THREE.Mesh(new THREE.BoxGeometry(LARGURA, 3.2, 1.6), concreteMat);
    fachada.position.set(0, 1.6, zBase - 2.6);
    fachada.receiveShadow = true;
    standGroup.add(fachada);

    const ledMat = new THREE.MeshStandardMaterial({
      color: 0x0c4a6e, emissive: 0x0ea5e9, emissiveIntensity: 0.5, roughness: 0.4,
    });
    const ledBand = new THREE.Mesh(new THREE.BoxGeometry(LARGURA, 1.1, 1.8), ledMat);
    ledBand.position.set(0, 2.6, zBase - 2.6);
    standGroup.add(ledBand);

    // 4. Multidão instanciada: corpo + cabeça em dois InstancedMesh (2 draw
    // calls no lugar de ~900), altura e cor variadas por torcedor.
    const corpoGeo = new THREE.CylinderGeometry(0.32, 0.36, 1.15, 7);
    const cabecaGeo = new THREE.SphereGeometry(0.23, 7, 6);
    const corpoMat = new THREE.MeshLambertMaterial({ color: 0xffffff });
    const cabecaMat = new THREE.MeshLambertMaterial({ color: 0xffffff });

    const fans = [];
    const porNivel = 96;
    for (let tier = 0; tier < NIVEIS; tier++) {
      for (let c = 0; c < porNivel; c++) {
        const x = -LARGURA / 2 + 5 + (c / (porNivel - 1)) * (LARGURA - 10) + (Math.random() - 0.5) * 1.5;
        if (emCorredor(x)) continue;
        fans.push({
          x: x,
          baseY: tier * 1.5 + 1.72,
          z: zBase + tier * 3.0 + (Math.random() - 0.5) * 0.9,
          fase: Math.random() * Math.PI * 2,
          escala: 0.85 + Math.random() * 0.45,
          cor: seatColors[Math.floor(Math.random() * seatColors.length)],
          pele: peleCores[Math.floor(Math.random() * peleCores.length)],
        });
      }
    }

    this.crowdData = fans;
    this.crowdCorpo = new THREE.InstancedMesh(corpoGeo, corpoMat, fans.length);
    this.crowdCabeca = new THREE.InstancedMesh(cabecaGeo, cabecaMat, fans.length);
    // A esfera da geometria base não cobre a multidão espalhada por 250m: sem
    // isso o Three descarta a torcida inteira em certos ângulos de câmera.
    this.crowdCorpo.frustumCulled = false;
    this.crowdCabeca.frustumCulled = false;

    const cor = new THREE.Color();
    fans.forEach((f, i) => {
      this.crowdCorpo.setColorAt(i, cor.setHex(f.cor));
      this.crowdCabeca.setColorAt(i, cor.setHex(f.pele));
    });
    if (this.crowdCorpo.instanceColor) this.crowdCorpo.instanceColor.needsUpdate = true;
    if (this.crowdCabeca.instanceColor) this.crowdCabeca.instanceColor.needsUpdate = true;

    standGroup.add(this.crowdCorpo);
    standGroup.add(this.crowdCabeca);
    this.atualizarTorcida(0); // já posiciona as instâncias na montagem

    // 5. Camarote VIP: laje, vidro espelhado e montantes brancos
    const laje = new THREE.Mesh(new THREE.BoxGeometry(LARGURA, 0.8, 5.6), concreteMat);
    laje.position.set(0, 15.2, zBase + 31.2);
    standGroup.add(laje);

    const glassMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, roughness: 0.1, metalness: 0.9 });
    const vip = new THREE.Mesh(new THREE.BoxGeometry(LARGURA, 6, 5), glassMat);
    vip.position.set(0, 18.5, zBase + 31.2);
    vip.castShadow = true;
    standGroup.add(vip);

    for (let mx = -125; mx <= 125; mx += 25) {
      const mullion = new THREE.Mesh(new THREE.BoxGeometry(0.5, 6.4, 0.35), mullionMat);
      mullion.position.set(mx, 18.5, zBase + 28.7); // atravessa a face do vidro
      standGroup.add(mullion);
    }

    // 6. Colunas de sustentação + parede de fundo (fecham o estádio por trás)
    const alturaColuna = 23;
    for (let cx = -105; cx <= 105; cx += 30) {
      const coluna = new THREE.Mesh(new THREE.BoxGeometry(1.1, alturaColuna, 1.1), mullionMat);
      coluna.position.set(cx, alturaColuna / 2, zBase + 36);
      coluna.castShadow = true;
      standGroup.add(coluna);
    }

    // Altura casada com a face de baixo do teto nesta profundidade (~y 22)
    const paredeFundo = new THREE.Mesh(new THREE.BoxGeometry(LARGURA, 22, 2.5), concreteMat);
    paredeFundo.position.set(0, 11, zBase + 37.6);
    paredeFundo.receiveShadow = true;
    standGroup.add(paredeFundo);

    // 7. Teto estendido até a parede + testa na borda da frente
    const roofGeo = new THREE.BoxGeometry(264, 2.0, 44);
    const roof = new THREE.Mesh(roofGeo, roofMat);
    roof.position.set(0, 26, zBase + 16);
    roof.rotation.x = 0.14;
    roof.castShadow = true;
    standGroup.add(roof);

    const testa = new THREE.Mesh(new THREE.BoxGeometry(268, 2.8, 1.4), roofMat);
    testa.position.set(0, 29.0, zBase - 5.6);
    testa.castShadow = true;
    standGroup.add(testa);

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

  // Torcida instanciada: recompõe a matriz de cada torcedor (corpo + cabeça)
  // a partir dos dados guardados em crowdData. Chamado na montagem e no update.
  atualizarTorcida(timeSeconds) {
    if (!this.crowdCorpo || !this.crowdCabeca || !this.crowdData.length) return;

    const pos = this._instPos;
    const esc = this._instEscala;
    const quat = this._instQuat;
    const mat = this._instMatriz;

    for (let i = 0; i < this.crowdData.length; i++) {
      const f = this.crowdData[i];
      const y = f.baseY + Math.sin(timeSeconds * 6.0 + f.fase) * 0.28;
      const s = f.escala;

      esc.set(s, s, s);

      pos.set(f.x, y, f.z);
      mat.compose(pos, quat, esc);
      this.crowdCorpo.setMatrixAt(i, mat);

      // A cabeça acompanha o corpo: topo do cilindro (0.575) + raio da esfera
      pos.set(f.x, y + 0.8 * s, f.z);
      mat.compose(pos, quat, esc);
      this.crowdCabeca.setMatrixAt(i, mat);
    }

    this.crowdCorpo.instanceMatrix.needsUpdate = true;
    this.crowdCabeca.instanceMatrix.needsUpdate = true;
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
    // O material fica guardado: o clima tinge as nuvens (douradas no pôr do
    // sol, escuras na tempestade).
    this.cloudMat = new THREE.MeshLambertMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.85
    });
    const cloudMat = this.cloudMat;

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
    t1.position.set(-halfStraight, 6.5, this.radius - this.trackWidth * 0.5 - 1.5);
    t1.castShadow = true;
    finishGroup.add(t1);

    const t2 = new THREE.Mesh(new THREE.CylinderGeometry(0.7, 0.9, 13, 16), pillarMat);
    t2.position.set(-halfStraight, 6.5, this.radius + this.trackWidth * 0.5 + 1.5);
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
    bannerTex.encoding = THREE.sRGBEncoding;
    const banner = new THREE.Mesh(
      new THREE.BoxGeometry(0.8, 3.2, this.trackWidth + 3.0),
      new THREE.MeshStandardMaterial({ map: bannerTex })
    );
    banner.position.set(-halfStraight, 12.0, this.radius);
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

    // Uma paleta por clima. Cada linha vira céu (topo/horizonte), neblina,
    // luzes, sol/estrelas, nuvens e o estado da pista (molhada = escura e
    // espelhada). Tudo num lugar só — antes cada clima mexia em um subconjunto
    // das luzes e sobrava estado velho do clima anterior.
    // Ambiente/hemisfério baixos + sol forte = contraste. Antes tudo era alto
    // e a cena saía estourada, sem sombra de verdade.
    const PALETAS = {
      CLEAR: {
        ceuTopo: 0x2f7ddb, horizonte: 0xc9ecff, neblina: 0.0012,
        ambiente: 0.32, hemi: 0.4, sol: 1.5, solCor: 0xfffaed, torres: 0.0,
        nuvemCor: 0xffffff, nuvemOpacidade: 0.85,
        solVisivel: true, solBrilho: 0xfff2c4, estrelas: 0.0,
        pistaCor: 0xffffff, pistaRugosidade: 0.92, pistaMetal: 0.04,
      },
      WIND: {
        ceuTopo: 0x3b82f6, horizonte: 0xdbeafe, neblina: 0.0010,
        ambiente: 0.32, hemi: 0.4, sol: 1.45, solCor: 0xfffaed, torres: 0.0,
        nuvemCor: 0xf1f5f9, nuvemOpacidade: 0.7,
        solVisivel: true, solBrilho: 0xfff2c4, estrelas: 0.0,
        pistaCor: 0xffffff, pistaRugosidade: 0.92, pistaMetal: 0.04,
      },
      SUNSET: {
        ceuTopo: 0x4c1d95, horizonte: 0xfb923c, neblina: 0.0016,
        ambiente: 0.3, hemi: 0.34, sol: 1.4, solCor: 0xffb066, torres: 0.7,
        nuvemCor: 0xffc9a3, nuvemOpacidade: 0.8,
        solVisivel: true, solBrilho: 0xff9d4d, estrelas: 0.15,
        pistaCor: 0xffd9b3, pistaRugosidade: 0.92, pistaMetal: 0.04,
      },
      NIGHT_LIGHTS: {
        ceuTopo: 0x020617, horizonte: 0x0f172a, neblina: 0.0017,
        ambiente: 0.16, hemi: 0.18, sol: 0.1, solCor: 0x93c5fd, torres: 2.6,
        nuvemCor: 0x475569, nuvemOpacidade: 0.55,
        solVisivel: false, solBrilho: 0xffffff, estrelas: 1.0,
        pistaCor: 0xcfd8e8, pistaRugosidade: 0.9, pistaMetal: 0.06,
      },
      RAIN: {
        ceuTopo: 0x475569, horizonte: 0x94a3b8, neblina: 0.0026,
        ambiente: 0.3, hemi: 0.34, sol: 0.34, solCor: 0xfffaed, torres: 1.2,
        nuvemCor: 0x94a3b8, nuvemOpacidade: 0.9,
        solVisivel: false, solBrilho: 0xffffff, estrelas: 0.0,
        pistaCor: 0x7f8ea3, pistaRugosidade: 0.42, pistaMetal: 0.18,
      },
      STORM: {
        ceuTopo: 0x1e293b, horizonte: 0x64748b, neblina: 0.0032,
        ambiente: 0.24, hemi: 0.26, sol: 0.26, solCor: 0xfffaed, torres: 1.6,
        nuvemCor: 0x64748b, nuvemOpacidade: 0.95,
        solVisivel: false, solBrilho: 0xffffff, estrelas: 0.0,
        pistaCor: 0x6b7a90, pistaRugosidade: 0.36, pistaMetal: 0.22,
      },
    };

    const p = PALETAS[weatherType] || PALETAS.CLEAR;

    // Céu + neblina na cor do horizonte (os objetos distantes se dissolvem
    // dentro do céu em vez de recortar contra ele).
    this.skyUniforms.topColor.value.setHex(p.ceuTopo);
    this.skyUniforms.horizonColor.value.setHex(p.horizonte);
    this._corHorizonteBase.setHex(p.horizonte);
    this.scene.background.setHex(p.horizonte);
    this.scene.fog.color.setHex(p.horizonte);
    this.scene.fog.density = p.neblina;

    // Luzes
    this.ambientLight.intensity = p.ambiente;
    this._ambienteBase = p.ambiente;
    this.hemiLight.intensity = p.hemi;
    this.sunLight.color.setHex(p.solCor);
    this.sunLight.intensity = p.sol;
    this.fillLight.intensity = weatherType === "NIGHT_LIGHTS" ? 0.0 : p.sol * 0.16;
    this.floodlights.forEach((f) => (f.intensity = p.torres));

    // Sol, estrelas e nuvens
    this.sunSprite.visible = p.solVisivel;
    this.sunSprite.material.color.setHex(p.solBrilho);
    this.stars.material.opacity = p.estrelas;
    this.cloudMat.color.setHex(p.nuvemCor);
    this.cloudMat.opacity = p.nuvemOpacidade;

    // Pista: molhada escurece e espelha (chuva/tempestade)
    this.trackMat.color.setHex(p.pistaCor);
    this.trackMat.roughness = p.pistaRugosidade;
    this.trackMat.metalness = p.pistaMetal;

    // Sair da tempestade apaga o clarão pendente
    this.flashIntensity = 0.0;
  }

  update(timeSeconds) {
    // O update recebe só o relógio; o dt sai da diferença entre chamadas.
    const dt = Math.min(0.1, Math.max(0, timeSeconds - this._ultimoTempo));
    this._ultimoTempo = timeSeconds;

    // 1. Torcida pulando e vibrando (instanciada: 2 uploads de matriz por frame)
    this.atualizarTorcida(timeSeconds);

    // 2. Nuvens flutuando no horizonte (passo por segundo, independe do FPS)
    for (let i = 0; i < this.clouds.length; i++) {
      const cl = this.clouds[i];
      cl.position.x += 0.77 * dt;
      if (cl.position.x > 450) {
        cl.position.x = -450;
      }
    }

    // 3. Bandeiras balançando no vento
    for (let i = 0; i < this.flags.length; i++) {
      const fl = this.flags[i];
      fl.rotation.y = Math.sin(timeSeconds * 4.0 + i) * 0.22;
    }

    // 4. Jatos da fonte central pulsando (eram estátuas de água parada)
    for (let i = 0; i < this.fountains.length; i++) {
      const jet = this.fountains[i];
      const onda = Math.sin(timeSeconds * 2.6 + i * 1.7);
      jet.scale.y = 1.0 + onda * 0.18;
      jet.material.opacity = 0.55 + 0.25 * Math.abs(onda);
    }

    // 5. Relâmpago da tempestade: clarão curto que acende o céu e o ambiente
    if (this.currentWeather === "STORM") {
      this.lightningTimer -= dt;
      if (this.lightningTimer <= 0) {
        this.flashIntensity = 0.85 + Math.random() * 0.35;
        this.lightningTimer = 3.0 + Math.random() * 6.0;
      }
      this.flashIntensity = Math.max(0, this.flashIntensity - dt * 3.2);
      const f = Math.min(1.0, this.flashIntensity);
      if (f > 0.001) {
        this.skyUniforms.horizonColor.value
          .copy(this._corHorizonteBase)
          .lerp(this._corBranca, f * 0.85);
        this.scene.fog.color.copy(this.skyUniforms.horizonColor.value);
        this.ambientLight.intensity = this._ambienteBase + f * 1.6;
      } else {
        // Devolve o céu ao estado da paleta depois do clarão
        this.skyUniforms.horizonColor.value.copy(this._corHorizonteBase);
        this.scene.fog.color.copy(this._corHorizonteBase);
        this.ambientLight.intensity = this._ambienteBase;
      }
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
