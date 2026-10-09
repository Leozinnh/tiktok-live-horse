import sys
import os
import argparse
import asyncio
import logging
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI

from config.settings import load_config
from backend.database.repository import DatabaseRepository
from game.engine import RaceEngine
from game.director import EventDirector
from game.narrador import Narrador
from tiktok.mock_adapter import MockTikTokAdapter
from tiktok.adapter import TikTokLiveAdapter
from web.server import create_app, run_simulation_loop

# Quando a saída é redirecionada para arquivo/serviço, o stdout do Windows cai
# para cp1252 e o banner com emojis derruba o boot com UnicodeEncodeError.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
# Bibliotecas barulhentas: o httpx loga TODA requisição (com a URL gigante do
# TikTok) em INFO e enterra as mensagens que importam. Só erro de verdade passa.
for _ruidoso in ("httpx", "httpcore", "websockets", "TikTokLive", "uvicorn.access"):
    logging.getLogger(_ruidoso).setLevel(logging.WARNING)

logger = logging.getLogger("live")

def str_to_bool(value: str) -> bool:
    """Converte valores de CLI ('True'/'False', '1'/'0') em booleano."""
    return str(value).strip().lower() not in ("false", "0", "no", "off")

def parse_args():
    parser = argparse.ArgumentParser(description="TikTok LIVE - Jogo de Corrida de Cavalos Interativo")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Endereço de escuta do servidor (padrão: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Porta HTTP/WebSocket (padrão: 8000)")
    parser.add_argument("--db-path", type=str, default="race_game.db", help="Caminho do banco SQLite (padrão: race_game.db)")
    parser.add_argument("--tiktok-user", type=str, default=None, help="Nome de usuário do TikTok LIVE (ex: seunome)")
    parser.add_argument("--test-mode", type=str_to_bool, nargs="?", const=True, default=True,
                        help="Modo de teste sem TikTok ao vivo (padrão: True). Use --test-mode=False para conectar ao TikTok real")
    return parser.parse_args()

def print_welcome_banner(port: int, tiktok_user: str | None):
    print("=" * 72)
    print("🏇  TIKTOK LIVE - CORRIDA DE CAVALOS INTERATIVA (60 FPS 3D)  🏇")
    print("=" * 72)
    print(f"  📺 OBS Browser Source:       http://localhost:{port}/")
    print(f"     Configuração no OBS:      Largura 1080 | Altura 1920 | 60 FPS")
    print(f"  🎮 Painel de Testes (Stream): http://localhost:{port}/test")
    print(f"  🔌 Conexão TikTok LIVE:      {f'@{tiktok_user}' if tiktok_user else 'MODO DE TESTE ATIVO'}")
    print(f"  ⭐ Princípio de Compliance:   Pontos 100% VIRTUAIS (Sem dinheiro/apostas)")
    print("=" * 72)
    print("Pressione Ctrl+C para encerrar o servidor com segurança.")
    print("=" * 72 + "\n")

def main():
    args = parse_args()
    config = load_config()
    
    # 1. Banco de Dados SQLite
    repo = DatabaseRepository(db_path=args.db_path)
    
    # 2. Motor de Corrida e Diretor (+ a voz da live, se ligada no config)
    narrador = Narrador(config.tts)
    engine = RaceEngine(config)
    director = EventDirector(config=config, engine=engine, repository=repo, narrador=narrador)
    
    # 3. Adaptadores
    mock_adapter = MockTikTokAdapter(director)
    tiktok_adapter = None
    if args.tiktok_user and not args.test_mode:
        tiktok_adapter = TikTokLiveAdapter(tiktok_username=args.tiktok_user, director=director)

    # 4. Servidor FastAPI (o ciclo de vida vive no lifespan — `on_event` está deprecado)
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # --- Startup ---
        # Inicializa tabelas
        await repo.init_db()
        logger.info(f"Banco de dados SQLite inicializado em '{args.db_path}'")

        # Inicia loop contínuo de simulação a 60 ticks/s
        asyncio.create_task(run_simulation_loop(director, app.state.manager, config.tick_rate))
        logger.info(f"Loop de corrida autônomo iniciado a {config.tick_rate} ticks/s.")

        # Sobe a thread da voz (inativo no config = nem sobe)
        narrador.ligar()
        if config.tts.active:
            logger.info(
                "🔊 Narração por voz LIGADA — as falas saem pelo áudio padrão do Windows "
                "(no OBS: Áudio do Desktop ou Captura de Áudio do Aplicativo no python.exe)."
            )
        else:
            logger.info("🔇 Narração por voz desligada (config: tts.active = false).")

        # Conecta ao TikTok se configurado
        if tiktok_adapter:
            asyncio.create_task(tiktok_adapter.start())
            logger.info(f"Conexão assíncrona ao TikTok LIVE disparada para @{args.tiktok_user}")

        yield

        # --- Shutdown ---
        # Corta a fala em andamento e a thread da voz, e encerra a reconexão do TikTok.
        narrador.parar()
        if tiktok_adapter:
            tiktok_adapter.stop()

    app = create_app(config, director, mock_adapter, repo, lifespan=lifespan)

    print_welcome_banner(args.port, args.tiktok_user)
    
    # 5. Execução do Servidor Uvicorn
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")

if __name__ == "__main__":
    main()
