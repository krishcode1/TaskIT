"""Pruebas de la capa de datos de TaskIT.

Estas pruebas NO abren Flet ni usan tu base de datos real.
Cada prueba recibe `tmp_path`, un directorio temporal que pytest crea y
elimina automáticamente. Pasamos ese directorio a db_path para aislar
los datos.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from db import (
    add_task,
    delete_task,
    get_db_path,
    get_task,
    init_db,
    list_tasks,
    set_completed,
    update_task,
)
from models import Task


def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


def test_add_and_list_task(tmp_path):
    db = temp_db(tmp_path)
    init_db(db)

    created = add_task(
        Task(title="Estudiar álgebra", subject="Matemáticas", due_date="2026-11-10"),
        db,
    )

    assert created.id is not None
    assert created.title == "Estudiar álgebra"
    assert created.created_at

    tasks = list_tasks(db)
    assert len(tasks) == 1
    assert tasks[0].id == created.id
    assert tasks[0].subject == "Matemáticas"
    assert tasks[0].due_date == "2026-11-10"
    assert tasks[0].completed is False


def test_subject_is_optional(tmp_path):
    db = temp_db(tmp_path)
    init_db(db)

    created = add_task(Task(title="Leer capítulo 2"), db)

    assert created.subject == ""
    assert get_task(created.id, db).subject == ""


def test_update_task(tmp_path):
    db = temp_db(tmp_path)
    init_db(db)
    created = add_task(Task(title="Borrador", subject="Historia"), db)

    created.title = "Ensayo final"
    created.subject = "Historia universal"
    created.due_date = "2026-11-20"
    update_task(created, db)

    loaded = get_task(created.id, db)
    assert loaded.title == "Ensayo final"
    assert loaded.subject == "Historia universal"
    assert loaded.due_date == "2026-11-20"


def test_set_completed(tmp_path):
    db = temp_db(tmp_path)
    init_db(db)
    created = add_task(Task(title="Entregar informe"), db)

    set_completed(created.id, True, db)
    assert get_task(created.id, db).completed is True

    set_completed(created.id, False, db)
    assert get_task(created.id, db).completed is False


def test_delete_task(tmp_path):
    db = temp_db(tmp_path)
    init_db(db)
    created = add_task(Task(title="Eliminarme"), db)

    delete_task(created.id, db)

    assert get_task(created.id, db) is None
    assert list_tasks(db) == []


def test_get_missing_task_returns_none(tmp_path):
    db = temp_db(tmp_path)
    init_db(db)
    assert get_task(9999, db) is None


def test_list_orders_pending_then_due_date(tmp_path):
    db = temp_db(tmp_path)
    init_db(db)

    later = add_task(Task(title="Después", due_date="2026-11-15"), db)
    sooner = add_task(Task(title="Antes", due_date="2026-11-10"), db)
    no_date = add_task(Task(title="Sin fecha"), db)
    done = add_task(Task(title="Hecha", due_date="2026-11-01", completed=True), db)

    tasks = list_tasks(db)
    assert [t.id for t in tasks] == [sooner.id, later.id, no_date.id, done.id]


def test_empty_title_is_rejected(tmp_path):
    db = temp_db(tmp_path)
    init_db(db)

    with pytest.raises(ValueError):
        add_task(Task(title="   "), db)


def test_missing_task_operations_fail(tmp_path):
    db = temp_db(tmp_path)
    init_db(db)

    with pytest.raises(ValueError):
        update_task(Task(id=123, title="No existe"), db)
    with pytest.raises(ValueError):
        set_completed(123, True, db)
    with pytest.raises(ValueError):
        delete_task(123, db)


def test_taskit_db_path_has_priority(tmp_path, monkeypatch):
    override = tmp_path / "override.db"
    monkeypatch.setenv("TASKIT_DB_PATH", str(override))
    monkeypatch.delenv("FLET_APP_STORAGE_DATA", raising=False)

    resolved = get_db_path()
    assert resolved == override

    init_db()
    add_task(Task(title="Prueba"), None)
    assert resolved.exists()
    assert list_tasks()[0].title == "Prueba"


def test_flet_app_storage_data_used_on_mobile_like_env(tmp_path, monkeypatch):
    storage = tmp_path / "storage"
    monkeypatch.delenv("TASKIT_DB_PATH", raising=False)
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(storage))

    resolved = get_db_path()
    assert resolved == storage / "taskit.db"
