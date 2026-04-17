import calendar
import json
import csv
from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk


APP_NAME = "Pocket Student Calendar and Todo list App-ver. 1.5"
WINDOW_SIZE = "920x560"
MIN_WINDOW_SIZE = (860, 500)
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_FILE = DATA_DIR / "todo_data.json"


@dataclass
class TodoItem:
    text: str
    done: bool = False
    created_at: str = ""

    @classmethod
    def from_dict(cls, raw: dict) -> "TodoItem":
        return cls(
            text=str(raw.get("text", "")).strip(),
            done=bool(raw.get("done", False)),
            created_at=str(raw.get("created_at", "")),
        )


class TodoDataError(Exception):
    pass


class JsonTodoRepository:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, list[TodoItem]] = {}

    def load(self) -> str | None:
        if not self.file_path.exists():
            self._data = {}
            self.save()
            return None

        try:
            raw = json.loads(self.file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            self._data = {}
            self.save()
            return (
                "The data file could not be parsed and was reset.\n"
                f"Reason: {exc.msg}\n"
                f"File: {self.file_path}"
            )
        except OSError as exc:
            raise TodoDataError(f"Failed to read data file: {exc}") from exc

        parsed: dict[str, list[TodoItem]] = {}
        if isinstance(raw, dict):
            # Parse saved JSON and filter out any corrupted or empty items
            # This prevents the application from crashing upon startup
            for day_key, items in raw.items():
                if not isinstance(day_key, str) or not isinstance(items, list):
                    continue
                parsed[day_key] = [
                    TodoItem.from_dict(item)
                    for item in items
                    if isinstance(item, dict) and str(item.get("text", "")).strip()
                ]

        self._data = parsed
        return None

    def save(self) -> None:
        # Only save days that actually contain tasks to keep the JSON file small
        payload = {
            day_key: [asdict(item) for item in items]
            for day_key, items in self._data.items()
            if items
        }

        try:
            self.file_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            raise TodoDataError(f"Failed to save data file: {exc}") from exc

    def get_tasks_for_date(self, selected_date: date) -> list[TodoItem]:
        # setdefault initializes an empty list if the date doesn't exist yet
        return self._data.setdefault(selected_date.isoformat(), [])

    def get_day_stats(self, selected_date: date) -> tuple[int, int]:
        tasks = self.get_tasks_for_date(selected_date)
        total = len(tasks)
        done = sum(task.done for task in tasks)
        return total, done

    def add_task(self, selected_date: date, text: str) -> None:
        cleaned = text.strip()
        if not cleaned:
            return

        self.get_tasks_for_date(selected_date).append(
            TodoItem(
                text=cleaned,
                done=False,
                created_at=datetime.now().isoformat(timespec="seconds"),
            )
        )
        self.save()

    def toggle_task(self, selected_date: date, task_index: int) -> None:
        tasks = self.get_tasks_for_date(selected_date)
        tasks[task_index].done = not tasks[task_index].done
        self.save()

    def update_task(self, selected_date: date, task_index: int, new_text: str) -> None:
        cleaned = new_text.strip()
        if not cleaned:
            raise ValueError("Task content cannot be empty.")

        tasks = self.get_tasks_for_date(selected_date)
        tasks[task_index].text = cleaned
        self.save()

    def delete_task(self, selected_date: date, task_index: int) -> None:
        tasks = self.get_tasks_for_date(selected_date)
        del tasks[task_index]
        self.save()

    def export_csv(self, file_path: Path) -> None:
        with file_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "text", "done", "created_at"])

            for day, items in self._data.items():
                for item in items:
                    writer.writerow([day, item.text, item.done, item.created_at])

    def import_csv(self, file_path: Path) -> None:
        with file_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            self._data.clear()

            for row in reader:
                day = row["date"]
                item = TodoItem(
                    text=row["text"],
                    done=row["done"] == "True",
                    created_at=row["created_at"],
                )
                self._data.setdefault(day, []).append(item)

        self.save()


