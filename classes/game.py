import os
import config as cfg
import pygame
from classes.commons import TRANSITION_FADE, TRANSITION_SLIDE_LEFT, TRANSITION_SLIDE_RIGHT, TRANSITION_SLIDE_UP, TRANSITION_SLIDE_DOWN, TRANSITION_ZOOM
from classes.resources import RES_MANAGER

class Animation:
    def __init__(self, spritesheet_file, num_frames, frame_width, frame_height, frame_duration=100):
        self.frames = []
        self.frame_duration = frame_duration
        self.current_frame = 0
        self.time_since_last_frame = 0

        full_path = os.path.join(cfg.ITEMS_DIR, spritesheet_file)
        try:
            if not os.path.exists(full_path):
                surf = pygame.Surface((frame_width, frame_height))
                surf.fill((255, 0, 255))
                self.frames.append(surf)
            else:
                spritesheet = pygame.image.load(full_path).convert_alpha()
                expected_width = num_frames * frame_width
                if spritesheet.get_width() < expected_width:
                    spritesheet = pygame.transform.scale(spritesheet, (expected_width, spritesheet.get_height()))

                actual_frame_height = min(frame_height, spritesheet.get_height())
                for i in range(num_frames):
                    frame_x = i * frame_width
                    frame_rect = pygame.Rect(frame_x, 0, frame_width, actual_frame_height)
                    frame = spritesheet.subsurface(frame_rect).copy()
                    if actual_frame_height < frame_height:
                        padded_frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA, 32)
                        padded_frame.blit(frame, (0, frame_height - actual_frame_height))
                        frame = padded_frame
                    self.frames.append(frame)
        except Exception as e:
            print(f"[ERROR] Anim {spritesheet_file}: {e}")
            self.frames = [pygame.Surface((frame_width, frame_height))]

    def update(self, dt):
        if len(self.frames) <= 1: return False
        looped = False
        self.time_since_last_frame += dt * 1000

        if self.time_since_last_frame >= self.frame_duration:
            frames_to_advance = int(self.time_since_last_frame / self.frame_duration)
            self.time_since_last_frame %= self.frame_duration
            next_frame = (self.current_frame + frames_to_advance) % len(self.frames)
            if next_frame < self.current_frame: looped = True
            self.current_frame = next_frame

        return looped

    def get_current_frame(self):
        return self.frames[self.current_frame] if self.frames else None

    def reset(self):
        self.current_frame = 0
        self.time_since_last_frame = 0


