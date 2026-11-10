"""Vista principal de tareas.

Responsabilidad: leer tareas desde la base de datos y construir los
controles Flet para mostrarlas. No contiene SQL: las operaciones de datos
se delegan a db.py.

Acciones por tarea:
- Checkbox: cambia entre pendiente y completada.
- Icono editar: abre TaskDialog en modo edición.
- Icono eliminar: pide confirmación antes de borrar.
"""

from __future__ import annotations

import flet as ft

from db import delete_task, list_tasks, set_completed
from models import Task
from ui.task_dialog import TaskDialog


def _task_subtitle(task: Task) -> str | None:
    """Construye un texto secundario simple (materia y/o fecha límite)."""

    parts: list[str] = []
    if task.subject:
        parts.append(task.subject)
    if task.due_date:
        parts.append(task.due_date)
    return " · ".join(parts) if parts else None


class TasksView(ft.Column):
    """Pantalla principal con pestañas Pendientes/Completadas."""

    def __init__(self, page: ft.Page):
        super().__init__(expand=True, spacing=0)
        self._page = page
        self._pending_view = ft.Container(expand=True)
        self._completed_view = ft.Container(expand=True)

        self.controls = [
            ft.Tabs(
                length=2,
                selected_index=0,
                expand=True,
                content=ft.Column(
                    expand=True,
                    controls=[
                        ft.TabBar(
                            tabs=[
                                ft.Tab(label="Pendientes"),
                                ft.Tab(label="Completadas"),
                            ]
                        ),
                        ft.TabBarView(
                            expand=True,
                            controls=[self._pending_view, self._completed_view],
                        ),
                    ],
                ),
            )
        ]

    def _task_tile(self, task: Task) -> ft.ListTile:
        """Fila de una tarea con sus acciones independientes.

        ListTile no tiene on_click: así el checkbox y los iconos nunca
        abren el formulario de edición por propagación del toque.
        """

        return ft.ListTile(
            key=f"task_{task.id}",
            leading=ft.Checkbox(
                key=f"toggle_{task.id}",
                value=task.completed,
                on_change=lambda e, t=task: self._toggle(t, e.control.value),
            ),
            title=ft.Text(task.title),
            subtitle=ft.Text(_task_subtitle(task)) if _task_subtitle(task) else None,
            trailing=ft.Row(
                tight=True,
                spacing=0,
                controls=[
                    ft.IconButton(
                        key=f"edit_{task.id}",
                        icon=ft.Icons.EDIT_OUTLINED,
                        tooltip="Editar tarea",
                        on_click=lambda e, t=task: self._edit(t),
                    ),
                    ft.IconButton(
                        key=f"delete_{task.id}",
                        icon=ft.Icons.DELETE_OUTLINE,
                        tooltip="Eliminar tarea",
                        on_click=lambda e, t=task: self._confirm_delete(t),
                    ),
                ],
            ),
        )

    def _tasks_list(
        self, tasks: list[Task], empty_text: str, empty_key: str
    ) -> ft.Control:
        """Lista de tareas o mensaje de estado vacío."""

        if not tasks:
            return ft.Container(
                key=empty_key,
                expand=True,
                alignment=ft.Alignment.CENTER,
                padding=20,
                content=ft.Text(empty_text, text_align=ft.TextAlign.CENTER),
            )

        return ft.ListView(
            expand=True,
            spacing=6,
            padding=10,
            controls=[self._task_tile(task) for task in tasks],
        )

    def refresh(self) -> None:
        """Recarga las tareas desde la base de datos y actualiza la vista."""

        tasks = list_tasks()
        pending = [task for task in tasks if not task.completed]
        completed = [task for task in tasks if task.completed]

        self._pending_view.content = self._tasks_list(
            pending,
            "No hay tareas pendientes.",
            "empty_pending",
        )
        self._completed_view.content = self._tasks_list(
            completed,
            "No hay tareas completadas.",
            "empty_completed",
        )

    def _toggle(self, task: Task, completed: bool) -> None:
        """Cambia el estado pendiente/completada de una tarea."""

        set_completed(task.id, bool(completed))
        self.refresh()
        self._page.update()

    def _edit(self, task: Task) -> None:
        """Abre el formulario existente en modo edición."""

        TaskDialog(self._page, on_saved=self.refresh, task=task).show()

    def _confirm_delete(self, task: Task) -> None:
        """Pide confirmación antes de eliminar una tarea."""

        dialog = ft.AlertDialog(
            key="delete_dialog",
            modal=True,
            title=ft.Text("Eliminar tarea"),
            content=ft.Text(f'¿Eliminar "{task.title}"?'),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    key="delete_cancel_button",
                    on_click=lambda e: self._page.pop_dialog(),
                ),
                ft.FilledButton(
                    "Eliminar",
                    key="delete_confirm_button",
                    on_click=lambda e, t=task: self._delete(t),
                ),
            ],
        )
        self._page.show_dialog(dialog)

    def _delete(self, task: Task) -> None:
        """Elimina una tarea confirmada y refresca la interfaz."""

        delete_task(task.id)
        # pop_dialog() marca una actualización explícita; el update() final
        # envía también los cambios de la lista al cliente.
        self._page.pop_dialog()
        self.refresh()
        self._page.update()
