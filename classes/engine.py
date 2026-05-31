import os
import pygame
import math
import heapq
import gc

import config as cfg
from classes.resources import RES_MANAGER
from scenes.variables import GAME_STATE
from classes.commons import TRANSITION_FADE, TRANSITION_ZOOM, draw_text_sharp
from classes.ui import MapNode


class Scene:
    def __init__(self, scene_id, name, background_image_path, walkable_mask_file=None, 
                scale_range=(1.0, 1.0), y_range=(0, 600), on_enter=None, on_exit=None,
                is_dark=False, light_flag=None, light_radius=150,
                parallax_paths=None, parallax_factors=None,
                auto_scroll_config=None,
                transition_type=TRANSITION_FADE,
                step_sound_key="step",
                lightmap_file=None):           
        self.id = scene_id 
        self.name = name
        self.step_sound_key = step_sound_key 
        self.bg_file = background_image_path
        self.mask_file = walkable_mask_file        
        self.min_scale, self.max_scale = scale_range
        self.min_y, self.max_y = y_range        
        self.on_enter = on_enter
        self.on_exit = on_exit
        self.is_dark = is_dark
        self.light_flag = light_flag
        self.light_radius = light_radius
        self.transition_type = transition_type
        self.parallax_paths = parallax_paths
        self.parallax_factors = parallax_factors
        self.parallax_layers = [] 
        self.parallax_layers_back = []  
        self.parallax_layers_front = [] 
        self.auto_scroll_config = auto_scroll_config 
        self.auto_scroll_offset_x = 0.0      
        self.hotspot_data = [] 
        self.exits = []        
        self.walkable_area = None 
        self.pathfinder = None
        self.hotspots = HotspotManager()
        self.camera_x = 0
        self.scene_width = cfg.CONFIG["GAME_WIDTH"]
        self.ambient_data = []  
        self.ambient_anims = [] 
        self.lightmap_file = lightmap_file   
        self.lightmap_surface = None         

    def _draw_layer_group(self, screen, layer_group):
        screen_h = screen.get_height() - cfg.UI_HEIGHT
        screen_w = cfg.CONFIG["GAME_WIDTH"]
        auto_layer_index = self.auto_scroll_config[0] if self.auto_scroll_config else -1
        auto_offset_val = self.auto_scroll_offset_x if self.auto_scroll_config else 0
        
        for i, layer_data in enumerate(self.parallax_layers):
             if layer_data not in layer_group: continue 
             img = layer_data["image"]
             factor = layer_data["factor"]
             img_w = img.get_width()
             y_pos = screen_h - img.get_height()
             
             if i == auto_layer_index: offset_total = auto_offset_val
             else: offset_total = self.camera_x * factor
             
             rel_x = (-offset_total) % img_w
             start_x = rel_x - img_w
             current_draw_x = start_x
             while current_draw_x < screen_w:
                 screen.blit(img, (int(current_draw_x), int(y_pos)))
                 current_draw_x += img_w

    def draw_background_layers(self, screen):
        if cfg.CONFIG.get("SHOW_WALKABLE_MASK", False):
            if self.walkable_area and self.walkable_area.mask:
                screen.blit(self.walkable_area.mask, (-int(self.camera_x), 0))
            else:
                screen.fill((255, 0, 0))
            return
        self._draw_layer_group(screen, self.parallax_layers_back)

    def draw_foreground_layers(self, screen):
        if cfg.CONFIG.get("SHOW_WALKABLE_MASK", False): return
        self._draw_layer_group(screen, self.parallax_layers_front)

    def get_dynamic_scale(self, current_y):
        if self.max_y == self.min_y: return self.max_scale
        factor = (current_y - self.min_y) / (self.max_y - self.min_y)
        factor = max(0.0, min(1.0, factor))
        return self.min_scale + (self.max_scale - self.min_scale) * factor

    def add_hotspot_data(self, **kwargs): 
        self.hotspot_data.append(kwargs)
    
    def add_exit(self, x, y, w, h, target_scene, spawn_x, spawn_y):
        rect = pygame.Rect(x, y, w, h)
        self.exits.append(SceneExit(rect, target_scene, spawn_x, spawn_y))

    def load_assets(self):
        self.parallax_layers = []
        self.parallax_layers_back = []
        self.parallax_layers_front = []
        target_h = cfg.GAME_AREA_HEIGHT

        if self.parallax_paths and self.parallax_factors:
            ground_index = -1
            if 1.0 in self.parallax_factors: ground_index = self.parallax_factors.index(1.0)
            else: ground_index = len(self.parallax_factors) - 1

            for i, file_name in enumerate(self.parallax_paths):
                full_path = os.path.join(cfg.BG_DIR, file_name)
                try:
                    if os.path.exists(full_path): raw_img = pygame.image.load(full_path).convert_alpha()
                    else: raise FileNotFoundError(f"No existe {file_name}")
                except Exception as e:
                    raw_img = pygame.Surface((800, 600)); raw_img.fill((100, 100, 100)); raw_img.set_alpha(150)
                
                try:
                    aspect_ratio = raw_img.get_width() / raw_img.get_height()
                    new_w = int(target_h * aspect_ratio)
                    if new_w < cfg.CONFIG["GAME_WIDTH"]: new_w = cfg.CONFIG["GAME_WIDTH"]
                    final_img = pygame.transform.scale(raw_img, (new_w, target_h))
                    speed = self.parallax_factors[i]
                    layer_data = {"image": final_img, "factor": speed} 
                    self.parallax_layers.append(layer_data)
                    if i <= ground_index:
                        self.parallax_layers_back.append(layer_data)
                        if i == ground_index: self.scene_width = new_w
                    else:
                        self.parallax_layers_front.append(layer_data)
                except Exception as e: print(f"[FATAL ERROR] {e}")
        else:
            full_bg_path = os.path.join(cfg.BG_DIR, self.bg_file)
            try: 
                bg_raw = pygame.image.load(full_bg_path).convert()
                aspect_ratio = bg_raw.get_width() / bg_raw.get_height()
                target_w = int(target_h * aspect_ratio)
                if target_w < cfg.CONFIG["GAME_WIDTH"]: target_w = cfg.CONFIG["GAME_WIDTH"]
                bg_final = pygame.transform.scale(bg_raw, (target_w, target_h))
                layer_data = {"image": bg_final, "factor": 1.0}
                self.parallax_layers.append(layer_data)
                self.parallax_layers_back.append(layer_data)
                self.scene_width = target_w
            except:
                fallback = pygame.Surface((cfg.CONFIG["GAME_WIDTH"], cfg.GAME_AREA_HEIGHT)); fallback.fill((50,50,50))
                self.parallax_layers.append({"image": fallback, "factor": 1.0})
                self.parallax_layers_back.append(self.parallax_layers[0])
                self.scene_width = cfg.CONFIG["GAME_WIDTH"]

        if self.lightmap_file:
            path = os.path.join(cfg.BG_DIR, self.lightmap_file)
            try:
                raw_lm = pygame.image.load(path).convert()
                self.lightmap_surface = pygame.transform.scale(raw_lm, (self.scene_width, cfg.GAME_AREA_HEIGHT))
            except: self.lightmap_surface = None
        else: self.lightmap_surface = None

        self.walkable_area = WalkableArea(self.mask_file, self.scene_width, cfg.GAME_AREA_HEIGHT)
        self.walkable_area.load()
        limit_rect = pygame.Rect(0, 0, self.scene_width, cfg.GAME_AREA_HEIGHT)
        self.pathfinder = Pathfinding(self.walkable_area, grid_size=cfg.CONFIG["PATHFINDING_GRID_SIZE"], limit_rect=limit_rect)
        
        self.hotspots.hotspots.empty()
        for data in self.hotspot_data:
            flag = data.get("flag_name")
            if flag and GAME_STATE.get(flag, False): continue            
            d = data.copy()
            label_key = d.get("label_id") 
            if label_key and label_key in cfg.tm.variables["items"]: d["label"] = cfg.tm.get("items", label_key)
            
            if "num_frames" in d:
                nf = d.pop("num_frames") 
                speed = d.pop("anim_speed", 150)
                anim_hs = AnimatedHotspot(num_frames=nf, anim_speed=speed, **d)
                self.hotspots.hotspots.add(anim_hs)
            else: self.hotspots.add_hotspot(**d)

        self.ambient_anims = []
        for d in self.ambient_data:
            flag = d.get("flag_name")
            if flag and not GAME_STATE.get(flag, False): continue
            anim = AmbientAnimation(**d)
            self.ambient_anims.append(anim)

        obs_list = []        
        for hs in self.hotspots.hotspots:
            if getattr(hs, "solid", False): obs_list.append(hs.rect.inflate(10, 10))        
        for anim in self.ambient_anims:
            if anim.solid: obs_list.append(anim.rect.inflate(0, -4))
        self.pathfinder.obstacles = obs_list

    def unload_assets(self):
        self.parallax_layers = [] 
        self.parallax_layers_back = []
        self.parallax_layers_front = []
        if self.walkable_area: self.walkable_area.unload()
        self.pathfinder = None
        self.hotspots.hotspots.empty()
        self.ambient_anims = []
        gc.collect()

    def update_camera(self, target_x, dt):
        screen_w = cfg.CONFIG["GAME_WIDTH"]
        half_screen = screen_w // 2
        target_cam = target_x - half_screen
        max_scroll = self.scene_width - screen_w
        if max_scroll < 0: max_scroll = 0
        target_clamped = max(0, min(target_cam, max_scroll))
        smooth_factor = cfg.CONFIG["CAMERA_SMOOTHING"] * dt
        self.camera_x += (target_clamped - self.camera_x) * smooth_factor
        if abs(self.camera_x - target_clamped) < 0.5: self.camera_x = target_clamped
        if self.auto_scroll_config and self.parallax_layers:
            layer_index, speed = self.auto_scroll_config
            self.auto_scroll_offset_x += speed * dt
            if layer_index < len(self.parallax_layers):
                 layer_width = self.parallax_layers[layer_index]["image"].get_width()
                 self.auto_scroll_offset_x %= layer_width
            
    def draw_sorted_elements(self, screen, character):
        render_list = []        
        char_tint = self.get_lighting_at(character.rect.centerx, character.rect.bottom)
        render_list.append({
            "y": character.rect.bottom, "type": "char",
            "func": lambda: character.draw(screen, self.camera_x, tint_color=char_tint)
        })        

        for hs in self.hotspots.hotspots:
            draw_pos_x = hs.rect.x - int(self.camera_x)
            if -hs.rect.width < draw_pos_x < cfg.CONFIG["GAME_WIDTH"]:
                render_list.append({
                    "y": hs.rect.bottom, "type": "hotspot",
                    "func": lambda img=hs.image, x=draw_pos_x, y=hs.rect.y: screen.blit(img, (x, y))
                })

        for anim in self.ambient_anims:
            if anim.layer == "back":
                draw_pos_x = anim.rect.x - int(self.camera_x)
                if -anim.rect.width < draw_pos_x < cfg.CONFIG["GAME_WIDTH"]:
                    render_list.append({
                        "y": anim.rect.bottom, "type": "ambient",
                        "func": lambda a=anim: a.draw(screen, self.camera_x)
                    })
        
        render_list.sort(key=lambda item: item["y"])        
        for item in render_list: item["func"]()

    def get_hotspot_at_mouse(self, screen_mx, screen_my):
        world_mx = screen_mx + self.camera_x
        for hotspot in self.hotspots.hotspots:
            if hotspot.rect.collidepoint(world_mx, screen_my): return hotspot
        for anim in reversed(self.ambient_anims):
            if anim.label_id and anim.rect.collidepoint(world_mx, screen_my): return anim
        return None
       
    def add_ambient(self, **kwargs): self.ambient_data.append(kwargs)
    def update_ambient(self, dt):
        for anim in self.ambient_anims: anim.update(dt)
    def draw_ambient(self, screen, layer_filter="back"):
        for anim in self.ambient_anims:
            if anim.layer == layer_filter: anim.draw(screen, self.camera_x)
    def get_lighting_at(self, x, y):
        if not self.lightmap_surface: return (255, 255, 255) 
        w, h = self.lightmap_surface.get_size()
        safe_x = max(0, min(int(x), w - 1)); safe_y = max(0, min(int(y), h - 1))        
        return self.lightmap_surface.get_at((safe_x, safe_y))[:3]



