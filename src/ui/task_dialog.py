"""Diálogo para crear o editar una tarea (Etapas 3 y 4).

Responsabilidades:
- Mostrar el formulario (título, materia opcional, fecha límite opcional).
- Validar que el título no esté vacío.
- En modo creación, guardar la tarea con db.add_task().
- En modo edición, actualizarla con db.update_task() conservando id,
  estado y fecha de creación.
- Permitir quitar una fecha límite existente.
- Cerrar el diálogo y avisar a la vista para que se actualice.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Callable

import flet as ft

from db import add_task, update_task
from models import Task


class TaskDialog(ft.AlertDialog):
    """Formulario de creación/edición de tarea como AlertDialog."""

    def __init__(
        self,
        page: ft.Page,
        on_saved: Callable[[], None],
        task: Task | None = None,
    ):
        # task=None -> modo creación; task con datos -> modo edición.
        is_edit = task is not None
        super().__init__(
            key="task_dialog",
            modal=True,
            title=ft.Text("Editar tarea" if is_edit else "Nueva tarea"),
        )
        self._page = page
        self._on_saved = on_saved
        self._task = task
        self._selected_due_date = task.due_date if task else None

        self.title_field = ft.TextField(
            key="task_title_field",
            label="Título",
            value=task.title if task else "",
            autofocus=True,
            on_change=self._clear_title_error,
        )
        self.subject_field = ft.TextField(
            key="task_subject_field",
            label="Materia (opcional)",
            value=task.subject if task else "",
        )
        self.due_date_field = ft.TextField(
            key="task_due_date_field",
            label="Fecha límite (opcional)",
            value=self._selected_due_date or "",
            read_only=True,
            hint_text="AAAA-MM-DD",
            expand=True,
            suffix=ft.IconButton(
                icon=ft.Icons.CALENDAR_MONTH,
                tooltip="Elegir fecha",
                on_click=self._open_date_picker,
            ),
            on_click=self._open_date_picker,
        )
        # Botón independiente para quitar la fecha; solo se muestra si hay una.
        self.clear_due_date_button = ft.IconButton(
            key="task_clear_due_date_button",
            icon=ft.Icons.CLEAR,
            tooltip="Quitar fecha",
            visible=bool(self._selected_due_date),
            on_click=self._clear_due_date,
        )

        self.content = ft.Column(
            tight=True,
            width=420,
            spacing=12,
            controls=[
                self.title_field,
                self.subject_field,
                ft.Row(
                    controls=[self.due_date_field, self.clear_due_date_button],
                    spacing=4,
                ),
            ],
        )
        self.actions = [
            ft.TextButton(
                "Cancelar",
                key="task_cancel_button",
                on_click=self._cancel,
            ),
            ft.FilledButton(
                "Guardar cambios" if is_edit else "Guardar",
                key="task_save_button",
                on_click=self._save,
            ),
        ]

    def _clear_title_error(self, e):
        # Quita el mensaje de error cuando el usuario empieza a corregir.
        if self.title_field.error:
            self.title_field.error = None
            self.title_field.update()

    def _open_date_picker(self, e):
        picker = ft.DatePicker(
            help_text="Selecciona la fecha límite",
            cancel_text="Cancelar",
            confirm_text="Aceptar",
            first_date=datetime(1900, 1, 1),
            last_date=datetime(2050, 1, 1),
            on_change=self._date_selected,
        )
        # No llamamos pop_dialog() en on_change: el DatePicker se cierra solo.
        # Cerrarlo manualmente aquí podría cerrar también este AlertDialog.
        self._page.show_dialog(picker)

    def _date_selected(self, e: ft.ControlEvent):
        # e.control es el DatePicker; su value es datetime/date o None.
        value = getattr(e.control, "value", None)
        if value is None:
            return
        self._selected_due_date = value.strftime("%Y-%m-%d")
        self.due_date_field.value = self._selected_due_date
        self.clear_due_date_button.visible = True
        self.due_date_field.update()
        self.clear_due_date_button.update()

    def _clear_due_date(self, e):
        # Guarda la tarea sin fecha: due_date=None.
        self._selected_due_date = None
        self.due_date_field.value = ""
        self.clear_due_date_button.visible = False
        self.due_date_field.update()
        self.clear_due_date_button.update()

    def _save(self, e):
        title = (self.title_field.value or "").strip()
        if not title:
            # Flet 1.1.2 usa 'error' en campos de formulario (no 'error_text').
            self.title_field.error = "El título es obligatorio."
            self.title_field.update()
            return

        subject = (self.subject_field.value or "").strip()
        if self._task is None:
            add_task(
                Task(
                    title=title,
                    subject=subject,
                    due_date=self._selected_due_date,
                )
            )
        else:
            # replace() conserva id, completed y created_at de la tarea original.
            update_task(
                replace(
                    self._task,
                    title=title,
                    subject=subject,
                    due_date=self._selected_due_date,
                )
            )

        # Cierra este diálogo y actualiza la lista solo tras guardar bien.
        self._page.pop_dialog()
        self._on_saved()
        # pop_dialog() marca una actualización explícita; sin este update(),
        # Flet puede omitir el auto-update final y la nueva tarea tarda en verse.
        self._page.update()

    def _cancel(self, e):
        self._page.pop_dialog()

    def show(self) -> None:
        """Abre el diálogo en la página."""
        self._page.show_dialog(self)
