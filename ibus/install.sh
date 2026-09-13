#!/bin/sh
# Install the Nepali Transliterate IBus engine (system-wide).
# After installing: ibus restart (or log out/in), then add it in
#   GNOME: Settings -> Keyboard -> Input Sources -> + -> Nepali
#   KDE/others: ibus-setup -> Input Method -> Add -> Nepali
# Switch EN <-> NP with Super+Space (GNOME default).
set -eu
SRC="$(cd "$(dirname "$0")/.." && pwd)"
DEST=/usr/share/ibus-nepali-transl
echo "installing to $DEST (needs root)..."
sudo mkdir -p "$DEST"
sudo cp -r "$SRC/core" "$DEST/"
sudo cp "$SRC/ibus/ibus-engine-nepali-transl" "$DEST/"
sudo chmod +x "$DEST/ibus-engine-nepali-transl"
sudo mkdir -p /usr/share/ibus/component
sudo cp "$SRC/ibus/nepali_translit.xml" /usr/share/ibus/component/
echo "done. Now run: ibus restart"
echo "then add 'Nepali Transliterate' under the Nepali section."
