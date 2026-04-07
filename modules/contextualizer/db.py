"""
db.py — SQLite helpers для таблицы source_files.
Глобальное хранилище исходников: один файл (по SHA-256) на весь сервер.
"""

import os
import sqlite3 as sq

from dotenv import load_dotenv

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))

# Загружаем .env относительно корня проекта
load_dotenv(os.path.normpath(os.path.join(_THIS_DIR, "../../.env")), override=False)

# DB_PATH: env-переменная задаёт путь относительно server/
_DB_RAW = os.getenv("DATABASE_NAME", "files/koritsu.db").strip()
_SERVER_DIR = os.path.normpath(os.path.join(_THIS_DIR, "../../server"))
DB_PATH = _DB_RAW if os.path.isabs(_DB_RAW) else os.path.join(_SERVER_DIR, _DB_RAW)

# Папка с глобальными исходниками
SOURCES_BASE = os.path.normpath(os.path.join(_THIS_DIR, "../../server/files/sources"))


def _get_db() -> sq.Connection:
    conn = sq.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sq.Row
    return conn


def init_source_files_table() -> None:
    """Создать таблицу source_files если не существует."""
    conn = _get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS source_files (
            hash              TEXT PRIMARY KEY,
            original_filename TEXT NOT NULL,
            file_type         TEXT NOT NULL,
            stored_path       TEXT NOT NULL,
            created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
            text_content      TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_source_by_hash(file_hash: str) -> dict | None:
    """Найти исходник по SHA-256. Возвращает None если не найден."""
    conn = _get_db()
    row = conn.execute(
        "SELECT * FROM source_files WHERE hash = ?", (file_hash,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def save_source(
    file_hash: str,
    original_filename: str,
    file_type: str,
    stored_path: str,
    text_content: str | None = None,
) -> None:
    """Сохранить или обновить запись об исходнике."""
    conn = _get_db()
    conn.execute(
        """
        INSERT OR REPLACE INTO source_files
            (hash, original_filename, file_type, stored_path, text_content)
        VALUES (?, ?, ?, ?, ?)
        """,
        (file_hash, original_filename, file_type, stored_path, text_content),
    )
    conn.commit()
    conn.close()


# Инициализация при импорте модуля
init_source_files_table()
