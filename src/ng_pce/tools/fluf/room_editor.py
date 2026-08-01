"""
Room Editor — FLUF
Clean rewrite: drag-to-move, corner handles to resize, sidebar object picker.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
from .draggable import DraggableObject
import json

# ── Layout constants ────────────────────────────────────────────────────────
SIDEBAR_W   = 220
CANVAS_H    = 900
CANVAS_W    = 1600
WIN_W       = CANVAS_W + SIDEBAR_W
WIN_H       = CANVAS_H

# ── Colour palette ──────────────────────────────────────────────────────────
BG          = "#1A1A2E"  # deep navy – canvas surround
SIDEBAR_BG  = "#16213E"  # slightly lighter navy
ACCENT      = "#E94560"  # coral-red
TEXT_LIGHT  = "#E0E0E0"
TEXT_DIM    = "#7A7A9A"




class RoomEditor:
    def __init__(self, root: tk.Tk, room_id: str):
        self.root       = root
        self.root.title(f"{room_id} - Room Editor — FLUF")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        self.room_id=room_id

        with open("meta.json") as f:
            self.meta=json.load(f)
            if room_id not in self.meta["rooms"]:
                raise NameError(f"Room {room_id} doesn't exist. Please create it first, with 'pce new room {room_id}'")
            self.meta_obj=self.meta["rooms"].get(room_id)

        self.objects: list[DraggableObject] = []
        self.selected: DraggableObject | None = None

        # interaction state
        self._drag_start   = None   # (mouse_x, mouse_y, obj_x, obj_y)
        self._resize_corner = None  # corner name
        self._resize_start  = None  # (mouse_x, mouse_y, obj_x, obj_y, obj_w, obj_h)

        self._bg_photo = None
        self._bg_id    = None

        self._build_ui()
        self._populate_sidebar()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── sidebar ──
        self.sidebar = tk.Frame(self.root, width=SIDEBAR_W, bg=SIDEBAR_BG)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="FLUF", font=("Helvetica", 22, "bold"),
                 fg=ACCENT, bg=SIDEBAR_BG).pack(pady=(20, 2))
        tk.Label(self.sidebar, text="Room Editor", font=("Helvetica", 10),
                 fg=TEXT_DIM, bg=SIDEBAR_BG).pack(pady=(0, 16))

        sep = tk.Frame(self.sidebar, height=1, bg=ACCENT)
        sep.pack(fill="x", padx=16, pady=(0, 16))

        tk.Label(self.sidebar, text="Rooms", font=("Helvetica", 9, "bold"),
                 fg=TEXT_DIM, bg=SIDEBAR_BG, anchor="w").pack(fill="x", padx=16)

        # scrollable list
        list_frame = tk.Frame(self.sidebar, bg=SIDEBAR_BG)
        list_frame.pack(fill="both", expand=True, padx=8, pady=8)

        scrollbar = tk.Scrollbar(list_frame, orient="vertical")
        self.rooms_list = tk.Listbox(
            list_frame, yscrollcommand=scrollbar.set,
            bg="#0F3460", fg=TEXT_LIGHT,
            selectbackground=ACCENT, selectforeground="#fff",
            font=("Helvetica", 11), bd=0, highlightthickness=0,
            activestyle="none", cursor="hand2"
        )
        scrollbar.config(command=self.rooms_list.yview)
        scrollbar.pack(side="right", fill="y")
        self.rooms_list.pack(fill="both", expand=True)
        self.rooms_list.bind("<<ListboxSelect>>", self._on_list_select)

        # placed-object selector
        sep2 = tk.Frame(self.sidebar, height=1, bg="#2A2A4A")
        sep2.pack(fill="x", padx=16, pady=(8, 8))

        tk.Label(self.sidebar, text="PLACED", font=("Helvetica", 9, "bold"),
                 fg=TEXT_DIM, bg=SIDEBAR_BG, anchor="w").pack(fill="x", padx=16)

        placed_frame = tk.Frame(self.sidebar, bg=SIDEBAR_BG)
        placed_frame.pack(fill="both", expand=True, padx=8, pady=8)

        pb_scroll = tk.Scrollbar(placed_frame, orient="vertical")
        self.obj_list = tk.Listbox(
            placed_frame, yscrollcommand=pb_scroll.set,
            bg="#0F3460", fg=TEXT_LIGHT,
            selectbackground=ACCENT, selectforeground="#fff",
            font=("Helvetica", 10), bd=0, highlightthickness=0,
            activestyle="none", cursor="hand2"
        )
        pb_scroll.config(command=self.obj_list.yview)
        pb_scroll.pack(side="right", fill="y")
        self.obj_list.pack(fill="both", expand=True)
        self.obj_list.bind("<<ListboxSelect>>", self._on_placed_select)

        # action buttons
        btn_frame = tk.Frame(self.sidebar, bg=SIDEBAR_BG)
        btn_frame.pack(fill="x", padx=12, pady=12)

        self._make_btn(btn_frame, "New Object",
                       self._load_background).pack(fill="x")

        self._btn_delete = self._make_btn(btn_frame, "Delete selected",
                                          self._delete_selected, danger=True)
        self._btn_delete.pack(fill="x", pady=(0, 6))



        # ── canvas ──
        canvas_container = tk.Frame(self.root, bg=BG)
        canvas_container.pack(side="left", fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_container, width=CANVAS_W, height=CANVAS_H,
                                bg="#0A0A1A", bd=0, highlightthickness=0, cursor="crosshair")
        self.canvas.pack()

        # canvas event bindings
        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        # status bar
        self.status_var = tk.StringVar(value="Load a room background, then place objects from the sidebar.")
        status = tk.Label(canvas_container, textvariable=self.status_var,
                          bg="#0A0A1A", fg=TEXT_DIM, font=("Helvetica", 9),
                          anchor="w", padx=10)
        status.pack(fill="x")

    def _make_btn(self, parent, text, cmd, danger=False):
        fg = "#fff"
        bg = "#C0392B" if danger else ACCENT
        active_bg = "#E57373" if danger else "#FF6B81"
        return tk.Button(parent, text=text, command=cmd,
                         bg=bg, fg=fg, activebackground=active_bg, activeforeground="#fff",
                         font=("Helvetica", 10, "bold"), bd=0,
                         pady=8, relief="flat", cursor="hand2")

    # ── Sidebar population ────────────────────────────────────────────────────

    def _populate_sidebar(self):
        """Scan the objects/ folder and list available assets."""
        self.rooms_list.delete(0, "end")
        files = sorted(f for f in os.listdir(folder)
                       if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")))
        if not files:
            self.obj_list.insert("end", "(folder is empty)")
        for f in files:
            self.obj_list.insert("end", "  " + os.path.splitext(f)[0])
        self._asset_files = files  # keep in sync with listbox indices

    def _refresh_placed_list(self):
        self.placed_list.delete(0, "end")
        for i, obj in enumerate(self.objects):
            name = os.path.splitext(os.path.basename(obj.img_path))[0]
            self.placed_list.insert("end", f"  {i+1}. {name}")

    # ── Event handlers — sidebar ──────────────────────────────────────────────

    def _on_list_select(self, event):
        sel = self.obj_list.curselection()
        if not sel:
            return
        idx = sel[0]
        if not hasattr(self, "_asset_files") or idx >= len(self._asset_files):
            return
        path = os.path.join("objects", self._asset_files[idx])
        self._place_object(path)

    def _on_placed_select(self, event):
        sel = self.placed_list.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx < len(self.objects):
            self._select_object(self.objects[idx])

    def _delete_selected(self):
        if self.selected is None:
            return
        obj = self.selected
        self.canvas.delete(obj.img_id)
        self.canvas.delete(obj.border_id)
        for h in obj.handle_ids:
            self.canvas.delete(h)
        self.objects.remove(obj)
        self.selected = None
        self._refresh_placed_list()
        self.status("Object deleted.")

    def _load_background(self):
        from tkinter.filedialog import askopenfilename
        path = askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.webp")])
        if not path:
            return
        img    = Image.open(path).convert("RGB")
        factor = CANVAS_H / img.height
        img    = img.resize((int(img.width * factor), CANVAS_H), Image.LANCZOS)
        if img.width < CANVAS_W:
            img = img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
        self._bg_photo = ImageTk.PhotoImage(img)
        if self._bg_id:
            self.canvas.delete(self._bg_id)
        self._bg_id = self.canvas.create_image(0, 0, anchor="nw", image=self._bg_photo)
        self.canvas.tag_lower(self._bg_id)   # keep background behind objects
        self.status(f"Background: {os.path.basename(path)}")

    # ── Object placement & selection ─────────────────────────────────────────

    def _place_object(self, path: str):
        obj = DraggableObject(self.canvas, path, x=80, y=80)
        self.objects.append(obj)
        self._select_object(obj)
        self._refresh_placed_list()
        self.status(f"Placed: {os.path.basename(path)} — drag to move, handles to resize.")

    def _select_object(self, obj: DraggableObject | None):
        if self.selected and self.selected is not obj:
            self.selected.set_selected(False)
        self.selected = obj
        if obj:
            obj.set_selected(True)
            # sync placed list highlight
            idx = self.objects.index(obj)
            self.placed_list.selection_clear(0, "end")
            self.placed_list.selection_set(idx)
            self.placed_list.see(idx)
            self._print_coords(obj)
        else:
            self.placed_list.selection_clear(0, "end")

    def _deselect_all(self):
        self._select_object(None)

    # ── Canvas mouse interactions ─────────────────────────────────────────────

    def _on_press(self, event):
        px, py = event.x, event.y

        # 1. Check handles first (only on selected object)
        if self.selected:
            corner = self.selected.handle_at(px, py)
            if corner:
                obj = self.selected
                self._resize_corner = corner
                self._resize_start  = (px, py, obj.x, obj.y, obj.w, obj.h)
                self.canvas.config(cursor=self._corner_cursor(corner))
                return

        # 2. Check if clicking an existing object (top-most wins)
        for obj in reversed(self.objects):
            if obj.hit_test(px, py):
                self._select_object(obj)
                self._drag_start = (px, py, obj.x, obj.y)
                self.canvas.config(cursor="fleur")
                return

        # 3. Clicked empty canvas — deselect
        self._deselect_all()

    def _on_drag(self, event):
        px, py = event.x, event.y

        if self._resize_corner and self.selected:
            self._do_resize(px, py)
            return

        if self._drag_start and self.selected:
            mx0, my0, ox, oy = self._drag_start
            dx, dy = px - mx0, py - my0
            new_x = max(0, min(CANVAS_W - self.selected.w, ox + dx))
            new_y = max(0, min(CANVAS_H - self.selected.h, oy + dy))
            self.selected.move_to(new_x, new_y)
            self._print_coords(self.selected)

    def _on_release(self, event):
        if self.selected:
            self._print_coords(self.selected)
        self._drag_start    = None
        self._resize_corner = None
        self._resize_start  = None
        self.canvas.config(cursor="crosshair")

    def _do_resize(self, px, py):
        if not self._resize_start or not self.selected:
            return
        mx0, my0, ox, oy, ow, oh = self._resize_start
        obj    = self.selected
        corner = self._resize_corner
        dx, dy = px - mx0, py - my0

        if corner == "se":
            obj.resize_to(ow + dx, oh + dy)
            obj.move_to(ox, oy)
        elif corner == "sw":
            new_w = ow - dx
            obj.resize_to(new_w, oh + dy)
            obj.move_to(ox + ow - obj.w, oy)
        elif corner == "ne":
            new_h = oh - dy
            obj.resize_to(ow + dx, new_h)
            obj.move_to(ox, oy + oh - obj.h)
        elif corner == "nw":
            new_w = ow - dx
            new_h = oh - dy
            obj.resize_to(new_w, new_h)
            obj.move_to(ox + ow - obj.w, oy + oh - obj.h)

        self._print_coords(obj)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _corner_cursor(self, corner: str) -> str:
        return {"nw": "top_left_corner", "ne": "top_right_corner",
                "sw": "bottom_left_corner", "se": "bottom_right_corner"}.get(corner, "crosshair")

    def _print_coords(self, obj: DraggableObject):
        name = os.path.splitext(os.path.basename(obj.img_path))[0]
        self.status(f"{name}  |  x={obj.x}  y={obj.y}  w={obj.w}  h={obj.h}")

    def status(self, msg: str):
        self.status_var.set(msg)


# ── Entry point ───────────────────────────────────────────────────────────────

def open_editor():
    root = tk.Tk()
    root.geometry(f"{WIN_W}x{WIN_H}")
    editor = RoomEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()