class AnimatedCharacter:
    def __init__(self, x, y, char_id="Gilo", text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, 32, 64)
        self.text_color = text_color
        self.animations = {}
        self.current_animation = None
        self.cached_surface = None
        self.last_frame_ref = None
        self.last_scale_ref = 0.0
        self.step_timer = 0
        self.step_interval = 0.35
        self.step_sound = cfg.SOUNDS.get("step")
        self.idle_timer = 0.0
        self.idle_threshold = cfg.CONFIG["IDLE_COOL_THRESHOLD"]
        self.swap_character(char_id)

    def swap_character(self, char_id):
        # Intentamos obtener el personaje solicitado
        if char_id in cfg.CHAR_DEFS:
            char_data = cfg.CHAR_DEFS[char_id]
        else:
            # Si no existe, cogemos EL PRIMERO que haya en la lista (Gilo, Bart, el que sea)
            # Esto evita el KeyError si borras un personaje concreto
            print(f"[WARNING] Character '{char_id}' not found. Loading default fallback.")
            char_data = list(cfg.CHAR_DEFS.values())[0]
        self.char_id = char_id
        self.prefix = char_data["prefix"]
        w = char_data["width"]
        h = char_data["height"]
        frames_cfg = char_data["frames"]
        self.base_scale = char_data.get("base_scale", 1.0)
        self.current_scale = self.base_scale

        old_bottom = self.rect.bottom
        old_centerx = self.rect.centerx
        self.rect.width = w
        self.rect.height = h
        self.rect.bottom = old_bottom
        self.rect.centerx = old_centerx

        self.animations = {}

        def load_anim(suffix, frame_key, duration=100):
            num_frames = frames_cfg.get(frame_key, 1)
            filename = f"{self.prefix}_{suffix}.gif"
            return Animation(filename, num_frames, w, h, frame_duration=duration)

        self.animations["idle_down"] = load_anim("d", "idle")
        self.animations["idle_left"] = load_anim("l", "idle")
        self.animations["idle_right"] = load_anim("r", "idle")
        self.animations["idle_up"] = load_anim("u", "idle")
        self.animations["walk_down"] = load_anim("wd", "walk_down", 120)
        self.animations["walk_left"] = load_anim("wl", "walk_left", 100)
        self.animations["walk_right"] = load_anim("wr", "walk_right", 100)
        self.animations["walk_up"] = load_anim("wu", "walk_up", 120)
        self.animations["talk_left"] = load_anim("tl", "talk_left", 150)
        self.animations["talk_right"] = load_anim("tr", "talk_right", 150)
        self.animations["talk_down"] = load_anim("td", "talk_down", 150)
        self.animations["push"] = load_anim("push", "push", 150)
        self.animations["pull"] = load_anim("pull", "pull", 150)
        self.animations["pick"] = load_anim("pick", "pick", 150)
        self.animations["give"] = load_anim("give", "give", 150)
        self.animations["open"] = load_anim("open", "open", 150)
        self.animations["close"] = load_anim("close", "close", 150)
        self.animations["cool"] = load_anim("cool", "cool", 300)
        self.set_animation("idle_down")

    def set_scale(self, scene_depth_factor):
        self.current_scale = scene_depth_factor * self.base_scale

    def set_animation(self, animation_name):
        if animation_name in self.animations:
            if self.current_animation != animation_name:
                if self.current_animation: self.animations[self.current_animation].reset()
                self.current_animation = animation_name

    def face_point(self, target_x, target_y):
        dx = target_x - self.rect.centerx
        dy = target_y - self.rect.centery
        if abs(dx) > abs(dy):
            self.set_animation("idle_right" if dx > 0 else "idle_left")
        else:
            self.set_animation("idle_down" if dy > 0 else "idle_up")

    def face_camera(self):
        self.set_animation("idle_down")

    def update(self, dt, is_moving=False, direction_x=0, direction_y=0, is_talking=False, forced_anim=None,
               current_scene_ref=None):
        # --- LÓGICA DE SONIDO DINÁMICO ---
        if is_moving and cfg.CONFIG["ENABLE_SOUND"]:
            self.step_timer -= dt
            if self.step_timer <= 0:
                # 1. Por defecto usamos el sonido estándar
                sound_key = "step"

                # 2. Si nos pasan la escena, miramos qué sonido tiene configurado
                if current_scene_ref and hasattr(current_scene_ref, "step_sound_key"):
                    sound_key = current_scene_ref.step_sound_key

                    # 3. Reproducimos el sonido si existe en el diccionario global
                if sound_key in cfg.SOUNDS:
                    cfg.SOUNDS[sound_key].play()
                elif "step" in cfg.SOUNDS:  # Fallback de seguridad
                    cfg.SOUNDS["step"].play()

                self.step_timer = self.step_interval
        else:
            self.step_timer = 0.05

        if is_moving or is_talking or forced_anim:
            self.idle_timer = 0.0

        if forced_anim:
            self.set_animation(forced_anim)
        elif is_moving:
            if abs(direction_x) > abs(direction_y):
                self.set_animation("walk_right" if direction_x > 0 else "walk_left")
            else:
                self.set_animation("walk_down" if direction_y > 0 else "walk_up")
        elif is_talking:
            if self.current_animation and "left" in self.current_animation:
                self.set_animation("talk_left")
            elif self.current_animation and "right" in self.current_animation:
                self.set_animation("talk_right")
            elif self.current_animation and "up" in self.current_animation:
                self.set_animation("talk_down")
            else:
                self.set_animation("talk_down")
        else:
            if self.current_animation == "cool":
                pass
            else:
                if self.current_animation:
                    ca = self.current_animation
                    if "walk_down" in ca or "talk_down" in ca:
                        self.set_animation("idle_down")
                    elif "walk_left" in ca or "talk_left" in ca:
                        self.set_animation("idle_left")
                    elif "walk_right" in ca or "talk_right" in ca:
                        self.set_animation("idle_right")
                    elif "walk_up" in ca:
                        self.set_animation("idle_up")
                    elif "push" in ca or "pull" in ca or "pick" in ca or "give" in ca:
                        self.set_animation("idle_down")
                self.idle_timer += dt
                if self.idle_timer >= self.idle_threshold:
                    self.set_animation("cool")
                    self.animations["cool"].reset()

        if self.current_animation:
            looped = self.animations[self.current_animation].update(dt)
            if self.current_animation == "cool" and looped:
                self.idle_timer = 0.0
                self.set_animation("idle_down")

    def draw(self, screen, camera_x=0, tint_color=(255, 255, 255)):
        if self.current_animation:
            original_frame = self.animations[self.current_animation].get_current_frame()
            if original_frame:
                final_surface = original_frame
                if self.current_scale != 1.0:
                    if (original_frame != self.last_frame_ref) or (self.current_scale != self.last_scale_ref):
                        width = int(original_frame.get_width() * self.current_scale)
                        height = int(original_frame.get_height() * self.current_scale)
                        self.cached_surface = pygame.transform.scale(original_frame, (width, height))
                        self.last_frame_ref = original_frame
                        self.last_scale_ref = self.current_scale
                    final_surface = self.cached_surface

                if tint_color != (255, 255, 255):
                    tinted_surface = final_surface.copy()
                    tinted_surface.fill(tint_color, special_flags=pygame.BLEND_MULT)
                    final_surface = tinted_surface

                world_x = self.rect.centerx - final_surface.get_width() // 2
                world_y = self.rect.bottom - final_surface.get_height()
                screen_x = world_x - camera_x
                screen.blit(final_surface, (screen_x, world_y))


