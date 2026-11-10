"""Acceso a la base de datos SQLite de TaskIT.

Responsabilidad: abrir conexiones, crear la tabla y ejecutar consultas.
La interfaz (Flet) no escribe SQL directamente; llama a estas funciones.

Conceptos clave:
- SQLite guarda los datos en un archivo local.
- Usamos una conexión por operación: es simple y evita problemas si
  varios eventos de la interfaz intentan usar la misma conexión.
- Las consultas usan parámetros '?' en lugar de concatenar texto; esto
  evita inyección SQL y maneja correctamente comillas y valores nulos.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Optional

from models import Task, utc_now_iso

# Nombre del archivo de base de datos.
DB_FILENAME = "taskit.db"


def get_db_path(db_path: str | Path | None = None) -> Path:
    """Resuelve la ruta del archivo SQLite.

    Orden de prioridad:
    1. db_path explícito (usado por pruebas).
    2. TASKIT_DB_PATH (útil para desarrollo/pruebas manuales).
    3. FLET_APP_STORAGE_DATA (carpeta persistente en Android/Flet).
    4. ~/.taskit/taskit.db (respaldo en escritorio).

    La ruta NUNCA apunta dentro de src/, para no mezclar código con datos.
    """

    if db_path is not None:
        path = Path(db_path)
    elif os.environ.get("TASKIT_DB_PATH"):
        path = Path(os.environ["TASKIT_DB_PATH"])
    elif os.environ.get("FLET_APP_STORAGE_DATA"):
        path = Path(os.environ["FLET_APP_STORAGE_DATA"]) / DB_FILENAME
    else:
        path = Path.home() / ".taskit" / DB_FILENAME

    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Abre una conexión a SQLite.

    row_factory=sqlite3.Row permite leer columnas por nombre:
    row["title"] en vez de row[1].
    """

    path = get_db_path(db_path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | Path | None = None) -> None:
    """Crea la tabla 'tasks' si no existe.

    Es seguro llamarla varias veces: CREATE TABLE IF NOT EXISTS no borra
    datos existentes.
    """

    with connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                subject TEXT NOT NULL DEFAULT '',
                due_date TEXT,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def list_tasks(db_path: str | Path | None = None) -> list[Task]:
    """Devuelve todas las tareas.

    Orden: pendientes primero; dentro de cada grupo, las que tienen fecha
    límite antes; las sin fecha al final; y luego por id.
    """

    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, title, subject, due_date, completed, created_at
            FROM tasks
            ORDER BY completed ASC,
                     (due_date IS NULL) ASC,
                     due_date ASC,
                     id ASC
            """
        ).fetchall()
    return [Task.from_row(row) for row in rows]


def get_task(task_id: int, db_path: str | Path | None = None) -> Optional[Task]:
    """Busca una tarea por id. Devuelve None si no existe."""

    with connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT id, title, subject, due_date, completed, created_at
            FROM tasks
            WHERE id = ?
            """,
            (task_id,),
        ).fetchone()
    return Task.from_row(row) if row else None


def add_task(task: Task, db_path: str | Path | None = None) -> Task:
    """Inserta una tarea nueva y devuelve una copia con id y created_at."""

    clean = task.normalized()
    if not clean.title:
        raise ValueError("El título de la tarea no puede estar vacío.")
    if not clean.created_at:
        clean.created_at = utc_now_iso()

    with connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO tasks (title, subject, due_date, completed, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                clean.title,
                clean.subject,
                clean.due_date,
                1 if clean.completed else 0,
                clean.created_at,
            ),
        )
        conn.commit()
        clean.id = int(cursor.lastrowid)
    return clean


def update_task(task: Task, db_path: str | Path | None = None) -> None:
    """Actualiza una tarea existente. Requiere task.id."""

    if task.id is None:
        raise ValueError("No se puede actualizar una tarea sin id.")
    clean = task.normalized()
    if not clean.title:
        raise ValueError("El título de la tarea no puede estar vacío.")

    with connect(db_path) as conn:
        cursor = conn.execute(
            """
            UPDATE tasks
            SET title = ?, subject = ?, due_date = ?, completed = ?
            WHERE id = ?
            """,
            (
                clean.title,
                clean.subject,
                clean.due_date,
                1 if clean.completed else 0,
                task.id,
            ),
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise ValueError(f"No existe una tarea con id={task.id}.")


def set_completed(
    task_id: int, completed: bool, db_path: str | Path | None = None
) -> None:
    """Marca o desmarca una tarea como completada."""

    with connect(db_path) as conn:
        cursor = conn.execute(
            "UPDATE tasks SET completed = ? WHERE id = ?",
            (1 if completed else 0, task_id),
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise ValueError(f"No existe una tarea con id={task_id}.")


def delete_task(task_id: int, db_path: str | Path | None = None) -> None:
    """Elimina una tarea por id."""

    with connect(db_path) as conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise ValueError(f"No existe una tarea con id={task_id}.")
