import pytest
from starlette.testclient import TestClient
from config.settings import load_config
from backend.database.repository import DatabaseRepository
from game.engine import RaceEngine
from game.director import EventDirector
from tiktok.mock_adapter import MockTikTokAdapter

@pytest.fixture
def test_app(tmp_path):
    from web.server import create_app
    
    config = load_config()
    db_file = tmp_path / "test_server.db"
    repo = DatabaseRepository(str(db_file))
    
    import asyncio
    asyncio.run(repo.init_db())
    
    engine = RaceEngine(config)
    director = EventDirector(config, engine, repo)
    mock_adapter = MockTikTokAdapter(director)
    
    app = create_app(config, director, mock_adapter, repo)
    return app

def test_api_state_and_test_injection(test_app):
    client = TestClient(test_app)
    
    # Verifica endpoint /api/state
    res = client.get("/api/state")
    assert res.status_code == 200
    data = res.json()
    assert "director_state" in data
    assert "engine" in data
    assert len(data["engine"]["horses"]) == 8
    
    # Injeta comentário de teste
    comment_payload = {
        "username": "tester1",
        "display_name": "Tester Um",
        "text": "1"
    }
    res_post = client.post("/api/test/inject_comment", json=comment_payload)
    assert res_post.status_code == 200
    res_json = res_post.json()
    assert res_json["status"] == "ok"
    assert res_json["horse_id"] == 1
    
    # Injeta presente de teste
    gift_payload = {
        "username": "tester1",
        "display_name": "Tester Um",
        "gift_name": "Rose",
        "count": 1
    }
    res_gift = client.post("/api/test/inject_gift", json=gift_payload)
    assert res_gift.status_code == 200
    assert res_gift.json()["status"] == "ok"

    # Injeta entrada de espectador de teste
    join_payload = {
        "username": "tester_join",
        "display_name": "Tester Entrou"
    }
    res_join = client.post("/api/test/inject_join", json=join_payload)
    assert res_join.status_code == 200
    assert res_join.json()["status"] == "ok"

    # Injeta seguidor de teste
    follow_payload = {
        "username": "tester_follow",
        "display_name": "Tester Seguiu"
    }
    res_follow = client.post("/api/test/inject_follow", json=follow_payload)
    assert res_follow.status_code == 200
    assert res_follow.json()["status"] == "ok"


def _boosts_of_horse(client, horse_id: int):
    data = client.get("/api/state").json()
    horse = next(h for h in data["engine"]["horses"] if h["id"] == horse_id)
    return horse["boosts"]


def test_gift_power_scales_with_value_and_count(test_app):
    client = TestClient(test_app)

    def last_boost(horse_id=1):
        return _boosts_of_horse(client, horse_id)[-1]

    # O doador ESCOLHE o cavalo 1: sem escolha, o presente cai num cavalo
    # sorteado (ver test_director.py) e o teste não teria onde ler o boost.
    client.post("/api/test/inject_comment", json={
        "username": "doador", "display_name": "Doador", "text": "1"})

    # Rosa x1 -> 1.20 | Rosa x10: +10% do delta por unidade extra (teto de 5) -> 1.30
    client.post("/api/test/inject_gift", json={
        "username": "doador", "display_name": "Doador", "gift_name": "Rose", "count": 1})
    assert last_boost()["power"] == 1.2

    client.post("/api/test/inject_gift", json={
        "username": "doador", "display_name": "Doador", "gift_name": "Rose", "count": 10})
    assert last_boost()["power"] == 1.3

    # Leão x1 -> 1.70 | Leão x100 estoura o teto -> 1.80
    client.post("/api/test/inject_gift", json={
        "username": "doador", "display_name": "Doador", "gift_name": "Lion", "count": 1})
    assert last_boost()["power"] == 1.7
    assert last_boost()["legendary"] is True

    client.post("/api/test/inject_gift", json={
        "username": "doador", "display_name": "Doador", "gift_name": "Lion", "count": 100})
    assert last_boost()["power"] == 1.8


def test_turbo_manual_do_admin_dura_o_que_a_live_ve(test_app):
    """O turbo manual do painel tem de ser VISÍVEL na prova, não um piscar.

    O endpoint tinha 1.2x por 4s cravado — calibrado para a prova de 1000m
    (~35s). Com a pista de 3000m (~110s), 4s são 3% da corrida: o cavalo
    dava um soquinho e o efeito sumia antes de a live perceber. Agora ele
    sai da tabela de presentes (mesmo Super Boost do Boné/Donut).
    """
    from game.director import GIFT_TIERS

    client = TestClient(test_app)
    prova = load_config().race_duration_seconds

    res = client.post("/api/test/boost_horse?horse_id=5")
    assert res.status_code == 200
    dados = res.json()
    assert dados["horse_name"], "a resposta precisa dizer em qual cavalo bateu"
    assert dados["power"] >= 1.3
    assert dados["duration"] >= prova * 0.10, "turbo some antes de a live ver"

    # É o MESMO Super Boost do Boné: se a tabela mudar, isto acompanha.
    super_boost = next(t for t in GIFT_TIERS if "cap" in t["keywords"])
    assert dados["power"] == super_boost["power"]
    assert dados["duration"] == super_boost["duration"]

    boosts = _boosts_of_horse(client, 5)
    assert any(b["name"] == "ADMIN_BOOST" for b in boosts)

    # Cavalo que não existe: erro, não um "ok" mentiroso.
    assert client.post("/api/test/boost_horse?horse_id=99").status_code == 404


