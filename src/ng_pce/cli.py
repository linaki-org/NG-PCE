import typer
from .tools.game_init import init_game, new_room
from .tools.voiceify import voiceify_patch
from .tools.reloader import start_reloader
#from .tools.fluf import open_room_editor

app=typer.Typer()


@app.command()
def run():
    """Run the game present in the working directory"""
    print("Trying to run game from working directory...")
    import ng_pce.engine as engine
    engine.init()
    engine.load_scripts("scripts")
    engine.mainloop()

@app.command()
def debug():
    """Run the game in debug mode (reload automatically when scripts changes)"""
    print("Trying to run game from working directory...")
    import ng_pce.engine as engine
    engine.cfg.debug_enabled = True
    engine.init()
    engine.load_scripts("scripts")
    reloader=start_reloader(engine, "scripts")
    engine.mainloop()

@app.command()
def bundle(directory: str):
    """Bundle assets, sound or scripts into a single file for distribution"""
    print("Bundle has not yet been implemented as a CLI feature")

@app.command()
def build(config: str = None):
    """Build the game entirely, using build.conf if provided"""
    print("Build feature has not yet been implemented")

@app.command()
def init(directory: str):
    """Init a game directory with all the necessary files and folders"""
    init_game(directory)

@app.command()
def voiceify(language: str):
    """Generate voices from a language patch using ElevenLabs TTS API"""
    voiceify_patch(language)

@app.command()
def fluf(fluf_type: str):
    """Open the FLUF editor for the specified entity"""
    if fluf_type not in ["room", "cost"]:
        print("Unknown FLUF type. FLUF type must be one of: room; cost")
    if fluf_type=="room":
        #open_room_editor()
        print("FLUF is unavailable in the current version of NG-PCE. Please upgrade to use it.")

@app.command()
def new(entity: str, entity_id: str):
    """Create a new entity of the desired type with the desired ID"""
    if entity not in ["room"]:
        print("Unknown entity type. Entity must be one of: room")
    if entity=="room":
        new_room(entity_id)

if __name__ == "__main__":
    app()