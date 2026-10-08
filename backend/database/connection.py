import aiosqlite
from pathlib import Path
from backend.database.models import CREATE_TABLES_SQL

class DatabaseConnection:
    def __init__(self, db_path: str = "race_game.db"):
        self.db_path = db_path
        
    def get_connection(self):
        return aiosqlite.connect(self.db_path)

    async def init_schema(self) -> None:
        # Garante diretório pai se existir caminho
        path = Path(self.db_path)
        if path.parent and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.executescript(CREATE_TABLES_SQL)
            await db.commit()