def test_hud_config_e_um_ajuste_que_soma(test_app):
    """O `top` do HUD é a altura da coluna de avisos — e o ajuste é incremental.

    O painel mandava `top` e o HUD ignorava o campo (a classificação já está
    ancorada no rodapé): mexia no número e nada saía do lugar na tela do OBS.
    Agora o `top` vale e o padrão do servidor é o mesmo 195px do CSS — quem
    abrir a transmissão vê os avisos onde sempre estiveram.
    """
    client = TestClient(test_app)

    assert test_app.state.hud_config["top"] == 195

    res = client.post("/api/test/hud_config", json={"scale": 1.2, "top": 120})
    assert res.status_code == 200
    config = res.json()["config"]
    assert config["scale"] == 1.2
    assert config["top"] == 120
    # O ajuste é um MERGE: o que não veio no corpo continua valendo.
    assert config["bottom"] == 24
    assert config["showProgress"] is True


def test_painel_tem_uma_identidade_so():
    """Um nome para o painel inteiro: o do voto é o do presente.

    Havia dois campos — "Nome do Espectador" (Leonardo) e "Nome do Doador"
    (João_Silva) — com valores diferentes de fábrica. Quem votava no #7 e
    mandava a galáxia via o voto sair como @leonardo e o presente como
    @joão_silva: dois espectadores para a mesma pessoa, e o caminho "votei
    aqui, o presente cai aqui" (o que a live vê) não fechava nunca.
    """
    from pathlib import Path

    raiz = Path(__file__).resolve().parents[1]
    html = (raiz / "web" / "static" / "test.html").read_text(encoding="utf-8")
    js = (raiz / "web" / "static" / "js" / "test_panel.js").read_text(encoding="utf-8")

    assert 'id="viewerUser"' in html, "falta o campo de identidade do painel"
    assert "Nome do Doador" not in html, "sobrou rótulo de identidade paralela"
    for orfao in ("commentUser", "giftUser"):
        assert orfao not in html, f"sobrou campo de identidade paralela: {orfao}"
        assert orfao not in js, f"sobrou campo de identidade paralela: {orfao}"

    # E ninguém lê o nome por fora da identidade única.
    assert js.count("identidade()") >= 5, "alguma ação do painel ficou sem o nome único"

    # Toda ação do painel passa pela identidade única.
    for endpoint in (
        "/api/test/inject_comment",
        "/api/test/inject_gift",
        "/api/test/inject_like",
        "/api/test/inject_join",
        "/api/test/inject_follow",
    ):
        assert endpoint in js


def test_painel_e_hud_nunca_vem_do_cache_do_navegador(test_app):
    """O navegador não pode servir o JS velho por conta própria.

    Aconteceu na reforma do painel: o /test abriu com o HTML novo e o
    test_panel.js ANTIGO em cache. O cartão "Corrida ao Vivo" ficou
    eternamente em "aguardando a largada…" (o JS velho nem conhecia o cartão) e
    o botão de pular votação respondia com a frase antiga — com o WebSocket
    conectado e tudo o mais parecendo certo. Durante a live isso é o pior tipo
    de defeito: parece que o código novo não funciona. `no-cache` obriga o
    navegador a revalidar (o ETag responde 304 quando nada mudou).
    """
    client = TestClient(test_app)

    for rota in ("/test", "/", "/static/js/test_panel.js", "/static/css/test_panel.css",
                 "/static/js/hud.js", "/api/state"):
        res = client.get(rota)
        assert res.status_code == 200, rota
        assert "no-cache" in res.headers.get("cache-control", ""), (
            f"{rota} pode ser servido do cache do navegador"
        )


