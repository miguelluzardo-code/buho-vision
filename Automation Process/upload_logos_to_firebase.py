"""
Sube todos los logos de ligas desde Google Drive local a Firebase Storage.
Corre UNA SOLA VEZ (o cuando agregues nuevos escudos).

Requiere: gcloud auth application-default login
"""
import sys
import os
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, storage

BUCKET = "buhovision-5bee4.appspot.com"
STORAGE_PREFIX = "logos"

LEAGUES_MAP = {
    "Liga Kings":               "01_Liga_Kings",
    "Liga Celeste":             "02_Liga_Celeste",
    "Liga Lokura":              "04_Liga_Lokura",
    "Piria Seven":              "05_Piria_Seven_League",
    "Liga MVD":                 "06_Liga_MVD",
    "Liga Nexo Futbol":         "07_Liga_Nexo_Futbol",
    "Liga Femenina Basketball": "08_Liga_Femenina_Basketball",
    "Liga Solo Futbol":         "09_Liga_Solo_Futbol",
    "Liga PRO":                 "12_Liga_PRO",
    "Liga OFI":                 "13_Liga_OFI",
    "Liga LVH":                 "14_Liga_LVH",
}

def get_ligas_base():
    candidates = [
        Path("/Users/miguelluzardo/Library/CloudStorage/GoogleDrive-miguelluzardo@gmail.com/Mi unidad/ProShot/LIGAS"),
        Path("G:/Mi unidad/ProShot/LIGAS"),
    ]
    for p in candidates:
        if p.exists():
            return p
    raise RuntimeError("No se encontró la carpeta de LIGAS")

def main():
    print("Iniciando Firebase Storage...")
    app = firebase_admin.initialize_app(options={"storageBucket": BUCKET})
    bucket = storage.bucket()
    print(f"Conectado a bucket: {bucket.name}")

    ligas_base = get_ligas_base()
    print(f"Base LIGAS: {ligas_base}")

    total_uploaded = 0
    total_skipped  = 0
    EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".svg"}

    for league_name, folder in LEAGUES_MAP.items():
        escudos_dir = ligas_base / folder / "01_Escudos"
        if not escudos_dir.exists():
            print(f"  [SKIP] {league_name}: no existe {escudos_dir}")
            continue

        files = [f for f in escudos_dir.iterdir() if f.suffix.lower() in EXTENSIONS]
        print(f"\n{league_name}: {len(files)} archivos")

        for f in files:
            dest = f"{STORAGE_PREFIX}/{folder}/01_Escudos/{f.name}"
            blob = bucket.blob(dest)
            # Skip if already uploaded (check exists)
            if blob.exists():
                total_skipped += 1
                continue
            mime = "image/png" if f.suffix.lower() == ".png" else "image/jpeg"
            blob.upload_from_filename(str(f), content_type=mime)
            blob.make_public()
            total_uploaded += 1
            print(f"  + {f.name}")

    print(f"\nListo: {total_uploaded} subidos, {total_skipped} ya existian")
    print(f"URL base: https://storage.googleapis.com/{BUCKET}/{STORAGE_PREFIX}/")

if __name__ == "__main__":
    main()