class SceneExit:
    def __init__(self, rect, target_scene, spawn_x, spawn_y):
        self.rect = rect
        self.target_scene = target_scene
        self.spawn_point = (spawn_x, spawn_y)



class Hotspot(pygame.sprite.Sprite):
    def __init__(self, name, x, y, width=50, height=50, image_file=None, 
                 scale=1.0, label=None, description=None, actions=None, 
                 primary_verb="LOOK AT", walk_to=None, flag_name=None, 
                 hint_message=None, solid=False, **kwargs):
        super().__init__()
        self.image_file = image_file 
        self.text_color = kwargs.get('text_color', (255, 255, 255))
        
        # 1. LÓGICA DE CARGA DE IMAGEN O SUPERFICIE INVISIBLE
        if image_file:
            loaded_img = RES_MANAGER.get_image(image_file, cfg.HTSPT_DIR)
            if loaded_img: self.original_image = loaded_img
            else: self.original_image = pygame.Surface((width, height)); self.original_image.fill((255, 0, 255))
        else:
            # Si no hay archivo, creamos una superficie transparente (zona invisible)
            self.original_image = pygame.Surface((width, height), pygame.SRCALPHA)
            self.original_image.fill((0, 0, 0, 0))
        
        # 2. ESCALADO
        if scale != 1.0:
            w = int(self.original_image.get_width() * scale)
            h = int(self.original_image.get_height() * scale)
            self.image = pygame.transform.scale(self.original_image, (w, h))
        else: 
            self.image = self.original_image.copy()
            
        # 3. POSICIONAMIENTO DEL RECTÁNGULO (AQUÍ ESTABA EL ERROR)
        self.rect = self.image.get_rect()
        
        if image_file:
            # Si es un objeto con gráfico (personaje, farol), la coordenada es la base (los pies)
            self.rect.midbottom = (x, y)
        else:
            # Si es una zona invisible (ventana), la coordenada es la esquina superior izquierda
            self.rect.topleft = (x, y)

        # 4. RESTO DE PROPIEDADES
        self.name = name
        self.label = label if label else name
        self.description = description
        self.actions = actions if actions else {}
        self.primary_verb = primary_verb
        self.walk_to = walk_to  
        self.flag_name = flag_name
        self.hint_message = hint_message
        self.solid = solid
        self.facing = kwargs.get('facing', None)

    def is_mouse_over(self, mouse_x, mouse_y): return self.rect.collidepoint(mouse_x, mouse_y)



