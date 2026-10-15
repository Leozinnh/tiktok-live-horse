// Rodízio de quadros da transmissão: o líder abre e volta sempre (é ele que
// decide a prova), mas a MAIORIA das tomadas é de outros cavalos. Antes o
// sujeito era sempre o primeiro colocado e só o ângulo mudava — a live passava
// a corrida inteira olhando o mesmo animal, de dois jeitos.
const RODIZIO_DE_QUADROS = [
  "PONTA", "PERSEGUICAO", "PELOTAO", "PONTA", "SUBINDO",
  "LANTERNA", "PONTA", "PERSEGUICAO", "SUBINDO", "PELOTAO",
];
const DURACAO_DO_QUADRO = 9.0;   // segundos por tomada
const AMOSTRA_DE_POSICOES = 6.0; // de quanto em quanto se mede "quem vem subindo"

// Legenda do quadro, mostrada no HUD: um corte para o último colocado sem
// explicação parece defeito; com a etiqueta, é transmissão.
const LEGENDA_DO_QUADRO = {
  PONTA: "NA PONTA",
  PERSEGUICAO: "A PERSEGUIÇÃO",
  PELOTAO: "O PELOTÃO",
  SUBINDO: "VEM SUBINDO",
  LANTERNA: "NA LANTERNA",
  PRESENTE: "PRESENTE",
  CHEGADA: "CHEGADA",
};

class CinematicCameraDirector {
  constructor(camera, trackScene, horseManager) {
    this.camera = camera;
    this.scene = trackScene;
    this.horseManager = horseManager;

    this.mode = "CAM_START"; // CAM_START, CAM_CHASE, CAM_SIDE, CAM_WIDE, CAM_DUEL, CAM_FINISH, CAM_PODIUM

    // Quem está na tela e por quê (o HUD lê `this.foco` para legendar o quadro).
    this.sujeito = null;   // id do cavalo enquadrado agora
    this.motivo = "PONTA"; // motivo do quadro atual (ver LEGENDA_DO_QUADRO)
    this.foco = null;      // {id, numero, nome, motivo, legenda, doador, emoji}
    this._quadroTimer = 0; // tempo na tomada atual
    this._rotacaoIdx = -1; // posição no rodízio (vira 0 no primeiro quadro)
    this._estadoAnterior = null;
    // Quem manda no presente/ultrapassagem: assinatura dos boosts de cada
    // cavalo (o payload não traz id de boost) e posições de uma amostra atrás.
    this._boostsVistos = {};
    this._posicoes = {};
    this._ganhos = {};
    this._amostraTimer = 0;

    // A âncora da câmera de largada é o portal de chegada (fim da reta, na
    // física é onde fica a linha dos 3000m). Os offsets da câmera continuam
    // os mesmos em metros ABSOLUTOS da pista antiga — só a âncora mudou.
    this.gate = trackScene.finishLinePosition || { x: -450, y: 0, z: 190.99 };
    this.targetPos = new THREE.Vector3(this.gate.x - 65, 36, this.gate.z + 76.34);
    this.targetLookAt = new THREE.Vector3(this.gate.x + 5, 4.0, this.gate.z + 11.34);
    this.currentLookAt = new THREE.Vector3(this.gate.x + 5, 4.0, this.gate.z + 11.34);

    this.timer = 0;
    this.podiumAngle = 0;
    this.camera.position.set(this.gate.x - 65, 36, this.gate.z + 76.34);
    this.camera.lookAt(this.currentLookAt);
  }

  setMode(mode) {
    this.mode = mode;
  }

  /** Normal que aponta para FORA da pista no ponto (x, z) — para a câmera
   *  aberta não ficar no meio do gramado nem dentro da cerca. */
  _normalExterna(x, z) {
    const meiaReta = (this.scene.straightLen || 900.0) / 2.0;
    if (Math.abs(x) <= meiaReta) {
      // Reta: a normal é o próprio eixo z, apontando para o lado do ponto.
      const s = z >= 0 ? 1 : -1;
      return { x: 0, z: s };
    }
    // Curva: a normal sai do centro do oval.
    const r = Math.hypot(x, z) || 1.0;
    return { x: x / r, z: z / r };
  }

