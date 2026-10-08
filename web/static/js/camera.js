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

    // 1. Seleção de Modo com base na fase da transmissão
    if (directorState === "VOTING" || directorState === "COUNTDOWN") {
      this.mode = "CAM_START";
    } else if (directorState === "PODIUM" || directorState === "XP_REWARDS" || directorState === "LEADERBOARD") {
      this.mode = "CAM_PODIUM";
    } else if (directorState === "RACING") {
      const currentTrackedHorse = horses.find((h) => h.id === targetHorseId);
      const trackedDist = currentTrackedHorse ? currentTrackedHorse.distance : 0;

      if (trackedDist >= 870 && trackedDist < 1000) {
        // Reta final e linha de chegada enquanto o cavalo ativo estiver cruzando
        this.mode = "CAM_FINISH";
      } else if (activeHorses.length === 0 && engineData.winner_horse_id) {
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
      case "CAM_START":
        // Vista aérea panorâmica dos boxes de largada e arquibancadas
        this.targetPos.set(-210, 36, 140);
        this.targetLookAt.set(-145, 4.0, 75);
        break;

      case "CAM_CHASE":
        // Câmera guindaste/aérea esportiva: bem afastada para trás e para cima
        // Enquadra perfeitamente todos os 8 cavalos, distâncias e ultrapassagens
        this.targetPos.set(
          leaderPos.x - fwdX * 44.0 + normX * 18.0,
          leaderPos.y + 24.0,
          leaderPos.z - fwdZ * 44.0 + normZ * 18.0
        );
        this.targetLookAt.set(
          leaderPos.x + fwdX * 8.0,
          leaderPos.y + 1.5,
          leaderPos.z + fwdZ * 8.0
        );
        break;

      case "CAM_SIDE":
        // Visão lateral de transmissão de TV (estilo helicóptero esportivo)
        this.targetPos.set(
          leaderPos.x - fwdX * 12.0 + normX * 46.0,
          leaderPos.y + 28.0,
          leaderPos.z - fwdZ * 12.0 + normZ * 46.0
        );
        this.targetLookAt.set(
          leaderPos.x + fwdX * 6.0,
          leaderPos.y + 1.5,
          leaderPos.z + fwdZ * 6.0
        );
        break;

      case "CAM_FINISH":
        // Câmera angular na reta de chegada enquadrando o portal e a aproximação
        this.targetPos.set(186, 15, this.scene.radius + 24.0);
        this.targetLookAt.set(142, 2.8, this.scene.radius + 4.0);
        break;

      case "CAM_PODIUM":
        // Órbita cinematográfica 360º ampla em torno do vencedor
        this.podiumAngle += dt * 0.35;
        const orbitRadius = 22.0;
        this.targetPos.set(
          winnerPos.x + Math.cos(this.podiumAngle) * orbitRadius,
          8.5,
          winnerPos.z + Math.sin(this.podiumAngle) * orbitRadius
        );
        this.targetLookAt.set(winnerPos.x, 2.5, winnerPos.z);
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
