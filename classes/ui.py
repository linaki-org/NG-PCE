import json
import yaml
import config as cfg
import pygame
import os
import math
from classes.commons import (get_sharp_font,
                            get_virtual_mouse_pos,
                            draw_text_sharp,
                            scale_factor)
from classes.resources import RES_MANAGER

VERB_STYLE = {
    "BG_MENU": (85, 85, 68),
    "BTN_BG": (68, 68, 68),
    "BORDER_LIGHT": (102, 102, 102),
    "BORDER_DARK": (34, 34, 34),
    "TEXT_NORMAL": (255, 255, 170),
    "TEXT_HOVER": (255, 100, 100),
    "TEXT_SELECTED": (255, 255, 255)
}
DIALOGUE_BTN_STYLE = VERB_STYLE


class ScrollButton:
    def __init__(self, x, y, size, direction):
        self.rect = pygame.Rect(x, y, size, size)
        self.direction = direction

    def is_mouse_over(self, mx, my):
        return self.rect.collidepoint(mx, my)

    def draw(self, screen, mx, my):
        # Lógica de Hover y Colores Originales
        hovered = self.rect.collidepoint(mx, my)
        bg_color = (80, 80, 80) if hovered else VERB_STYLE["BTN_BG"]
        arrow_color = VERB_STYLE["TEXT_HOVER"] if hovered else VERB_STYLE["TEXT_NORMAL"]

        pygame.draw.rect(screen, bg_color, self.rect)
        # Bordes 3D
        pygame.draw.line(screen, VERB_STYLE["BORDER_LIGHT"], (self.rect.left, self.rect.top),
                         (self.rect.right, self.rect.top), 2)
        pygame.draw.line(screen, VERB_STYLE["BORDER_LIGHT"], (self.rect.left, self.rect.top),
                         (self.rect.left, self.rect.bottom), 2)
        pygame.draw.line(screen, VERB_STYLE["BORDER_DARK"], (self.rect.left, self.rect.bottom),
                         (self.rect.right, self.rect.bottom), 2)
        pygame.draw.line(screen, VERB_STYLE["BORDER_DARK"], (self.rect.right, self.rect.top),
                         (self.rect.right, self.rect.bottom), 2)

        cx, cy = self.rect.centerx, self.rect.centery
        size = 6
        points = [(cx, cy - size), (cx - size, cy + size), (cx + size, cy + size)] if self.direction == "up" else [
            (cx, cy + size), (cx - size, cy - size), (cx + size, cy - size)]
        pygame.draw.polygon(screen, arrow_color, points)


class DialogueButton:
    def __init__(self, x, y, width, height, text, option_data):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.option_data = option_data
        self.is_hovered = False

    def draw(self, screen):
        bg_color = DIALOGUE_BTN_STYLE["BTN_BG"]
        pygame.draw.rect(screen, bg_color, self.rect)
        pygame.draw.line(screen, DIALOGUE_BTN_STYLE["BORDER_LIGHT"], (self.rect.left, self.rect.top),
                         (self.rect.right, self.rect.top), 2)
        pygame.draw.line(screen, DIALOGUE_BTN_STYLE["BORDER_LIGHT"], (self.rect.left, self.rect.top),
                         (self.rect.left, self.rect.bottom), 2)
        pygame.draw.line(screen, DIALOGUE_BTN_STYLE["BORDER_DARK"], (self.rect.left, self.rect.bottom),
                         (self.rect.right, self.rect.bottom), 2)
        pygame.draw.line(screen, DIALOGUE_BTN_STYLE["BORDER_DARK"], (self.rect.right, self.rect.top),
                         (self.rect.right, self.rect.bottom), 2)

    def draw_text_hd(self):
        text_color = DIALOGUE_BTN_STYLE["TEXT_HOVER"] if self.is_hovered else DIALOGUE_BTN_STYLE["TEXT_NORMAL"]
        draw_text_sharp(text=self.text, virtual_x=self.rect.centerx, virtual_y=self.rect.centery, base_size=18,
                        color=text_color, align="center")


class DialogueSystem:
    def __init__(self):
        self.active = False
        self.closing = False
        self.current_node_id = None
        self.conversation_tree = {}

        # --- VARIABLES PARA TURNOS ---
        self.pending_response_data = None
        self.is_player_talking = False

        # --- CONFIGURACIÓN DE VISUALIZACIÓN ---
        self.buttons = []
        self.scroll_offset = 0

        # Area principal (calculada dinámicamente con las globales importadas)
        self.area_y = cfg.GAME_AREA_HEIGHT + cfg.CONFIG["TEXTBOX_HEIGHT"] + 5
        self.area_h = cfg.CONFIG["VERB_MENU_HEIGHT"] - 10
        self.area_w = cfg.CONFIG["GAME_WIDTH"]

        # Layout Vertical
        self.cols = 1
        self.rows = 3
        self.max_visible_options = self.cols * self.rows

        # --- DIMENSIONES ---
        self.side_margin = 20
        self.arrow_size = 30
        self.gap_arrow = 10

        arrow_x = self.area_w - self.side_margin - self.arrow_size

        # Crear botones de Scroll
        self.btn_prev = ScrollButton(arrow_x, self.area_y, self.arrow_size, "up")

        btn_next_y = self.area_y + self.area_h - self.arrow_size
        self.btn_next = ScrollButton(arrow_x, btn_next_y, self.arrow_size, "down")

        # Variable para guardar NPC actual
        self.current_npc = None

    def start_dialogue(self, tree_data, start_node="start", npc_ref=None):
        # --- AQUÍ ESTABA EL ERROR: Faltaban argumentos ---
        self.conversation_tree = tree_data

        # Guardamos el NPC si se proporciona
        if npc_ref is not None:
            self.current_npc = npc_ref

        self.current_node_id = start_node
        self.active = True
        self.closing = False
        self.scroll_offset = 0

        # Reseteo de estados de turno
        self.pending_response_data = None
        self.is_player_talking = False

        # Limpiezas externas se deben manejar fuera o mediante callbacks,
        # pero aquí inicializamos los botones.
        self.refresh_buttons()

    def end_dialogue(self):
        self.active = False
        self.closing = False
        self.current_node_id = None
        self.conversation_tree = {}
        self.buttons = []
        self.pending_response_data = None
        self.is_player_talking = False

    def abort_dialogue(self):
        """Fuerza el cierre inmediato."""
        if not self.active: return
        # Nota: La limpieza de textos globales (SCREEN_OVERLAY_TEXT) se debe hacer en el main loop
        # aquí solo cerramos la lógica interna.
        self.end_dialogue()

    def get_valid_options(self):
        node = self.conversation_tree.get(self.current_node_id)
        if not node: return []
        valid_options = []
        # Importamos GAME_STATE localmente para evitar dependencias circulares si es necesario,
        # o asumimos que ya está importado arriba en classes.py
        from scenes.variables import GAME_STATE

        for opt in node.get("options", []):
            if opt.get("condition") and not GAME_STATE.get(opt.get("condition"), False): continue
            if opt.get("once") and opt.get("seen", False): continue
            valid_options.append(opt)
        return valid_options

    def refresh_buttons(self):
        self.buttons = []

        # IMPORTANTE: Necesitamos saber si hay texto en pantalla.
        # Como classes.py no ve SCREEN_OVERLAY_TEXT directamente, confiamos en is_player_talking
        # Ojo: En tu lógica original chequeabas SCREEN_OVERLAY_TEXT aquí.
        # Para mantener modularidad, asumiremos que si is_player_talking es True, no refrescamos.
        if self.is_player_talking:
            return

        options = self.get_valid_options()
        start = self.scroll_offset
        end = start + self.max_visible_options
        visible_subset = options[start:end]

        vertical_margin = 8
        padding = 6

        usable_height = self.area_h - (2 * vertical_margin)
        num_options = self.max_visible_options

        total_gap_height = padding * (num_options - 1)
        btn_height = (usable_height - total_gap_height) // num_options
        btn_height = max(24, btn_height)

        total_available_width = self.area_w - (self.side_margin * 2)
        btn_width = total_available_width - self.arrow_size - self.gap_arrow

        start_x = self.side_margin
        start_y = self.area_y + vertical_margin

        for i, opt in enumerate(visible_subset):
            x = start_x
            y = start_y + i * (btn_height + padding)

            btn = DialogueButton(x, y, btn_width, btn_height, opt["text"], opt)
            self.buttons.append(btn)

    def handle_click(self, mx, my, game_play_event_callback, player_ref):
        # Necesitamos recibir la función game_play_event y el player desde main
        if not self.active: return False

        if self.is_player_talking: return False

        options = self.get_valid_options()

        # Scroll logic
        if self.scroll_offset > 0:
            if self.btn_prev.is_mouse_over(mx, my):
                self.scroll_offset -= 1
                self.refresh_buttons()
                return True

        if self.scroll_offset + self.max_visible_options < len(options):
            if self.btn_next.is_mouse_over(mx, my):
                self.scroll_offset += 1
                self.refresh_buttons()
                return True

        # Button logic
        for btn in self.buttons:
            if btn.rect.collidepoint(mx, my):
                self.execute_choice(btn.option_data, game_play_event_callback, player_ref)
                return True

        return False

    def execute_choice(self, choice, game_play_event, player):
        """FASE 1: Habla el Jugador"""
        choice["seen"] = True
        player_text = choice["text"]

        # Calculamos tiempo aproximado
        time_duration = max(2.0, len(player_text) * 0.08)

        # Ejecutamos el evento usando el callback pasado
        game_play_event(texto=player_text, text_time=time_duration, speaker=player)

        self.pending_response_data = choice
        self.is_player_talking = True
        self.buttons = []

    def continue_dialogue(self, game_play_event):
        """FASE 2: Habla el NPC"""
        if not self.pending_response_data:
            return

        choice = self.pending_response_data
        response_text = choice.get("response")

        if response_text:
            time_duration = max(2.5, len(response_text) * 0.08)
            # AHORA SÍ LE PASAMOS LA DURACIÓN CALCULADA
            game_play_event(texto=response_text, text_time=time_duration, speaker=self.current_npc)

        action = choice.get("action")
        if callable(action): action()

        next_node = choice.get("next")
        if next_node == "EXIT":
            if response_text:
                self.closing = True
                self.current_node_id = None
            else:
                self.end_dialogue()
        elif next_node:
            self.current_node_id = next_node
            self.scroll_offset = 0

        self.pending_response_data = None
        self.is_player_talking = False

    def scroll_up(self):
        if self.scroll_offset > 0:
            self.scroll_offset -= 1
            self.refresh_buttons()

    def scroll_down(self):
        options = self.get_valid_options()
        if self.scroll_offset + self.max_visible_options < len(options):
            self.scroll_offset += 1
            self.refresh_buttons()

    def draw(self, screen):
        if not self.active: return

        # Fondo (Pixel Art / Low Res)
        menu_bg_rect = pygame.Rect(0, self.area_y - 5, self.area_w, self.area_h + 10)
        pygame.draw.rect(screen, VERB_STYLE["BG_MENU"], menu_bg_rect)
        pygame.draw.line(screen, VERB_STYLE["BORDER_LIGHT"], (0, menu_bg_rect.top), (self.area_w, menu_bg_rect.top), 2)

        mx, my = get_virtual_mouse_pos()

        for btn in self.buttons:
            btn.is_hovered = btn.rect.collidepoint(mx, my)
            btn.draw(screen)

        options = self.get_valid_options()
        if self.scroll_offset > 0: self.btn_prev.draw(screen, mx, my)
        if self.scroll_offset + self.max_visible_options < len(options): self.btn_next.draw(screen, mx, my)

    def draw_text_hd(self):
        if not self.active: return

        # Renderizado de texto nítido en ventana real
        for btn in self.buttons:
            btn.draw_text_hd()


