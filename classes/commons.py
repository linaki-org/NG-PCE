import config as cfg
import pygame

# ==========================================
#  CONSTANTES DE TRANSICIÓN
# ==========================================
TRANSITION_FADE = "FADE"
TRANSITION_SLIDE_LEFT = "SLIDE_L"
TRANSITION_SLIDE_RIGHT = "SLIDE_R"
TRANSITION_SLIDE_UP = "SLIDE_U"
TRANSITION_SLIDE_DOWN = "SLIDE_D"
TRANSITION_NONE = "NONE"
TRANSITION_ZOOM = "ZOOM"

# ==========================================
#  UTILIDADES GRAFICAS
# ==========================================
SHARP_FONT_CACHE = {}
scale_factor = 1.0
offset_x = 0
offset_y = 0


def update_graphics_metrics(sf, ox, oy):
    global scale_factor, offset_x, offset_y
    scale_factor = sf
    offset_x = ox
    offset_y = oy


def get_sharp_font(base_size):
    global scale_factor
    real_size = int(base_size * scale_factor)
    if real_size < 1: real_size = 1
    key = (cfg.UI_FONT_PATH, real_size)
    if key not in SHARP_FONT_CACHE:
        try:
            SHARP_FONT_CACHE[key] = pygame.font.Font(cfg.UI_FONT_PATH, real_size)
        except:
            SHARP_FONT_CACHE[key] = pygame.font.SysFont("arial", real_size)
    return SHARP_FONT_CACHE[key]


def draw_text_sharp(text, virtual_x, virtual_y, base_size, color, align="topleft", shadow=False, target_surface=None):
    if target_surface is None:
        target_surface = pygame.display.get_surface()

    font = get_sharp_font(base_size)
    text_surf = font.render(str(text), True, color)

    real_x = virtual_x * scale_factor + offset_x
    real_y = virtual_y * scale_factor + offset_y

    dest_rect = text_surf.get_rect()
    if align == "topleft":
        dest_rect.topleft = (real_x, real_y)
    elif align == "center":
        dest_rect.center = (real_x, real_y)
    elif align == "midtop":
        dest_rect.midtop = (real_x, real_y)
    elif align == "midbottom":
        dest_rect.midbottom = (real_x, real_y)
    elif align == "midleft":
        dest_rect.midleft = (real_x, real_y)
    elif align == "midright":
        dest_rect.midright = (real_x, real_y)
    elif align == "bottomleft":
        dest_rect.bottomleft = (real_x, real_y)
    elif align == "bottomright":
        dest_rect.bottomright = (real_x, real_y)

    if shadow:
        shadow_surf = font.render(str(text), True, (0, 0, 0))
        s_rect = dest_rect.copy()
        s_rect.x += max(1, int(2 * scale_factor))
        s_rect.y += max(1, int(2 * scale_factor))
        target_surface.blit(shadow_surf, s_rect)

    target_surface.blit(text_surf, dest_rect)


def get_virtual_mouse_pos():
    if scale_factor == 0: return 0, 0
    mouse_x, mouse_y = pygame.mouse.get_pos()
    virtual_x = (mouse_x - offset_x) / scale_factor
    virtual_y = (mouse_y - offset_y) / scale_factor
    virtual_x = max(0, min(cfg.CONFIG["GAME_WIDTH"] - 1, int(virtual_x)))
    virtual_y = max(0, min(cfg.CONFIG["GAME_HEIGHT"] - 1, int(virtual_y)))
    return virtual_x, virtual_y