class SceneManager:
    def __init__(self):
        self.scenes = {}
        self.current_scene = None
        self.fade_surface = pygame.Surface((cfg.CONFIG["GAME_WIDTH"], cfg.CONFIG["GAME_HEIGHT"]))
        self.fade_surface.fill((0, 0, 0))
        self.last_frame = None
        self.transition_mode = "IDLE"
        self.progress = 0.0
        self.transition_speed = 2.0
        self.next_scene_name = None
        self.next_spawn_point = None
        self.target_effect = TRANSITION_FADE
        self.player = None  # Variable interna para guardar al jugador
        self.reset_ui_callback = None  # Variable para guardar la función de limpieza

    # Método para recibir la función desde main.py ---
    def set_ui_callback(self, func):
        self.reset_ui_callback = func

    def add_scene(self, scene):
        self.scenes[scene.id] = scene

    def get_current_scene(self):
        return self.current_scene

    def set_player(self, player_instance):
        self.player = player_instance

    # ELIMINADO EL ARGUMENTO player_ref de aquí abajo
    def change_scene_with_effect(self, target_scene_id, spawn_point, forced_effect=None):
        if self.transition_mode != "IDLE": return
        target_scene_obj = self.scenes.get(target_scene_id)
        if not target_scene_obj: return
        # Ejecutar la limpieza de UI si existe la función ---
        if self.reset_ui_callback:
            self.reset_ui_callback()
        effect = forced_effect if forced_effect else target_scene_obj.transition_type

        self.next_scene_name = target_scene_id
        self.next_spawn_point = spawn_point
        self.target_effect = effect
        self.progress = 0.0

        # Ya no seteamos self.player_ref aquí, usamos self.player que ya debe estar seteado

        if effect == TRANSITION_FADE:
            self.transition_mode = "FADE_OUT"
            self.transition_speed = 600
        elif effect in [TRANSITION_SLIDE_LEFT, TRANSITION_SLIDE_RIGHT, TRANSITION_SLIDE_UP, TRANSITION_SLIDE_DOWN]:
            self.last_frame = pygame.display.get_surface().copy()
            self._perform_switch()
            self.transition_mode = "SLIDE"
            self.transition_speed = 1.5
        elif effect == TRANSITION_ZOOM:
            self.last_frame = pygame.display.get_surface().copy()
            self.transition_mode = "ZOOM_IN"
            self.transition_speed = 2.0
        else:
            self._perform_switch()

    # ... (update_transition y draw_transition se quedan igual) ...
    def update_transition(self, dt):
        if self.transition_mode == "IDLE": return

        if "FADE" in self.transition_mode:
            if self.transition_mode == "FADE_OUT":
                self.progress += self.transition_speed * dt
                if self.progress >= 255:
                    self.progress = 255
                    self._perform_switch()
                    self.transition_mode = "FADE_IN"
            elif self.transition_mode == "FADE_IN":
                self.progress -= self.transition_speed * dt
                if self.progress <= 0:
                    self.progress = 0
                    self.transition_mode = "IDLE"
        elif self.transition_mode == "SLIDE":
            self.progress += dt * self.transition_speed
            if self.progress >= 1.0:
                self.progress = 1.0
                self.transition_mode = "IDLE"
                self.last_frame = None
        elif self.transition_mode == "ZOOM_IN":
            self.progress += dt * self.transition_speed
            if self.progress >= 1.0:
                self.progress = 1.0
                self._perform_switch()
                self.transition_mode = "ZOOM_OUT"
        elif self.transition_mode == "ZOOM_OUT":
            self.progress -= dt * self.transition_speed
            if self.progress <= 0.0:
                self.progress = 0.0
                self.transition_mode = "IDLE"
                self.last_frame = None

    def draw_transition(self, screen):
        if self.transition_mode == "IDLE": return
        w, h = cfg.CONFIG["GAME_WIDTH"], cfg.CONFIG["GAME_HEIGHT"]
        if "FADE" in self.transition_mode:
            alpha = int(max(0, min(255, self.progress)))
            self.fade_surface.set_alpha(alpha)
            screen.blit(self.fade_surface, (0, 0))
        elif self.transition_mode == "SLIDE" and self.last_frame:
            new_scene_img = screen.copy()
            screen.fill((0, 0, 0))
            t = self.progress
            smooth_t = t * (2 - t)
            old_x, old_y, new_x, new_y = 0, 0, 0, 0
            if self.target_effect == TRANSITION_SLIDE_LEFT:
                offset = int(smooth_t * w)
                old_x = -offset
                new_x = w - offset
            elif self.target_effect == TRANSITION_SLIDE_RIGHT:
                offset = int(smooth_t * w)
                old_x = offset
                new_x = -w + offset
            elif self.target_effect == TRANSITION_SLIDE_UP:
                offset = int(smooth_t * h)
                old_y = -offset
                new_y = h - offset
            elif self.target_effect == TRANSITION_SLIDE_DOWN:
                offset = int(smooth_t * h)
                old_y = offset
                new_y = -h + offset
            screen.blit(self.last_frame, (old_x, old_y))
            screen.blit(new_scene_img, (new_x, new_y))
        elif "ZOOM" in self.transition_mode:
            current_scale = 1.0 + (self.progress * 3.0)
            target_img = self.last_frame if self.transition_mode == "ZOOM_IN" else screen.copy()
            screen.fill((0, 0, 0))
            new_w = int(w * current_scale)
            new_h = int(h * current_scale)
            scaled_surf = pygame.transform.smoothscale(target_img, (new_w, new_h))
            dest_x = (w - new_w) // 2
            dest_y = (h - new_h) // 2
            screen.blit(scaled_surf, (dest_x, dest_y))

    def _perform_switch(self):
        if self.next_scene_name:
            if self.next_scene_name not in self.scenes: return
            new_s = self.scenes[self.next_scene_name]
            if self.current_scene:
                if hasattr(self.current_scene, 'on_exit') and self.current_scene.on_exit: self.current_scene.on_exit()
                self.current_scene.unload_assets()
            RES_MANAGER.clear_cache()
            self.current_scene = new_s
            self.current_scene.load_assets()
            if self.current_scene.on_enter: self.current_scene.on_enter()

            # --- AQUÍ ESTÁ EL ARREGLO PRINCIPAL ---
            # Usamos self.player directamente (inyectado previamente)
            if self.next_spawn_point and self.player:
                px, py = self.next_spawn_point
                self.player.rect.centerx = px
                self.player.rect.bottom = py
                s = new_s.get_dynamic_scale(py)
                self.player.set_scale(s)

                screen_w = cfg.CONFIG["GAME_WIDTH"]
                target_cam = px - (screen_w // 2)
                max_scroll = new_s.scene_width - screen_w
                if max_scroll < 0: max_scroll = 0
                new_s.camera_x = max(0, min(target_cam, max_scroll))

    def is_transitioning(self):
        return self.transition_mode != "IDLE"

    def change_scene(self, name):
        if name not in self.scenes: return None
        self.next_scene_name = name
        self.next_spawn_point = None
        self._perform_switch()
        return self.current_scene


class TranslationManager:
    """New class to handle the translations and language changes"""
    def __init__(self, default_language="en"):
        self.language=default_language
        self.variables={}
        self.variables["items"] = {}
        self.variables["descs"] = {}
        self.variables["scenes"] = {}
        self.variables["msgs"] = {}
        self.variables["verbs"] = {}
        self.variables["title"] = {}
        self.variables["cine"] = {}
        self.variables["dialogue"] = {}
        self.variables["menu"] = {}
        self.verb_keys=[]

    def load_translation(self, data):
        self.variables["items"].clear()
        self.variables["items"].update(data["items"])
        self.variables["descs"].clear()
        self.variables["descs"].update(data["descriptions"])
        self.variables["scenes"].clear()
        self.variables["scenes"].update(data["scenes"])
        self.variables["msgs"].clear()
        self.variables["msgs"].update(data["system_messages"])
        self.variables["verbs"].clear()
        self.variables["verbs"].update(data["verbs"])
        self.variables["menu"].clear()
        self.variables["menu"].update(data["menus"])
        self.variables["title"].clear()
        self.variables["title"].update(data["titles"])
        self.variables["cine"].clear()
        self.variables["cine"].update(data["cinematics"])
        self.variables["dialogue"].clear()
        self.variables["dialogue"].update(data.get("dialogues", {}))

        self.variables["msgs"]["VERB_USE"] = self.variables["verbs"].get("USE", "USE")
        self.verb_keys = list(self.variables["verbs"].keys())

    def get(self, namespace, var, fallback=None):
        if namespace not in self.variables:
            raise NameError(f"Namespace {namespace} doesn't exist")
        if var in self.variables[namespace]:
            return self.variables[namespace][var]
        if fallback: return fallback
        return var


class String:
    """New class representing a string displayed on screen. It is an abstraction layer for the translation model;
    you use it like a string, but it changes with the current language behind the hood"""
    def __init__(self, value, namespace, manager):
        self.manager=manager
        if isinstance(value, str): #Value is a simple string
            self.isDynamic=False
            self.staticString=value
        else:
            self.isDynamic=True
            self.dynamicVar=value.value
            self.dynamicNamespace=namespace

    def __repr__(self):
        if not self.isDynamic:
            return self.staticString
        else:
            return self.manager.get(self.dynamicNamespace, self.dynamicVar)

    def __hash__(self):
        return self.__repr__().__hash__()

    def __len__(self):
        return len(self.__repr__())

    def __getitem__(self, item):
        return self.__repr__().__getitem__(item)

    def split(self, arg):
        string=self.__repr__()
        return string.split(arg)

    def upper(self):
        string=self.__repr__()
        return string.upper()


class ActionsManager:
    """Just a simple class to store refs to gameplay functions"""
    def __init__(self):
        pass