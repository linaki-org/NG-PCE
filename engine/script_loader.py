"""The Script_loader is in charge to load the parsed scripts to the game"""

from classes import Scene, SceneExit, TRANSITION_FADE, TRANSITION_SLIDE_LEFT, TRANSITION_SLIDE_UP, TRANSITION_ZOOM, \
    String
from config import GLOBAL_STATE, GAME_AREA_HEIGHT
from pcscript.dataclasses import Scene as dc_Scene, Hotspot as dc_Hotspot, Exit as dc_Exit, DynamicValue as dc_dynamic
import config as cfg
#Transitions ID definitions
TRANSITIONS = {"fade" : TRANSITION_FADE,
               "slide_left" : TRANSITION_SLIDE_LEFT,
               "slide_up" : TRANSITION_SLIDE_UP,
               "zoom" : TRANSITION_ZOOM}

GLOBAL_VARS=["GAME_AREA_HEIGHT", "LOOKAT", "WALK", "OPEN", "PUSH", "CLOSE", "PULL", "PICKUP", "USE", "TALKTO", "GIVE"]
LOOKAT="LOOK AT"
WALK="WALK"
OPEN="OPEN"
PUSH="PUSH"
CLOSE="CLOSE"
PULL="PULL"
PICKUP="PICK UP"
USE="USE"
TALKTO="TALK TO"
GIVE="GIVE"

def getprop(property):
    """Utility to automatically turn variable expressions (E.g scenes or translations) into their value"""
    if not isinstance(property, dc_dynamic): #Property is a regular value, return it as is
        return property
    if property.value in GLOBAL_VARS: #Property is an accessible global variable
        return globals()[property.value]

    #Cannot find any match, raise an error
    raise NameError(f"Cannot find anything matching the expression {property.value}")


def objprop(property):
    if not isinstance(property, dc_dynamic):
        return property
    return property.value

def load_scripts(scripts, deps):
    """Load provided scripts into the game"""

    #Unpack provided ugly dependencies
    scene_manager = deps["scene_manager"]
    player = deps["player"]
    inventory = deps["inventory"]
    game_play_event = deps["game_play_event"]
    play_scene_music = deps["play_scene_music"]
    stop_scene_music = deps["stop_scene_music"]
    cutscene_manager = deps["cutscene_manager"]
    dialogue_system = deps["dialogue_system"]
    map_system = deps["map_system"]
    ending_manager = deps["ending_manager"]
    GAME_STATE = deps["GAME_STATE"]
    PLAYER_CONFIG = deps["PLAYER_CONFIG"]

    # Logic funcs
    smart_move_to = deps["smart_move_to"]
    execute_hotspot_action = deps["execute_hotspot_action"]
    change_player_active = deps["change_player_active"]
    crafting = deps["crafting"]
    play_object_animation = deps["play_object_animation"]
    change_state_object = deps["change_state_object"]
    load_and_open_map = deps["load_and_open_map"]

    #First, load only scenes
    for object in scripts:
        if isinstance(object, dc_Scene):
            load_scene(object, scene_manager)

    #Then, load all the rest
    for object in scripts:
        if isinstance(object, dc_Hotspot):
            load_hotspot(object, scene_manager)

        if isinstance(object, dc_Exit):
            load_exit(object, scene_manager)

def check_properties(props, required_props, all_props, object_name):
    """Check if all required properties are present and all properties exists"""
    for prop in props:
        if prop not in all_props:
            raise NameError(f"Unknown property {prop} for {object_name}")

    for prop in required_props:
        if prop not in props:
            raise TypeError(f"Missing required property {prop} for {object_name}")

def load_scene(scene, scene_manager):
    props=scene.properties
    required_properties=["name", "bg_img"]
    all_properties=["name", "bg_img", "walk_img", "scale_min", "scale_max",
                    "y_min", "y_max", "transition", "step_snd", "lightmap", "is_dark"]
    check_properties(props, required_properties, all_properties, scene.name)

    #Generate args dict for scene definition
    args={}
    args["scene_id"] = scene.name
    args["background_image_path"] = props["bg_img"]
    args["name"] = String(props["name"], "scenes", cfg.tm)
    if "walk_img" in props:
        args["walkable_mask_file"] = props["walk_img"]
    if "scale_min" in props and "scale_max" in props:
        args["scale_range"] = (props["scale_min"], props["scale_max"])
    if "y_min" in props and "y_max" in props:
        args["y_range"] = (props["y_min"], props["y_max"])
    if "transition" in props:
        transition_id = props["transition"]
        if not isinstance(transition_id, dc_dynamic) or transition_id.value not in TRANSITIONS:
            raise NameError(f"Unknown transition {transition_id} for scene {scene.name}. Transition ID needs to be one of {', '.join(TRANSITIONS.keys())}")
        args["transition_type"]=TRANSITIONS[transition_id.value]

    scene=Scene(**args) #Create the scene with generated args
    scene_manager.add_scene(scene)


def load_hotspot(hotspot, scene_manager):
    props = hotspot.properties
    required_properties = ["x", "y"]
    all_properties = ["x", "y", "width", "height", "img", "scale", "label",
                      "label", "description", "verb", "walk_x", "walk_y", "hint", "solid", "flag"]
    check_properties(props, required_properties, all_properties, hotspot.name)

    # Generate args dict for hotspot definition
    args = {}
    args["name"] = hotspot.name
    args["x"] = props["x"]
    args["y"]=props["y"]

    if "img" in props:
        args["image_file"] = props["img"]
    if "label" in props:
        args["label_id"] = String(props["label"], "items", cfg.tm)
    if "hint" in props:
        args["hint_message"] = String(props["hint"], "hints", cfg.tm)
    if "scale" in props:
        args["scale"] = props["scale"]
    if "walk_x" in props and "walk_y" in props:
        args["walk_to"] = (props["walk_x"], props["walk_y"])
    if "description" in props:
        args["description"] = String(props["description"], "descs", cfg.tm)
    if "verb" in props:
        args["primary_verb"] = getprop(props["verb"])

    if hotspot.scene not in scene_manager.scenes:
        raise NameError(f"Scene {hotspot.scene} doesn't exist for hotspot {hotspot.name}")

    scene = scene_manager.scenes.get(hotspot.scene)  # Retrieve the scene where the hotspot lives
    scene.add_hotspot_data(**args) #Create the hotspot data in the scene

def load_exit(exit, scene_manager):
    props = exit.properties
    print(props)
    required_properties = ["x", "y", "w", "h", "target", "spawn_x", "spawn_y"]
    all_properties = required_properties
    check_properties(props, required_properties, all_properties, exit.name)

    # Generate args dict for exit definition
    args = {}
    args["x"] = props["x"]
    args["y"]=props["y"]
    args["w"]=getprop(props["w"])
    args["h"]=getprop(props["h"])
    args["target_scene"]=objprop(props["target"])
    args["spawn_x"]=props["spawn_x"]
    args["spawn_y"]=props["spawn_y"]

    if exit.scene not in scene_manager.scenes:
        raise NameError(f"Scene {exit.scene} doesn't exist for exit {exit.name}")

    scene = scene_manager.scenes.get(exit.scene)  # Retrieve the scene where the exit lives
    scene.add_exit(**args) #Create the exit data in the scene