class AnimatedHotspot(Hotspot):
    def __init__(self, num_frames=1, anim_speed=150, **kwargs):
        super().__init__(**kwargs) 
        self.frames = []
        self.current_frame = 0
        self.anim_timer = 0
        self.anim_speed = anim_speed
        self.num_frames = num_frames
        self.locked_frame = None 
        self.is_playing_oneshot = False
        
        if self.original_image and num_frames > 1:
            sheet_w = self.original_image.get_width()
            sheet_h = self.original_image.get_height()
            frame_width = sheet_w // num_frames
            target_scale = kwargs.get('scale', 1.0)
            for i in range(num_frames):
                frame_rect = pygame.Rect(i * frame_width, 0, frame_width, sheet_h)
                frame = self.original_image.subsurface(frame_rect).copy()
                if target_scale != 1.0:
                    w = int(frame.get_width() * target_scale)
                    h = int(frame.get_height() * target_scale)
                    frame = pygame.transform.scale(frame, (w, h))
                self.frames.append(frame)
            self.image = self.frames[0]
            self.rect = self.image.get_rect()
            self.rect.midbottom = (kwargs.get('x'), kwargs.get('y'))
            
    def play_oneshot(self):
        self.is_playing_oneshot = True
        self.current_frame = 0
        self.anim_timer = 0

    def update(self, dt):
        if self.is_playing_oneshot:
            self.anim_timer += dt * 1000
            if self.anim_timer >= self.anim_speed:
                self.anim_timer = 0
                self.current_frame += 1
                if self.current_frame >= self.num_frames:
                    self.is_playing_oneshot = False
                    self.current_frame = 0
                    self.image = self.frames[0]
                else: self.image = self.frames[self.current_frame]
            return 

        is_talking = False
        current_text = cfg.GLOBAL_STATE["screen_text"]
        current_speaker = cfg.GLOBAL_STATE["current_speaker"]
        
        if current_text: 
            if current_speaker == self: is_talking = True
            elif current_speaker is None:
                text_upper = current_text.upper()
                nombre_upper = self.label.upper() if self.label else ""
                if nombre_upper and (nombre_upper + ":") in text_upper: is_talking = True

        if is_talking:
            self.anim_timer += dt * 1000
            if self.anim_timer >= self.anim_speed:
                self.anim_timer = 0
                self.current_frame = (self.current_frame + 1) % self.num_frames
                self.image = self.frames[self.current_frame]
        else:
            if self.locked_frame is not None:
                idx = min(self.locked_frame, len(self.frames) - 1)
                self.image = self.frames[idx]
                self.current_frame = idx
            else:
                self.image = self.frames[0]
                self.current_frame = 0



