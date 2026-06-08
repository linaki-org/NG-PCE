VALID_COMMANDS=["init", "run", "build", "bundle"]

def main(args):
    if len(args)<=1:
        print(cli_help)
        return
    cmd=args[1]
    if cmd not in VALID_COMMANDS: # Command doesn't exists
        print(f"Invalid command '{cmd}'")

    if cmd == "run":  # Run command
        print("Trying to run game from working directory...")
        import engine
        engine.load_scripts("game/scripts")
        engine.mainloop()


import sys

if __name__=="__main__":
    main(sys.argv)