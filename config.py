import os
import json

# Los definimos aquí vacíos para poder importarlos desde classes.py y main.py
ITEM_NAMES = {}
OBJ_DESCS = {}
SCENE_NAMES = {}
GAME_MSGS = {}
SOUNDS = {}
MENU_TEXTS = {}
TITLE_TEXTS = {}
VERBS_LOCALIZED = {}
VERB_KEYS = []
CINE_TEXTS = {}      # También suele ser necesario compartir cinemáticas
DIALOGUE_TEXTS = {}  # También suele ser necesario compartir diálogos

GAME_DIR="game"
ASSETS_DIR="game/assets"
SND_DIR="game/snd"
LANG_DIR="game/languages"
CURSOR_DIR="game/cursor"
SAVE_DIR="game/saves"
ITEMS_DIR="game/assets/items"
BG_DIR="game/assets/backgrounds"
HTSPT_DIR="game/assets/hotspots"
OBJ_DIR="game/assets/objects"


with open(os.path.join(GAME_DIR, "game_config.json")) as config_file:
    CONFIG = json.load(config_file)

DEFAULT_LANG_FILE=CONFIG["DEFAULT_LANGUAGE"]+".yaml"

with open(os.path.join(GAME_DIR, "char_config.json")) as char_config_file:
    char_config=json.load(char_config_file)
    PLAYER_CONFIG=char_config["PLAYER"]
    CHAR_DEFS=char_config["CHARACTERS"]

with open(os.path.join(GAME_DIR, "ui_config.json")) as ui_config_file:
    UI_CONFIG=json.load(ui_config_file)

with open(os.path.join(GAME_DIR, "game_state.json")) as gstate_config_file:
    GAME_STATE=json.load(gstate_config_file)


with open(os.path.join(GAME_DIR, "game_credits.txt")) as credits_file:
    CREDITS_TEXT = credits_file.read()


TEXT_CONFIG = UI_CONFIG["TEXT_STYLE"]
UI_FONT_PATH=TEXT_CONFIG["FONT_NAME"]

# ================================================
# DO NOT TOUCH
# ================================================
UI_HEIGHT = CONFIG["TEXTBOX_HEIGHT"] + CONFIG["VERB_MENU_HEIGHT"] + CONFIG["BOTTOM_MARGIN"]
GAME_AREA_HEIGHT = CONFIG["GAME_HEIGHT"] - UI_HEIGHT

# Fill DIALOGUE_STYLE entries if set to auto
if UI_CONFIG["DIALOGUE_STYLE"]["AREA_Y"]=="auto":
    UI_CONFIG["DIALOGUE_STYLE"]["AREA_Y"]=GAME_AREA_HEIGHT

if UI_CONFIG["DIALOGUE_STYLE"]["AREA_HEIGHT"]=="auto":
    UI_CONFIG["DIALOGUE_STYLE"]["AREA_HEIGHT"]=UI_HEIGHT

GLOBAL_STATE = {
    "screen_text": "",    # Texto actual en pantalla
    "current_speaker": None, # Quién está hablando
    "current_lang_file": CONFIG["DEFAULT_LANGUAGE"]
}

STEP_TYPES = {
    "step": "step.ogg",
    "step_wood": "step_wood.ogg",
    "step_grass": "step_grass.ogg",
    "step_rug": "step_rug.ogg"
}

