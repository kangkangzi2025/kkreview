"""SQLite database operations for kkreview."""

import json
import sqlite3
from pathlib import Path
from uuid import uuid4

from .models import EvaluationResult, GeneratedChallenge

DATA_DIR = Path.home() / ".kkreview"
DB_PATH = DATA_DIR / "kkreview.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS config (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id              TEXT PRIMARY KEY,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    language        TEXT NOT NULL,
    category        TEXT NOT NULL,
    difficulty      TEXT NOT NULL,
    code_snippet    TEXT NOT NULL,
    hidden_issues   TEXT NOT NULL,
    user_findings   TEXT NOT NULL,
    evaluation      TEXT NOT NULL,
    score           REAL NOT NULL,
    found_count     INTEGER NOT NULL,
    total_count     INTEGER NOT NULL,
    false_positives INTEGER NOT NULL DEFAULT 0,
    duration_secs   INTEGER
);

CREATE TABLE IF NOT EXISTS category_stats (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    category        TEXT NOT NULL,
    subcategory     TEXT NOT NULL,
    times_tested    INTEGER NOT NULL DEFAULT 0,
    times_found     INTEGER NOT NULL DEFAULT 0,
    last_tested_at  TEXT,
    UNIQUE(category, subcategory)
);
"""


class Database:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self):
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self):
        self.conn.close()

    # -- Config --

    def get_config(self, key: str, default: str | None = None) -> str | None:
        row = self.conn.execute(
            "SELECT value FROM config WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

    def set_config(self, key: str, value: str):
        self.conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (key, value),
        )
        self.conn.commit()

    def get_all_config(self) -> dict[str, str]:
        rows = self.conn.execute("SELECT key, value FROM config").fetchall()
        return {row["key"]: row["value"] for row in rows}

    # -- Sessions --

    def save_session(
        self,
        challenge: GeneratedChallenge,
        difficulty: str,
        user_findings: str,
        evaluation: EvaluationResult,
        duration_secs: int | None = None,
    ) -> str:
        session_id = str(uuid4())
        self.conn.execute(
            """INSERT INTO sessions
            (id, language, category, difficulty, code_snippet, hidden_issues,
             user_findings, evaluation, score, found_count, total_count,
             false_positives, duration_secs)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                challenge.language,
                challenge.issues[0].category if challenge.issues else "mixed",
                difficulty,
                challenge.code,
                json.dumps([i.model_dump() for i in challenge.issues]),
                user_findings,
                evaluation.model_dump_json(),
                evaluation.score,
                evaluation.found_count,
                evaluation.total_count,
                len(evaluation.false_positives),
                duration_secs,
            ),
        )
        self.conn.commit()
        return session_id

    def get_sessions(
        self,
        limit: int = 10,
        category: str | None = None,
        language: str | None = None,
    ) -> list[dict]:
        query = "SELECT * FROM sessions WHERE 1=1"
        params: list = []
        if category:
            query += " AND category = ?"
            params.append(category)
        if language:
            query += " AND language = ?"
            params.append(language)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = self.conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_session_count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) as cnt FROM sessions").fetchone()
        return row["cnt"]

    def get_average_score(self) -> float | None:
        row = self.conn.execute("SELECT AVG(score) as avg FROM sessions").fetchone()
        return row["avg"]

    def get_best_score(self) -> float | None:
        row = self.conn.execute("SELECT MAX(score) as best FROM sessions").fetchone()
        return row["best"]

    # -- Category Stats --

    def update_category_stats(self, category: str, subcategory: str, found: bool):
        self.conn.execute(
            """INSERT INTO category_stats (category, subcategory, times_tested, times_found, last_tested_at)
            VALUES (?, ?, 1, ?, datetime('now'))
            ON CONFLICT(category, subcategory) DO UPDATE SET
                times_tested = times_tested + 1,
                times_found = times_found + ?,
                last_tested_at = datetime('now')""",
            (category, subcategory, int(found), int(found)),
        )
        self.conn.commit()

    def get_category_stats(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM category_stats ORDER BY category, subcategory"
        ).fetchall()
        return [dict(row) for row in rows]

    def get_category_summary(self) -> list[dict]:
        rows = self.conn.execute(
            """SELECT category,
                      SUM(times_tested) as tested,
                      SUM(times_found) as found,
                      CASE WHEN SUM(times_tested) > 0
                           THEN ROUND(CAST(SUM(times_found) AS REAL) / SUM(times_tested) * 100, 1)
                           ELSE 0 END as accuracy
               FROM category_stats
               GROUP BY category
               ORDER BY accuracy ASC"""
        ).fetchall()
        return [dict(row) for row in rows]