class TitleMenu:
    def __init__(self):
        self.start_y = cfg.CONFIG["GAME_HEIGHT"] // 2.2
        self.options = []
        self.selected_index = 0
        self.btn_width = 220
        self.btn_height = 35
        self.btn_spacing = 10
        self.bg = None
        bg_path = os.path.join(cfg.BG_DIR, "pycapge_tittle.png")
        if os.path.exists(bg_path):
            self.bg = pygame.transform.scale(pygame.image.load(bg_path).convert(),
                                             (cfg.CONFIG["GAME_WIDTH"], cfg.CONFIG["GAME_HEIGHT"]))
        self.refresh_texts()

    def refresh_texts(self):
        lang_label = cfg.TITLE_TEXTS.get("LANGUAGE", "LANGUAGE")
        self.options = [cfg.TITLE_TEXTS["NEW_GAME"], cfg.TITLE_TEXTS["LOAD_GAME"], lang_label,
                        cfg.TITLE_TEXTS["CREDITS"], cfg.TITLE_TEXTS["EXIT"]]

    def handle_input(self, event, callbacks):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.options)
            elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                self.execute_selection(callbacks)
        elif event.type == pygame.MOUSEMOTION:
            mx, my = get_virtual_mouse_pos()
            center_x = cfg.CONFIG["GAME_WIDTH"] // 2
            for i in range(len(self.options)):
                rect = pygame.Rect(center_x - self.btn_width // 2,
                                   self.start_y + i * (self.btn_height + self.btn_spacing), self.btn_width,
                                   self.btn_height)
                if rect.collidepoint(mx, my): self.selected_index = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = get_virtual_mouse_pos()
            center_x = cfg.CONFIG["GAME_WIDTH"] // 2
            for i in range(len(self.options)):
                rect = pygame.Rect(center_x - self.btn_width // 2,
                                   self.start_y + i * (self.btn_height + self.btn_spacing), self.btn_width,
                                   self.btn_height)
                if rect.collidepoint(mx, my):
                    self.selected_index = i
                    self.execute_selection(callbacks)

    def execute_selection(self, callbacks):
        sel = self.options[self.selected_index]
        if sel == cfg.TITLE_TEXTS["NEW_GAME"]:
            callbacks["new_game"]()
        elif sel == cfg.TITLE_TEXTS["LOAD_GAME"]:
            callbacks["load_game"]()
        elif sel == cfg.TITLE_TEXTS.get("LANGUAGE", "LANGUAGE"):
            callbacks["open_lang"]()
        elif sel == cfg.TITLE_TEXTS["CREDITS"]:
            callbacks["open_credits"]()
        elif sel == cfg.TITLE_TEXTS["EXIT"]:
            callbacks["exit_game"]()

    def draw(self, screen):
        if self.bg:
            screen.blit(self.bg, (0, 0))
        else:
            screen.fill((20, 20, 40))
        center_x = cfg.CONFIG["GAME_WIDTH"] // 2
        for i in range(len(self.options)):
            rect = pygame.Rect(center_x - self.btn_width // 2, self.start_y + i * (self.btn_height + self.btn_spacing),
                               self.btn_width, self.btn_height)
            bg_color = (80, 80, 80) if i == self.selected_index else VERB_STYLE["BTN_BG"]
            pygame.draw.rect(screen, bg_color, rect)
            pygame.draw.line(screen, VERB_STYLE["BORDER_LIGHT"], (rect.left, rect.top), (rect.right, rect.top), 3)
            pygame.draw.line(screen, VERB_STYLE["BORDER_LIGHT"], (rect.left, rect.top), (rect.left, rect.bottom), 3)
            pygame.draw.line(screen, VERB_STYLE["BORDER_DARK"], (rect.left, rect.bottom), (rect.right, rect.bottom), 3)
            pygame.draw.line(screen, VERB_STYLE["BORDER_DARK"], (rect.right, rect.top), (rect.right, rect.bottom), 3)

    def draw_text_hd(self):
        if not self.bg:
            draw_text_sharp("Python Classic Adventure Engine", cfg.CONFIG["GAME_WIDTH"] // 2, 150, 24, (255, 200, 50),
                            align="center", shadow=True)
        center_x = cfg.CONFIG["GAME_WIDTH"] // 2
        for i, opt_text in enumerate(self.options):
            center_y = self.start_y + i * (self.btn_height + self.btn_spacing) + (self.btn_height // 2)
            color = (255, 255, 255) if i == self.selected_index else VERB_STYLE["TEXT_NORMAL"]
            draw_text_sharp(opt_text, center_x, center_y, 20, color, align="center", shadow=(i == self.selected_index))


class SaveLoadUI:
    def __init__(self):
        self.active = False
        self.mode = "SAVE"
        self.previous_state = "TITLE"
        self.width = 500
        self.height = 450
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = (cfg.CONFIG["GAME_WIDTH"] // 2, cfg.CONFIG["GAME_HEIGHT"] // 2)
        self.slots_data = []
        self.scroll_offset = 0
        self.visible_slots = 5
        self.slot_height = 50
        self.slot_spacing = 10
        self.total_slots = 25
        list_height = (self.visible_slots * (self.slot_height + self.slot_spacing))
        self.list_area_rect = pygame.Rect(self.rect.x + 30, self.rect.y + 70, self.rect.width - 80, list_height)
        self.close_btn_rect = pygame.Rect(self.rect.centerx - 60, self.rect.bottom - 55, 120, 45)
        self.dragging_scrollbar = False
        self.scrollbar_rect = pygame.Rect(0, 0, 0, 0)
        self.thumb_rect = pygame.Rect(0, 0, 0, 0)
        self.slot_bg_color = (50, 50, 50)
        self.slot_hover_color = (80, 80, 80)
        self.save_callback = None
        self.load_callback = None
        self.close_callback = None

    def open_menu(self, mode, current_state_callback):
        self.previous_state = current_state_callback()
        self.mode = mode
        self.active = True
        self.scroll_offset = 0
        self.dragging_scrollbar = False
        self.scan_saves()  # <--- IMPORTANTE: Escanea y actualiza textos al abrir

    def close_menu(self):
        self.active = False
        self.dragging_scrollbar = False
        if self.close_callback: self.close_callback()

    def scan_saves(self):
        self.slots_data = []
        # Leemos los textos AQUÍ para que estén actualizados al idioma actual
        empty_txt = cfg.GAME_MSGS.get("SLOT_EMPTY", "Empty Slot")
        corrupt_txt = cfg.GAME_MSGS.get("SLOT_CORRUPT", "Corrupt File")

        for i in range(self.total_slots):
            filename = os.path.join(cfg.SAVE_DIR, f"savegame_{i}.json")
            display_text = f"Slot {i + 1}: {empty_txt}"
            if os.path.exists(filename):
                try:
                    with open(filename, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        date_str = data.get("timestamp", "???")
                        scene_raw = data.get("scene", "???")
                        scene_display = cfg.SCENE_NAMES.get(scene_raw, scene_raw)
                        display_text = f"{i + 1}. {scene_display} [{date_str}]"
                except:
                    display_text = f"{i + 1}. {corrupt_txt}"
            self.slots_data.append({"file": filename, "text": display_text})

    def handle_wheel(self, y_value):
        if not self.active: return
        self.scroll_offset = max(0, min(self.scroll_offset - y_value, self.total_slots - self.visible_slots))

    def handle_click_down(self, mx, my, reload_callback=None):
        if not self.active: return
        if self.close_btn_rect.collidepoint(mx, my):
            self.close_menu()
            return
        if self.scrollbar_rect.collidepoint(mx, my):
            self.dragging_scrollbar = True
            self.update_drag(my)
            return
        if self.list_area_rect.collidepoint(mx, my):
            rel_y = my - self.list_area_rect.y
            idx = rel_y // (self.slot_height + self.slot_spacing)
            real_index = self.scroll_offset + int(idx)
            if 0 <= real_index < len(self.slots_data):
                data = self.slots_data[real_index]
                if self.mode == "SAVE" and self.save_callback:
                    self.save_callback(data["file"])
                    self.close_menu()
                elif self.mode == "LOAD" and self.load_callback:
                    if os.path.exists(data["file"]): self.load_callback(data["file"]); self.close_menu()

    def handle_mouse_up(self):
        self.dragging_scrollbar = False

    def set_callbacks(self, save_cb, load_cb, close_cb):
        self.save_callback = save_cb
        self.load_callback = load_cb
        self.close_callback = close_cb

    def handle_mouse_motion(self, my):
        if self.dragging_scrollbar: self.update_drag(my)

    def update_drag(self, my):
        track_h = self.scrollbar_rect.height - self.thumb_rect.height
        if track_h > 0:
            pct = (my - self.scrollbar_rect.y - self.thumb_rect.height / 2) / track_h
            self.scroll_offset = int(max(0, min(1, pct)) * (self.total_slots - self.visible_slots))

    def draw(self, screen):
        s = pygame.Surface((self.width, self.height))
        s.set_alpha(220)
        s.fill((20, 20, 20))
        screen.blit(s, (self.rect.x, self.rect.y))
        pygame.draw.rect(screen, (180, 160, 120), self.rect, 2)

        current_y = self.list_area_rect.y
        mx, my = get_virtual_mouse_pos()

        start_index = self.scroll_offset
        end_index = min(start_index + self.visible_slots, self.total_slots)

        for i in range(start_index, end_index):
            slot_rect = pygame.Rect(self.list_area_rect.x, current_y, self.list_area_rect.width, self.slot_height)
            is_hover = slot_rect.collidepoint(mx, my) and not self.dragging_scrollbar
            color = self.slot_hover_color if is_hover else self.slot_bg_color
            pygame.draw.rect(screen, color, slot_rect)
            pygame.draw.rect(screen, (100, 100, 100), slot_rect, 1)
            current_y += (self.slot_height + self.slot_spacing)

        sb_x = self.list_area_rect.right + 10
        self.scrollbar_rect = pygame.Rect(sb_x, self.list_area_rect.y, 14, self.list_area_rect.height)
        pygame.draw.rect(screen, (30, 30, 30), self.scrollbar_rect)
        thumb_h = max(30, self.scrollbar_rect.height * (self.visible_slots / self.total_slots))
        thumb_y = self.scrollbar_rect.y + (self.scrollbar_rect.height - thumb_h) * (
                    self.scroll_offset / max(1, self.total_slots - self.visible_slots))
        self.thumb_rect = pygame.Rect(sb_x, thumb_y, 14, thumb_h)
        pygame.draw.rect(screen, (200, 200, 200) if self.dragging_scrollbar else (150, 150, 150), self.thumb_rect)
        c_col = (200, 50, 50) if self.close_btn_rect.collidepoint(mx, my) else (150, 50, 50)
        pygame.draw.rect(screen, c_col, self.close_btn_rect)
        pygame.draw.rect(screen, (255, 255, 255), self.close_btn_rect, 1)

    def draw_text_hd(self):
        if not self.active: return
        title_key = "SAVE_CMD" if self.mode == "SAVE" else "LOAD_CMD"
        title = cfg.MENU_TEXTS.get(title_key, self.mode)  # Uso de .get para evitar crash

        draw_text_sharp(title, self.rect.centerx, self.rect.y + 25, 28, (255, 255, 255), align="center", shadow=True)
        current_y = self.list_area_rect.y
        for i in range(self.scroll_offset, min(self.scroll_offset + self.visible_slots, self.total_slots)):
            txt = self.slots_data[i]["text"] if i < len(self.slots_data) else "Empty"
            draw_text_sharp(txt, self.list_area_rect.x + 15, current_y + self.slot_height // 2, 16, (255, 255, 255),
                            align="midleft")
            current_y += (self.slot_height + self.slot_spacing)

        close_txt = cfg.MENU_TEXTS.get("CLOSE_CMD", "Close")
        draw_text_sharp(close_txt, self.close_btn_rect.centerx, self.close_btn_rect.centery, 18, (255, 255, 255),
                        align="center")


class LanguageUI:
    def __init__(self):
        self.active = False

        self.width = 400
        self.height = 380
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        # Centramos el rectángulo en pantalla usando la configuración global
        self.rect.center = (cfg.CONFIG["GAME_WIDTH"] // 2, cfg.CONFIG["GAME_HEIGHT"] // 2)

        # Colores
        self.bg_color = (0, 0, 0, 240)
        self.border_color = (180, 160, 120)
        self.slot_bg_color = (68, 68, 68)
        self.slot_hover_color = (100, 100, 100)

        # Scrollbar
        self.scrollbar_bg = (30, 30, 30)
        self.scrollbar_color = (150, 150, 150)
        self.scrollbar_active_color = (200, 200, 200)

        # Fuentes
        if os.path.exists(cfg.UI_FONT_PATH):
            self.font = pygame.font.Font(cfg.UI_FONT_PATH, 18)
            self.title_font = pygame.font.Font(cfg.UI_FONT_PATH, 24)
        else:
            self.font = pygame.font.SysFont("arial", 18)
            self.title_font = pygame.font.SysFont("arial", 24, bold=True)

        # Configuración Lista
        self.languages = []
        self.scroll_offset = 0
        self.visible_slots = 5
        self.slot_height = 40
        self.slot_spacing = 10

        # Área donde empiezan a dibujarse los botones
        # Ajustamos un poco más abajo para que no pegue con el título
        list_start_y = self.rect.y + 80
        list_h = self.visible_slots * (self.slot_height + self.slot_spacing)

        # Definimos el área general de la lista
        self.list_area_rect = pygame.Rect(self.rect.x + 30, list_start_y, self.rect.width - 70, list_h)

        # Botón Cerrar
        btn_x = self.rect.centerx - 50
        self.close_btn_rect = pygame.Rect(btn_x, self.rect.bottom - 46, 100, 40)

        # Variables Drag (Arrastrar barra)
        self.dragging_scrollbar = False
        self.scrollbar_rect = pygame.Rect(0, 0, 0, 0)
        self.thumb_rect = pygame.Rect(0, 0, 0, 0)

        self.scan_languages()

    def scan_languages(self):
        self.languages = []
        folder = cfg.LANG_DIR
        if not os.path.exists(folder): os.makedirs(folder)
        try:
            for filename in os.listdir(folder):
                if filename.endswith(".yaml") or filename.endswith(".yml"):
                    display_name = filename.split(".")[0].upper()
                    try:
                        full_path = os.path.join(folder, filename)
                        with open(full_path, "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f)
                            if data and "language_name" in data:
                                display_name = data["language_name"]
                    except:
                        pass
                    self.languages.append({"label": display_name, "file": filename})

            # Ordenamos alfabéticamente para que sea predecible
            self.languages.sort(key=lambda x: x["label"])

        except Exception as e:
            print(f"Error scanning languages: {e}")
            self.languages = [{"label": "Español", "file": "es.yaml"}]

    def open_menu(self):
        self.scan_languages()
        self.scroll_offset = 0
        self.dragging_scrollbar = False
        self.active = True

    def close_menu(self):
        self.active = False
        self.dragging_scrollbar = False
        # Si tenemos un callback definido en main, lo ejecutamos para cambiar el estado
        if hasattr(self, 'close_callback') and self.close_callback:
            self.close_callback()

    def handle_wheel(self, y_value):
        if not self.active: return
        if y_value > 0:
            self.scroll_offset -= 1
        elif y_value < 0:
            self.scroll_offset += 1
        self.clamp_scroll()

    def clamp_scroll(self):
        max_scroll = max(0, len(self.languages) - self.visible_slots)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

    def handle_click_down(self, mx, my, reload_callback):
        if not self.active: return

        # 1. Botón Cerrar
        if self.close_btn_rect.collidepoint(mx, my):
            self.close_menu()
            return

        # 2. Barra de Scroll
        if self.scrollbar_rect.collidepoint(mx, my):
            self.dragging_scrollbar = True
            self.update_drag(my)
            return

        # 3. Lista de Idiomas (LÓGICA ORIGINAL RESTAURADA)
        if self.list_area_rect.collidepoint(mx, my):
            # Calculamos la Y relativa al inicio de la lista
            rel_y = my - self.list_area_rect.y

            # Calculamos el índice visual dividiendo por la altura total del bloque (botón + espacio)
            # Tal como estaba en vedad_absoluta.py
            idx = rel_y // (self.slot_height + self.slot_spacing)

            # Sumamos el desplazamiento del scroll
            real_idx = self.scroll_offset + int(idx)

            # Solo comprobamos que el índice exista en la lista
            if 0 <= real_idx < len(self.languages):
                lang = self.languages[real_idx]
                file_target = lang["file"]

                # Si el idioma es diferente, ejecutamos el callback de recarga
                if file_target != cfg.GLOBAL_STATE.get("current_lang_file"):
                    try:
                        reload_callback(file_target)
                    except Exception as e:
                        print(f"Error loading language: {e}")

                self.close_menu()

    def handle_mouse_up(self):
        self.dragging_scrollbar = False

    def handle_mouse_motion(self, my):
        if self.dragging_scrollbar:
            self.update_drag(my)

    def update_drag(self, my):
        track_y = self.scrollbar_rect.y
        track_h = self.scrollbar_rect.height
        thumb_h = self.thumb_rect.height
        if track_h <= thumb_h: return

        rel_y = my - track_y - (thumb_h / 2)
        percent = rel_y / (track_h - thumb_h)
        percent = max(0.0, min(1.0, percent))

        max_scroll = max(0, len(self.languages) - self.visible_slots)
        self.scroll_offset = int(percent * max_scroll)

    def draw(self, screen):
        if not self.active: return

        # Fondo oscuro
        overlay = pygame.Surface((cfg.CONFIG["GAME_WIDTH"], cfg.CONFIG["GAME_HEIGHT"]), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        # Ventana Principal
        pygame.draw.rect(screen, self.bg_color, self.rect)
        pygame.draw.rect(screen, self.border_color, self.rect, 2)

        # Título
        title_txt = cfg.MENU_TEXTS.get("LANG_TITLE", "LANGUAGE")
        t_surf = self.title_font.render(title_txt, True, (255, 255, 255))
        screen.blit(t_surf, (self.rect.centerx - t_surf.get_width() // 2, self.rect.y + 25))

        mx, my = get_virtual_mouse_pos()

        # --- DIBUJAR LISTA ---
        start_index = self.scroll_offset
        end_index = min(start_index + self.visible_slots, len(self.languages))

        # Y inicial EXACTA (debe coincidir con handle_click_down)
        current_y = self.list_area_rect.y

        for i in range(start_index, end_index):
            lang = self.languages[i]

            # Rectángulo del botón
            slot_rect = pygame.Rect(
                self.list_area_rect.x,
                current_y,
                self.list_area_rect.width,
                self.slot_height
            )

            # Lógica visual
            is_current = (lang["file"] == cfg.GLOBAL_STATE.get("current_lang_file"))
            is_hover = slot_rect.collidepoint(mx, my) and not self.dragging_scrollbar

            # Colores
            if is_current:
                color = (50, 160, 50)  # Verde seleccionado
            elif is_hover:
                color = self.slot_hover_color
            else:
                color = self.slot_bg_color

            pygame.draw.rect(screen, color, slot_rect)

            # Borde del botón
            border_col = (255, 255, 255) if (is_current or is_hover) else (100, 100, 100)
            pygame.draw.rect(screen, border_col, slot_rect, 1)

            # Texto
            label = lang["label"]
            if is_current: label = "> " + label + " <"

            try:
                txt_surf = self.font.render(label, True, (255, 255, 255))
            except:
                txt_surf = self.font.render("???", True, (255, 255, 255))

            screen.blit(txt_surf, (slot_rect.centerx - txt_surf.get_width() // 2,
                                   slot_rect.centery - txt_surf.get_height() // 2))

            # Avanzar Y para el siguiente botón
            current_y += (self.slot_height + self.slot_spacing)

        # --- DIBUJAR SCROLLBAR ---
        scrollbar_x = self.list_area_rect.right + 10
        self.scrollbar_rect = pygame.Rect(scrollbar_x, self.list_area_rect.y, 12, self.list_area_rect.height)

        pygame.draw.rect(screen, self.scrollbar_bg, self.scrollbar_rect)

        max_scroll = max(1, len(self.languages) - self.visible_slots)
        if len(self.languages) > self.visible_slots:
            thumb_height = max(30, self.scrollbar_rect.height * (self.visible_slots / len(self.languages)))
            scroll_ratio = self.scroll_offset / max_scroll
            thumb_y = self.scrollbar_rect.y + (self.scrollbar_rect.height - thumb_height) * scroll_ratio

            self.thumb_rect = pygame.Rect(scrollbar_x, thumb_y, 12, thumb_height)
            col = self.scrollbar_active_color if self.dragging_scrollbar else self.scrollbar_color
            pygame.draw.rect(screen, col, self.thumb_rect)

        # --- DIBUJAR BOTÓN CERRAR ---
        c_color = (200, 50, 50) if self.close_btn_rect.collidepoint(mx, my) else (150, 50, 50)
        pygame.draw.rect(screen, c_color, self.close_btn_rect)
        pygame.draw.rect(screen, (255, 255, 255), self.close_btn_rect, 1)
        close_surf = self.font.render(cfg.MENU_TEXTS.get("CLOSE_CMD", "CLOSE"), True, (255, 255, 255))
        screen.blit(close_surf, (self.close_btn_rect.centerx - close_surf.get_width() // 2,
                                 self.close_btn_rect.centery - close_surf.get_height() // 2))


class SystemMenu:
    def __init__(self):
        # Configuración visual
        self.bar_height = 24
        self.btn_width = 160  # Ancho ajustado para que quepan bien los textos
        self.visible = True
        self.callback = None

        # Variable de estado para recordar qué submenú estamos mirando
        self.last_active_item_index = -1

        # DEFINICIÓN DINÁMICA DE LOS MENÚS (Inicialmente vacíos hasta refresh_texts)
        self.menus = []
        self.refresh_texts()

    def set_callback(self, cb):
        self.callback = cb

    def refresh_texts(self):
        """Reconstruye los menús con los textos actuales de CONFIG"""
        # Guardamos qué menú estaba abierto para no cerrárselo al jugador en la cara si cambia el idioma
        old_open_indices = [i for i, m in enumerate(self.menus) if m.get("is_open", False)]

        self.menus = [
            {
                "title": cfg.MENU_TEXTS.get("FILE_TITLE", "FILE"),
                "items": [cfg.MENU_TEXTS.get("SAVE_CMD", "SAVE"), cfg.MENU_TEXTS.get("LOAD_CMD", "LOAD")],
                "rect": None, "is_open": False
            },
            {
                "title": cfg.MENU_TEXTS.get("HELP_TITLE", "HELP"),
                "items": [
                    cfg.MENU_TEXTS.get("DEBUG_OPT", "DEBUG"),
                    cfg.MENU_TEXTS.get("GAME_HELP_OPT", "HINTS"),
                    cfg.MENU_TEXTS.get("NO_OPT", "OFF")
                ],
                "rect": None, "is_open": False
            },
            {
                "title": cfg.MENU_TEXTS.get("TEXT_TITLE", "TEXT"),
                "items": [
                    {"label": cfg.MENU_TEXTS.get("VEL_LABEL", "SPEED"),
                     "options": cfg.MENU_TEXTS.get("VEL_OPTS", ["SLOW", "MED", "FAST"])},
                    {"label": cfg.MENU_TEXTS.get("SIZE_LABEL", "SIZE"),
                     "options": cfg.MENU_TEXTS.get("SIZE_OPTS", ["SMALL", "MED", "LARGE"])}
                ],
                "rect": None, "is_open": False
            },
            {
                "title": cfg.MENU_TEXTS.get("SOUND_TITLE", "SOUND"),
                "items": [cfg.MENU_TEXTS.get("YES_OPT", "ON"), cfg.MENU_TEXTS.get("NO_OPT", "OFF")],
                "rect": None, "is_open": False
            },
            {
                "title": cfg.MENU_TEXTS.get("CURSOR_TITLE", "CURSOR"),
                "items": [cfg.MENU_TEXTS.get("CURSOR_CLASSIC", "CLASSIC"),
                          cfg.MENU_TEXTS.get("CURSOR_MODERN", "MODERN")],
                "rect": None, "is_open": False
            }
        ]

        # Recalcular posiciones X
        current_x = 0
        # Ajuste: Si hay muchos menús, dividimos el ancho de pantalla
        # self.btn_width = cfg.CONFIG["GAME_WIDTH"] // len(self.menus)

        for i, menu in enumerate(self.menus):
            menu["rect"] = pygame.Rect(current_x, 0, self.btn_width, self.bar_height)
            current_x += self.btn_width
            # Restaurar estado abierto
            if i in old_open_indices: menu["is_open"] = True

    def toggle(self):
        self.visible = not self.visible
        if not self.visible:
            self.close_all()

    def close_all(self):
        for menu in self.menus:
            menu["is_open"] = False
        self.last_active_item_index = -1

    def get_active_item_index(self, menu, mx, my):
        """Determina qué ítem del menú desplegable está activo (hover)."""
        if not menu["is_open"]: return -1

        # 1. Chequear si estamos sobre algún ítem PRINCIPAL del desplegable
        dy_temp = self.bar_height
        for i, item in enumerate(menu["items"]):
            p_rect = pygame.Rect(menu["rect"].x, dy_temp, self.btn_width, self.bar_height)
            if p_rect.collidepoint(mx, my):
                self.last_active_item_index = i
                return i
            dy_temp += self.bar_height

        # 2. Si no estamos sobre el principal, ¿estamos sobre el SUBMENÚ del ítem activo anterior?
        # Esto permite mover el ratón en diagonal hacia el submenú sin que se cierre.
        if self.last_active_item_index != -1 and self.last_active_item_index < len(menu["items"]):
            idx = self.last_active_item_index
            item = menu["items"][idx]

            if isinstance(item, dict):
                # Calculamos dónde está dibujado este submenú
                item_y = self.bar_height + (idx * self.bar_height)
                # Rectángulo teórico del padre
                p_rect_ref = pygame.Rect(menu["rect"].x, item_y, self.btn_width, self.bar_height)

                # Rectángulo del submenú (a la derecha)
                sub_h = len(item["options"]) * self.bar_height
                sub_area = pygame.Rect(p_rect_ref.right, p_rect_ref.top, self.btn_width, sub_h)

                if sub_area.collidepoint(mx, my):
                    return idx  # Mantenemos el índice activo

        return -1

    def handle_click(self, mx, my, external_callback=None):
        if not self.visible: return False
        active_cb = external_callback if external_callback else self.callback

        # 1. Clic en la barra superior (Títulos)
        if my < self.bar_height:
            clicked_on_menu = False
            for menu in self.menus:
                if menu["rect"].collidepoint(mx, my):
                    was_open = menu["is_open"]
                    self.close_all()
                    menu["is_open"] = not was_open
                    clicked_on_menu = True
                    return True

                    # Si clicamos en la barra negra pero no en un botón, cerramos todo
            if not clicked_on_menu:
                self.close_all()
                return False  # Dejamos pasar el clic al juego si es zona muerta

        # 2. Clic en los desplegables
        for menu in self.menus:
            if menu["is_open"]:
                # Usamos la lógica robusta de índices
                active_index = self.get_active_item_index(menu, mx, my)

                if active_index != -1:
                    item = menu["items"][active_index]
                    # Posición Y de este ítem
                    item_y = self.bar_height + (active_index * self.bar_height)
                    item_rect = pygame.Rect(menu["rect"].x, item_y, self.btn_width, self.bar_height)

                    # CASO A: Es un submenú (Diccionario)
                    if isinstance(item, dict):
                        sub_y = item_rect.top
                        sub_x = item_rect.right
                        for sub_opt in item["options"]:
                            sub_btn_rect = pygame.Rect(sub_x, sub_y, self.btn_width, self.bar_height)
                            if sub_btn_rect.collidepoint(mx, my):
                                # Ejecutar acción
                                if active_cb: active_cb(menu["title"], sub_opt, context_label=item["label"])
                                self.close_all()
                                return True
                            sub_y += self.bar_height
                        return True  # Consumimos el clic si fue en el área del submenú pero no en una opción

                    # CASO B: Es un ítem normal (String)
                    else:
                        if item_rect.collidepoint(mx, my):
                            if active_cb: active_cb(menu["title"], item, context_label=None)
                            self.close_all()
                            return True

                # Si clicamos fuera del menú desplegado, cerrar
                # (Opcional: puedes quitar esto si quieres que se cierre solo al clicar en el juego)
                self.close_all()
                return True

        return False

    def draw(self, screen):
        """Dibuja las cajas (Pixel Art / Low Res)"""
        if not self.visible: return
        mx, my = get_virtual_mouse_pos()

        # Fondo barra negra
        pygame.draw.rect(screen, (0, 0, 0), (0, 0, cfg.CONFIG["GAME_WIDTH"], self.bar_height))

        for menu in self.menus:
            rect = menu["rect"]
            is_hover_title = rect.collidepoint(mx, my) or menu["is_open"]
            bg_color = (60, 60, 60) if is_hover_title else (0, 0, 0)

            # Caja Título
            pygame.draw.rect(screen, bg_color, rect)
            pygame.draw.line(screen, (100, 100, 100), (rect.right - 1, rect.top), (rect.right - 1, rect.bottom))

            if menu["is_open"]:
                # Calcular qué ítem está activo
                active_index = self.get_active_item_index(menu, mx, my)
                dy = self.bar_height

                for i, item in enumerate(menu["items"]):
                    item_rect = pygame.Rect(rect.x, dy, self.btn_width, self.bar_height)
                    is_active = (i == active_index)

                    # Color fondo ítem
                    item_bg = (100, 100, 80) if is_active else (85, 85, 68)  # VERB_STYLE["BG_MENU"]

                    pygame.draw.rect(screen, item_bg, item_rect)
                    pygame.draw.rect(screen, (102, 102, 102), item_rect, 1)  # Borde light

                    # Si es submenú y está activo, dibujar las opciones a la derecha
                    if isinstance(item, dict) and is_active:
                        sub_dy = dy
                        sub_x = item_rect.right
                        for sub_opt in item["options"]:
                            sub_rect = pygame.Rect(sub_x, sub_dy, self.btn_width, self.bar_height)
                            sub_hover = sub_rect.collidepoint(mx, my)

                            s_bg = (120, 120, 100) if sub_hover else (85, 85, 68)

                            pygame.draw.rect(screen, s_bg, sub_rect)
                            pygame.draw.rect(screen, (102, 102, 102), sub_rect, 1)

                            sub_dy += self.bar_height

                    dy += self.bar_height

    def draw_text_hd(self):
        """Dibuja el texto nítido encima de las cajas"""
        if not self.visible: return
        mx, my = get_virtual_mouse_pos()
        FONT_SIZE = 14

        for menu in self.menus:
            rect = menu["rect"]
            is_hover_title = rect.collidepoint(mx, my) or menu["is_open"]

            # Color Título
            col = VERB_STYLE["TEXT_SELECTED"] if is_hover_title else VERB_STYLE["TEXT_NORMAL"]
            draw_text_sharp(menu["title"], rect.centerx, rect.centery, FONT_SIZE, col, align="center")

            if menu["is_open"]:
                active_index = self.get_active_item_index(menu, mx, my)
                dy = self.bar_height

                for i, item in enumerate(menu["items"]):
                    item_rect = pygame.Rect(rect.x, dy, self.btn_width, self.bar_height)
                    is_active = (i == active_index)

                    # Etiqueta
                    label = item["label"] if isinstance(item, dict) else item

                    # Color Ítem
                    tcol = VERB_STYLE["TEXT_SELECTED"] if is_active else VERB_STYLE["TEXT_NORMAL"]

                    # Texto alineado a la izquierda con padding
                    draw_text_sharp(label, item_rect.left + 10, item_rect.centery, FONT_SIZE, tcol, align="midleft")

                    # Si es submenú y está activo, dibujar las opciones
                    if isinstance(item, dict):
                        # Flechita indicadora >
                        draw_text_sharp(">", item_rect.right - 10, item_rect.centery, FONT_SIZE, tcol, align="midright")

                        if is_active:
                            sub_dy = dy
                            sub_x = item_rect.right
                            for sub_opt in item["options"]:
                                sub_rect = pygame.Rect(sub_x, sub_dy, self.btn_width, self.bar_height)
                                sub_hover = sub_rect.collidepoint(mx, my)

                                scol = VERB_STYLE["TEXT_SELECTED"] if sub_hover else VERB_STYLE["TEXT_NORMAL"]

                                draw_text_sharp(sub_opt, sub_rect.left + 10, sub_rect.centery, FONT_SIZE, scol,
                                                align="midleft")

                                sub_dy += self.bar_height

                    dy += self.bar_height


class TextBox:
    def __init__(self):
        self.rect = pygame.Rect(0, cfg.GAME_AREA_HEIGHT, cfg.CONFIG["GAME_WIDTH"], cfg.CONFIG["TEXTBOX_HEIGHT"])
        self.visible = True
        self.current_text = ""

    def set_text(self, text):
        self.current_text = text

    def draw(self, screen):
        if self.visible: pygame.draw.rect(screen, (0, 0, 0), self.rect)

    def draw_text_only(self):
        if self.visible and self.current_text:
            draw_text_sharp(self.current_text, self.rect.centerx, self.rect.centery, 18, (255, 255, 255),
                            align="center")


# ==========================================
#  CORRECCIÓN CLASES VERBOS (engine/classes.py)
# ==========================================

class VerbButton:
    def __init__(self, verb_id, x, y, width, height):
        self.verb_id = verb_id
        self.rect = pygame.Rect(int(x), int(y), int(width), int(height))
        self.selected = False
        self.width = width
        self.height = height
        self.lines = []
        self.final_size = 18
        self.line_spacing = 0
        self.refresh_label()

    def refresh_label(self):
        """Calcula el tamaño de fuente ideal y divide en líneas si es necesario."""
        # Necesitamos VERBS_LOCALIZED. Si no está importado, usamos el ID como fallback
        from config import VERBS_LOCALIZED
        raw_text = VERBS_LOCALIZED.get(self.verb_id, self.verb_id)
        max_w = self.width - 6

        font, size = self.get_dynamic_font(raw_text, max_w, self.height, 18, 12)
        w, _ = font.size(raw_text)

        if w <= max_w:
            self.lines = [raw_text]
            self.final_size = size
        else:
            words = raw_text.split(' ')
            if len(words) >= 2:
                mid = math.ceil(len(words) / 2)
                line1 = " ".join(words[:mid])
                line2 = " ".join(words[mid:])
                test_size = 13
                test_font = get_sharp_font(test_size)  # Usamos el helper global

                # Nota: get_sharp_font devuelve fuente escalada, para cálculo lógico
                # usamos una dummy si queremos precisión exacta o ajustamos lógica.
                # Para simplificar y mantener paridad con vedad_absoluta:
                try:
                    dummy_font = pygame.font.Font(cfg.UI_FONT_PATH, test_size)
                except:
                    dummy_font = pygame.font.SysFont("arial", test_size)

                if dummy_font.size(line1)[0] <= max_w and dummy_font.size(line2)[0] <= max_w:
                    self.lines = [line1, line2]
                    self.final_size = test_size
                else:
                    self.make_truncated(raw_text, max_w)
            else:
                self.make_truncated(raw_text, max_w)

    def make_truncated(self, text, max_w):
        try:
            font = pygame.font.Font(cfg.UI_FONT_PATH, 11)
        except:
            font = pygame.font.SysFont("arial", 11)
        temp_text = text
        while len(temp_text) > 0 and font.size(temp_text + "...")[0] > max_w:
            temp_text = temp_text[:-1]
        self.lines = [temp_text + "..."]
        self.final_size = 11

    def get_dynamic_font(self, text, max_width, max_height, max_size, min_size):
        size = max_size
        while size >= min_size:
            try:
                font = pygame.font.Font(cfg.UI_FONT_PATH, size)
            except:
                font = pygame.font.SysFont("arial", size)
            text_w, text_h = font.size(text)
            if text_w <= max_width: return font, size
            size -= 1
        return pygame.font.Font(cfg.UI_FONT_PATH, min_size), min_size

    def is_mouse_over(self, mx, my):
        return self.rect.collidepoint(mx, my)

    def draw(self, screen, mx, my, active_verb_context=None):
        # Dibujado de caja (Pixel Art)
        pygame.draw.rect(screen, VERB_STYLE["BTN_BG"], self.rect)
        light = VERB_STYLE["BORDER_LIGHT"]
        dark = VERB_STYLE["BORDER_DARK"]
        pygame.draw.line(screen, light, (self.rect.left, self.rect.top), (self.rect.right, self.rect.top), 2)
        pygame.draw.line(screen, light, (self.rect.left, self.rect.top), (self.rect.left, self.rect.bottom), 2)
        pygame.draw.line(screen, dark, (self.rect.left, self.rect.bottom), (self.rect.right, self.rect.bottom), 2)
        pygame.draw.line(screen, dark, (self.rect.right, self.rect.top), (self.rect.right, self.rect.bottom), 2)

    def draw_text_hd(self, active_verb_context=None):
        """Renderizado HD con centrado matemático real."""
        mx, my = get_virtual_mouse_pos()

        # --- BORRA EL BLOQUE IF/ELSE ANTIGUO Y PON ESTE ---

        # 1. Si el botón está seleccionado fijamente (clic) -> BLANCO
        if self.selected:
            color = VERB_STYLE["TEXT_SELECTED"]

            # 2. Si el ratón está FÍSICAMENTE encima del botón -> BLANCO (Tu petición)
        elif self.rect.collidepoint(mx, my):
            color = VERB_STYLE["TEXT_SELECTED"]

            # 3. Si el botón se ilumina porque el Hotspot lo sugiere -> ROJO
        elif active_verb_context == self.verb_id:
            color = VERB_STYLE["TEXT_HOVER"]

        # 4. Estado normal -> AMARILLO PÁLIDO
        else:
            color = VERB_STYLE["TEXT_NORMAL"]

        # --------------------------------------------------

        if not self.lines: return

        # (El resto de la función sigue igual, no toques nada hacia abajo)
        font = get_sharp_font(self.final_size)
        real_line_height = font.get_height() / scale_factor

        num_lines = len(self.lines)
        total_block_h = (num_lines * real_line_height) + ((num_lines - 1) * self.line_spacing)

        start_y = self.rect.centery - (total_block_h / 2) + (real_line_height / 2) - 1

        for i, line in enumerate(self.lines):
            ly = start_y + i * (real_line_height + self.line_spacing)
            draw_text_sharp(line, self.rect.centerx, ly, self.final_size, color, align="center")


class VerbMenu:
    def __init__(self):
        self.rect = pygame.Rect(0, cfg.GAME_AREA_HEIGHT + cfg.CONFIG["TEXTBOX_HEIGHT"], cfg.CONFIG["GAME_WIDTH"],
                                cfg.CONFIG["VERB_MENU_HEIGHT"])
        self.buttons = []
        # Importamos aquí para evitar referencias circulares si config no está listo al inicio
        self.refresh_verbs()
        self.visible = True
        self.selected_verb = None

    def refresh_verbs(self):
        from config import VERBS_LOCALIZED, VERB_KEYS
        self.buttons = []
        # Usamos VERB_KEYS si existe para mantener orden, o las keys directas
        keys = VERB_KEYS if 'VERB_KEYS' in globals() else list(VERBS_LOCALIZED.keys())

        verbs = [k for k in keys if k not in ["WALK", "WITH"]][:9]

        sx = 10
        sy = self.rect.y + 8
        w = 88
        h = 36
        pad = 6
        for i, vid in enumerate(verbs):
            r, c = divmod(i, 3)
            self.buttons.append(VerbButton(vid, sx + c * (w + pad), sy + r * (h + pad), w, h))

    def handle_click(self, mx, my):
        if not self.visible: return False
        for btn in self.buttons:
            if btn.rect.collidepoint(mx, my):
                if self.selected_verb == btn.verb_id:
                    self.selected_verb = None; btn.selected = False
                else:
                    self.clear_selection(); self.selected_verb = btn.verb_id; btn.selected = True
                return True
        return False

    def clear_selection(self):
        self.selected_verb = None
        for b in self.buttons: b.selected = False

    def get_selected_verb(self):
        return self.selected_verb

    def draw(self, screen, mx, my, context):
        if not self.visible: return
        pygame.draw.rect(screen, VERB_STYLE["BG_MENU"], self.rect)
        for b in self.buttons: b.draw(screen, mx, my, context)

    # --- AQUÍ ESTÁ EL ARREGLO IMPORTANTE ---
    def draw_text_hd(self, highlight_verb=None):
        if not self.visible: return
        mx, my = get_virtual_mouse_pos()

        # 1. Detectar si el ratón está sobre un botón (Prioridad 1)
        hovered_button_verb = None
        for b in self.buttons:
            if b.rect.collidepoint(mx, my):
                hovered_button_verb = b.verb_id

        # 2. Decidir qué verbo iluminar
        # Si el ratón está sobre un botón, iluminamos ese botón.
        # Si no, iluminamos el 'suggested_verb' que nos manda el main.py (ej: "Mirar" al pasar sobre un objeto)
        final_context = hovered_button_verb if hovered_button_verb else highlight_verb

        for b in self.buttons:
            b.draw_text_hd(active_verb_context=final_context)


class InventorySlot:
    def __init__(self, x, y, size):
        self.rect = pygame.Rect(x, y, size, size)
        self.item = None

    def set_item(self, item): self.item = item

    def get_item(self): return self.item

    def is_mouse_over(self, mx, my): return self.rect.collidepoint(mx, my)

    def draw(self, screen):
        # Estilo gráfico original
        pygame.draw.rect(screen, (68, 68, 68), self.rect)
        pygame.draw.line(screen, (102, 102, 102), (self.rect.left, self.rect.top), (self.rect.right, self.rect.top), 2)
        pygame.draw.line(screen, (102, 102, 102), (self.rect.left, self.rect.top), (self.rect.left, self.rect.bottom),
                         2)
        pygame.draw.line(screen, (34, 34, 34), (self.rect.left, self.rect.bottom), (self.rect.right, self.rect.bottom),
                         2)
        pygame.draw.line(screen, (34, 34, 34), (self.rect.right, self.rect.top), (self.rect.right, self.rect.bottom), 2)

        if self.item and self.item.image:
            img_x = self.rect.centerx - self.item.image.get_width() // 2
            img_y = self.rect.centery - self.item.image.get_height() // 2
            screen.blit(self.item.image, (img_x, img_y))


class Inventory:
    def __init__(self):
        self.screen_width = cfg.CONFIG["GAME_WIDTH"]
        self.visible = True

        # CÁLCULO DINÁMICO (COPIADO DE VERDAD ABSOLUTA)
        verb_menu_y = cfg.GAME_AREA_HEIGHT + cfg.CONFIG["TEXTBOX_HEIGHT"]
        verb_btn_width = 88
        verb_padding = 6
        verb_cols = 3
        verb_menu_end_x = 10 + (verb_cols * (verb_btn_width + verb_padding)) - verb_padding

        arrow_padding = 8
        arrow_w = 40
        arrow_h = 40
        arrow_x = verb_menu_end_x + arrow_padding
        verb_block_height = 120
        self.start_y = verb_menu_y + 8

        self.scroll_up = ScrollButton(arrow_x, self.start_y, arrow_w, "up")
        self.scroll_down = ScrollButton(arrow_x, self.start_y + verb_block_height - arrow_h, arrow_w, "down")

        self.start_x = arrow_x + arrow_w + arrow_padding
        self.slot_size = 58
        margin_right = 10
        available_width = self.screen_width - self.start_x - margin_right

        min_padding = 4
        self.slots_per_row = int(available_width // (self.slot_size + min_padding))
        if self.slots_per_row < 1: self.slots_per_row = 1

        if self.slots_per_row > 1:
            total_slot_width = self.slots_per_row * self.slot_size
            remaining_space = available_width - total_slot_width
            self.padding = remaining_space // (self.slots_per_row - 1)
        else:
            self.padding = min_padding

        self.visible_rows = 2

        self.slots = []
        for r in range(self.visible_rows):
            for c in range(self.slots_per_row):
                x = self.start_x + c * (self.slot_size + self.padding)
                y = self.start_y + r * (self.slot_size + min_padding)
                self.slots.append(InventorySlot(x, y, self.slot_size))

        self.items = []
        self.scroll_offset = 0
        self.active_item = None

    def add_item(self, item_id, name_fallback, img, actions=None, label_id=None):
        if label_id and label_id in cfg.ITEM_NAMES:
            final_name = cfg.ITEM_NAMES[label_id]
        else:
            final_name = cfg.ITEM_NAMES.get(item_id, name_fallback)
        # OJO: InventoryItem debe existir (copia la clase de abajo si no la tienes)
        new_item = InventoryItem(item_id, final_name, img, actions, self.slot_size, label_id=label_id)
        self.items.append(new_item)
        self.update_visible()

    def remove_item(self, item_id):
        self.items = [i for i in self.items if i.id != item_id]
        self.update_visible()

    def update_visible(self):
        for i, slot in enumerate(self.slots):
            idx = i + self.scroll_offset
            slot.set_item(self.items[idx] if idx < len(self.items) else None)

    def handle_click(self, mx, my):
        if self.scroll_up.is_mouse_over(mx, my):
            if self.scroll_offset > 0:
                self.scroll_offset = max(0, self.scroll_offset - self.slots_per_row)
                self.update_visible()
            return None
        if self.scroll_down.is_mouse_over(mx, my):
            max_scroll = len(self.items) - (self.visible_rows * self.slots_per_row)
            if self.scroll_offset < max_scroll:
                self.scroll_offset += self.slots_per_row
                self.update_visible()
            return None
        for slot in self.slots:
            if slot.is_mouse_over(mx, my) and slot.get_item(): return slot.get_item()
        return None

    def get_hovered_item(self, mx, my):
        for slot in self.slots:
            if slot.is_mouse_over(mx, my): return slot.get_item()
        return None

    def draw(self, screen):
        if not self.visible: return
        mx, my = get_virtual_mouse_pos()
        for slot in self.slots: slot.draw(screen)
        self.scroll_up.draw(screen, mx, my)
        self.scroll_down.draw(screen, mx, my)


class InventoryItem:
    # AÑADIMOS slot_size AL INIT para corregir el error de argumentos múltiples
    def __init__(self, item_id, name, image_file, actions=None, slot_size=58, label_id=None):
        self.id = item_id
        self.name = name
        self.label_id = label_id
        self.actions = actions if actions else {}
        self.image = None

        # Carga de imagen usando el Gestor de Recursos
        # Asegúrate de que RES_MANAGER está importado al principio de classes.py
        loaded_img = RES_MANAGER.get_image(image_file, cfg.OBJ_DIR)

        if loaded_img:
            # Lógica de escalado para que quepa en el slot (usando slot_size)
            max_dim = slot_size - 6
            width = loaded_img.get_width()
            height = loaded_img.get_height()

            if width > 0 and height > 0:
                scale = min(max_dim / width, max_dim / height)
                new_w = int(width * scale)
                new_h = int(height * scale)
                self.image = pygame.transform.scale(loaded_img, (new_w, new_h))
            else:
                self.image = loaded_img
        else:
            # Fallback visual por si falla la imagen
            self.image = pygame.Surface((slot_size - 10, slot_size - 10))
            self.image.fill((100, 100, 100))


# ==========================================
#  CLASE DEBUG CONSOLE (RESTAURADA FULL)
# ==========================================
class DebugConsole:
    def __init__(self):
        self.lines = []
        self.max_lines = 100

        # Configuración visual
        self.font_size = 14
        # Usamos la fuente global cfg.UI_FONT_PATH en lugar de Arial
        try:
            self.font = pygame.font.Font(cfg.UI_FONT_PATH, self.font_size)
        except:
            self.font = pygame.font.SysFont("arial", self.font_size)

        self.bg_color = (0, 0, 0, 200)
        self.header_color = (0, 100, 0, 200)
        self.text_color = (0, 255, 0)

        # Tamaño ajustado para dejar márgenes
        self.rect = pygame.Rect(10, 10, 425, 300)

        self.line_height = self.font_size + 4
        self.lines_per_page = (self.rect.height - 20) // self.line_height
        self.scroll_offset = 0

        # Variables Drag (Arrastrar ventana)
        self.dragging = False
        self.drag_offset = (0, 0)

    def log(self, *args):
        message = " ".join(map(str, args))
        self.lines.append(message)
        if len(self.lines) > self.max_lines:
            self.lines.pop(0)
        # Auto-scroll al final al recibir nuevo mensaje
        if len(self.lines) > self.lines_per_page:
            self.scroll_offset = len(self.lines) - self.lines_per_page
        else:
            self.scroll_offset = 0

    def scroll(self, direction):
        total_lines = len(self.lines)
        if total_lines <= self.lines_per_page: return

        max_scroll = total_lines - self.lines_per_page

        # Invertimos dirección para que la rueda se sienta natural (arriba sube, abajo baja)
        if direction > 0:  # Rueda arriba
            self.scroll_offset -= 1
        elif direction < 0:  # Rueda abajo
            self.scroll_offset += 1

        if self.scroll_offset < 0: self.scroll_offset = 0
        if self.scroll_offset > max_scroll: self.scroll_offset = max_scroll

    def handle_event(self, event):
        """Maneja eventos de ratón para arrastrar y hacer scroll"""
        # Si no hay debug, no consumimos eventos
        if not cfg.CONFIG.get("DEBUG_MODE", False) or cfg.CONFIG.get("SHOW_HINTS_ONLY", False):
            self.dragging = False
            return False

        mx, my = get_virtual_mouse_pos()

        # 1. ARRASTRAR (DRAG & DROP)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Clic Izquierdo
                if self.rect.collidepoint(mx, my):
                    self.dragging = True
                    self.drag_offset = (self.rect.x - mx, self.rect.y - my)
                    return True  # Consumimos el evento

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.rect.x = mx + self.drag_offset[0]
                self.rect.y = my + self.drag_offset[1]
                return True

        # 2. SCROLL (RUEDA)
        elif event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(mx, my):
                # event.y es positivo hacia arriba, negativo hacia abajo
                self.scroll(event.y)
                return True

        return False

    def draw(self, screen):
        # Visibilidad
        if not cfg.CONFIG.get("DEBUG_MODE", False): return
        if cfg.CONFIG.get("SHOW_HINTS_ONLY", False): return

        # 1. Dibujar fondo y Header
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        s.fill(self.bg_color)

        # Barra de título verde oscuro
        pygame.draw.rect(s, self.header_color, (0, 0, self.rect.width, 20))

        screen.blit(s, (self.rect.x, self.rect.y))

        # Borde blanco
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 1)

        # Texto del Header
        try:
            header_font = get_sharp_font(12)  # Usamos la utilidad grafica si está disponible, o self.font
        except:
            header_font = self.font

        # Usamos GAME_MSGS si está disponible, sino texto fijo
        title = cfg.GAME_MSGS.get("DEBUG_TITLE", "DEBUG CONSOLE") if 'GAME_MSGS' in globals() else "DEBUG CONSOLE"
        h_txt = self.font.render(title, True, (200, 200, 200))
        screen.blit(h_txt, (self.rect.x + 5, self.rect.y + 2))

        # 2. Dibujar líneas de log
        if not self.lines: return

        # Renderizamos las líneas visibles según scroll
        start_index = self.scroll_offset
        end_index = min(start_index + self.lines_per_page, len(self.lines))
        visible_slice = self.lines[start_index:end_index]

        # Empezamos a dibujar debajo del header
        y_pos = self.rect.y + 25

        for line in visible_slice:
            # Recortar texto si es muy largo visualmente (aprox)
            if len(line) > 60: line = line[:57] + "..."

            txt_surf = self.font.render(line, True, self.text_color)
            screen.blit(txt_surf, (self.rect.x + 5, y_pos))
            y_pos += self.line_height

        # Indicador visual de Scroll (si hay más líneas de las que caben)
        if len(self.lines) > self.lines_per_page:
            bar_h = self.rect.height - 20
            ratio = self.lines_per_page / len(self.lines)
            thumb_h = max(10, bar_h * ratio)

            # Posición thumb
            max_scroll = len(self.lines) - self.lines_per_page
            progress = self.scroll_offset / max_scroll if max_scroll > 0 else 0
            thumb_y = self.rect.y + 20 + (progress * (bar_h - thumb_h))

            pygame.draw.rect(screen, (100, 100, 100), (self.rect.right - 8, self.rect.y + 20, 8, bar_h))
            pygame.draw.rect(screen, (200, 200, 200), (self.rect.right - 8, thumb_y, 8, thumb_h))


# ==========================================
#  CLASE CREDITS WINDOW (RESTAURADA FULL)
# ==========================================
class CreditsWindow:
    def __init__(self):
        self.font_size = 16
        try:
            self.font = pygame.font.Font(cfg.UI_FONT_PATH, self.font_size)
        except:
            self.font = pygame.font.SysFont("arial", self.font_size)

        self.bg_color = (0, 0, 0, 220)
        self.header_color = (180, 160, 120, 255)
        self.text_color = (255, 255, 255)
        self.border_color = (90, 70, 50)

        # Dimensiones y Posición (Centrado)
        w, h = 400, 350
        x = (cfg.CONFIG["GAME_WIDTH"] - w) // 2
        y = (cfg.CONFIG["GAME_HEIGHT"] - h) // 2
        self.rect = pygame.Rect(x, y, w, h)

        # Botón cerrar absoluto (Esquina superior derecha de la ventana)
        self.close_rect_absolute = pygame.Rect(self.rect.right - 25, self.rect.y, 25, 20)

        self.line_height = self.font_size + 4
        self.lines_per_page = (self.rect.height - 30) // self.line_height

        self.visible = False
        self.scroll_offset = 0
        self.dragging = False
        self.drag_offset = (0, 0)

        # Cargamos el texto de créditos global
        self.lines = cfg.CREDITS_TEXT.strip().split('\n')

    def show(self):
        self.visible = True
        self.scroll_offset = 0

    def hide(self):
        self.visible = False

    def scroll(self, direction):
        if not self.visible: return
        # direction: positivo o negativo desde mousewheel
        if direction > 0:  # Rueda arriba
            self.scroll_offset -= 1
        elif direction < 0:  # Rueda abajo
            self.scroll_offset += 1

        max_scroll = max(0, len(self.lines) - self.lines_per_page)

        if self.scroll_offset < 0: self.scroll_offset = 0
        if self.scroll_offset > max_scroll: self.scroll_offset = max_scroll

    def handle_event(self, event):
        if not self.visible: return False

        mx, my = get_virtual_mouse_pos()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:

                # Clic en Cerrar (X)
                if self.close_rect_absolute.collidepoint(mx, my):
                    self.hide()
                    return True

                # Clic en Arrastrar
                if self.rect.collidepoint(mx, my):
                    self.dragging = True
                    self.drag_offset = (self.rect.x - mx, self.rect.y - my)
                    return True

        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.rect.x = mx + self.drag_offset[0]
                self.rect.y = my + self.drag_offset[1]

                # IMPORTANTE: Actualizar posición del botón cerrar al mover la ventana
                self.close_rect_absolute.x = self.rect.right - 25
                self.close_rect_absolute.y = self.rect.y
                return True

        elif event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(mx, my):
                self.scroll(event.y)
                return True
        return False

    def draw(self, screen):
        if not self.visible: return

        # Fondo
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        s.fill(self.bg_color)

        # Barra superior
        pygame.draw.rect(s, self.header_color, (0, 0, self.rect.width, 20))

        # Botón X (Visualmente relativo a la superficie s)
        rect_visual_relativo = pygame.Rect(self.rect.width - 25, 0, 25, 20)
        pygame.draw.rect(s, (180, 50, 50), rect_visual_relativo)

        close_txt = self.font.render("X", True, (255, 255, 255))
        s.blit(close_txt, (self.rect.width - 18, 2))

        screen.blit(s, (self.rect.x, self.rect.y))

        # Borde y Título
        pygame.draw.rect(screen, self.border_color, self.rect, 2)

        title_str = cfg.GAME_MSGS.get("CREDITS_TITLE", "CREDITS") if 'GAME_MSGS' in globals() else "CREDITS"
        h_txt = self.font.render(title_str, True, (40, 30, 10))
        screen.blit(h_txt, (self.rect.x + 5, self.rect.y + 2))

        # Texto con Scroll
        start_index = self.scroll_offset
        end_index = start_index + self.lines_per_page
        visible_slice = self.lines[start_index:end_index]

        y_pos = self.rect.y + 25
        for line in visible_slice:
            txt_surf = self.font.render(line, True, self.text_color)
            # Centrado horizontal
            x_pos = self.rect.centerx - (txt_surf.get_width() // 2)
            screen.blit(txt_surf, (x_pos, y_pos))
            y_pos += self.line_height

        # Barra de scroll visual (Simplificada)
        if len(self.lines) > self.lines_per_page:
            max_scroll = len(self.lines) - self.lines_per_page
            if max_scroll > 0:
                scroll_pct = self.scroll_offset / max_scroll
                bar_height = self.rect.height - 30
                indicator_y = self.rect.y + 25 + (bar_height * scroll_pct)
                # Clamp visual
                if indicator_y > self.rect.bottom - 5: indicator_y = self.rect.bottom - 5

                pygame.draw.circle(screen, (200, 200, 200), (self.rect.right - 5, int(indicator_y)), 4)


class MapNode:
    def __init__(self, scene_id, map_x, map_y, spawn_x, spawn_y, icon_file=None):
        self.scene_id = scene_id
        # Intenta obtener el nombre traducido, si no usa el ID
        self.label = cfg.SCENE_NAMES.get(scene_id, scene_id)

        self.rect = pygame.Rect(map_x - 20, map_y - 20, 40, 40)
        self.center = (map_x, map_y)
        self.spawn = (spawn_x, spawn_y)  # Nota: En main usabas .spawn, aquí lo unificamos
        self.image = None

        if icon_file:
            # Usamos el gestor de recursos para cargar el pin
            self.image = RES_MANAGER.get_image(icon_file, cfg.OBJ_DIR)


class Movement:
    def __init__(self):
        self.speed = cfg.CONFIG["PLAYER_SPEED"]
        self.path = []
        self.idx = 0
        self.is_moving = False
        self.dir_x = 0
        self.dir_y = 0
        self.callback = None

    def set_path(self, path, cb=None):
        if path:
            self.path = path; self.idx = 0; self.is_moving = True; self.callback = cb
        else:
            self.stop()

    def stop(self):
        self.is_moving = False; self.path = []; self.dir_x = 0; self.dir_y = 0; self.callback = None

    def update(self, char):
        if not self.is_moving or not self.path: self.stop(); return False
        tx, ty = self.path[self.idx]
        cx, cy = char.rect.centerx, char.rect.bottom
        dx = tx - cx
        dy = ty - cy
        dist = math.sqrt(dx ** 2 + dy ** 2)
        if dist > 0: self.dir_x = dx / dist; self.dir_y = dy / dist
        if dist < self.speed:
            char.rect.centerx = tx
            char.rect.bottom = ty
            self.idx += 1
            if self.idx >= len(self.path):
                self.is_moving = False
                self.path = []
                self.dir_x = 0
                self.dir_y = 0
                if self.callback: cb = self.callback; self.callback = None; cb()
                return False
        else:
            char.rect.centerx += self.dir_x * self.speed
            char.rect.bottom += self.dir_y * self.speed
        return True


class CutsceneManager:
    def __init__(self):
        self.active = False
        self.queue = []
        self.curr = None
        self.timer = 0
        # --- CORRECCIÓN AQUÍ: Nombres unificados ---
        self.waiting_move = False
        self.waiting_text = False

        # DEPENDENCIAS
        self.func_smart_move = None
        self.func_say = None
        self.func_face = None
        self.func_set_anim = None
        self.check_text_timer_func = None

    def set_dependencies(self, smart_move_func, say_func, face_func, set_anim_func, check_text_timer):
        self.func_smart_move = smart_move_func
        self.func_say = say_func
        self.func_face = face_func
        self.func_set_anim = set_anim_func
        self.check_text_timer_func = check_text_timer

    def start_cutscene(self, actions):
        self.queue = actions
        self.active = True
        self.next_action()

    def end_cutscene(self):
        self.active = False
        self.curr = None
        # main.py detectará active=False y cambiará el estado

    def skip_cutscene(self):
        if not self.active: return
        # Ejecutar lógica crítica
        while self.queue:
            action = self.queue.pop(0)
            atype = action.get("type")
            if atype == "FUNC":
                func = action.get("func")
                if callable(func): func()
        self.end_cutscene()

    def next_action(self):
        if not self.queue:
            self.end_cutscene()
            return

        self.curr = self.queue.pop(0)
        atype = self.curr.get("type")

        # 1. MOVIMIENTO
        if atype == "MOVE":
            target_x = self.curr.get("x")
            target_y = self.curr.get("y")
            if self.func_smart_move:
                self.func_smart_move(target_x, target_y)
                # --- CORRECCIÓN: Usar waiting_move ---
                self.waiting_move = True
            else:
                self.next_action()

        # 2. DIÁLOGO (SAY)
        elif atype == "SAY":
            text = self.curr.get("text")
            duration = self.curr.get("time", 3.0)
            if self.func_say:
                self.func_say(text, duration)
                # --- CORRECCIÓN: Usar waiting_text ---
                self.waiting_text = True
            else:
                self.next_action()

        # 3. ESPERA (WAIT)
        elif atype == "WAIT":
            self.timer = self.curr.get("seconds", 1.0)

        # 4. MIRAR (FACE)
        elif atype == "FACE":
            direction = self.curr.get("dir", "down")
            if self.func_face:
                self.func_face(direction)
            self.next_action()

        # 5. ANIMACIÓN (ANIM)
        elif atype == "ANIM":
            anim_name = self.curr.get("name")
            if self.func_set_anim:
                self.func_set_anim(anim_name)
            duration = self.curr.get("duration", 0)
            if duration > 0:
                self.timer = duration
            else:
                self.next_action()

        # 6. FUNCIÓN (FUNC)
        elif atype == "FUNC":
            func = self.curr.get("func")
            if callable(func): func()
            self.next_action()

    def update(self, dt, is_player_moving):
        if not self.active: return

        # 1. ESPERA POR MOVIMIENTO
        if self.waiting_move:
            if not is_player_moving:
                self.waiting_move = False
                self.next_action()
            return

        # 2. ESPERA POR TEXTO
        if self.waiting_text:
            if self.check_text_timer_func:
                timeLeft = self.check_text_timer_func()
                if timeLeft <= 0:
                    self.waiting_text = False
                    self.next_action()
            return

        # 3. RESTO DE TIMERS
        if self.timer > 0:
            self.timer -= dt
            if self.timer <= 0:
                if self.curr and self.curr.get("type") == "ANIM" and self.func_set_anim:
                    self.func_set_anim(None)
                self.next_action()