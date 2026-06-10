#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared Memory - Backend SQLite para agentes Hermes.
Compartido entre multiples agentes (Terminal, Gateway, etc).

Uso:
    python shared_memory.py add "Contenido de la memoria" --tags tag1,tag2 --source terminal
    python shared_memory.py search "texto"
    python shared_memory.py context --limit 10
    python shared_memory.py list --source terminal
    python shared_memory.py stats
    python shared_memory.py clear --days 30
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

# DB path configurable via env var, defaults to ~/.hermes/shared-memory/memory.db
DB_PATH = Path(os.environ.get(
    "SHARED_MEMORY_DB",
    Path.home() / ".hermes" / "shared-memory" / "memory.db"
))


def get_db():
    """Obtener conexion SQLite con WAL mode para concurrencia segura."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn):
    """Crear tablas si no existen."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS memories (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            source      TEXT        NOT NULL DEFAULT 'unknown',
            content     TEXT        NOT NULL,
            tags        TEXT        DEFAULT '',
            metadata    TEXT        DEFAULT '{}',
            created_at  TEXT        NOT NULL DEFAULT (datetime('now')),
            expires_at  TEXT        DEFAULT NULL,
            archived    INTEGER     NOT NULL DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_memories_source ON memories(source);
        CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at);
        CREATE INDEX IF NOT EXISTS idx_memories_archived ON memories(archived);

        CREATE TABLE IF NOT EXISTS memory_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            action      TEXT        NOT NULL,
            memory_id   INTEGER,
            detail      TEXT        DEFAULT '',
            created_at  TEXT        NOT NULL DEFAULT (datetime('now'))
        );
    """)
    conn.commit()


def add_memory(source, content, tags="", metadata=None, expires_days=None):
    """Agregar una entrada de memoria. Retorna el ID."""
    conn = get_db()
    init_db(conn)

    expires_at = None
    if expires_days:
        expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()

    meta_json = json.dumps(metadata or {})

    cursor = conn.execute(
        "INSERT INTO memories (source, content, tags, metadata, expires_at) VALUES (?, ?, ?, ?, ?)",
        (source, content, tags, meta_json, expires_at)
    )
    memory_id = cursor.lastrowid

    conn.execute(
        "INSERT INTO memory_log (action, memory_id, detail) VALUES (?, ?, ?)",
        ("add", memory_id, "source=" + source)
    )
    conn.commit()
    conn.close()
    return memory_id


def search_memories(query, source=None, limit=10):
    """Buscar memorias por contenido o tags."""
    conn = get_db()
    init_db(conn)

    sql = """
        SELECT id, source, content, tags, metadata, created_at, expires_at
        FROM memories
        WHERE archived = 0
          AND (expires_at IS NULL OR expires_at > datetime('now'))
          AND (content LIKE ? OR tags LIKE ?)
    """
    params = ["%" + query + "%", "%" + query + "%"]

    if source:
        sql += " AND source = ?"
        params.append(source)

    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_context(limit=20, source=None):
    """Obtener las memorias mas recientes para inyectar como contexto."""
    conn = get_db()
    init_db(conn)

    sql = """
        SELECT id, source, content, tags, created_at
        FROM memories
        WHERE archived = 0
          AND (expires_at IS NULL OR expires_at > datetime('now'))
    """
    params = []

    if source:
        sql += " AND source = ?"
        params.append(source)

    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    return [dict(row) for row in rows]


def list_all(source=None, limit=50):
    """Listar todas las memorias."""
    conn = get_db()
    init_db(conn)

    sql = """
        SELECT id, source, content, tags, created_at, archived
        FROM memories
        WHERE 1=1
    """
    params = []

    if source:
        sql += " AND source = ?"
        params.append(source)

    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    return [dict(row) for row in rows]


def archive_memory(memory_id):
    """Archivar una memoria (soft delete)."""
    conn = get_db()
    init_db(conn)
    cursor = conn.execute("UPDATE memories SET archived = 1 WHERE id = ?", (memory_id,))
    conn.execute(
        "INSERT INTO memory_log (action, memory_id, detail) VALUES (?, ?, ?)",
        ("archive", memory_id, "")
    )
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def clear_old(days=30):
    """Archivar memorias mas antiguas que N dias."""
    conn = get_db()
    init_db(conn)
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    cursor = conn.execute(
        "UPDATE memories SET archived = 1 WHERE created_at < ? AND archived = 0",
        (cutoff,)
    )
    count = cursor.rowcount
    conn.execute(
        "INSERT INTO memory_log (action, detail) VALUES (?, ?)",
        ("clear_old", "archived " + str(count) + " memories older than " + str(days) + " days")
    )
    conn.commit()
    conn.close()
    return count


def get_stats():
    """Estadisticas de la memoria."""
    conn = get_db()
    init_db(conn)

    total = conn.execute("SELECT COUNT(*) FROM memories WHERE archived = 0").fetchone()[0]
    by_source = {}
    for row in conn.execute("SELECT source, COUNT(*) as cnt FROM memories WHERE archived = 0 GROUP BY source"):
        by_source[row[0]] = row[1]

    last_7d = conn.execute(
        "SELECT COUNT(*) FROM memories WHERE archived = 0 AND created_at > datetime('now', '-7 days')"
    ).fetchone()[0]

    conn.close()
    return {"total": total, "by_source": by_source, "last_7_days": last_7d}


def format_context_for_prompt(memories):
    """Formatear memorias como texto para inyectar en un prompt."""
    if not memories:
        return ""

    lines = ["## Contexto compartido (memorias recientes):"]
    for m in memories:
        tags = " [" + m['tags'] + "]" if m['tags'] else ""
        lines.append("- [" + m['source'] + "] " + m['content'] + tags + " (" + m['created_at'] + ")")

    return "\n".join(lines)


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(description="Shared Memory - Memoria compartida para agentes")
    sub = parser.add_subparsers(dest="command")

    # ADD
    p_add = sub.add_parser("add", help="Agregar memoria")
    p_add.add_argument("content", help="Contenido de la memoria")
    p_add.add_argument("--source", default="unknown", help="Origen: terminal, telegram, system, gateway")
    p_add.add_argument("--tags", default="", help="Tags separados por coma")
    p_add.add_argument("--meta", default="{}", help="Metadata JSON")
    p_add.add_argument("--expires-days", type=int, default=None, help="Expira en N dias")

    # SEARCH
    p_search = sub.add_parser("search", help="Buscar memorias")
    p_search.add_argument("query", help="Texto a buscar")
    p_search.add_argument("--source", default=None, help="Filtrar por origen")
    p_search.add_argument("--limit", type=int, default=10, help="Maximo resultados")

    # CONTEXT
    p_ctx = sub.add_parser("context", help="Obtener contexto reciente")
    p_ctx.add_argument("--limit", type=int, default=20, help="Cantidad")
    p_ctx.add_argument("--source", default=None, help="Filtrar por origen")
    p_ctx.add_argument("--format", choices=["text", "json", "prompt"], default="text", help="Formato de salida")

    # LIST
    p_list = sub.add_parser("list", help="Listar memorias")
    p_list.add_argument("--source", default=None, help="Filtrar por origen")
    p_list.add_argument("--limit", type=int, default=50, help="Maximo")

    # ARCHIVE
    p_arch = sub.add_parser("archive", help="Archivar memoria")
    p_arch.add_argument("id", type=int, help="ID de la memoria")

    # CLEAR
    p_clear = sub.add_parser("clear", help="Limpiar memorias antiguas")
    p_clear.add_argument("--days", type=int, default=30, help="Archivar mayores a N dias")

    # STATS
    sub.add_parser("stats", help="Estadisticas")

    args = parser.parse_args()

    if args.command == "add":
        meta = json.loads(args.meta)
        mid = add_memory(args.source, args.content, args.tags, meta, args.expires_days)
        print("Memoria agregada: ID=" + str(mid))

    elif args.command == "search":
        results = search_memories(args.query, args.source, args.limit)
        if not results:
            print("Sin resultados.")
        else:
            for r in results:
                tags = " [" + r['tags'] + "]" if r['tags'] else ""
                print("  [" + str(r['id']) + "] (" + r['source'] + ") " + r['content'] + tags)

    elif args.command == "context":
        memories = get_context(args.limit, args.source)
        if args.format == "prompt":
            print(format_context_for_prompt(memories))
        elif args.format == "json":
            print(json.dumps(memories, indent=2, ensure_ascii=False))
        else:
            if not memories:
                print("Sin memorias recientes.")
            else:
                for m in memories:
                    tags = " [" + m['tags'] + "]" if m['tags'] else ""
                    print("  [" + str(m['id']) + "] (" + m['source'] + ") " + m['content'] + tags + " -- " + m['created_at'])

    elif args.command == "list":
        results = list_all(args.source, args.limit)
        if not results:
            print("Sin memorias.")
        else:
            for r in results:
                if r['archived']:
                    status = "[archived]"
                else:
                    status = "[active]"
                print("  " + status + " [" + str(r['id']) + "] (" + r['source'] + ") " + r['content'][:80])

    elif args.command == "archive":
        ok = archive_memory(args.id)
        if ok:
            print("Memoria " + str(args.id) + " archivada.")
        else:
            print("Memoria " + str(args.id) + " no encontrada.")

    elif args.command == "clear":
        count = clear_old(args.days)
        print("Se archivaron " + str(count) + " memorias antiguas.")

    elif args.command == "stats":
        stats = get_stats()
        print("Total activas: " + str(stats['total']))
        print("Ultimos 7 dias: " + str(stats['last_7_days']))
        print("Por fuente:")
        for src, cnt in stats["by_source"].items():
            print("  " + src + ": " + str(cnt))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
