"""The Script_loader is in charge to load the parsed scripts to the game"""

from ng_pce.classes import Scene, SceneExit, TRANSITION_FADE, TRANSITION_SLIDE_LEFT, TRANSITION_SLIDE_UP, TRANSITION_ZOOM, \
    String
from ng_pce.config import GLOBAL_STATE, GAME_AREA_HEIGHT
from ng_pce.pcscript.dataclasses import (Scene as dc_Scene,
                                  Hotspot as dc_Hotspot,
                                  Exit as dc_Exit,
                                  DynamicValue as dc_dynamic,
                                  ObjAction as dc_Action,
                                  Ambient as dc_Ambient)
import ng_pce.config as cfg
import ng_pce.engine.script_runner as runner
#Transitions ID definitions
TRANSITIONS = {"fade" : TRANSITION_FADE,
               "slide_left" : TRANSITION_SLIDE_LEFT,
               "slide_up" : TRANSITION_SLIDE_UP,
               "zoom" : TRANSITION_ZOOM}

GLOBAL_VARS=["GAME_AREA_HEIGHT", "LOOKAT", "WALK", "OPEN", "PUSH", "CLOSE", "PULL", "PICKUP", "USE", "TALKTO", "GIVE", "BACK", "true", "false",
             "LEFT", "RIGHT"]

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
BACK="back"
true=True
false=False
LEFT="left"
RIGHT="right"

TRIGGER_VERBS={"lookat": LOOKAT,
               "walk": WALK,
               "open": OPEN,
               "push": PUSH,
               "close" : CLOSE,
               "pull": PULL,
               "pickup" : PICKUP,
               "use" : USE,
               "talkto" : TALKTO,
               "give" : GIVE}

GP_ACTIONS={"say" : "texto",
            "sound" : "play_sound",
            "flag" : "flag",
            "delitem" : "delete_item",
            "anim" : "anim",
            "duration" : "text_time",
            "speaker" : "speaker"}

ALL_ACTIONS=["say", "sound", "flag", "delitem", "anim", "duration", "speaker", "start_dialogue", "run"]

def getprop(property):
    """Utility to automatically turn variable expressions (E.g scenes or translations) into their value"""
    if not isinstance(property, dc_dynamic): #Property is a regular value, return it as is
        return property
    if property.value in GLOBAL_VARS: #Property is an accessible global variable
        return globals()[property.value]

    #Cannot find any match, raise an error
    raise NameError(f"Cannot find anything matching the expression {property.value}")



def dynalink(property):
    """Make sure the property is a dynamic value and return the reference to the object"""
    if not isinstance(property, dc_dynamic):
        raise TypeError(f"Argument {property} cannot be a string; a dynamic reference value is required")
    return property.value

def load_scripts(scripts, deps):
    """Load provided scripts into the game"""
    global action_manager

    #Unpack provided ugly dependencies
    scene_manager = deps["scene_manager"]
    action_manager = deps["action_manager"]

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

        if isinstance(object, dc_Ambient):
            load_ambient(object, scene_manager)

def check_properties(props, required_props, all_props, object_name):
    """Check if all required properties are present and all properties exists"""
    for prop in props:
        if prop not in all_props:
            raise NameError(f"Unknown property {prop} for {object_name}. Available props are {','.join(all_props)}")

    for prop in required_props:
        if prop not in props:
            raise TypeError(f"Missing required property {prop} for {object_name}")


def run_action_funcs(funcs_to_call):
    for func in funcs_to_call:
        func()


def generate_action_lambda(actions):
    if len(actions)==1 and actions[0].action=="say":  # Action is a simple say command
        return String(actions[0].arg, "descs", cfg.tm)

    #Generate list of functions to call
    funcs_to_call=[]
    for action in actions:
        if isinstance(action, dc_Action):
            if action.action not in ALL_ACTIONS:
                raise NameError(f"Action {action.action} was not found")
            if action.action in GP_ACTIONS:
                if action.action in ["say"]:
                    action_value=String(action.arg, "descs", cfg.tm)
                    funcs_to_call.append(lambda: action_manager.text_event(action_value))
                if action.action in ["anim"]:
                    action_value=dynalink(action.arg)
                    funcs_to_call.append(lambda: action_manager.play_object_animation(action_value))
                if action.action in ["flag"]:
                    action_value=dynalink(action.arg)
                    funcs_to_call.append(lambda: action_manager.flag_event(action_value))
                if action.action in ["del"]:
                    action_value=dynalink(action.arg)
                    funcs_to_call.append(lambda: action_manager.delitem_event(action_value))

    return lambda: run_action_funcs(funcs_to_call)


def translate_event_trigger(trigger):
    """Turn a Trigger object into a trigger string"""
    if trigger.verb not in TRIGGER_VERBS:
        raise NameError(f"Trigger {trigger.verb} doesn't exist")
    verb=TRIGGER_VERBS.get(trigger.verb)
    if not trigger.target1: #Event is a simple verb
         return verb
    else: #Event has a target
        trigger_key=f"{verb}_{trigger.target1.upper()}_ON_{trigger.target2.upper()}"
        return trigger_key


