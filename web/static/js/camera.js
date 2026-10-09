class CinematicCameraDirector {
  constructor(camera, trackScene, horseManager) {
    this.camera = camera;
    this.scene = trackScene;
    this.horseManager = horseManager;

    this.mode = "CAM_START"; // CAM_START, CAM_CHASE, CAM_SIDE, CAM_FINISH, CAM_PODIUM
    this.targetPos = new THREE.Vector3(-210, 36, 140);
    this.targetLookAt = new THREE.Vector3(-145, 4.0, 75);
    this.currentLookAt = new THREE.Vector3(-145, 4.0, 75);

    this.timer = 0;
    this.podiumAngle = 0;
    this.camera.position.set(-210, 36, 140);
    this.camera.lookAt(this.currentLookAt);
  }

  setMode(mode) {
    this.mode = mode;
  }

  update(dt, directorState, engineData) {
    this.timer += dt;

    let targetHorseId = engineData.leader_horse_id || 1;
    const horses = engineData.horses || [];
    const activeHorses = horses.filter((h) => !h.finished);

    // Se o líder geral já cruzou a linha, foca no líder da disputa restante (2º e 3º lugares)
    if (activeHorses.length > 0) {
      const activeLeader = activeHorses.slice().sort((a, b) => b.distance - a.distance)[0];
      targetHorseId = activeLeader.id;
    } else {
      targetHorseId = engineData.winner_horse_id || targetHorseId;
    }

    const leaderPos = this.horseManager.getHorsePosition(targetHorseId);
    const leaderRot = this.horseManager.getHorseRotationY(targetHorseId);
    const winnerId = engineData.winner_horse_id || targetHorseId;
    const winnerPos = this.horseManager.getHorsePosition(winnerId);

    // Vetores unitários de direção instantânea do cavalo líder
    const fwdX = Math.sin(leaderRot);
    const fwdZ = Math.cos(leaderRot);
    const normX = Math.cos(leaderRot);
    const normZ = -Math.sin(leaderRot);

    // Cálculo do centro do pelotão para enquadrar todos os 8 cavalos
    let packCenterX = 0, packCenterY = 0, packCenterZ = 0;
    const trackedList = activeHorses.length > 0 ? activeHorses : horses;
    if (trackedList.length > 0) {
      for (let h of trackedList) {
        const p = this.horseManager.getHorsePosition(h.id);
        packCenterX += p.x;
        packCenterY += p.y;
        packCenterZ += p.z;
      }
      packCenterX /= trackedList.length;
      packCenterY /= trackedList.length;
      packCenterZ /= trackedList.length;
    } else {
      packCenterX = leaderPos.x;
      packCenterY = leaderPos.y;
      packCenterZ = leaderPos.z;
    }

    // Ponto focal balanceado entre o líder e o centro do pelotão (mantém todos visíveis!)
    const focusX = leaderPos.x * 0.45 + packCenterX * 0.55;
    const focusY = leaderPos.y * 0.45 + packCenterY * 0.55;
    const focusZ = leaderPos.z * 0.45 + packCenterZ * 0.55;

    // 1. Seleção de Modo com base na fase da transmissão
    if (directorState === "VOTING" || directorState === "COUNTDOWN") {
      this.mode = "CAM_START";
    } else if (directorState === "PODIUM" || directorState === "XP_REWARDS" || directorState === "LEADERBOARD") {
      this.mode = "CAM_PODIUM";
    } else if (directorState === "RACING") {
      const currentTrackedHorse = horses.find((h) => h.id === targetHorseId);
      const trackedDist = currentTrackedHorse ? currentTrackedHorse.distance : 0;

      const winnerDefined = !!engineData.winner_horse_id;
      if (trackedDist >= 895 && trackedDist < 1000) {
        // Curva final do cavalo ativo rumo à linha (x=-150)
        this.mode = "CAM_FINISH";
      } else if (winnerDefined && activeHorses.length > 0 && trackedDist >= 800) {
        // Vencedor já cruzou: fica na linha mostrando os PRÓXIMOS cruzamentos
        // (o alvo é o cavalo mais adiantado da disputa)
        this.mode = "CAM_FINISH";
      } else if (activeHorses.length === 0 && winnerDefined) {
        // Todos cruzaram, já foca no vencedor celebrando
        this.mode = "CAM_PODIUM";
      } else {
        // Alternância suave entre perseguição ampla e visão lateral de helicóptero
        const cycle = Math.floor(this.timer / 12.0) % 2;
        this.mode = cycle === 0 ? "CAM_CHASE" : "CAM_SIDE";
      }
    }

    // 2. Cálculo dos pontos de câmera bem mais afastados (ampla visão esportiva)
    switch (this.mode) {
      case "CAM_START": {
        // Deriva cinematográfica ao redor dos boxes de largada: no menu de
        // votação a câmera ficava 100% parada e parecia que a tela travou.
        // Órbita lenta (~22s por volta) + balanço vertical suave.
        const a = this.timer * 0.28;
        this.targetPos.set(
          -215.0 + Math.cos(a) * 18.0,
          33.0 + Math.sin(a * 1.7) * 3.0,
          128.0 + Math.sin(a) * 14.0
        );
        // Olhar passeia devagar pelos boxes, sem perder a área de largada
        this.targetLookAt.set(-148.0 + Math.sin(a * 0.9) * 4.0, 3.5, 63.66);
        break;
      }

      case "CAM_CHASE":
        // Câmera guindaste/aérea esportiva: bem afastada para trás e para cima
        // Enquadra perfeitamente todos os 8 cavalos, distâncias e ultrapassagens
        this.targetPos.set(
          focusX - fwdX * 58.0 + normX * 18.0,
          focusY + 30.0,
          focusZ - fwdZ * 58.0 + normZ * 18.0
        );
        this.targetLookAt.set(
          focusX + fwdX * 6.0,
          focusY + 2.0,
          focusZ + fwdZ * 6.0
        );
        break;

      case "CAM_SIDE":
        // Visão lateral de transmissão de TV (estilo helicóptero esportivo)
        this.targetPos.set(
          focusX - fwdX * 14.0 + normX * 52.0,
          focusY + 32.0,
          focusZ - fwdZ * 14.0 + normZ * 52.0
        );
        this.targetLookAt.set(
          focusX + fwdX * 4.0,
          focusY + 2.0,
          focusZ + fwdZ * 4.0
        );
        break;

      case "CAM_FINISH": {
        // Câmera de chegada ancorada na LINHA REAL da pista (x=-150):
        // fica por fora da curva final olhando o portal e o alvo é o cavalo
        // que está cruzando. Quando o vencedor passa, o alvo vira o próximo
        // da disputa e a câmera acompanha — antes ela travava num ponto fixo
        // do outro lado da pista e a chegada dos demais ficava fora de quadro.
        const line = this.scene.finishLinePosition || {
          x: -this.scene.straightLen / 2.0,
          z: this.scene.radius
        };
        this.targetPos.set(line.x - 42.0, 17.0, line.z + 34.0);
        this.targetLookAt.set(leaderPos.x, leaderPos.y + 1.6, leaderPos.z);
        break;
      }

      case "CAM_PODIUM":
        // Órbita cinematográfica em ângulo heróico e dinâmico em torno do campeão empinado
        this.podiumAngle += dt * 0.42;
        const orbitRadius = 14.5;
        this.targetPos.set(
          winnerPos.x + Math.cos(this.podiumAngle) * orbitRadius,
          5.0 + Math.sin(this.podiumAngle * 0.8) * 1.5,
          winnerPos.z + Math.sin(this.podiumAngle) * orbitRadius
        );
        this.targetLookAt.set(winnerPos.x, 3.2, winnerPos.z);
        break;
    }

    // 3. Interpolação suave e contínua sem saltos ou tremores
    const posLerp = Math.min(1.0, 5.5 * dt);
    const lookLerp = Math.min(1.0, 7.5 * dt);

    this.camera.position.lerp(this.targetPos, posLerp);
    this.currentLookAt.lerp(this.targetLookAt, lookLerp);

    // Efeito de Screen Shake de impacto lendário
    if (this.horseManager && this.horseManager.particles) {
      const shake = this.horseManager.particles.screenShakeIntensity || 0;
      if (shake > 0.01) {
        this.camera.position.x += (Math.random() - 0.5) * 2.2 * shake;
        this.camera.position.y += (Math.random() - 0.5) * 1.8 * shake;
        this.camera.position.z += (Math.random() - 0.5) * 2.2 * shake;
      }
    }

    this.camera.lookAt(this.currentLookAt);
  }
}
