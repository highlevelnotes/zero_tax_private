# db.py
import os
import sqlite3
from contextlib import contextmanager
from typing import Iterable, Dict, Any, List, Tuple

DB_PATH = os.environ.get("APP_DB_PATH", "app.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            qty INTEGER NOT NULL DEFAULT 0,
            price REAL NOT NULL DEFAULT 0.0,
            note TEXT
        )
        """)
        cur.execute("SELECT COUNT(*) FROM items")
        if cur.fetchone()[0] == 0:
            cur.executemany(
                "INSERT INTO items (name, qty, price, note) VALUES (?, ?, ?, ?)",
                [
                    ("사과", 10, 1.2, "신선"),
                    ("바나나", 6, 0.8, "묶음"),
                    ("배", 4, 2.0, None),
                ],
            )
        conn.commit()

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        yield conn
        conn.commit()
    finally:
        conn.close()

def fetch_all() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, qty, price, note FROM items ORDER BY id")
        rows = cur.fetchall()
        return [dict(r) for r in rows]

def insert_rows(rows: Iterable[Dict[str, Any]]) -> None:
    rows = list(rows)
    if not rows:
        return
    with get_conn() as conn:
        cur = conn.cursor()
        cur.executemany(
            "INSERT INTO items (name, qty, price, note) VALUES (?, ?, ?, ?)",
            [
                (
                    r.get("name") or "New",
                    int(r.get("qty") or 0),
                    float(r.get("price") or 0.0),
                    r.get("note"),
                )
                for r in rows
            ],
        )

def update_rows(updates: Iterable[Tuple[int, Dict[str, Any]]]) -> None:
    updates = list(updates)
    if not updates:
        return
    with get_conn() as conn:
        cur = conn.cursor()
        for row_id, changed in updates:
            sets = []
            params = []
            for col in ("name", "qty", "price", "note"):
                if col in changed:
                    sets.append(f"{col} = ?")
                    if col == "qty":
                        params.append(int(changed[col]))
                    elif col == "price":
                        params.append(float(changed[col]))
                    else:
                        params.append(changed[col])
            if sets:
                params.append(row_id)
                cur.execute(f"UPDATE items SET {', '.join(sets)} WHERE id = ?", params)

def delete_by_ids(ids: Iterable[int]) -> None:
    ids = list(ids)
    if not ids:
        return
    placeholders = ",".join(["?"] * len(ids))
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM items WHERE id IN ({placeholders})", ids)
