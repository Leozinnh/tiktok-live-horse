import aiosqlite
from typing import List, Dict, Any, Optional
from backend.database.connection import DatabaseConnection
from backend.progression import calculate_level

class DatabaseRepository:
    def __init__(self, db_path: str = "race_game.db"):
        self.connection = DatabaseConnection(db_path)
        
    async def init_db(self) -> None:
        await self.connection.init_schema()
        
    async def get_or_create_viewer(self, tiktok_username: str, display_name: str) -> Dict[str, Any]:
        username = tiktok_username.strip().lower()
        name = display_name.strip() or username
        
        async with self.connection.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM viewers WHERE tiktok_username = ?", (username,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    if row["display_name"] != name:
                        await db.execute(
                            "UPDATE viewers SET display_name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                            (name, row["id"])
                        )
                        await db.commit()
                    return dict(row)
            
            # Cria novo viewer
            await db.execute(
                """
                INSERT INTO viewers (tiktok_username, display_name, xp, level, races_count, wins_count)
                VALUES (?, ?, 0, 1, 0, 0)
                """,
                (username, name)
            )
            await db.commit()
            
            async with db.execute(
                "SELECT * FROM viewers WHERE tiktok_username = ?", (username,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row)

    async def create_race(self, race_number: int) -> int:
        async with self.connection.get_connection() as db:
            cursor = await db.execute(
                "INSERT INTO races (race_number, status) VALUES (?, 'VOTING')",
                (race_number,)
            )
            await db.commit()
            return cursor.lastrowid

    async def record_choice(self, race_id: int, viewer_id: int, horse_id: int) -> bool:
        async with self.connection.get_connection() as db:
            try:
                await db.execute(
                    """
                    INSERT INTO race_choices (race_id, viewer_id, horse_id)
                    VALUES (?, ?, ?)
                    ON CONFLICT(race_id, viewer_id) DO UPDATE SET horse_id = excluded.horse_id
                    """,
                    (race_id, viewer_id, horse_id)
                )
                await db.commit()
                return True
            except Exception:
                return False

    async def get_race_choices(self, race_id: int) -> List[Dict[str, Any]]:
        async with self.connection.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT rc.horse_id, rc.viewer_id, v.tiktok_username, v.display_name, v.level
                FROM race_choices rc
                JOIN viewers v ON rc.viewer_id = v.id
                WHERE rc.race_id = ?
                """,
                (race_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def finish_race(self, race_id: int, winner_horse_id: int, results: List[Dict[str, Any]]) -> None:
        async with self.connection.get_connection() as db:
            await db.execute(
                """
                UPDATE races 
                SET status = 'FINISHED', winner_horse_id = ?, finished_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (winner_horse_id, race_id)
            )
            
            for res in results:
                await db.execute(
                    """
                    INSERT INTO race_results (race_id, horse_id, final_position, finish_time_ms)
                    VALUES (?, ?, ?, ?)
                    """,
                    (race_id, res["horse_id"], res["final_position"], res.get("finish_time_ms", 0))
                )
            await db.commit()

    async def distribute_race_xp(
        self,
        race_id: int,
        winner_horse_id: int,
        top_3_horse_ids: List[int],
        xp_participation: int = 20,
        xp_win: int = 150,
        xp_top3: int = 50
    ) -> List[Dict[str, Any]]:
        updated_viewers = []
        async with self.connection.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT rc.viewer_id, rc.horse_id, v.xp, v.level, v.races_count, v.wins_count, v.display_name, v.tiktok_username
                FROM race_choices rc
                JOIN viewers v ON rc.viewer_id = v.id
                WHERE rc.race_id = ?
                """,
                (race_id,)
            ) as cursor:
                choices = await cursor.fetchall()
                
            for row in choices:
                viewer_id = row["viewer_id"]
                chosen_horse = row["horse_id"]
                old_xp = row["xp"]
                
                earned_xp = xp_participation
                won = (chosen_horse == winner_horse_id)
                top3 = (chosen_horse in top_3_horse_ids)
                
                if won:
                    earned_xp += xp_win
                elif top3:
                    earned_xp += xp_top3
                    
                new_xp = old_xp + earned_xp
                new_level = calculate_level(new_xp)
                new_races = row["races_count"] + 1
                new_wins = row["wins_count"] + (1 if won else 0)
                
                await db.execute(
                    """
                    UPDATE viewers
                    SET xp = ?, level = ?, races_count = ?, wins_count = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (new_xp, new_level, new_races, new_wins, viewer_id)
                )
                
                updated_viewers.append({
                    "id": viewer_id,
                    "tiktok_username": row["tiktok_username"],
                    "display_name": row["display_name"],
                    "xp": new_xp,
                    "earned_xp": earned_xp,
                    "level": new_level,
                    "level_up": new_level > row["level"],
                    "wins_count": new_wins,
                    "won": won
                })
                
            await db.commit()
            return updated_viewers

    async def add_gift_xp(self, viewer_id: int, xp_amount: int) -> Dict[str, Any]:
        async with self.connection.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM viewers WHERE id = ?", (viewer_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return {}
            
            new_xp = row["xp"] + xp_amount
            new_level = calculate_level(new_xp)
            await db.execute(
                "UPDATE viewers SET xp = ?, level = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_xp, new_level, viewer_id)
            )
            await db.commit()
            return {
                "id": viewer_id,
                "tiktok_username": row["tiktok_username"],
                "display_name": row["display_name"],
                "xp": new_xp,
                "level": new_level,
                "level_up": new_level > row["level"]
            }

    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        async with self.connection.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT id, tiktok_username, display_name, xp, level, races_count, wins_count
                FROM viewers
                ORDER BY xp DESC, wins_count DESC
                LIMIT ?
                """,
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_all_viewers(self, limit: int = 500) -> List[Dict[str, Any]]:
        """Lista todos os espectadores cadastrados (painel admin /test)."""
        async with self.connection.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT id, tiktok_username, display_name, xp, level, races_count, wins_count, created_at, updated_at
                FROM viewers
                ORDER BY xp DESC, wins_count DESC
                LIMIT ?
                """,
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def reset_viewer(self, viewer_id: int) -> bool:
        """Zera XP, nível e estatísticas de um espectador (mantém a identidade)."""
        async with self.connection.get_connection() as db:
            cursor = await db.execute(
                """
                UPDATE viewers
                SET xp = 0, level = 1, races_count = 0, wins_count = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (viewer_id,)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def reset_all_viewers(self) -> int:
        """Zera XP, nível e estatísticas de TODOS os espectadores. Retorna quantos foram zerados."""
        async with self.connection.get_connection() as db:
            cursor = await db.execute(
                """
                UPDATE viewers
                SET xp = 0, level = 1, races_count = 0, wins_count = 0, updated_at = CURRENT_TIMESTAMP
                """
            )
            await db.commit()
            return cursor.rowcount
