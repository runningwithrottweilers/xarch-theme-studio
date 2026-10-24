"""Safe local installer for downloaded freedesktop icon themes (directories, zip, tar)."""
from pathlib import Path
import os
import re
import shutil
import stat
import tarfile
import tempfile
import zipfile

ALLOWED = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,90}$")

def valid_theme(path):
    path = Path(path)
    if not path.is_dir() or not (path / "index.theme").is_file():
        return False
    # Icon packs use 16x16, scalable etc; do not accept empty placeholder directories.
    return any(p.is_file() and p.suffix.lower() in (".svg", ".png", ".xpm") for p in path.rglob("*"))

def _extract(archive, target):
    archive = Path(archive)
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as z:
            members = z.infolist()
            if len(members) > 25000 or sum(m.file_size for m in members) > 700 * 1024 * 1024:
                raise ValueError("Archiwum jest zbyt duże")
            for info in members:
                path = Path(info.filename)
                mode = (info.external_attr >> 16)
                if path.is_absolute() or ".." in path.parts or stat.S_ISLNK(mode):
                    raise ValueError("Niebezpieczna ścieżka w ZIP")
                dest = target / path
                if info.is_dir():
                    dest.mkdir(parents=True, exist_ok=True)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with z.open(info) as src, dest.open("wb") as out:
                        shutil.copyfileobj(src, out)
    elif tarfile.is_tarfile(archive):
        with tarfile.open(archive) as t:
            members = t.getmembers()
            if len(members) > 25000 or sum(m.size for m in members) > 700 * 1024 * 1024:
                raise ValueError("Archiwum jest zbyt duże")
            for info in members:
                path = Path(info.name)
                if path.is_absolute() or ".." in path.parts or not (info.isfile() or info.isdir()):
                    raise ValueError("Niedozwolony element archiwum TAR")
                dest = target / path
                if info.isdir():
                    dest.mkdir(parents=True, exist_ok=True)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with t.extractfile(info) as src, dest.open("wb") as out:
                        shutil.copyfileobj(src, out)
    else:
        raise ValueError("Obsługiwane archiwa: ZIP, TAR, TAR.GZ, TAR.XZ, TAR.ZST (jeśli Python obsługuje)")

def discover(source):
    source = Path(source)
    return [p for p in [source, *source.rglob("index.theme")] if valid_theme(p if p.is_dir() else p.parent)]

def install(source, destination, backups):
    source, destination, backups = Path(source), Path(destination), Path(backups)
    with tempfile.TemporaryDirectory(prefix="xarch-import-") as temp:
        base = Path(temp)
        if source.is_dir():
            # Copy into temporary staging so source isn't mutated
            shutil.copytree(source, base / source.name, symlinks=False)
        else:
            _extract(source, base)
        found = []
        for entry in base.rglob("index.theme"):
            folder = entry.parent
            if valid_theme(folder) and ALLOWED.fullmatch(folder.name):
                found.append(folder)
        if not found:
            raise ValueError("Nie znaleziono poprawnego motywu z index.theme i ikonami")
        destination.mkdir(parents=True, exist_ok=True)
        backups.mkdir(parents=True, exist_ok=True)
        installed = []
        for folder in found:
            name = folder.name
            target = destination / name
            if target.exists():
                from datetime import datetime
                stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
                shutil.copytree(target, backups / f"{name}-before-import-{stamp}", symlinks=False)
                shutil.rmtree(target)
            shutil.copytree(folder, target, symlinks=False)
            installed.append(name)
        return installed