class AmbientAnimation:
    def __init__(self, x, y, image_file, num_frames=1, anim_speed=150, scale=1.0, layer="back", solid=False, 
                 move_to=None, move_speed=50, loop_move=True, label_id=None, actions=None, walk_to=None):
        self.solid = solid
        self.layer = layer
        self.anim_speed = anim_speed
        self.scale = scale
        self.label_id = label_id
        if self.label_id and self.label_id in cfg.tm.variables["items"]: self.label = cfg.tm.get("items", self.label_id)
        else: self.label = label_id if label_id else "Ambiente"
        self.name = label_id if label_id else "ambient_obj"
        self.actions = actions if actions else {}
        self.primary_verb = "LOOK AT" 
        self.walk_to = walk_to
        self.facing = None
        self.frames = []
        self.current_frame_index = 0
        self.anim_timer = 0
        self.num_frames = num_frames
        
        full_img = RES_MANAGER.get_image(image_file, cfg.HTSPT_DIR)
        if full_img:
            sheet_w = full_img.get_width(); sheet_h = full_img.get_height()
            frame_width = sheet_w // num_frames
            for i in range(num_frames):
                frame_rect = pygame.Rect(i * frame_width, 0, frame_width, sheet_h)
                frame = full_img.subsurface(frame_rect).copy()
                if scale != 1.0:
                    w = int(frame.get_width() * scale); h = int(frame.get_height() * scale)
                    frame = pygame.transform.scale(frame, (w, h))
                self.frames.append(frame)
        else:
            fallback = pygame.Surface((32, 32)); fallback.fill((0, 0, 255)) 
            self.frames.append(fallback)

        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.rect.midbottom = (x, y) 
        self.start_pos = (x, y); self.exact_x = float(self.rect.x); self.exact_y = float(self.rect.y)
        self.target_pos = None; self.move_speed = move_speed; self.loop_move = loop_move; self.direction = (0, 0)
        
        if move_to:
            target_rect = self.rect.copy(); target_rect.midbottom = move_to
            self.target_pos = (target_rect.x, target_rect.y)

    def update(self, dt):
        self.anim_timer += dt * 1000
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0
            self.current_frame_index = (self.current_frame_index + 1) % len(self.frames)
            self.image = self.frames[self.current_frame_index]

        if self.target_pos:
            target_x, target_y = self.target_pos
            dx = target_x - self.exact_x; dy = target_y - self.exact_y
            distance = math.sqrt(dx**2 + dy**2)
            if distance > 1.0:
                dir_x = dx / distance; dir_y = dy / distance
                self.exact_x += dir_x * self.move_speed * dt; self.exact_y += dir_y * self.move_speed * dt
                self.rect.x = int(self.exact_x); self.rect.y = int(self.exact_y)
            else:
                if self.loop_move:
                    self.rect.midbottom = self.start_pos
                    self.exact_x = float(self.rect.x); self.exact_y = float(self.rect.y)
                else: self.target_pos = None

    def draw(self, screen, camera_x):
        draw_x = self.rect.x - int(camera_x)
        if -self.image.get_width() < draw_x < cfg.CONFIG["GAME_WIDTH"]:
            screen.blit(self.image, (draw_x, self.rect.y))



