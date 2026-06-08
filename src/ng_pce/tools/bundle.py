"""A little wrapper for .PCB bundles, used to store basically all game data, including scripts, assets and language patches.
A PCB Bundle is simply a tiny sqlite3 database."""
import sqlite3
import os
import time


CREATE_META_TABLE = "CREATE TABLE metadata (id INT PRIMARY KEY, parameter varchar(32), value varchar(1024))"
CREATE_ASSETS_TABLE = "CREATE TABLE assets (id INT PRIMARY KEY, type int, data BLOB);"
CREATE_SCRIPTS_TABLE = "CREATE TABLE scripts (id INT PRIMARY KEY, script text);"
CREATE_DEF_TABLE = "CREATE TABLE defs (id INT PRIMARY KEY, def_type int, properties text)"


class Bundle:
    def __init__(self):
        self.cnx=None
        return
        if os.path.exists(filename):
            self.load_bundle(filename)
        else:
            self.create_bundle(filename)

    def connect_bundle(self, filename):
        self.cnx = sqlite3.connect(filename)

    def sql_query(self, query, args=None, commit=False):
        cur = self.cnx.cursor()
        if isinstance(args, list):  # there are several args
            res = cur.executemany(query, args)
        elif args:
            res = cur.execute(query, args)
        else:
            res = cur.execute(query)

        data = res.fetchall()

        if commit:
            self.cnx.commit()
        cur.close()
        return data

    def load_bundle(self, filename):
        self.connect_bundle(filename)

    def create_bundle(self, filename):
        if os.path.exists(filename):
            print("[BUNDLE] Bundle already exists, deleting old one")
            os.remove(filename)
        self.connect_bundle(filename)
        self.sql_query(CREATE_ASSETS_TABLE, commit=True)
        self.sql_query(CREATE_SCRIPTS_TABLE, commit=True)
        self.sql_query(CREATE_DEF_TABLE, commit=True)

    def close(self):
        if self.cnx:
            self.cnx.close()

    def add_asset(self, filename, asset_type=1, asset_id=None):
        if not asset_id:
            asset_id=hash(filename)
        with open(filename, "rb") as asset_file:
            ablob = asset_file.read()
            self.sql_query("INSERT INTO assets (id, type, data) VALUES(?, ?, ?)",
                           (asset_id, asset_type, sqlite3.Binary(ablob)), commit=True)

    def list_assets(self, type=None):
        if not type:
            assets = self.sql_query("select id from assets")
        else:
            assets = self.sql_query("select id from assets where type=?", (type,))
        return assets

    def get_asset(self, asset_id):
        response = self.sql_query("select data from assets where id=?", (asset_id,))
        if not response:
            raise KeyError(f"Asset {asset_id} doesn't exist in game bundle")
        blob = response[0][0]
        return blob

if __name__=="__main__":
    bundle=Bundle()
    bundle.load_bundle("../game/releases/TENTACLE")
    """bundle.create_bundle("../game/releases/GARBA")
    for i, filename in enumerate(os.listdir("../game/assets/backgrounds")):
        try:
            bundle.add_asset("../game/assets/backgrounds/"+filename, 1, i+1)
        except PermissionError:
            print("Permission denied")
    lastI=i+1

    for i, filename in enumerate(os.listdir("../game/assets/hotspots")):
        try:
            bundle.add_asset("../game/assets/hotspots/"+filename, 1, i+lastI+1)
        except PermissionError:
            print("Permission denied")"""
    assets = bundle.list_assets()
    print(assets)

    start = time.time()
    asset_data=bundle.get_asset(11628)
    end = time.time()
    print(f"Queried one asset in {float(end - start).__round__(5)} seconds")

    start=time.time()
    with open("../game/releases/asset.png", "wb") as f:
        f.write(bundle.get_asset(11628))
    end = time.time()
    print(f"Retrieved one asset in {(end - start).__round__(5)} seconds")

    start=time.time()
    with open("../game/releases/asset.png", "rb") as f:
        asset_data=f.read()
    end=time.time()
    print(f"Loaded one asset file in {(end - start).__round__(5)} seconds")

    print("ZIP test")

    import zipfile

    with zipfile.ZipFile("../game/releases/TENTACLE.zip") as zip:
        start = time.time()
        asset_data=zip.read("room 067.png")
        end=time.time()
    print(f"Loaded one asset file in {(end - start).__round__(5)} seconds")



    bundle.close()