import os
import yaml
from gettext import translation

# Los definimos aquí vacíos para poder importarlos desde classes.py y main.py

SOUNDS = {}


GAME_DIR="."
ASSETS_DIR="./assets"
SND_DIR="./snd"
LANG_DIR="./lang"
CURSOR_DIR="./cursor"
SAVE_DIR="./save"
ITEMS_DIR="./assets/items"
BG_DIR="./assets/bg"
HTSPT_DIR="./assets/htspt"
OBJ_DIR="./assets/obj"
VOICE_DIR="./voice/en"

config_filename=os.path.join(GAME_DIR, "game.cfg")
if not os.path.exists(config_filename):
    raise FileNotFoundError("Cannot find game.cfg file in the game directory")

with open(config_filename) as config_file:
    CONFIG = yaml.safe_load(config_file)

DEFAULT_LANG_FILE=CONFIG["DEFAULT_LANGUAGE"]+".yaml"


char_config_filename=os.path.join(GAME_DIR, "chars.cfg")
if not os.path.exists(char_config_filename):
    raise FileNotFoundError("Cannot find chars.cfg file in the game directory")

with open(char_config_filename) as char_config_file:
    char_config=yaml.safe_load(char_config_file)
    PLAYER_CONFIG=char_config["PLAYER"]
    CHAR_DEFS=char_config["CHARACTERS"]


ui_config_filename=os.path.join(GAME_DIR, "ui.cfg")
if not os.path.exists(ui_config_filename):
    raise FileNotFoundError("Cannot find ui.cfg file in the game directory")

with open(ui_config_filename) as ui_config_file:
    UI_CONFIG=yaml.safe_load(ui_config_file)


gstate_config_filename=os.path.join(GAME_DIR, "gstate.cfg")
if not os.path.exists(gstate_config_filename):
    raise FileNotFoundError("Cannot find gstate.cfg file in the game directory")

with open(gstate_config_filename) as gstate_config_file:
    GAME_STATE=yaml.safe_load(gstate_config_file)


credits_filename=os.path.join(GAME_DIR, "credits.txt")
if not os.path.exists(credits_filename):
    print("Game credits file not found, defaulting to engine credits")
    CREDITS_TEXT="NG-PCE Engine by @Linaki.0rg & Contributors"
else:
    with open(credits_filename) as credits_file:
        CREDITS_TEXT = credits_file.read()


TEXT_CONFIG = UI_CONFIG["TEXT_STYLE"]
VERB_STYLE= UI_CONFIG["VERB_STYLE"]
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

tm=None

