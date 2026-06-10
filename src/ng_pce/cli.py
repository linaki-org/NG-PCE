import typer
from .tools.game_init import init_game
from .tools.voiceify import voiceify_patch
from .tools.reloader import start_reloader

app=typer.Typer()


@app.command()
def run():
    """Run the game present in the working directory"""
    print("Trying to run game from working directory...")
    import ng_pce.engine as engine
    engine.load_scripts("scripts")
    engine.mainloop()

@app.command()
def debug():
    """Run the game in debug mode (reload automatically when scripts changes)"""
    print("Trying to run game from working directory...")
    import ng_pce.engine as engine
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

if __name__ == "__main__":
    app()