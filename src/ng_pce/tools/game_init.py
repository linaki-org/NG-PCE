"""A little tool to init a game directory by creating necessary files and folders"""

import os
from importlib.resources import files as res_files

def make_dir(root_dir, dir_to_make):
    directory=os.path.join(root_dir, dir_to_make)
    if os.path.exists(directory):
        raise FileExistsError(f"Cannot init {directory}, directory already exists")
    else:
        os.makedirs(directory)

def write_cfg(root_dir, cfg_file, cfg_resource):
    filepath=os.path.join(root_dir, cfg_file)
    if os.path.exists(filepath):
        raise FileExistsError(f"Cannot init {filepath}, configuration file already exists")
    cfg_resource=res_files("ng_pce.tools.templates") / cfg_resource
    with open(filepath, "w") as f:
        f.write(cfg_resource.read_text())

def write_bytes(root_dir, cfg_file, cfg_resource):
    filepath=os.path.join(root_dir, cfg_file)
    if os.path.exists(filepath):
        raise FileExistsError(f"Cannot init {filepath}, file already exists")
    cfg_resource=res_files("ng_pce.tools.templates") / cfg_resource
    with open(filepath, "wb") as f:
        f.write(cfg_resource.read_bytes())

def init_game(directory: str):
    print(f"Initializing a game in {directory}")
    print("Making directories...")
    make_dir(directory, "scripts")
    make_dir(directory, "snd")
    make_dir(directory, "assets/bg")
    make_dir(directory, "assets/htspt")
    make_dir(directory, "assets/items")
    make_dir(directory, "assets/obj")
    make_dir(directory, "lang")
    make_dir(directory, "save")
    make_dir(directory, "cursor")
    make_dir(directory, "dist")

    print("Making CFG files...")
    write_cfg(directory, "game.cfg", "game.cfg")
    write_cfg(directory, "chars.cfg", "chars.cfg")
    write_cfg(directory, "gstate.cfg", "gstate.cfg")
    write_cfg(directory, "ui.cfg", "ui.cfg")
    write_cfg(directory, "credits.txt", "credits.txt")
    write_cfg(directory, "lang/en.yaml", "lang.yaml")
    write_bytes(directory, "arial.ttf", "arial.ttf")



