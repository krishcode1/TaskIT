"""Modelos de datos de TaskIT.

Un "modelo" representa la información que maneja la aplicación.
Aquí usamos dataclasses: una forma sencilla de definir clases que
principalmente almacenan datos, sin escribir mucho código repetitivo.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

# sqlite3.Row se comporta como un diccionario de solo lectura: permite
# acceder a las columnas por nombre (row["title"]) en lugar de por índice.
RowLike = Any


def utc_now_iso() -> str:
    """Devuelve la fecha y hora actual en formato ISO (UTC).

    Guardamos fechas como texto porque SQLite no tiene un tipo de fecha
    nativo tan estricto como otras bases de datos; el formato ISO se
    ordena bien como texto y es fácil de leer.
    """

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class Task:
    """Representa una tarea académica.

    - title: obligatorio.
    - subject: materia; puede ser texto vacío si el usuario no la indica.
    - due_date: fecha límite en formato YYYY-MM-DD, o None si no tiene.
    - completed: True/False en Python; en SQLite se guarda como 1/0.
    - id: lo asigna SQLite al insertar; es None antes de guardar.
    - created_at: momento de creación en formato ISO.
    """

    title: str
    subject: str = ""
    due_date: str | None = None
    completed: bool = False
    id: int | None = None
    created_at: str = ""

    @classmethod
    def from_row(cls, row: RowLike) -> "Task":
        """Crea un Task a partir de una fila devuelta por SQLite.

        SQLite devuelve la columna 'completed' como entero (0 o 1);
        aquí la convertimos a bool para que el resto del código sea claro.
        """

        return cls(
            id=row["id"],
            title=row["title"],
            subject=row["subject"],
            due_date=row["due_date"],
            completed=bool(row["completed"]),
            created_at=row["created_at"],
        )

    def normalized(self) -> "Task":
        """Devuelve una copia con valores limpios y por defecto.

        - title/subject: sin espacios extra al inicio/final.
        - due_date: None si viene vacío.
        - created_at: se genera si falta.
        """

        return Task(
            id=self.id,
            title=self.title.strip(),
            subject=self.subject.strip(),
            due_date=(self.due_date.strip() or None) if self.due_date else None,
            completed=bool(self.completed),
            created_at=self.created_at or utc_now_iso(),
        )