class WalkableArea:
    def __init__(self, mask_file, width, height):
        self.mask_file = mask_file
        self.width = width
        self.height = height
        self.mask = None 
        self.default_mask = pygame.Surface((width, height))
        self.default_mask.fill((255, 255, 255))

    def load(self):
        if self.mask_file:
            path = os.path.join(cfg.BG_DIR, self.mask_file)
            try:
                surface = pygame.image.load(path).convert()
                self.mask = pygame.transform.scale(surface, (self.width, self.height))
            except: self.mask = self.default_mask
        else: self.mask = self.default_mask

    def unload(self): self.mask = None 
            
    def is_walkable(self, x, y):
        target_mask = self.mask if self.mask else self.default_mask
        try:
            if x < 0 or x >= target_mask.get_width() or y < 0 or y >= target_mask.get_height(): return False
            return target_mask.get_at((int(x), int(y)))[0] > 50 
        except: return False



class Pathfinding:
    def __init__(self, walkable_area, grid_size=15, limit_rect=None): 
        self.walkable_area = walkable_area
        self.grid_size = grid_size
        self.limit_rect = limit_rect if limit_rect else pygame.Rect(0,0,800,600)
        self.obstacles = []
        
        # OPTIMIZACIÓN: Guardar el modo en una variable local al iniciar
        self.mode = cfg.CONFIG.get("PATHFINDING_TYPE", "EUCLIDEAN")
    
    def heuristic(self, x1, y1, x2, y2):
        # Usar self.mode es más rápido que consultar el diccionario CONFIG cada vez
        dx = abs(x1 - x2); dy = abs(y1 - y2)
        
        if self.mode == "MANHATTAN": return (dx + dy) * 10
        elif self.mode == "DIAGONAL": return (10 * (dx + dy) + (14 - 2 * 10) * min(dx, dy))
        else: return math.hypot(dx, dy) * 10 # EUCLIDEAN
    
    def is_position_valid(self, x, y):
        if not self.limit_rect.collidepoint(x, y): return False
        for rect in self.obstacles: 
            if rect.collidepoint(x, y): return False 
        return self.walkable_area.is_walkable(x, y)

    def get_neighbors(self, node):
        neighbors = []
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dx, dy in directions:
            new_x = node.x + dx * self.grid_size
            new_y = node.y + dy * self.grid_size
            if self.is_position_valid(new_x, new_y):
                cost = 14 if dx != 0 and dy != 0 else 10
                neighbors.append((new_x, new_y, cost))
        return neighbors
    
    def find_nearest_walkable(self, x, y, max_radius=200, step=None):
        if step is None: step = self.grid_size 
        x = max(self.limit_rect.left, min(x, self.limit_rect.right))
        y = max(self.limit_rect.top, min(y, self.limit_rect.bottom))
        if self.is_position_valid(x, y): return (x, y)
        for r in range(step, max_radius, step):
            points = 8 
            for i in range(points):
                angle = 6.28 * i / points
                check_x = int(x + r * math.cos(angle))
                check_y = int(y + r * math.sin(angle))
                if self.is_position_valid(check_x, check_y): return (check_x, check_y)
        return None

    def find_path(self, start_x, start_y, goal_x, goal_y):
        gx, gy = self.find_nearest_walkable(goal_x, goal_y) or (goal_x, goal_y)
        start_node_pos = (int(start_x // self.grid_size) * self.grid_size, int(start_y // self.grid_size) * self.grid_size)
        goal_node_pos = (int(gx // self.grid_size) * self.grid_size, int(gy // self.grid_size) * self.grid_size)
        start_node = Node(start_node_pos[0], start_node_pos[1])
        goal_node = Node(goal_node_pos[0], goal_node_pos[1])
        if start_node == goal_node: return [(gx, gy)]
        open_list = []; heapq.heappush(open_list, start_node)
        open_dict = {(start_node.x, start_node.y): start_node}
        closed_set = set()
        iterations = 0; max_iterations = 10000 
        while open_list and iterations < max_iterations: 
            iterations += 1
            current = heapq.heappop(open_list)
            if (current.x, current.y) in open_dict: del open_dict[(current.x, current.y)]
            if abs(current.x - goal_node.x) < self.grid_size and abs(current.y - goal_node.y) < self.grid_size:
                path = []
                while current: path.append((current.x, current.y)); current = current.parent
                path = path[::-1]; 
                if path: path[-1] = (gx, gy) 
                return path
            closed_set.add((current.x, current.y))
            for nx, ny, cost in self.get_neighbors(current):
                if (nx, ny) in closed_set: continue
                new_g = current.g + cost
                if (nx, ny) in open_dict and open_dict[(nx, ny)].g <= new_g: continue
                h = self.heuristic(nx, ny, goal_node.x, goal_node.y) * 10
                neighbor = Node(nx, ny, new_g, h, current)
                heapq.heappush(open_list, neighbor)
                open_dict[(nx, ny)] = neighbor
        return None



class Node:
    def __init__(self, x, y, g=0, h=0, parent=None):
        self.x = x; self.y = y; self.g = g; self.h = h; self.f = g + h; self.parent = parent
    def __lt__(self, other): return self.f < other.f
    def __eq__(self, other): return self.x == other.x and self.y == other.y
    def __hash__(self): return hash((self.x, self.y))



class HotspotManager:
    def __init__(self): self.hotspots = pygame.sprite.Group()
    def add_hotspot(self, **kwargs):
        hs = Hotspot(**kwargs)
        self.hotspots.add(hs)
    def get_hotspot_at(self, x, y):
        for hotspot in self.hotspots:
            if hotspot.is_mouse_over(x, y): return hotspot
        return None
    def get_hotspot_by_name(self, name_id):
        for hotspot in self.hotspots:
            if hotspot.name == name_id: return hotspot
        return None
    def draw(self, screen): self.hotspots.draw(screen)



class MapSystem:
    def __init__(self, bg_file):
        self.active = False
        self.nodes = []
        self.current_location_node = None
        self.target_node = None
        self.bg = RES_MANAGER.get_image(bg_file, cfg.BG_DIR)
        
        # Si la imagen de fondo existe, la escalamos al tamaño del juego
        if self.bg:
            self.bg = pygame.transform.scale(self.bg, (cfg.CONFIG["GAME_WIDTH"], cfg.CONFIG["GAME_HEIGHT"]))
        else:
            self.bg = pygame.Surface((cfg.CONFIG["GAME_WIDTH"], cfg.CONFIG["GAME_HEIGHT"]))
            self.bg.fill((200, 200, 200))
        
        self.traveling = False
        self.anim_progress = 0.0 
        self.anim_speed = 1.5 
    
    def add_node(self, scene_id, map_x, map_y, spawn_x, spawn_y, icon_file=None):
        self.nodes.append(MapNode(scene_id, map_x, map_y, spawn_x, spawn_y, icon_file))

    def refresh_map_labels(self):
        """Recarga los textos de los nodos basado en el idioma actual"""
        for node in self.nodes:
            node.label = cfg.tm.get("scenes", node.scene_id)

    def open_map(self, current_scene_id):
        self.active = True
        self.traveling = False
        self.target_node = None
        self.anim_progress = 0.0
        self.refresh_map_labels() 
        
        self.current_location_node = None
        for node in self.nodes:
            if node.scene_id == current_scene_id:
                self.current_location_node = node
                break

    def close_map(self):
        self.active = False

    def handle_click(self, mx, my, scene_manager_ref, player_ref):
        if self.traveling: return 
        
        for node in self.nodes:
            if node.rect.collidepoint(mx, my):
                if node == self.current_location_node:
                    self.close_map()
                else:
                    self.target_node = node
                    self.traveling = True
                    self.anim_progress = 0.0
                return

    def update(self, dt, scene_manager_ref, player_ref):
        if self.traveling and self.target_node:
            self.anim_progress += dt * self.anim_speed
            
            if self.anim_progress >= 1.0:
                self.anim_progress = 1.0
                self.traveling = False
                
                # Efecto ZOOM al viajar
                scene_manager_ref.change_scene_with_effect(
                    self.target_node.scene_id, 
                    self.target_node.spawn,
                    forced_effect=TRANSITION_ZOOM 
                )
                self.close_map()

    def draw(self, screen):
        """Dibuja SOLO los elementos gráficos (fondo, líneas, iconos) en la capa de juego."""
        if not self.active: return
        
        # 1. Dibujar Fondo
        if self.bg: screen.blit(self.bg, (0,0))
        
        # 2. Dibujar Líneas de Trayectoria (Puntos rojos)
        if self.current_location_node and self.target_node:
            start = self.current_location_node.center
            end = self.target_node.center
            total_dist = math.hypot(end[0]-start[0], end[1]-start[1])
            
            if total_dist > 0:
                current_dist = total_dist * self.anim_progress
                steps = int(current_dist / 15)
                for i in range(steps + 1):
                    t = i * 15 / total_dist
                    if t > self.anim_progress: break
                    px = start[0] + (end[0] - start[0]) * t
                    py = start[1] + (end[1] - start[1]) * t
                    pygame.draw.circle(screen, (200, 0, 0), (int(px), int(py)), 4)

        # 3. Dibujar Nodos (Iconos o Círculos)
        for node in self.nodes:
            if node.image:
                img_rect = node.image.get_rect(center=node.center)
                screen.blit(node.image, img_rect)
                if node == self.target_node:
                    pygame.draw.rect(screen, (255, 0, 0), img_rect, 2)
            else:
                color = (0, 150, 0) if node == self.current_location_node else (0, 0, 0)
                if node == self.target_node: color = (200, 0, 0)
                pygame.draw.circle(screen, color, node.center, 8)
                pygame.draw.circle(screen, (255, 255, 255), node.center, 8, 2)
        
        # NOTA: Hemos quitado el dibujado de texto de aquí.
    # EN classes.py -> class MapSystem

    def draw_text_hd(self):
        """Dibuja los textos en Alta Resolución sobre la ventana final."""
        if not self.active: return
        
        # Configuración de colores
        text_color = (50, 50, 50)       
        shadow_color = (200, 200, 200) 
        
        for node in self.nodes:
            # --- CÁLCULO DE POSICIÓN ---
            txt_x = node.center[0] + 15
            
            # ANTES ESTABA: node.center[1] - 8
            # CAMBIO: Sumamos pixels para BAJAR el texto. 
            # Prueba con +5 o +10 según tu gusto.
            txt_y = node.center[1] + 1   #estaba a +5
            
            # 1. Sombra
            draw_text_sharp(
                text=node.label, 
                virtual_x=txt_x + 1, 
                virtual_y=txt_y + 1, 
                base_size=20,  # 24 es muy grande
                color=shadow_color, 
                align="topleft" # Alineado a la esquina superior izquierda del texto
            )
            
            # 2. Texto Principal
            draw_text_sharp(
                text=node.label, 
                virtual_x=txt_x, 
                virtual_y=txt_y, 
                base_size=20, # 24 es muy grande
                color=text_color, 
                align="topleft"
            )
