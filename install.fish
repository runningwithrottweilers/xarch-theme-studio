#!/usr/bin/env fish
# X-ARCH Theme Studio 0.1.0-beta
# Install only into unused paths. Never overwrite or delete user files.

set -l root (cd (dirname (status filename)); and pwd -P)
or exit 1

set -l mode standard
if test (count $argv) -gt 1
    echo 'Usage: fish install.fish [--test]'
    exit 2
end
if test (count $argv) -eq 1
    if test "$argv[1]" != '--test'
        echo "Unknown argument: $argv[1]"
        exit 2
    end
    set mode test
end

if test "$mode" = test
    set -l prefix "$root/.install-test"
    set bindir "$prefix/bin"
    set datadir "$prefix/share/xarch-theme-studio"
    set desktopdir "$prefix/share/applications"
    set icondir "$prefix/share/icons/hicolor/256x256/apps"
    set launcher "$prefix/run-test.fish"
else
    set bindir "$HOME/.local/bin"
    set datadir "$HOME/.local/share/xarch-theme-studio"
    set desktopdir "$HOME/.local/share/applications"
    set icondir "$HOME/.local/share/icons/hicolor/256x256/apps"
end

set -l bin "$bindir/xarch-theme-studio"
set -l desktop "$desktopdir/xarch-theme-studio.desktop"
set -l icon "$icondir/xarch-theme-studio.png"

echo "=== X-ARCH THEME STUDIO 0.1.0-BETA ==="
echo "MODE: $mode"

for tool in cargo python3 desktop-file-validate
    if not command -q $tool
        echo "ERROR: Missing dependency: $tool"
        exit 1
    end
end

for source in "$root/Cargo.toml" "$root/gui/studio.py" "$root/gui/theme_import.py" "$root/gui/assets/rottweilers.png"
    if not test -f "$source"
        echo "ERROR: Missing source: $source"
        exit 1
    end
end

# Reject conflicts before building or creating installation directories.
for destination in "$bin" "$datadir" "$desktop" "$icon"
    if test -e "$destination"; or test -L "$destination"
        echo "STOP: Destination already exists: $destination"
        exit 1
    end
end
if test "$mode" = test
    if test -e "$prefix"; or test -L "$prefix"
        echo "STOP: Test directory already exists: $prefix"
        exit 1
    end
end

cd "$root"; or exit 1
cargo build --release; or exit 1
python3 -c 'import ast,pathlib; ast.parse(pathlib.Path("gui/studio.py").read_text()); import gi; gi.require_version("Gtk", "4.0"); from gi.repository import Gtk'
or exit 1

# Stage application data before exposing a launcher.
mkdir -p "$bindir" "$desktopdir" "$icondir"; or exit 1
mkdir "$datadir"; or exit 1
cp -a "$root/gui" "$datadir/gui"; or exit 1
install -m 755 "$root/target/release/xarch-theme-studio" "$bin"; or exit 1
cp "$root/gui/assets/rottweilers.png" "$icon"; or exit 1

if test "$mode" = test
    printf '%s\n' \
        '#!/usr/bin/env fish' \
        "set -gx XARCH_BACKEND \"$bin\"" \
        "python3 \"$datadir/gui/studio.py\"" > "$launcher"
    or exit 1
    chmod 755 "$launcher"; or exit 1
    set exec_command "fish $launcher"
else
    set exec_command "$bin gui"
end

printf '%s\n' \
    '[Desktop Entry]' \
    'Type=Application' \
    'Name=X-ARCH Theme Studio' \
    'Comment=Visual icon theme manager' \
    "Exec=$exec_command" \
    "Icon=$icon" \
    'Terminal=false' \
    'Categories=Settings;' > "$desktop"
or exit 1

desktop-file-validate "$desktop"; or exit 1

if test "$mode" = standard
    if command -q update-desktop-database
        update-desktop-database "$desktopdir"
    end
end

echo 'INSTALLATION COMPLETED'
echo "BIN: $bin"
echo "GUI: $datadir/gui"
echo "DESKTOP: $desktop"
echo "ICON: $icon"
