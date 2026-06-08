import typer

app=typer.Typer()


@app.command()
def run():
    """Run the game present in the working directory"""
    print("Trying to run game from working directory...")
    import ng_pce.engine as engine
    engine.load_scripts("game/scripts")
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
def init():
    """Init a game directory with all the necessary files and folders"""
    print("Init feature has not yet been implemented")

if __name__ == "__main__":
    app()