  /** Tira uma foto da ordem da pista; o ganho de posições vira o "VEM SUBINDO". */
  _amostrarPosicoes(ordem) {
    const agora = {};
    ordem.forEach((h, i) => { agora[h.id] = i + 1; });
    if (Object.keys(this._posicoes).length > 0) {
      for (const id of Object.keys(agora)) {
        const antes = this._posicoes[id];
        // Positivo = ganhou posições desde a amostra anterior (1º lugar = 1).
        if (antes !== undefined) this._ganhos[id] = antes - agora[id];
      }
    }
    this._posicoes = agora;
  }

  /** Quem mais subiu de posição na última amostra (ninguém subiu = penúltimo). */
  _quemVemSubindo(ordem) {
    let melhor = null;
    let melhorGanho = 0;
    for (const h of ordem) {
      const ganho = this._ganhos[h.id] || 0;
      if (ganho > melhorGanho) {
        melhorGanho = ganho;
        melhor = h;
      }
    }
    return melhor || ordem[Math.max(0, ordem.length - 2)];
  }

  /** O cavalo do quadro, segundo o motivo: ponta, 2º, meio do pelotão, quem
   *  subiu ou o último. Sempre um cavalo NA PISTA (quem cruzou sai da fila). */
  _sujeitoDoQuadro(motivo, ordem) {
    if (!ordem || ordem.length === 0) return null;
    switch (motivo) {
      case "PERSEGUICAO":
        return ordem.length > 1 ? ordem[1].id : ordem[0].id;
      case "PELOTAO":
        // O do MEIO do pelotão: é onde a corrida ferve sem ser a ponta.
        return ordem[Math.floor((ordem.length - 1) / 2)].id;
      case "SUBINDO":
        return this._quemVemSubindo(ordem).id;
      case "LANTERNA":
        return ordem[ordem.length - 1].id;
      case "PONTA":
      default:
        return ordem[0].id;
    }
  }

  /** Algum cavalo recebeu boost AGORA? Devolve o id do último que recebeu.
   *
   * O payload não traz id de boost nem tempo restante: o que denuncia um
   * presente novo é a lista de boosts CRESCER (ou a força subir, quando o
   * mesmo presente é reenviado e amplia o bônus). Queda de força é boost
   * vencendo — não é presente novo. */
  _presenteNovo(horses) {
    let achado = null;
    for (const h of horses) {
      const boosts = h.boosts || [];
      const forca = boosts.reduce((s, b) => s + (b.power || 0), 0);
      const visto = this._boostsVistos[h.id] || { qtd: 0, forca: 0, doador: null };
      const cresceu = boosts.length > visto.qtd || forca > visto.forca + 0.01;
      const trocouDoador =
        !!h.donor_name && h.donor_name !== visto.doador && forca >= visto.forca - 0.01;
      this._boostsVistos[h.id] = {
        qtd: boosts.length,
        forca,
        doador: h.donor_name || null,
      };
      if (boosts.length > 0 && (cresceu || trocouDoador)) achado = h.id;
    }
    return achado;
  }

  _escalar(horseId, motivo) {
    this.sujeito = horseId;
    this.motivo = motivo;
    this._quadroTimer = 0;
  }

