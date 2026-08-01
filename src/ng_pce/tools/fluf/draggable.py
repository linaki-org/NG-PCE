from PIL import Image, ImageTk


HANDLE_R    = 6          # radius of resize handles (pixels)
MIN_SIZE    = 30         # minimum object dimension

HANDLE_COL  = "#E94560"
HANDLE_OUT  = "#FFFFFF"
SEL_BORDER  = "#E94560"


class DraggableObject:
    """Represents one placed object on the canvas."""

    def __init__(self, canvas, img_path: str, x=100, y=100):
        self.canvas     = canvas
        self.img_path   = img_path
        self.x          = x          # top-left corner
        self.y          = y
        self.orig_img   = Image.open(img_path).convert("RGBA")
        self.w          = self.orig_img.width
        self.h          = self.orig_img.height
        self._photo     = None
        self.img_id     = None
        self.border_id  = None
        self.handle_ids = []
        self.selected   = False
        self._draw()

    # ── Rendering ────────────────────────────────────────────────────────────

    def _render_image(self):
        resized    = self.orig_img.resize((max(MIN_SIZE, self.w), max(MIN_SIZE, self.h)),
                                          Image.LANCZOS)
        self._photo = ImageTk.PhotoImage(resized)

    def _draw(self):
        self._render_image()
        c = self.canvas
        if self.img_id is not None:
            c.delete(self.img_id)
        self.img_id = c.create_image(self.x, self.y, anchor="nw",
                                     image=self._photo, tags=("obj", f"obj_{id(self)}"))
        self._draw_selection()

    def _draw_selection(self):
        c = self.canvas
        # remove old decoration
        if self.border_id:
            c.delete(self.border_id)
        for h in self.handle_ids:
            c.delete(h)
        self.handle_ids = []
        self.border_id  = None

        if not self.selected:
            return

        x1, y1 = self.x,          self.y
        x2, y2 = self.x + self.w, self.y + self.h

        # dashed selection border
        self.border_id = c.create_rectangle(
            x1, y1, x2, y2,
            outline=SEL_BORDER, width=2, dash=(6, 3),
            tags=("decoration",)
        )

        # four corner handles
        corners = [(x1, y1, "nw"), (x2, y1, "ne"),
                   (x1, y2, "sw"), (x2, y2, "se")]
        for hx, hy, corner in corners:
            hid = c.create_oval(
                hx - HANDLE_R, hy - HANDLE_R,
                hx + HANDLE_R, hy + HANDLE_R,
                fill=HANDLE_COL, outline=HANDLE_OUT, width=2,
                tags=("handle", f"handle_{corner}_{id(self)}", "decoration")
            )
            self.handle_ids.append(hid)

    def redraw(self):
        self._draw()

    def move_to(self, x, y):
        self.x, self.y = x, y
        self.canvas.moveto(self.img_id, x, y)
        self._draw_selection()

    def resize_to(self, w, h):
        self.w = max(MIN_SIZE, w)
        self.h = max(MIN_SIZE, h)
        self._draw()

    def set_selected(self, value: bool):
        self.selected = value
        self._draw_selection()

    def hit_test(self, px, py) -> bool:
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h

    def handle_at(self, px, py):
        """Return corner string ('nw','ne','sw','se') if (px,py) is on a handle, else None."""
        corners = {
            "nw": (self.x,          self.y),
            "ne": (self.x + self.w, self.y),
            "sw": (self.x,          self.y + self.h),
            "se": (self.x + self.w, self.y + self.h),
        }
        for name, (hx, hy) in corners.items():
            if abs(px - hx) <= HANDLE_R + 2 and abs(py - hy) <= HANDLE_R + 2:
                return name
        return None
