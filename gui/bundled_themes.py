"""Install bundled Alien icon themes without overwriting user themes."""
from pathlib import Path
import shutil

THEMES = (
    "X-ARCH-Alien-Contact",
    "X-ARCH-Alien-Crimson",
    "X-ARCH-Alien-Arctic",
    "X-ARCH-Alien-Violet",
    "X-ARCH-Alien-Amber",
    "X-ARCH-Alien-Toxic",
)

def install_missing(source, destination):
    source = Path(source)
    destination = Path(destination)
    installed = []
    for name in THEMES:
        src = source / name
        dst = destination / name
        if not (src / "index.theme").is_file():
            continue
        if dst.exists() or dst.is_symlink():
            continue
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst)
        installed.append(name)
    return installed