  /** A direção de TV: escolhe QUEM está na tela (e por quê). */
  _dirigirQuadros(dt, horses, ordem) {
    this._quadroTimer += dt;
    this._amostraTimer += dt;
    if (this._amostraTimer >= AMOSTRA_DE_POSICOES) {
      this._amostraTimer = 0;
      this._amostrarPosicoes(ordem);
    }

    // 1. Presente caiu: a câmera VAI no cavalo que recebeu, na hora. É o
    //    momento de quem mandou o presente — e o único jeito de o doador se
    //    ver na tela. Corta mesmo no meio de outro quadro: presente manda.
    const presenteId = this._presenteNovo(horses);
    if (presenteId !== null && ordem.some((h) => h.id === presenteId)) {
      this._escalar(presenteId, "PRESENTE");
      return;
    }

    // 2. Tomada vencida: passa para o próximo quadro do rodízio.
    if (this.sujeito === null || this._quadroTimer >= DURACAO_DO_QUADRO) {
      this._rotacaoIdx = (this._rotacaoIdx + 1) % RODIZIO_DE_QUADROS.length;
      const motivo = RODIZIO_DE_QUADROS[this._rotacaoIdx];
      this._escalar(this._sujeitoDoQuadro(motivo, ordem), motivo);
      return;
    }

    // 3. Mesmo quadro, dono novo — e SEM reiniciar o relógio da tomada (senão
    //    o quadro nunca vence e a câmera empaca num motivo só). Troca de dono
    //    em dois casos: o cavalo da vez saiu da pista (cruzou a linha), ou o
    //    motivo é de disputa e a troca É a notícia. Nas tomadas de cor (pelotão,
    //    subindo, lanterna) o cavalo fica o resto da tomada: se a legenda do
    //    HUD mudasse a cada ultrapassagem, ela piscaria na tela.
    if (this.motivo !== "PRESENTE" && this.motivo !== "CHEGADA") {
      const aindaNaPista = this.sujeito !== null && ordem.some((h) => h.id === this.sujeito);
      const ehDisputa = this.motivo === "PONTA" || this.motivo === "PERSEGUICAO";
      if (!aindaNaPista || ehDisputa) {
        const novo = this._sujeitoDoQuadro(this.motivo, ordem);
        if (novo !== null) this.sujeito = novo;
      }
    }
  }

  /** O ângulo da câmera para o quadro atual. */
  _anguloDoQuadro() {
    switch (this.motivo) {
      case "PELOTAO":
        return "CAM_WIDE";
      case "PERSEGUICAO":
        return "CAM_DUEL";
      case "LANTERNA":
      case "SUBINDO":
        return "CAM_SIDE";
      case "PONTA":
        // Na ponta alterna perseguição e lateral, senão a tomada mais comum
        // do rodízio fica sempre com a mesma cara.
        return this._rotacaoIdx % 2 === 0 ? "CAM_CHASE" : "CAM_SIDE";
      case "PRESENTE":
      default:
        return "CAM_CHASE";
    }
  }

