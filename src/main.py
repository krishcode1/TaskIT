"""Punto de entrada de TaskIT.

Coordina el arranque: inicializa la base de datos y monta la interfaz.
La lógica de datos vive en db.py/models.py; la vista en ui/tasks_view.py.
"""

import flet as ft

from db import init_db
from ui.task_dialog import TaskDialog
from ui.tasks_view import TasksView


def main(page: ft.Page):
    # Título visible en escritorio/web; en móvil ayuda a identificar la app.
    page.title = "TaskIT"

    # Crea la tabla si es la primera ejecución. Usa la ruta persistente
    # configurada por db.get_db_path() (FLET_APP_STORAGE_DATA en Android).
    init_db()

    page.appbar = ft.AppBar(
        title=ft.Text("TaskIT", key="app_title"),
        center_title=True,
    )

    view = TasksView(page)
    view.refresh()

    def open_new_task_dialog(e: ft.Event[ft.FloatingActionButton]):
        # Abre el formulario; al guardar, on_saved refresca la lista.
        TaskDialog(page, on_saved=view.refresh).show()

    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.Icons.ADD,
        key="add_task_fab",
        tooltip="Agregar tarea",
        on_click=open_new_task_dialog,
    )

    page.add(ft.SafeArea(expand=True, content=view))


if __name__ == "__main__":
    ft.run(main)
