"""A little wrapper for .PCB bundles, used to store basically all game data, including scripts, assets and language patches"""
import struct
from pathlib import Path

MAGIC = b"NGPCE.gameBundle.v1"

def create_bundle(output_file, files):
    with open(output_file, "wb") as f:
        f.write(MAGIC)

        # Number of assets
        f.write(struct.pack("<I", len(files)))

        index_entries = []
        data_offset = 8  # magic + count

        # Calculate index size
        for name, path in files.items():
            name_bytes = name.encode("utf-8")
            size = Path(path).stat().st_size

            index_entries.append((name_bytes, size))
            data_offset += 2 + len(name_bytes) + 8 + 8

        current_offset = data_offset

        # Write index
        for (name_bytes, size), (_, path) in zip(index_entries, files.items()):
            f.write(struct.pack("<H", len(name_bytes)))
            f.write(name_bytes)
            f.write(struct.pack("<Q", current_offset))
            f.write(struct.pack("<Q", size))

            current_offset += size

        # Write data
        for path in files.values():
            with open(path, "rb") as asset:
                f.write(asset.read())