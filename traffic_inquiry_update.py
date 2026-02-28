import os
import zipfile
from typing import Dict

import pandas as pd
from pandas.api.types import is_numeric_dtype
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import system_style
from sort_algorithms import sort_array
from collections import defaultdict, deque


DEFAULT_M06A_COLUMNS = [
    "VehicleType",
    "DerectionTime_O",
    "GantryID_O",
    "DerectionTime_D",
    "GantryID_D",
    "TripLength",
    "TripEnd",
    "TripInformation",
]


class TrafficInquiryGUI:
    def __init__(self, root):
        self.root = root
        self.datasets: Dict[str, pd.DataFrame] = {}
        # 每个数据集一个“历史栈”，用于 Undo
        self.history: Dict[str, list[pd.DataFrame]] = {}
        self._build_ui()

    # ====================== UI Construction ======================

    def _build_ui(self):
        # Left side：Dataset list + Function buttons
        left_frame = ttk.Frame(self.root, padding=5)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(left_frame, text="Datasets").pack(anchor="w")

        self.dataset_list = tk.Listbox(left_frame, height=18)
        self.dataset_list.pack(fill=tk.Y, expand=False)
        self.dataset_list.bind("<<ListboxSelect>>", self._on_dataset_selected)

        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(btn_frame, text="Import", command=self.import_data) \
            .pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Preview", command=self.preview_dataset) \
            .pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Search", command=self.open_search_window) \
            .pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Sort", command=self.open_sort_window) \
            .pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Join", command=self.open_join_window) \
            .pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Export", command=self.export_dataset) \
            .pack(fill=tk.X, pady=2)

        # 新增 Undo 按钮
        ttk.Button(btn_frame, text="Undo", command=self.undo_last_operation) \
            .pack(fill=tk.X, pady=(10, 2))

        ttk.Button(btn_frame, text="Quit", command=self.root.destroy) \
            .pack(fill=tk.X, pady=(10, 2))

        # Right side：Shown area of datasheets
        right_frame = ttk.Frame(self.root, padding=5)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.view_title = ttk.Label(
            right_frame,
            text="Results will be shown here."
        )
        self.view_title.grid(row=0, column=0, columnspan=2, sticky="w")

        self.table = ttk.Treeview(right_frame, show="headings")
        self.table.grid(row=1, column=0, sticky="nsew")

        yscroll = ttk.Scrollbar(
            right_frame, orient="vertical", command=self.table.yview
        )
        yscroll.grid(row=1, column=1, sticky="ns")

        xscroll = ttk.Scrollbar(
            right_frame, orient="horizontal", command=self.table.xview
        )
        xscroll.grid(row=2, column=0, sticky="ew")

        self.table.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        right_frame.rowconfigure(1, weight=1)
        right_frame.columnconfigure(0, weight=1)

    # ====================== History / Undo ======================

    def save_history(self, name: str):
        if name not in self.datasets:
            return
        if name not in self.history:
            self.history[name] = []
        # 深拷贝当前 df
        self.history[name].append(self.datasets[name].copy())

    def undo_last_operation(self):
        """
        将当前选中的数据集回退到上一版本。
        """
        name = self.get_selected_dataset_name()
        if not name:
            return

        hist = self.history.get(name, [])
        if not hist:
            messagebox.showinfo("Undo", "No previous version to restore.")
            return

        last_version = hist.pop()
        self.datasets[name] = last_version
        self.show_dataframe_in_table(last_version, info=f"Undo applied to '{name}'")

    # ====================== Tool Function ======================

    def refresh_dataset_list(self):
        self.dataset_list.delete(0, tk.END)
        for name in sorted(self.datasets.keys()):
            self.dataset_list.insert(tk.END, name)

    def get_selected_dataset_name(self):
        sel = self.dataset_list.curselection()
        if not sel:
            messagebox.showwarning("No dataset", "Please select a dataset on the left.")
            return None
        return self.dataset_list.get(sel[0])

    def show_dataframe_in_table(self, df, info):
        self.table.delete(*self.table.get_children())
        self.table["columns"] = list(df.columns)

        for col in df.columns:
            self.table.heading(col, text=col)
            self.table.column(col, width=120, anchor="center")

        max_rows = 200
        for i, (_, row) in enumerate(df.iterrows()):
            if i >= max_rows:
                break
            values = [str(v) for v in row.tolist()]
            self.table.insert("", tk.END, values=values)

        if not info:
            info = f"{len(df)} rows (showing up to {max_rows})."
        else:
            info = info + f"  |  {len(df)} rows (showing up to {max_rows})."
        self.view_title.config(text=info)

    def _on_dataset_selected(self, event=None):
        sel = self.dataset_list.curselection()
        if not sel:
            return

        name = self.dataset_list.get(sel[0])
        df = self.datasets.get(name)
        if df is not None:
            self.show_dataframe_in_table(df, info=f"Preview of '{name}'")

    # ====================== Import / Export ======================

    def _init_history_for_dataset(self, dataset_name: str, df: pd.DataFrame):
        """
        新导入或新创建的数据集，初始化 history。
        这里默认“当前状态是初始状态”，history 为空列表，
        以后每次修改前再存历史。
        """
        self.datasets[dataset_name] = df
        self.history[dataset_name] = []

    def import_data(self):
        path = filedialog.askopenfilename(
            title="Select CSV or ZIP file",
            filetypes=[
                ("CSV or ZIP", "*.csv *.zip"),
                ("CSV files", "*.csv"),
                ("ZIP files", "*.zip"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return

        if path.lower().endswith(".zip"):
            self._import_from_zip(path)
        elif path.lower().endswith(".csv"):
            self._import_one_csv(path, dataset_name=None)
        else:
            messagebox.showerror(
                "Unsupported file",
                "Please select a .csv or .zip file."
            )
            return

        self.refresh_dataset_list()

    def _import_from_zip(self, path):
        try:
            with zipfile.ZipFile(path) as zf:
                csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
                if not csv_names:
                    messagebox.showwarning(
                        "No CSV",
                        "No CSV files were found in this ZIP."
                    )
                    return

                for name in csv_names:
                    with zf.open(name) as f:
                        df = pd.read_csv(f, header=None)
                        if df.shape[1] == len(DEFAULT_M06A_COLUMNS):
                            df.columns = DEFAULT_M06A_COLUMNS
                        dataset_name = os.path.splitext(os.path.basename(name))[0]
                        self._init_history_for_dataset(dataset_name, df)
                messagebox.showinfo(
                    "Import finished",
                    f"Imported {len(csv_names)} CSV files from ZIP."
                )
        except zipfile.BadZipFile:
            messagebox.showerror("Error", "Not a valid ZIP file.")
        except Exception as e:
            messagebox.showerror("Error", f"Import failed: {e}")

    def _import_one_csv(self, path, dataset_name):
        if dataset_name is None:
            base = os.path.splitext(os.path.basename(path))[0]
            dataset_name = base

        try:
            try:
                df = pd.read_csv(path)
            except Exception:
                df = pd.read_csv(path, header=None)

            if df.shape[1] == len(DEFAULT_M06A_COLUMNS):
                df.columns = DEFAULT_M06A_COLUMNS

            self._init_history_for_dataset(dataset_name, df)
            messagebox.showinfo(
                "Imported",
                f"Imported dataset '{dataset_name}' with "
                f"{len(df)} rows x {len(df.columns)} columns."
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read CSV: {e}")

    def export_dataset(self):
        name = self.get_selected_dataset_name()
        if not name:
            return
        df = self.datasets[name]

        path = filedialog.asksaveasfilename(
            title="Export to CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"{name}.csv",
        )
        if not path:
            return

        try:
            df.to_csv(path, index=False)
            messagebox.showinfo("Exported", f"Dataset '{name}' exported to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")

    # ====================== Preview ======================

    def preview_dataset(self):
        name = self.get_selected_dataset_name()
        if not name:
            return
        df = self.datasets[name]
        self.show_dataframe_in_table(df, info=f"Preview of '{name}'")

    # ====================== Search ======================

    def open_search_window(self):
        name = self.get_selected_dataset_name()
        if not name:
            return
        df = self.datasets[name]

        win = tk.Toplevel(self.root)
        win.title(f"Search in dataset: {name}")
        win.grab_set()  # 模态

        ttk.Label(win, text=f"Dataset: {name}").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(5, 5)
        )

        ttk.Label(win, text="Column:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        col_var = tk.StringVar()
        col_combo = ttk.Combobox(
            win, textvariable=col_var, values=list(df.columns), state="readonly"
        )
        col_combo.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(win, text="Mode:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        mode_var = tk.StringVar()
        mode_combo = ttk.Combobox(win, textvariable=mode_var, state="readonly")
        mode_combo.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(win, text="Value:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        value_var = tk.StringVar()
        ttk.Entry(win, textvariable=value_var, width=25) \
            .grid(row=3, column=1, sticky="w", padx=5, pady=5)

        type_label = ttk.Label(win, text="Column type: -")
        type_label.grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        def update_modes():
            col = col_var.get()
            if not col:
                return
            series = df[col]
            if is_numeric_dtype(series):
                mode_combo["values"] = ["==", ">=", "<="]
                mode_var.set("==")
                type_label.config(text="Column type: numeric")
            else:
                mode_combo["values"] = ["exact", "contains"]
                mode_var.set("contains")
                type_label.config(text="Column type: text")

        def do_search():
            col = col_var.get()
            mode = mode_var.get()
            val = value_var.get().strip()
            if not col or not mode or not val:
                messagebox.showwarning(
                    "Missing input",
                    "Please choose column, mode and input value."
                )
                return
            series = df[col]

            try:
                if is_numeric_dtype(series):
                    num = float(val)
                    if mode == "==":
                        mask = series == num
                    elif mode == ">=":
                        mask = series >= num
                    elif mode == "<=":
                        mask = series <= num
                    else:
                        messagebox.showerror("Error", "Invalid mode.")
                        return
                else:
                    s = series.astype(str)
                    if mode == "exact":
                        mask = s == val
                    elif mode == "contains":
                        mask = s.str.contains(val, case=False, na=False)
                    else:
                        messagebox.showerror("Error", "Invalid mode.")
                        return

                result = df[mask]
                if len(result) == 0:
                    messagebox.showinfo("Search result", "No matching rows found.")
                else:
                    self.show_dataframe_in_table(
                        result,
                        info=(
                            f"Search in '{name}' | column '{col}' "
                            f"| mode '{mode}' | value '{val}'"
                        ),
                    )
            except Exception as e:
                messagebox.showerror("Error", f"Search failed: {e}")

        col_combo.bind("<<ComboboxSelected>>", lambda e: update_modes())
        if df.columns.size > 0:
            col_var.set(df.columns[0])
            update_modes()

        ttk.Button(win, text="Search", command=do_search) \
            .grid(row=5, column=0, columnspan=2, pady=10)

        for i in range(2):
            win.columnconfigure(i, weight=1)

    # ====================== Sort ======================

    def open_sort_window(self):
        name = self.get_selected_dataset_name()
        if not name:
            return
        df = self.datasets[name]

        win = tk.Toplevel(self.root)
        win.title(f"Sort dataset: {name}")
        win.grab_set()

        ttk.Label(win, text=f"Dataset: {name}") \
            .grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        # Column
        ttk.Label(win, text="Column:") \
            .grid(row=1, column=0, sticky="e", padx=5, pady=5)
        col_var = tk.StringVar(value=df.columns[0] if len(df.columns) > 0 else "")
        col_combo = ttk.Combobox(
            win, textvariable=col_var, values=list(df.columns), state="readonly"
        )
        col_combo.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # Order
        ttk.Label(win, text="Order:") \
            .grid(row=2, column=0, sticky="e", padx=5, pady=5)
        order_var = tk.StringVar(value="asc")
        ttk.Radiobutton(
            win, text="Ascending", variable=order_var, value="asc"
        ).grid(row=2, column=1, sticky="w", padx=5)
        ttk.Radiobutton(
            win, text="Descending", variable=order_var, value="desc"
        ).grid(row=3, column=1, sticky="w", padx=5)

        # 🔹 排序算法选择
        ttk.Label(win, text="Algorithm:") \
            .grid(row=4, column=0, sticky="e", padx=5, pady=5)
        algo_var = tk.StringVar(value="Quick Sort")
        algo_combo = ttk.Combobox(
            win,
            textvariable=algo_var,
            values=[
                "Quick Sort",
                "Merge Sort",
                "Heap Sort",
                "Shell Sort",
                "AVL Sort",
                "RBT Sort",
            ],
            state="readonly",
        )
        algo_combo.grid(row=4, column=1, sticky="w", padx=5, pady=5)

        # 按照前%排序
        ttk.Label(win, text="Sort first %:") \
            .grid(row=5, column=0, sticky="e", padx=5, pady=5)
        percent_var = tk.StringVar(value="100")
        ttk.Entry(win, textvariable=percent_var, width=10) \
            .grid(row=5, column=1, sticky="w", padx=5, pady=5)

        def do_sort():
            col = col_var.get()
            if not col:
                messagebox.showwarning("No column", "Please choose a column.")
                return
            ascending = order_var.get() == "asc"
            algo = algo_var.get()
            try:
                percent = float(percent_var.get())
            except ValueError:
                messagebox.showwarning("Invalid percent", "Please input a number for percent.")
                return
            percent = max(1.0, min(percent, 100.0))

            # 在修改数据前保存历史，以便 Undo
            self.save_history(name)

            try:
                n = len(df)
                split_idx = int(n * percent / 100.0)
                if split_idx <= 0:
                    split_idx = 1
                if split_idx > n:
                    split_idx = n

                df_head = df.iloc[:split_idx]
                df_tail = df.iloc[split_idx:]

                # ---- 自定义排序算法 ----
                arr = df_head[col].tolist()

                arr = [v.item() if hasattr(v, "item") else v for v in arr]

                nan_placeholder = object()
                arr_fixed = []
                for v in arr:
                    if isinstance(v, float) and pd.isna(v):
                        arr_fixed.append(nan_placeholder)
                    else:
                        arr_fixed.append(v)

                sorted_vals = sort_array(arr_fixed, algorithm=algo)


                pos = defaultdict(deque)
                for i, v in enumerate(arr_fixed):
                    pos[v].append(i)

                new_order = [pos[v].popleft() for v in sorted_vals]
                sorted_head = df_head.iloc[new_order]

                if not ascending:
                    sorted_head = sorted_head.iloc[::-1]

                sorted_df = pd.concat([sorted_head, df_tail], ignore_index=True)

                self.datasets[name] = sorted_df
                self.show_dataframe_in_table(
                    sorted_df,
                    info=(
                        f"Dataset '{name}' sorted by '{col}' "
                        f"({'ascending' if ascending else 'descending'}) "
                        f"| algo={algo} | first {percent:.1f}%"
                    ),
                )
                messagebox.showinfo("Sorted", f"Dataset '{name}' has been sorted.")

                # 先刷新列表
                self.refresh_dataset_list()

                # 按列表使用的排序顺序来找到 name 所在行
                keys_sorted = sorted(self.datasets.keys())
                idx = keys_sorted.index(name)

                # 再在 Listbox 中重新选中当前数据集
                self.dataset_list.selection_clear(0, tk.END)
                self.dataset_list.selection_set(idx)
                self.dataset_list.activate(idx)

                win.destroy()

            except Exception as e:
                messagebox.showerror("Error", f"Sort failed: {e}")

        ttk.Button(win, text="Sort", command=do_sort) \
            .grid(row=6, column=0, columnspan=2, pady=10)

        for i in range(2):
            win.columnconfigure(i, weight=1)

    # ====================== Join ======================

    def open_join_window(self):
        if len(self.datasets) < 2:
            messagebox.showwarning(
                "Not enough datasets",
                "At least two datasets are required for join."
            )
            return

        names = sorted(self.datasets.keys())

        win = tk.Toplevel(self.root)
        win.title("Join datasets")
        win.grab_set()

        ttk.Label(win, text="Dataset A:") \
            .grid(row=0, column=0, sticky="e", padx=5, pady=5)
        a_var = tk.StringVar(value=names[0])
        ttk.Combobox(
            win, textvariable=a_var, values=names, state="readonly"
        ).grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(win, text="Dataset B:") \
            .grid(row=1, column=0, sticky="e", padx=5, pady=5)
        b_var = tk.StringVar(value=names[1])
        ttk.Combobox(
            win, textvariable=b_var, values=names, state="readonly"
        ).grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(win, text="Result name:") \
            .grid(row=2, column=0, sticky="e", padx=5, pady=5)
        result_var = tk.StringVar(value="join_result")
        ttk.Entry(win, textvariable=result_var, width=25) \
            .grid(row=2, column=1, sticky="w", padx=5, pady=5)

        def do_join():
            name_a = a_var.get()
            name_b = b_var.get()
            result_name = result_var.get().strip() or "join_result"
            if name_a == name_b:
                messagebox.showwarning(
                    "Same dataset",
                    "Please choose two different datasets."
                )
                return

            df1 = self.datasets[name_a]
            df2 = self.datasets[name_b]

            if list(df1.columns) != list(df2.columns):
                proceed = messagebox.askyesno(
                    "Different columns",
                    "Two datasets have different columns.\n"
                    "Join using only common columns?"
                )
                if not proceed:
                    return
                common_cols = [c for c in df1.columns if c in df2.columns]
                if not common_cols:
                    messagebox.showerror(
                        "No common columns",
                        "There are no common columns to join on."
                    )
                    return
                df1_use = df1[common_cols]
                df2_use = df2[common_cols]
            else:
                df1_use = df1
                df2_use = df2

            try:
                joined = pd.concat([df1_use, df2_use], ignore_index=True)
                # 新的数据集也初始化 history
                self._init_history_for_dataset(result_name, joined)
                self.refresh_dataset_list()
                self.show_dataframe_in_table(
                    joined,
                    info=(
                        f"Join '{name_a}' + '{name_b}' "
                        f"-> '{result_name}'"
                    ),
                )
                messagebox.showinfo(
                    "Joined",
                    f"Created dataset '{result_name}' with {len(joined)} rows."
                )
                win.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Join failed: {e}")

        ttk.Button(win, text="Join", command=do_join) \
            .grid(row=3, column=0, columnspan=2, pady=10)

        for i in range(2):
            win.columnconfigure(i, weight=1)


def main():
    system_style.enhance_traffic_gui_style(TrafficInquiryGUI)
    root = tk.Tk()
    app = TrafficInquiryGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
