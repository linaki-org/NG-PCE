import engine as ng_pce

ng_pce.load_scripts("game/scripts")   # Load scripts in debug mode
# ng_pce.load_bundles("bundles/")   # Load bundles in release mode
ng_pce.mainloop()