def test_todo_botao_do_painel_chama_funcao_que_existe():
    """Botão do painel nunca pode ficar órfão.

    Os botões chamam as funções por `onclick` no HTML: renomear ou apagar uma
    função do JS derruba o botão em silêncio (o navegador só reclama no
    console, quando alguém clica — no meio da live). Foi assim que a rajada
    de curtidas ficou sem função numa das limpezas do painel.
    """
    import re
    from pathlib import Path

    raiz = Path(__file__).resolve().parents[1]
    html = (raiz / "web" / "static" / "test.html").read_text(encoding="utf-8")
    js = (raiz / "web" / "static" / "js" / "test_panel.js").read_text(encoding="utf-8")

    chamadas = set(re.findall(r'on(?:click|input|change)="([A-Za-z_$][\w$]*)\(', html))
    assert chamadas, "nenhum botão encontrado — o regex do teste quebrou?"

    for nome in sorted(chamadas):
        assert re.search(rf"function\s+{re.escape(nome)}\s*\(", js), (
            f"o painel chama {nome}() e ela não existe no test_panel.js"
        )


def _like_boosts(client):
    """Todos os boosts de curtida da pista — sem autor identificável, o
    empurrão cai num cavalo SORTEADO, então o teste procura em toda a pista."""
    achados = []
    for horse_id in range(1, 9):
        achados += [
            b for b in _boosts_of_horse(client, horse_id) if b["name"] == "GALERA CURTIU"
        ]
    return achados


def test_like_burst_gives_light_boost(test_app):
    from game.director import LIKE_EXTRA_SPEED

    client = TestClient(test_app)

    # Rajada de 5+ curtidas de quem não escolheu cavalo: empurrão bem leve,
    # somado como VELOCIDADE DIRETA (+0.2 m/s), nunca como multiplicador.
    res = client.post("/api/test/inject_like", json={
        "username": "torcedor", "display_name": "Torcedor", "count": 5})
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    like_boosts = _like_boosts(client)
    assert len(like_boosts) == 1
    assert like_boosts[0]["power"] == LIKE_EXTRA_SPEED
    assert like_boosts[0]["additive"] is True
    assert like_boosts[0]["emoji"] == "❤️"

    # Rajada maior não empurra mais forte: o extra por rajada é fixo — quem
    # cresce é a SOMA (sem teto, ver horses.py).
    client.post("/api/test/inject_like", json={
        "username": "torcedor", "display_name": "Torcedor", "count": 30})
    potencias = sorted(b["power"] for b in _like_boosts(client))
    assert potencias == [LIKE_EXTRA_SPEED, LIKE_EXTRA_SPEED]

    # Menos de 5 de uma vez: nenhum boost
    client.post("/api/test/inject_like", json={
        "username": "torcedor", "display_name": "Torcedor", "count": 4})
    assert len(_like_boosts(client)) == 2

    # Curtida não cria usuário nem rende XP/estatística
    names = [v["tiktok_username"] for v in client.get("/api/test/viewers").json()["viewers"]]
    assert "torcedor" not in names


def test_like_burst_goes_to_supporters_horse(test_app):
    client = TestClient(test_app)

    # Espectador escolhe o cavalo 3 e depois manda curtidas: boost vai para o cavalo dele
    client.post("/api/test/inject_comment", json={
        "username": "fa", "display_name": "Fã", "text": "3"})
    client.post("/api/test/inject_like", json={
        "username": "fa", "display_name": "Fã", "count": 10})

    boosts = _boosts_of_horse(client, 3)
    assert any(b["name"] == "GALERA CURTIU" for b in boosts)
    assert not any(b["name"] == "GALERA CURTIU" for b in _boosts_of_horse(client, 1))


def test_viewers_list_and_reset(test_app):
    client = TestClient(test_app)

    # Cria um usuário com XP via presente
    client.post("/api/test/inject_gift", json={
        "username": "vitima", "display_name": "Vítima", "gift_name": "Rose", "count": 2})

    data = client.get("/api/test/viewers").json()
    assert data["total"] >= 1
    viewer = next(v for v in data["viewers"] if v["tiktok_username"] == "vitima")
    assert viewer["xp"] > 0

    # Zera só esse usuário
    res = client.post("/api/test/reset_viewer", json={"viewer_id": viewer["id"]})
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    viewer = next(v for v in client.get("/api/test/viewers").json()["viewers"] if v["id"] == viewer["id"])
    assert (viewer["xp"], viewer["level"], viewer["races_count"], viewer["wins_count"]) == (0, 1, 0, 0)

    # ID inexistente -> 404
    res = client.post("/api/test/reset_viewer", json={"viewer_id": 999999})
    assert res.status_code == 404

    # Zerar todos
    client.post("/api/test/inject_gift", json={
        "username": "outro", "display_name": "Outro", "gift_name": "Lion", "count": 1})
    res = client.post("/api/test/reset_all_viewers")
    assert res.status_code == 200
    assert res.json()["reset_count"] >= 2

    for v in client.get("/api/test/viewers").json()["viewers"]:
        assert (v["xp"], v["level"], v["races_count"], v["wins_count"]) == (0, 1, 0, 0)