class CalendarPanel(ttk.Frame):
    def __init__(self, master, on_prev_month, on_next_month, on_select_day):
        super().__init__(master, padding=10)
        self.on_prev_month = on_prev_month
        self.on_next_month = on_next_month
        self.on_select_day = on_select_day

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        header.columnconfigure(1, weight=1)

        self.prev_button = ttk.Button(header, text="<", command=self.on_prev_month)
        self.prev_button.grid(row=0, column=0, padx=(0, 6))

        self.month_label = ttk.Label(header, text="", anchor="center", font=("Helvetica", 13, "bold"))
        self.month_label.grid(row=0, column=1, sticky="ew")

        self.next_button = ttk.Button(header, text=">", command=self.on_next_month)
        self.next_button.grid(row=0, column=2, padx=(6, 0))

        weekday_frame = ttk.Frame(self)
        weekday_frame.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        for column, weekday_name in enumerate(WEEKDAYS):
            label = ttk.Label(weekday_frame, text=weekday_name, anchor="center")
            label.grid(row=0, column=column, padx=2, sticky="ew")
            weekday_frame.columnconfigure(column, weight=1)

        self.days_frame = ttk.Frame(self)
        self.days_frame.grid(row=2, column=0, sticky="nsew")
        for row in range(6):
            self.days_frame.rowconfigure(row, weight=1)
        for column in range(7):
            self.days_frame.columnconfigure(column, weight=1)

    def render_month(self, year: int, month: int, selected_day: date, stats_provider) -> None:
        for child in self.days_frame.winfo_children():
            child.destroy()

        self.month_label.config(text=f"{year}-{month:02d}")
        month_matrix = calendar.Calendar(firstweekday=0).monthdayscalendar(year, month)

        for row_index, week in enumerate(month_matrix):
            for column_index, day_number in enumerate(week):
                # day_number == 0 means the day belongs to the previous/next month (empty slots)
                if day_number == 0:
                    ttk.Label(self.days_frame, text="").grid(
                        row=row_index,
                        column=column_index,
                        padx=2,
                        pady=2,
                        sticky="nsew",
                    )
                    continue

                current_date = date(year, month, day_number)
                total, done = stats_provider(current_date)
                suffix = f"\n{done}/{total}" if total else ""
                style_name = "Selected.TButton" if current_date == selected_day else "TButton"

                ttk.Button(
                    self.days_frame,
                    text=f"{day_number}{suffix}",
                    style=style_name,
                    command=lambda chosen_date=current_date: self.on_select_day(chosen_date),
                ).grid(row=row_index, column=column_index, padx=2, pady=2, sticky="nsew")


class TaskPanel(ttk.Frame):
    def __init__(self, master, data_file: Path):
        super().__init__(master, padding=10)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.selected_label = ttk.Label(self, text="", font=("Helvetica", 13, "bold"))
        self.selected_label.grid(row=0, column=0, sticky="w")

        input_row = ttk.Frame(self)
        input_row.grid(row=1, column=0, sticky="ew", pady=(8, 8))
        input_row.columnconfigure(0, weight=1)

        self.task_input = ttk.Entry(input_row)
        self.task_input.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.add_button = ttk.Button(input_row, text="Add")
        self.add_button.grid(row=0, column=1)

        self.task_list = tk.Listbox(self, activestyle="dotbox", font=("Helvetica", 11))
        self.task_list.grid(row=2, column=0, sticky="nsew")

        button_row = ttk.Frame(self)
        button_row.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        button_row.columnconfigure((0, 1, 2), weight=1)

        self.toggle_button = ttk.Button(button_row, text="Toggle Done")
        self.toggle_button.grid(row=0, column=0, padx=2, sticky="ew")

        self.edit_button = ttk.Button(button_row, text="Edit")
        self.edit_button.grid(row=0, column=1, padx=2, sticky="ew")

        self.delete_button = ttk.Button(button_row, text="Delete")
        self.delete_button.grid(row=0, column=2, padx=2, sticky="ew")

        self.export_button = ttk.Button(button_row, text="Export")
        self.export_button.grid(row=1, column=0, padx=2, pady=(6, 0), sticky="ew")

        self.import_button = ttk.Button(button_row, text="Import")
        self.import_button.grid(row=1, column=1, padx=2, pady=(6, 0), sticky="ew")

        footer = ttk.Label(
            self,
            text=f"Data file: {data_file}",
            font=("Helvetica", 9),
            foreground="#666666",
            wraplength=400,
            justify="left",
        )
        footer.grid(row=4, column=0, sticky="w", pady=(10, 0))

    def bind_actions(self, on_add, on_toggle, on_edit, on_delete, on_export, on_import) -> None:
        self.add_button.config(command=on_add)
        self.toggle_button.config(command=on_toggle)
        self.edit_button.config(command=on_edit)
        self.delete_button.config(command=on_delete)
        self.export_button.config(command=on_export)
        self.import_button.config(command=on_import)

        self.task_input.bind("<Return>", lambda _event: on_add())
        self.task_list.bind("<Double-Button-1>", lambda _event: on_edit())

    def get_input_text(self) -> str:
        return self.task_input.get().strip()

    def clear_input(self) -> None:
        self.task_input.delete(0, tk.END)

    def focus_input(self) -> None:
        self.task_input.focus_set()

    def get_selected_index(self) -> int | None:
        selected = self.task_list.curselection()
        return selected[0] if selected else None

    def render_tasks(self, selected_date: date, tasks: list[TodoItem]) -> None:
        self.selected_label.config(text=f"Todo - {selected_date.isoformat()}")
        self.task_list.delete(0, tk.END)

        for index, task in enumerate(tasks, start=1):
            marker = "[x]" if task.done else "[ ]"
            self.task_list.insert(tk.END, f"{index}. {marker} {task.text}")


