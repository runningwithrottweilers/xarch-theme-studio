import hashlib
import shutil
from pathlib import Path

THEMES = (
    "X-ARCH-Alien-Contact",
    "X-ARCH-Alien-Crimson",
    "X-ARCH-Alien-Arctic",
    "X-ARCH-Alien-Violet",
    "X-ARCH-Alien-Amber",
    "X-ARCH-Alien-Toxic",
)

ORIGINAL_HASHES = {
    "X-ARCH-Alien-Amber": "71ce2d5d86c0809184765c33f9eb1fa12352bd428dad46761d283ab34068cfff",
    "X-ARCH-Alien-Arctic": "5bc00ea41be649d50437395cd69c2130c07d0d1640b8a37645cadbf43b5bbf35",
    "X-ARCH-Alien-Contact": "5c545b7ba2bc89985720480c0cf5213b6f4948e0b50300f3afb0b2645bf0784a",
    "X-ARCH-Alien-Crimson": "177da1085fb71c98330de6d9872ab5c6c79ccb3927c6cc8a7a45b3a5f8cccf20",
    "X-ARCH-Alien-Toxic": "b5c5e8cd46f39c2afb59688f7b0cbcb9e4e7e5fb71032f2fbdea576d5a28b2ab",
    "X-ARCH-Alien-Violet": "bc1bd9d769b30c7f993cb78ef91e67018e75b12d4ae049cb5758107e319d97b5",
}

ORIGINAL_INDEX_HASHES = {'X-ARCH-Alien-Amber': '5b550c239bfb155e400f34b34b08a5c88edc5e7121761944874356c0e50209af', 'X-ARCH-Alien-Arctic': '4d7fcb69a2a42c9fabef94c6ad94612f595907be25ee589595f6d40aac469b64', 'X-ARCH-Alien-Contact': '70143527f84057a9532efa15686debed94177fe0cf27ced12b60bff1aa736607', 'X-ARCH-Alien-Crimson': 'bb1e6f25e2a42cf6bc2d6b5566fd0b9eb8a21a98318fc49967bfb52d3c1242dd', 'X-ARCH-Alien-Toxic': '97d4814bd85b40ad84b819dfee7becf1a3b899eea9941530ab8d667438b4d525', 'X-ARCH-Alien-Violet': 'dd459ecf7f31d28fd137958027df2ccfb9cd96de69ac68ab039a0f2762ed8fd8'}

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def install_missing(source, destination):
    source = Path(source)
    destination = Path(destination)
    installed = []
    for name in THEMES:
        src = source / name
        dst = destination / name
        if not (src / "index.theme").is_file():
            continue
        if dst.is_symlink():
            continue
        if not dst.exists():
            destination.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dst)
            installed.append(name)
            continue
        if not dst.is_dir():
            continue
        folder = dst / "scalable/places/folder.svg"
        alias = dst / "scalable/places/inode-directory.svg"
        if folder.is_file() and not folder.is_symlink() and not alias.exists() and not alias.is_symlink():
            if sha256(folder) == ORIGINAL_HASHES[name]:
                shutil.copy2(folder, alias)
        index = dst / "index.theme"
        if not index.is_file() or index.is_symlink():
            continue
        old = index.read_text(encoding="utf-8")
        old_line = "Directories=scalable/places"
        if sha256(index) != ORIGINAL_INDEX_HASHES[name]:
            continue
        if old.count(old_line) != 1:
            continue
        if "[scalable/apps]" in old or "[scalable/mimetypes]" in old:
            continue
        updated = old.replace(old_line, "Directories=scalable/places,scalable/apps,scalable/mimetypes", 1)
        updated = updated.rstrip() + "\n\n[scalable/apps]\nSize=64\nType=Scalable\nMinSize=16\nMaxSize=512\nContext=Applications\n\n[scalable/mimetypes]\nSize=64\nType=Scalable\nMinSize=16\nMaxSize=512\nContext=MimeTypes\n"
        backup = index.with_name("index.theme.xarch-v011-backup")
        if backup.exists() or backup.is_symlink():
            continue
        shutil.copy2(index, backup)
        index.write_text(updated, encoding="utf-8")
    return installed
