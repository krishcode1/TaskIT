"""Configuración compartida de pruebas.

Aísla la base de datos de las pruebas de UI antes de que arranque el
fixture `flet_app`. Así, la aplicación de prueba nunca modifica datos
reales del usuario.
"""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def isolated_taskit_db(tmp_path, monkeypatch):
    """Usa una base de datos SQLite temporal para cada prueba.

    TASKIT_DB_PATH tiene prioridad en db.get_db_path(). Se establece aquí
    para que main.py/init_db() y cualquier operación de UI usen esta ruta.
    """

    db_path = tmp_path / "ui_test.db"
    monkeypatch.setenv("TASKIT_DB_PATH", str(db_path))
    yield db_path
    # monkeypatch restaura el entorno automáticamente.
