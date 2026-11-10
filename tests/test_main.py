"""Pruebas de interfaz (Etapas 3 y 4).

Usan `flet_app` (plugin de Flet). `tests/conftest.py` establece
TASKIT_DB_PATH a una ruta temporal por prueba para evitar tocar datos
reales. Las comprobaciones se hacen desde la UI (estado visible),
porque en modo dispositivo la app puede ejecutarse en un proceso aparte.
"""

import flet.testing as ftt

from db import add_task, get_task, init_db
from models import Task
from ui.task_dialog import TaskDialog


class _FakePage:
    """Página mínima para probar TaskDialog sin arrancar Flutter."""

    def __init__(self):
        self.dialogs = []

    def show_dialog(self, dialog):
        self.dialogs.append(dialog)

    def pop_dialog(self):
        if self.dialogs:
            self.dialogs.pop()

    def update(self):
        pass


async def _create_task(tester, title: str, subject: str = "") -> None:
    """Crea una tarea desde el formulario de la interfaz."""

    await tester.tap(await tester.find_by_key("add_task_fab"))
    await tester.pump_and_settle()

    await tester.enter_text(await tester.find_by_key("task_title_field"), title)
    if subject:
        await tester.enter_text(
            await tester.find_by_key("task_subject_field"), subject
        )

    await tester.tap(await tester.find_by_key("task_save_button"))
    await tester.pump_and_settle()


async def _open_tab(tester, label: str) -> None:
    """Cambia a la pestaña indicada por su etiqueta."""

    await tester.tap(await tester.find_by_text(label))
    await tester.pump_and_settle()


async def test_initial_screen_shows_title_empty_state_and_fab(flet_app: ftt.FletTestApp):
    tester = flet_app.tester
    await tester.pump_and_settle()

    assert (await tester.find_by_key("app_title")).count == 1
    assert (await tester.find_by_key("empty_pending")).count == 1
    assert (await tester.find_by_key("add_task_fab")).count == 1


async def test_create_task_updates_list(flet_app: ftt.FletTestApp):
    tester = flet_app.tester
    await tester.pump_and_settle()

    await tester.tap(await tester.find_by_key("add_task_fab"))
    await tester.pump_and_settle()

    assert (await tester.find_by_key("task_dialog")).count == 1

    await tester.enter_text(await tester.find_by_key("task_title_field"), "Estudiar física")
    await tester.enter_text(
        await tester.find_by_key("task_subject_field"), "Ciencias"
    )
    await tester.tap(await tester.find_by_key("task_save_button"))
    await tester.pump_and_settle()

    # El diálogo debe cerrarse tras guardar correctamente.
    assert (await tester.find_by_key("task_dialog")).count == 0
    assert (await tester.find_by_text("Estudiar física")).count >= 1
    assert (await tester.find_by_key("empty_pending")).count == 0


async def test_empty_title_is_rejected(flet_app: ftt.FletTestApp):
    tester = flet_app.tester
    await tester.pump_and_settle()

    await tester.tap(await tester.find_by_key("add_task_fab"))
    await tester.pump_and_settle()

    await tester.tap(await tester.find_by_key("task_save_button"))
    await tester.pump_and_settle()

    # No se guarda: el diálogo permanece abierto y muestra el error.
    assert (await tester.find_by_key("task_dialog")).count == 1
    assert (await tester.find_by_text("El título es obligatorio.")).count >= 1
    assert (await tester.find_by_key("empty_pending")).count == 1


async def test_cancel_does_not_create_task(flet_app: ftt.FletTestApp):
    tester = flet_app.tester
    await tester.pump_and_settle()

    await tester.tap(await tester.find_by_key("add_task_fab"))
    await tester.pump_and_settle()
    await tester.enter_text(await tester.find_by_key("task_title_field"), "No guardar")
    await tester.tap(await tester.find_by_key("task_cancel_button"))
    await tester.pump_and_settle()

    assert (await tester.find_by_key("task_dialog")).count == 0
    assert (await tester.find_by_key("empty_pending")).count == 1
    assert (await tester.find_by_text("No guardar")).count == 0


async def test_edit_task_updates_list(flet_app: ftt.FletTestApp):
    tester = flet_app.tester
    await tester.pump_and_settle()

    await _create_task(tester, "Título original", "Materia original")

    # La primera tarea creada en una base temporal usa id=1.
    await tester.tap(await tester.find_by_key("edit_1"))
    await tester.pump_and_settle()

    assert (await tester.find_by_key("task_dialog")).count == 1
    assert (await tester.find_by_text("Editar tarea")).count >= 1

    await tester.enter_text(
        await tester.find_by_key("task_title_field"), "Título editado"
    )
    await tester.enter_text(
        await tester.find_by_key("task_subject_field"), "Materia editada"
    )
    await tester.tap(await tester.find_by_key("task_save_button"))
    await tester.pump_and_settle()

    # Se actualiza la misma tarea: no se crea otra.
    assert (await tester.find_by_key("task_dialog")).count == 0
    assert (await tester.find_by_text("Título editado")).count >= 1
    assert (await tester.find_by_text("Materia editada")).count >= 1
    assert (await tester.find_by_text("Título original")).count == 0
    assert (await tester.find_by_text("Materia original")).count == 0
    assert (await tester.find_by_key("task_1")).count == 1
    assert (await tester.find_by_key("task_2")).count == 0


