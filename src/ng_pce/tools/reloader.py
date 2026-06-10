"""A simple system to detect whenever game scripts changes to reload the game with the new scripts"""
import threading
import os
import hashlib
from time import sleep

reloader_thread=None

class Reloader(threading.Thread):
    def __init__(self, engine, scripts_dir, check_delay=1.5):
        threading.Thread.__init__(self)
        self.engine=engine
        self.scripts_dir=scripts_dir
        self.hashes=self.hash_directory()
        self.check_delay=check_delay
        print(f"Hashes in {scripts_dir} :", self.hashes)

    def hash_directory(self):
        hashes = []
        for file in os.listdir(self.scripts_dir):
            filepath=os.path.join(self.scripts_dir, file)
            with open(filepath, "r") as f:
                file_hash=hash(f.read())
                hashes.append(file_hash)
        return hashes


    def has_dir_changed(self):
        old_hashes=self.hashes.copy()
        new_hashes=self.hash_directory()
        self.hashes = new_hashes
        if len(new_hashes) != len(old_hashes):
            return True
        for new, old in zip(new_hashes, old_hashes):
            if new != old:
                return True
        return False

    def run(self):
        while self.engine.running: #Little 'hack' to stop reloader automatically on game close
            sleep(self.check_delay)
            if self.has_dir_changed():
                print("Game scripts have changed, reloading the engine")
                self.engine.logic_save_game("debug_reload.json")  # Save current game state
                print("Reiniting")
                self.engine.init_managers()  # Re-init game engine
                print("Reloading")
                self.engine.load_scripts(self.scripts_dir)  # Reload game scripts
                self.engine.logic_load_game("debug_reload.json")  # Load saved game state



def start_reloader(engine, scripts_dir):
    global reloader_thread
    reloader_thread=Reloader(engine, scripts_dir)
    reloader_thread.start()