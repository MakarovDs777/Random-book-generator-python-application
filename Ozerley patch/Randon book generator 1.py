import tkinter as tk
from tkinter import messagebox
import random
import threading
import os
import datetime

# Генератор случайных «книг» — сетка символов, обновляемая через заданный интервал
# По умолчанию: 10x10, между символами 1 пробел, алфавит: русские буквы + пробел + точка с запятой

DEFAULT_ROWS = 10
DEFAULT_COLS = 10
DEFAULT_INTERVAL = 0.6  # сек

RUSSIAN_ALPHABET = list("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
DEFAULT_EXTRA = " ;"  # пробел и точка с запятой

class RandomBookGenerator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Генератор случайных книг 1")
        self.geometry("720x520")

        # Параметры
        params_frame = tk.Frame(self)
        params_frame.pack(padx=10, pady=8, anchor="w")

        tk.Label(params_frame, text="Строк (rows):").grid(row=0, column=0, sticky="w")
        self.rows_var = tk.IntVar(value=DEFAULT_ROWS)
        self.rows_spin = tk.Spinbox(params_frame, from_=1, to=200, width=6, textvariable=self.rows_var)
        self.rows_spin.grid(row=0, column=1, padx=6)

        tk.Label(params_frame, text="Столбцов (cols):").grid(row=0, column=2, sticky="w")
        self.cols_var = tk.IntVar(value=DEFAULT_COLS)
        self.cols_spin = tk.Spinbox(params_frame, from_=1, to=200, width=6, textvariable=self.cols_var)
        self.cols_spin.grid(row=0, column=3, padx=6)

        tk.Label(params_frame, text="Интервал (сек):").grid(row=0, column=4, sticky="w")
        self.interval_var = tk.StringVar(value=str(DEFAULT_INTERVAL))
        self.interval_entry = tk.Entry(params_frame, width=6, textvariable=self.interval_var)
        self.interval_entry.grid(row=0, column=5, padx=6)

        tk.Label(params_frame, text="Доп. символы (включите пробел/; если нужно):").grid(row=1, column=0, columnspan=3, sticky="w", pady=(8,0))
        self.extra_entry = tk.Entry(params_frame, width=40)
        self.extra_entry.insert(0, DEFAULT_EXTRA)
        self.extra_entry.grid(row=1, column=3, columnspan=3, sticky="w", padx=6, pady=(8,0))

        # Кнопки управления
        controls_frame = tk.Frame(self)
        controls_frame.pack(padx=10, pady=6, anchor="w")

        self.start_btn = tk.Button(controls_frame, text="Старт", command=self.start)
        self.start_btn.grid(row=0, column=0, padx=6)

        self.stop_btn = tk.Button(controls_frame, text="Стоп", command=self.stop, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=6)

        self.randomize_btn = tk.Button(controls_frame, text="Сгенерировать сейчас", command=self.generate_once)
        self.randomize_btn.grid(row=0, column=2, padx=6)

        self.save_btn = tk.Button(controls_frame, text="Сохранить книгу на рабочий стол", command=self.save_to_desktop)
        self.save_btn.grid(row=0, column=3, padx=6)

        # Поле вывода текста (книга)
        self.text = tk.Text(self, wrap=tk.NONE, font=("Consolas", 12))
        self.text.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        self.text.configure(state=tk.DISABLED)

        # Внутренние данные
        self._running = False
        self._job = None
        self.grid_chars = []

        # Инициализация начальной сетки
        self._init_grid()
        self._render()

        # Обработчик закрытия
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _get_alphabet(self):
        extra = self.extra_entry.get()
        # Если пользователь не ввёл ничего, используем дефолт
        if extra is None:
            extra = DEFAULT_EXTRA
        # Собираем набор символов: русский алфавит + дополнительные символы (удаляем дубликаты, но сохраняем порядок)
        base = RUSSIAN_ALPHABET[:]
        for ch in extra:
            if ch not in base:
                base.append(ch)
        return base

    def _init_grid(self):
        rows = max(1, int(self.rows_var.get()))
        cols = max(1, int(self.cols_var.get()))
        alphabet = self._get_alphabet()
        self.grid_chars = [[random.choice(alphabet) for _ in range(cols)] for _ in range(rows)]

    def _render(self):
        # Отобразить сетку: каждый символ + один пробел между символами
        rows = len(self.grid_chars)
        cols = len(self.grid_chars[0]) if rows > 0 else 0
        lines = []
        for r in range(rows):
            lines.append(" ".join(self.grid_chars[r]))
        text_out = "\n".join(lines)
        self.text.configure(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, text_out)
        self.text.configure(state=tk.DISABLED)

    def _update_once(self):
        # Смена каждой буквы на случайную
        rows = len(self.grid_chars)
        cols = len(self.grid_chars[0]) if rows > 0 else 0
        alphabet = self._get_alphabet()
        for r in range(rows):
            for c in range(cols):
                self.grid_chars[r][c] = random.choice(alphabet)
        self._render()

    def generate_once(self):
        # Немедленная генерация сетки (с текущими параметрами размеров/алфавита)
        try:
            self._init_grid()
            self._update_once()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _tick(self):
        if not self._running:
            return
        try:
            self._update_once()
        except Exception:
            pass
        # Планируем следующий вызов
        try:
            interval = float(self.interval_var.get())
            if interval <= 0:
                interval = DEFAULT_INTERVAL
        except Exception:
            interval = DEFAULT_INTERVAL
        ms = max(10, int(interval * 1000))
        self._job = self.after(ms, self._tick)

    def start(self):
        if self._running:
            return
        # Применяем размеры и создаём сетку
        try:
            rows = int(self.rows_var.get())
            cols = int(self.cols_var.get())
            if rows <= 0 or cols <= 0:
                raise ValueError("Размеры должны быть положительными числами")
        except Exception as e:
            messagebox.showerror("Ошибка параметров", f"Неверные размеры: {e}")
            return

        try:
            interval = float(self.interval_var.get())
            if interval <= 0:
                raise ValueError()
        except Exception:
            messagebox.showerror("Ошибка параметров", "Интервал должен быть положительным числом (сек).")
            return

        self._init_grid()
        self._running = True
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self.randomize_btn.configure(state=tk.DISABLED)
        # Первый тик
        self._tick()

    def stop(self):
        if not self._running:
            return
        self._running = False
        if self._job is not None:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.randomize_btn.configure(state=tk.NORMAL)

    def save_to_desktop(self):
        # Сохранить текущее содержимое текстового поля на рабочий стол
        try:
            content = self.text.get("1.0", tk.END)
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            if not os.path.isdir(desktop):
                # если папки Desktop нет (например, в некоторых системах), сохраняем в домашнюю директорию
                desktop = os.path.expanduser("~")
            fname = f"random_book_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            path = os.path.join(desktop, fname)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("Сохранено", f"Книга сохранена:\n{path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")

    def _on_close(self):
        self.stop()
        self.destroy()


if __name__ == '__main__':
    app = RandomBookGenerator()
    app.mainloop()