def generate_actions(actions_defs):
    actions={}
    for event in actions_defs:
        trigger=translate_event_trigger(event.trigger)
        action=generate_action_lambda(event.body)
        actions[trigger]=action

    return actions


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
        if not dynalink(transition_id) or transition_id.value not in TRANSITIONS:
            raise NameError(f"Unknown transition {transition_id} for scene {scene.name}. Transition ID needs to be one of {', '.join(TRANSITIONS.keys())}")
        args["transition_type"]=TRANSITIONS[transition_id.value]


    scene=Scene(**args) #Create the scene with generated args
    scene_manager.add_scene(scene)


def load_hotspot(hotspot, scene_manager):
    props = hotspot.properties
    required_properties = ["x", "y"]
    all_properties = ["x", "y", "width", "height", "img", "scale", "label", "frames", "speed",
                      "label", "description", "verb", "walk_x", "walk_y", "hint", "solid", "flag", "facing"]
    check_properties(props, required_properties, all_properties, hotspot.name)

    # Generate args dict for hotspot definition
    args = {}
    args["name"] = hotspot.name
    args["x"] = props["x"]
    args["y"]=props["y"]

    if "img" in props:
        args["image_file"] = props["img"]
    if "label" in props:
        args["label"] = String(props["label"], "items", cfg.tm)
    if "hint" in props:
        args["hint_message"] = String(props["hint"], "descs", cfg.tm)
    if "scale" in props:
        args["scale"] = props["scale"]
    if "walk_x" in props and "walk_y" in props:
        args["walk_to"] = (props["walk_x"], props["walk_y"])
    if "description" in props:
        args["description"] = String(props["description"], "descs", cfg.tm)
    if "verb" in props:
        args["primary_verb"] = getprop(props["verb"])
    if "flag" in props:
        args["flag"] = dynalink(props["flag"])
    if "frames" in props:
        args["num_frames"] = props["frames"]
    if "speed" in props:
        args["anim_speed"] = props["speed"]
    if "solid" in props:
        args["solid"] = getprop(props["solid"])
    if "facing" in props:
        args["facing"] = getprop(props["facing"])

    if hotspot.scene not in scene_manager.scenes:
        raise NameError(f"Scene {hotspot.scene} doesn't exist for hotspot {hotspot.name}")

    #Generate action calls for this HS
    actions=generate_actions(hotspot.events)
    args["actions"]=actions

    scene = scene_manager.scenes.get(hotspot.scene)  # Retrieve the scene where the hotspot lives
    scene.add_hotspot_data(**args) #Create the hotspot data in the scene


def load_exit(exit, scene_manager):
    props = exit.properties
    required_properties = ["x", "y", "w", "h", "target", "spawn_x", "spawn_y"]
    all_properties = required_properties
    check_properties(props, required_properties, all_properties, exit.name)

    # Generate args dict for exit definition
    args = {}
    args["x"] = props["x"]
    args["y"]=props["y"]
    args["w"]=getprop(props["w"])
    args["h"]=getprop(props["h"])
    args["target_scene"]=dynalink(props["target"])
    args["spawn_x"]=props["spawn_x"]
    args["spawn_y"]=props["spawn_y"]

    if exit.scene not in scene_manager.scenes:
        raise NameError(f"Scene {exit.scene} doesn't exist for exit {exit.name}")

    scene = scene_manager.scenes.get(exit.scene)  # Retrieve the scene where the exit lives
    scene.add_exit(**args) #Create the exit data in the scene

def load_ambient(ambient, scene_manager):
    props = ambient.properties
    required_properties = ["x", "y", "img"]
    all_properties = ["x", "y", "img", "frames", "speed", "scale", "label", "layer", "solid",
                      "moveto_x", "moveto_y", "move_speed", "loop", "label", "walk_x", "walk_y"]
    check_properties(props, required_properties, all_properties, ambient.name)

    # Generate args dict for hotspot definition
    args = {}
    #args["name"] = ambient.name
    args["x"] = props["x"]
    args["y"]=props["y"]
    args["image_file"] = props["img"]
    if "label" in props:
        args["label_id"] = String(props["label"], "items", cfg.tm)
    if "hint" in props:
        args["hint_message"] = String(props["hint"], "descs", cfg.tm)
    if "scale" in props:
        args["scale"] = props["scale"]
    if "walk_x" in props and "walk_y" in props:
        args["walk_to"] = (props["walk_x"], props["walk_y"])
    if "moveto_x" in props and "moveto_y" in props:
        args["move_to"] = (props["moveto_x"], props["moveto_y"])
    if "frames" in props:
        args["num_frames"] = props["frames"]
    if "speed" in props:
        args["anim_speed"] = props["speed"]
    if "solid" in props:
        args["solid"] = getprop(props["solid"])
    if "facing" in props:
        args["facing"] = getprop(props["facing"])
    if "loop" in props:
        args["loop_move"] = getprop(props["loop"])

    if ambient.scene not in scene_manager.scenes:
        raise NameError(f"Scene {ambient.scene} doesn't exist for ambient {ambient.name}")

    #Generate action calls for this HS
    #actions=generate_actions(hotspot.events)
    #args["actions"]=actions

    scene = scene_manager.scenes.get(ambient.scene)  # Retrieve the scene where the hotspot lives
    scene.add_ambient(**args) #Create the hotspot data in the scene