  update(dt, directorState, engineData) {
    this.timer += dt;

    const horses = engineData.horses || [];
    const activeHorses = horses.filter((h) => !h.finished);
    // Com a prova decidida, os que já cruzaram saem do quadro: o rodízio passa
    // a olhar quem ainda está correndo (é o que sobra para mostrar).
    const naPista = activeHorses.length > 0 ? activeHorses : horses;
    const ordem = naPista.slice().sort((a, b) => b.distance - a.distance);

    // Começou a corrida: a primeira leitura só MARCA o que já está na pista —
    // os presentes mandados na votação não são "presente novo" na largada.
    if (directorState === "RACING" && this._estadoAnterior !== "RACING") {
      this._presenteNovo(horses);
      this._posicoes = {};
      this._ganhos = {};
      this._amostrarPosicoes(ordem);
      this.sujeito = null;
      this._rotacaoIdx = -1;
      this._amostraTimer = 0;
    }
    this._estadoAnterior = directorState;

    const liderDaDisputa = ordem[0];
    const leaderHorseId = liderDaDisputa
      ? liderDaDisputa.id
      : (engineData.leader_horse_id || 1);
    const leaderPos = this.horseManager.getHorsePosition(leaderHorseId);
    const leaderRot = this.horseManager.getHorseRotationY(leaderHorseId);
    const winnerId = engineData.winner_horse_id || leaderHorseId;
    const winnerPos = this.horseManager.getHorsePosition(winnerId);

    // Cálculo do centro do pelotão para enquadrar todos os 8 cavalos
    let packCenterX = 0, packCenterY = 0, packCenterZ = 0;
    const trackedList = naPista;
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

    // 1. Seleção de Modo com base na fase da transmissão
    if (directorState === "VOTING" || directorState === "COUNTDOWN") {
      this.mode = "CAM_START";
      this.foco = null;
    } else if (directorState === "PODIUM" || directorState === "XP_REWARDS" || directorState === "LEADERBOARD") {
      this.mode = "CAM_PODIUM";
      this.foco = null;
    } else if (directorState === "RACING") {
      const currentTrackedHorse = horses.find((h) => h.id === leaderHorseId);
      const trackedDist = currentTrackedHorse ? currentTrackedHorse.distance : 0;
      // Gatilhos por fração da pista: 105m finais = ~3,7s (igual ao "895" da
      // pista de 1000m) e os 200m finais para quem ainda está na disputa.
      const trackLength = engineData.track_length || this.scene.trackLength || 3000.0;

      const winnerDefined = !!engineData.winner_horse_id;
      if (trackedDist >= trackLength - 105 && trackedDist < trackLength) {
        // Curva final do cavalo ativo rumo à linha (x=-450)
        this.mode = "CAM_FINISH";
        this.motivo = "CHEGADA";
      } else if (winnerDefined && activeHorses.length > 0 && trackedDist >= trackLength - 200) {
        // Vencedor já cruzou: fica na linha mostrando os PRÓXIMOS cruzamentos
        // (o alvo é o cavalo mais adiantado da disputa)
        this.mode = "CAM_FINISH";
        this.motivo = "CHEGADA";
      } else if (activeHorses.length === 0 && winnerDefined) {
        // Todos cruzaram, já foca no vencedor celebrando
        this.mode = "CAM_PODIUM";
      } else {
        // Rodízio de quadros: a câmera troca de cavalo (e de ângulo) no meio
        // da prova, em vez de ficar presa no primeiro colocado.
        this._dirigirQuadros(dt, horses, ordem);
        this.mode = this._anguloDoQuadro();
      }
    }

    // O quadro da vez, resolvido para o HUD: o sujeito é sempre um cavalo que
    // está na pista (a ponta pode ter mudado de dono no tick seguinte).
    const sujeitoId =
      this.sujeito !== null && naPista.some((h) => h.id === this.sujeito)
        ? this.sujeito
        : leaderHorseId;
    const sujeitoPos = this.horseManager.getHorsePosition(sujeitoId);
    const sujeitoRot = this.horseManager.getHorseRotationY(sujeitoId);
    const sujeitoFwdX = Math.sin(sujeitoRot);
    const sujeitoFwdZ = Math.cos(sujeitoRot);
    const sujeitoNormX = Math.cos(sujeitoRot);
    const sujeitoNormZ = -Math.sin(sujeitoRot);

    if (directorState === "RACING") {
      const alvo =
        naPista.find((h) => h.id === sujeitoId) ||
        horses.find((h) => h.id === sujeitoId) ||
        liderDaDisputa;
      this.foco = alvo
        ? {
            id: alvo.id,
            numero: alvo.number !== undefined ? alvo.number : alvo.id,
            nome: alvo.name || "",
            motivo: this.motivo,
            legenda: LEGENDA_DO_QUADRO[this.motivo] || this.motivo,
            doador: alvo.donor_name || null,
            emoji: alvo.gift_emoji || null,
          }
        : null;
    }

    // 2. Cálculo dos pontos de câmera
    switch (this.mode) {
      case "CAM_START": {
        // Deriva cinematográfica ao redor dos boxes de largada: no menu de
        // votação a câmera ficava 100% parada e parecia que a tela travou.
        // Órbita lenta (~22s por volta) + balanço vertical suave.
        const a = this.timer * 0.28;
        this.targetPos.set(
          this.gate.x - 65 + Math.cos(a) * 18.0,
          33.0 + Math.sin(a * 1.7) * 3.0,
          this.gate.z + 64.34 + Math.sin(a) * 14.0
        );
        // Olhar passeia devagar pelos boxes, sem perder a área de largada
        this.targetLookAt.set(this.gate.x + 2 + Math.sin(a * 0.9) * 4.0, 3.5, this.gate.z);
        break;
      }

      case "CAM_CHASE": {
        // Perseguição esportiva: logo atrás do cavalo DO QUADRO (nunca perde o
        // foco mesmo em disparadas com Galáxia!). No presente a tomada é mais
        // baixa e mais perto — o cavalo empurrado passa na cara do público.
        const ehPresente = this.motivo === "PRESENTE";
        const tras = ehPresente ? 34.0 : 48.0;
        const lado = ehPresente ? 12.0 : 16.0;
        const altura = ehPresente ? 17.0 : 26.0;
        this.targetPos.set(
          sujeitoPos.x - sujeitoFwdX * tras + sujeitoNormX * lado,
          sujeitoPos.y + altura,
          sujeitoPos.z - sujeitoFwdZ * tras + sujeitoNormZ * lado
        );
        this.targetLookAt.set(
          sujeitoPos.x + sujeitoFwdX * 5.0,
          sujeitoPos.y + 2.0,
          sujeitoPos.z + sujeitoFwdZ * 5.0
        );
        break;
      }

      case "CAM_SIDE": {
        // Visão lateral de transmissão de TV (helicóptero acompanhando o
        // cavalo do quadro). Na lanterna a tomada é rente ao chão: o último
        // colocado passando baixinho é o que dá drama ao fim do pelotão.
        const ehLanterna = this.motivo === "LANTERNA";
        const ladoLanterna = ehLanterna ? 34.0 : 46.0;
        const alturaLanterna = ehLanterna ? 15.0 : 28.0;
        this.targetPos.set(
          sujeitoPos.x - sujeitoFwdX * 12.0 + sujeitoNormX * ladoLanterna,
          sujeitoPos.y + alturaLanterna,
          sujeitoPos.z - sujeitoFwdZ * 12.0 + sujeitoNormZ * ladoLanterna
        );
        this.targetLookAt.set(
          sujeitoPos.x + sujeitoFwdX * 4.0,
          sujeitoPos.y + 2.0,
          sujeitoPos.z + sujeitoFwdZ * 4.0
        );
        break;
      }

      case "CAM_WIDE": {
        // Plano aberto do pelotão: câmera alta e por FORA da pista, olhando o
        // meio do grupo — é a tomada que mostra a corrida inteira de uma vez.
        const n = this._normalExterna(packCenterX, packCenterZ);
        this.targetPos.set(
          packCenterX + n.x * 92.0,
          packCenterY + 56.0,
          packCenterZ + n.z * 92.0
        );
        this.targetLookAt.set(packCenterX, packCenterY + 2.0, packCenterZ);
        break;
      }

      case "CAM_DUEL": {
        // Plano da perseguição: atrás do 2º colocado, olhando POR CIMA dele
        // para o líder — o perseguidor em primeiro plano e o líder na frente,
        // os dois no quadro. Um plano lateral no meio dos dois não cabe no
        // celular: 40m de vão em 9:16 joga um cavalo para fora de cada lado
        // (o enquadramento vertical é estreito), então a briga se mostra em
        // profundidade, como na transmissão de turfe.
        const segundo = ordem[1];
        const segPos = segundo ? this.horseManager.getHorsePosition(segundo.id) : leaderPos;
        const segRot = segundo ? this.horseManager.getHorseRotationY(segundo.id) : leaderRot;
        const segFwdX = Math.sin(segRot);
        const segFwdZ = Math.cos(segRot);
        const segNormX = Math.cos(segRot);
        const segNormZ = -Math.sin(segRot);
        const vao = Math.hypot(leaderPos.x - segPos.x, leaderPos.z - segPos.z);
        const tras = Math.min(70.0, 22.0 + vao * 0.6);
        this.targetPos.set(
          segPos.x - segFwdX * tras + segNormX * 11.0,
          segPos.y + 17.0 + Math.min(16.0, vao * 0.2),
          segPos.z - segFwdZ * tras + segNormZ * 11.0
        );
        this.targetLookAt.set(
          (segPos.x + leaderPos.x) / 2.0,
          (segPos.y + leaderPos.y) / 2.0 + 2.2,
          (segPos.z + leaderPos.z) / 2.0
        );
        break;
      }

      case "CAM_FINISH": {
        // Câmera de chegada ancorada na LINHA REAL da pista (x=-450):
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

window.CinematicCameraDirector = CinematicCameraDirector;
