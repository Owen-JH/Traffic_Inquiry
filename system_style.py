import tkinter as tk
from tkinter import ttk
from typing import Type


def enhance_traffic_gui_style(TrafficInquiryGUI: Type):
    """
    对传进来的 TrafficInquiryGUI 类做 monkey-patch：
    - 包一层新的 __init__，在原有 UI 基础上加样式
    - 替换 show_dataframe_in_table，增加斑马线配色
    """
    orig_init = TrafficInquiryGUI.__init__
    orig_show = getattr(TrafficInquiryGUI, "show_dataframe_in_table", None)

    def styled_init(self, root, *args, **kwargs):
        orig_init(self, root, *args, **kwargs)

        self._bg_main = "#f4f5fb"
        self._bg_sidebar = "#e4e6f2"
        self._bg_table_even = "#ffffff"
        self._bg_table_odd = "#f9fafb"
        self._accent = "#4f46e5"
        self._accent_soft = "#e0e7ff"

        # Window title & Background
        try:
            self.root.configure(bg=self._bg_main)
            self.root.title("Traffic Data Inquiry System")
        except Exception:
            pass

        # ttk style
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            # Default
            pass

        style.configure("TFrame", background=self._bg_main)
        style.configure(
            "TLabel",
            background=self._bg_main,
            foreground="#222222",
            font=("Segoe UI", 10),
        )
        style.configure(
            "TButton",
            font=("Segoe UI", 10),
            padding=6,
        )
        style.map(
            "TButton",
            background=[("active", self._accent_soft)],
        )
        style.configure(
            "Treeview",
            background=self._bg_table_even,
            fieldbackground=self._bg_table_even,
            foreground="#222222",
            rowheight=24,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Treeview.Heading",
            background=self._accent_soft,
            foreground="#111827",
            font=("Segoe UI", 9, "bold"),
        )
        style.map(
            "Treeview.Heading",
            background=[("active", "#cbd5f5")],
        )

        if hasattr(self, "dataset_list"):
            try:
                self.dataset_list.configure(
                    bg=self._bg_sidebar,
                    fg="#111827",
                    highlightthickness=0,
                    borderwidth=0,
                    selectbackground=self._accent_soft,
                    selectforeground="#111827",
                )
            except Exception:
                pass

        mapping = {
            "Import": "Import",
            "Preview": "Preview",
            "Search": "Search",
            "Sort": "Sort",
            "Join": "Join",
            "Export": "Export",
            "Quit": "Quit",
        }

        def decorate_buttons(widget):
            for child in widget.winfo_children():
                try:
                    if isinstance(child, ttk.Button):
                        txt = child.cget("text")
                        if txt in mapping:
                            child.config(text=mapping[txt])
                except Exception:
                    pass
                decorate_buttons(child)

        try:
            decorate_buttons(self.root)
        except Exception:
            pass

    def styled_show_dataframe(self, df, info):
        """
        改写表格展示：加 Treeview 斑马线背景，其他逻辑和你原来的类似。
        """
        self.table.delete(*self.table.get_children())
        self.table["columns"] = list(df.columns)

        for col in df.columns:
            self.table.heading(col, text=col)
            self.table.column(col, width=120, anchor="center")

        bg_even = getattr(self, "_bg_table_even", "#ffffff")
        bg_odd = getattr(self, "_bg_table_odd", "#f9fafb")
        try:
            self.table.tag_configure("evenrow", background=bg_even)
            self.table.tag_configure("oddrow", background=bg_odd)
        except Exception:
            pass

        max_rows = 200
        for i, (_, row) in enumerate(df.iterrows()):
            if i >= max_rows:
                break
            values = [str(v) for v in row.tolist()]
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.table.insert("", tk.END, values=values, tags=(tag,))

        if not info:
            info = f"{len(df)} rows (showing up to {max_rows})."
        else:
            info = info + f"  |  {len(df)} rows (showing up to {max_rows})."
        self.view_title.config(text=info)

    TrafficInquiryGUI.__init__ = styled_init
    if orig_show is not None:
        TrafficInquiryGUI.show_dataframe_in_table = styled_show_dataframe