class CalendarTodoApp(tk.Tk):
    def __init__(self, repository: JsonTodoRepository):
        super().__init__()
        self.repository = repository
        self.dark_mode = False

        today = date.today()
        self.current_year = today.year
        self.current_month = today.month
        self.selected_day = today

        self.title(APP_NAME)
        self.geometry(WINDOW_SIZE)
        self.minsize(*MIN_WINDOW_SIZE)

        self._configure_styles()
        self._create_layout()
        self._load_initial_data()
        self.refresh_all()
        self.task_panel.focus_input()

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
            
        # UI Update: Native Tkinter doesn't support rounded corners directly.
        # We use a "flat" borderless design to make buttons look modern instead of blocky.
        style.configure("TButton", relief="flat", borderwidth=0, padding=4)
        style.configure("Selected.TButton", relief="flat", borderwidth=0, background="#b3d9ff")
        # Ensure initial light mode is set to pure white (#ffffff)
        self.configure(bg="#ffffff")
        style.configure("TFrame", background="#ffffff")
        style.configure("TLabel", background="#ffffff")

    def _create_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self, padding=(10, 6))
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        toolbar.columnconfigure(0, weight=1)

        self.theme_button = ttk.Button(toolbar, text="Dark Mode", command=self.toggle_theme)
        self.theme_button.grid(row=0, column=1, sticky="e")

        self.calendar_panel = CalendarPanel(
            self,
            on_prev_month=lambda: self.change_month(-1),
            on_next_month=lambda: self.change_month(1),
            on_select_day=self.select_day,
        )
        self.calendar_panel.grid(row=1, column=0, sticky="nsew")

        self.task_panel = TaskPanel(self, DATA_FILE)
        self.task_panel.grid(row=1, column=1, sticky="nsew")
        self.task_panel.bind_actions(
            on_add=self.add_task,
            on_toggle=self.toggle_selected_task,
            on_edit=self.edit_selected_task,
            on_delete=self.delete_selected_task,
            on_export=self.export_data,
            on_import=self.import_data,
        )

    def _load_initial_data(self) -> None:
        try:
            warning_message = self.repository.load()
        except TodoDataError as exc:
            messagebox.showerror("Data error", str(exc), parent=self)
            warning_message = None

        if warning_message:
            messagebox.showwarning("Data load warning", warning_message, parent=self)

    def refresh_all(self) -> None:
        self.calendar_panel.render_month(
            self.current_year,
            self.current_month,
            self.selected_day,
            stats_provider=self.repository.get_day_stats,
        )
        self.task_panel.render_tasks(
            self.selected_day,
            self.repository.get_tasks_for_date(self.selected_day),
        )

    def select_day(self, selected_day: date) -> None:
        self.selected_day = selected_day
        self.current_year = selected_day.year
        self.current_month = selected_day.month
        self.refresh_all()

    def change_month(self, delta: int) -> None:
        # Calculate new month and handle year wrap-around (e.g., Dec -> Jan)
        month = self.current_month + delta
        year = self.current_year

        if month < 1:
            month = 12
            year -= 1
        elif month > 12:
            month = 1
            year += 1

        self.current_year = year
        self.current_month = month
        self.selected_day = date(year, month, 1)
        self.refresh_all()

    def add_task(self) -> None:
        task_text = self.task_panel.get_input_text()
        if not task_text:
            return

        try:
            self.repository.add_task(self.selected_day, task_text)
        except TodoDataError as exc:
            messagebox.showerror("Save failed", str(exc), parent=self)
            return

        self.task_panel.clear_input()
        self.refresh_all()

    def _require_selected_index(self) -> int | None:
        selected_index = self.task_panel.get_selected_index()
        if selected_index is None:
            messagebox.showinfo("Hint", "Please select a task first.", parent=self)
            return None
        return selected_index

    def toggle_selected_task(self) -> None:
        selected_index = self._require_selected_index()
        if selected_index is None:
            return

        try:
            self.repository.toggle_task(self.selected_day, selected_index)
        except TodoDataError as exc:
            messagebox.showerror("Save failed", str(exc), parent=self)
            return

        self.refresh_all()

    def edit_selected_task(self) -> None:
        selected_index = self._require_selected_index()
        if selected_index is None:
            return

        current_task = self.repository.get_tasks_for_date(self.selected_day)[selected_index]
        new_text = simpledialog.askstring(
            "Edit Task",
            "Task content:",
            initialvalue=current_task.text,
            parent=self,
        )
        if new_text is None:
            return

        try:
            self.repository.update_task(self.selected_day, selected_index, new_text)
        except ValueError as exc:
            messagebox.showwarning("Invalid task", str(exc), parent=self)
            return
        except TodoDataError as exc:
            messagebox.showerror("Save failed", str(exc), parent=self)
            return

        self.refresh_all()

    def delete_selected_task(self) -> None:
        selected_index = self._require_selected_index()
        if selected_index is None:
            return

        should_delete = messagebox.askyesno(
            "Delete Task",
            "Delete the selected task?",
            parent=self,
        )
        if not should_delete:
            return

        try:
            self.repository.delete_task(self.selected_day, selected_index)
        except TodoDataError as exc:
            messagebox.showerror("Save failed", str(exc), parent=self)
            return

        self.refresh_all()

    def export_data(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
        )
        if not path:
            return

        try:
            self.repository.export_csv(Path(path))
        except (TodoDataError, OSError) as exc:
            messagebox.showerror("Export failed", str(exc), parent=self)

    def import_data(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path:
            return

        try:
            self.repository.import_csv(Path(path))
        except (TodoDataError, OSError, KeyError) as exc:
            messagebox.showerror("Import failed", str(exc), parent=self)
            return

        self.refresh_all()

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        style = ttk.Style(self)

        if self.dark_mode:
            # Apply Dark Mode Colors
            self.configure(bg="#2b2b2b")
            style.configure("TFrame", background="#2b2b2b")
            style.configure("TLabel", background="#2b2b2b", foreground="white")
            style.configure("TButton", background="#444", foreground="white")
            style.configure("Selected.TButton", background="#555", foreground="white")
            style.configure("TEntry", fieldbackground="#3a3a3a", foreground="white")
            style.map("TButton", background=[("active", "#555")])
            self.task_panel.task_list.configure(
                bg="#3a3a3a",
                fg="white",
                selectbackground="#555555",
                selectforeground="white",
                highlightbackground="#2b2b2b",
            )
            self.task_panel.task_input.configure(background="#3a3a3a", foreground="white", insertbackground="white")
            self.theme_button.config(text="Light Mode")
        else:
            # Apply Light Mode Colors (Updated to pure white instead of SystemButtonFace)
            self.configure(bg="#ffffff")
            style.configure("TFrame", background="#ffffff")
            style.configure("TLabel", background="#ffffff", foreground="black")
            # Buttons have a very slight grey tint so they don't disappear on white bg
            style.configure("TButton", background="#f2f2f2", foreground="black")
            style.configure("Selected.TButton", background="#b3d9ff", foreground="black") 
            style.configure("TEntry", fieldbackground="#ffffff", foreground="black")
            style.map("TButton", background=[("active", "#e6e6e6")])
            self.task_panel.task_list.configure(
                bg="#ffffff",
                fg="black",
                selectbackground="#cce8ff",
                selectforeground="black",
                highlightbackground="#ffffff",
            )
            self.task_panel.task_input.configure(background="#ffffff", foreground="black", insertbackground="black")
            self.theme_button.config(text="Dark Mode")


def main() -> None:
    repository = JsonTodoRepository(DATA_FILE)
    app = CalendarTodoApp(repository)
    app.mainloop()


if __name__ == "__main__":
    main()