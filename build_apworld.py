"""Package the world as opuc1.apworld (a zip of the world folder)."""
import pathlib
import zipfile

ROOT = pathlib.Path(__file__).parent
WORLD = ROOT / "opuc1"
OUT = ROOT / "opuc1.apworld"
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for path in sorted(WORLD.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            z.write(path, path.relative_to(ROOT).as_posix())
print(f"Wrote {OUT.name}")