async def test_edit_keeps_completed_status(flet_app: ftt.FletTestApp):
    tester = flet_app.tester
    await tester.pump_and_settle()

    await _create_task(tester, "Tarea pendiente")

    # Completar la tarea y comprobar que se mueve a Completadas.
    await tester.tap(await tester.find_by_key("toggle_1"))
    await tester.pump_and_settle()
    await _open_tab(tester, "Completadas")
    assert (await tester.find_by_text("Tarea pendiente")).count >= 1

    # Editarla: debe seguir completada, no volver a Pendientes.
    await tester.tap(await tester.find_by_key("edit_1"))
    await tester.pump_and_settle()
    await tester.enter_text(
        await tester.find_by_key("task_title_field"), "Tarea completada editada"
    )
    await tester.tap(await tester.find_by_key("task_save_button"))
    await tester.pump_and_settle()

    assert (await tester.find_by_key("task_dialog")).count == 0
    assert (await tester.find_by_text("Tarea completada editada")).count >= 1
    assert (await tester.find_by_key("empty_completed")).count == 0


async def test_toggle_moves_task_between_tabs(flet_app: ftt.FletTestApp):
    tester = flet_app.tester
    await tester.pump_and_settle()

    await _create_task(tester, "Tarea móvil")

    # Pendiente -> Completada.
    await tester.tap(await tester.find_by_key("toggle_1"))
    await tester.pump_and_settle()
    assert (await tester.find_by_key("empty_pending")).count == 1

    await _open_tab(tester, "Completadas")
    assert (await tester.find_by_text("Tarea móvil")).count >= 1

    # Completada -> Pendiente.
    await tester.tap(await tester.find_by_key("toggle_1"))
    await tester.pump_and_settle()
    assert (await tester.find_by_key("empty_completed")).count == 1

    await _open_tab(tester, "Pendientes")
    assert (await tester.find_by_text("Tarea móvil")).count >= 1


async def test_delete_cancel_keeps_task(flet_app: ftt.FletTestApp):
    tester = flet_app.tester
    await tester.pump_and_settle()

    await _create_task(tester, "No borrar")

    await tester.tap(await tester.find_by_key("delete_1"))
    await tester.pump_and_settle()
    assert (await tester.find_by_key("delete_dialog")).count == 1

    await tester.tap(await tester.find_by_key("delete_cancel_button"))
    await tester.pump_and_settle()

    assert (await tester.find_by_key("delete_dialog")).count == 0
    assert (await tester.find_by_text("No borrar")).count >= 1
    assert (await tester.find_by_key("empty_pending")).count == 0


async def test_delete_confirmed_removes_task(flet_app: ftt.FletTestApp):
    tester = flet_app.tester
    await tester.pump_and_settle()

    await _create_task(tester, "Tarea a borrar")

    await tester.tap(await tester.find_by_key("delete_1"))
    await tester.pump_and_settle()
    assert (await tester.find_by_key("delete_dialog")).count == 1

    await tester.tap(await tester.find_by_key("delete_confirm_button"))
    await tester.pump_and_settle()

    assert (await tester.find_by_key("delete_dialog")).count == 0
    assert (await tester.find_by_text("Tarea a borrar")).count == 0
    assert (await tester.find_by_key("empty_pending")).count == 1


async def test_edit_rejects_empty_title(flet_app: ftt.FletTestApp):
    tester = flet_app.tester
    await tester.pump_and_settle()

    await _create_task(tester, "Título válido")

    await tester.tap(await tester.find_by_key("edit_1"))
    await tester.pump_and_settle()

    # Espacios en blanco: se limpian y el título queda vacío.
    await tester.enter_text(await tester.find_by_key("task_title_field"), "   ")
    await tester.tap(await tester.find_by_key("task_save_button"))
    await tester.pump_and_settle()

    # No se guarda: el diálogo sigue abierto, muestra el error y la
    # tarea original permanece sin cambios.
    assert (await tester.find_by_key("task_dialog")).count == 1
    assert (await tester.find_by_text("El título es obligatorio.")).count >= 1
    assert (await tester.find_by_text("Título válido")).count >= 1


def test_dialog_edit_preserves_status_and_created_at():
    """Verifica la lógica de edición sin depender del harness de Flutter."""

    init_db()
    original = add_task(
        Task(
            title="Original",
            subject="Materia",
            due_date="2026-11-10",
            completed=True,
        )
    )
    page = _FakePage()
    dialog = TaskDialog(page, on_saved=lambda: None, task=original)

    # En modo edición los campos se precargan con los datos actuales.
    assert dialog.title_field.value == "Original"
    assert dialog.subject_field.value == "Materia"
    assert dialog.due_date_field.value == "2026-11-10"
    assert dialog.clear_due_date_button.visible is True

    dialog.title_field.value = "Editada"
    dialog.subject_field.value = "Nueva materia"
    dialog._save(None)

    saved = get_task(original.id)
    assert saved is not None
    assert saved.title == "Editada"
    assert saved.subject == "Nueva materia"
    assert saved.due_date == "2026-11-10"
    assert saved.completed is True
    assert saved.created_at == original.created_at
    assert saved.id == original.id


def test_dialog_clear_due_date_saves_none():
    """Quitar la fecha deja due_date=None sin perder el resto de datos."""

    init_db()
    original = add_task(Task(title="Con fecha", due_date="2026-11-10"))
    page = _FakePage()
    dialog = TaskDialog(page, on_saved=lambda: None, task=original)

    # Evita update() de controles que no están montados en una página real.
    dialog.due_date_field.update = lambda: None
    dialog.clear_due_date_button.update = lambda: None
    dialog._clear_due_date(None)

    assert dialog._selected_due_date is None
    assert dialog.due_date_field.value == ""
    assert dialog.clear_due_date_button.visible is False

    dialog._save(None)

    saved = get_task(original.id)
    assert saved is not None
    assert saved.due_date is None
    assert saved.title == "Con fecha"
    assert saved.created_at == original.created_at
