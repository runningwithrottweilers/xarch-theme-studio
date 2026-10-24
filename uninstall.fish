#!/usr/bin/env fish

if test (count $argv) -ne 1; or test "$argv[1]" != "--test"
    echo "Uzycie: fish uninstall.fish --test"
    echo "Standardowa instalacja nie jest obslugiwana."
    exit 2
end

set -l root (cd (dirname (status filename)); and pwd -P)
set -l prefix "$root/.install-test"
set -l bin "$prefix/bin/xarch-theme-studio"
set -l gui "$prefix/share/xarch-theme-studio/gui"
set -l desktop "$prefix/share/applications/xarch-theme-studio.desktop"
set -l icon "$prefix/share/icons/hicolor/256x256/apps/xarch-theme-studio.png"
set -l launcher "$prefix/run-test.fish"

if not test -d "$prefix"
    echo "Brak instalacji testowej."
    exit 0
end

for path in "$bin" "$gui/studio.py" "$gui/theme_import.py" "$desktop" "$icon" "$launcher"
    if not test -f "$path"; or test -L "$path"
        echo "STOP: Niekompletna lub nietypowa instalacja: $path"
        exit 1
    end
end

if not grep -Fq "$bin" "$launcher"
    echo "STOP: Launcher nie wskazuje testowego backendu."
    exit 1
end

if not grep -Fq "Exec=fish $launcher" "$desktop"
    echo "STOP: Skrot nie wskazuje testowej binarki."
    exit 1
end

echo "Instalacja testowa zostala rozpoznana."

set -l backups "$HOME/.local/state/xarch-theme-studio/uninstalled-tests"
set -l stamp (date +%Y%m%d-%H%M%S)
set -l destination "$backups/uninstalled-test-$stamp"

mkdir -p "$backups"
or exit 1

if test -e "$destination"
    echo "STOP: Katalog docelowy juz istnieje."
    exit 1
end

mv -- "$prefix" "$destination"
or exit 1

echo "INSTALACJA TESTOWA PRZENIESIONA DO BACKUPU"
echo "BACKUP: $destination"
