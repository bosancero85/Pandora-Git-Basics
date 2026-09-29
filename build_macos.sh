#!/usr/bin/env bash
# ============================================================
#  Pandora Git Basics - lokaler Build fuer macOS
#  Ergebnis: Pandora-Git-Basics-Mac.dmg
#  Ausfuehren im Repo-Hauptordner (neben pandora_git_basics.py): ./build_macos.sh
#  Falls noetig zuerst: chmod +x build_macos.sh
# ============================================================
set -euo pipefail
cd "$(dirname "$0")"

ENTRY_FILE="pandora_git_basics.py"
APP_NAME="Pandora-Git-Basics"
ICON_ICO="pandora_git_basics_icon.ico"
ICON_PNG="pandora_git_basics_icon.png"
ICON_PNG_256="pandora_git_basics_icon_256.png"
VENV=".build-venv"

echo "[1/6] Startdatei, Sprach-Plugin und Icons prüfen ..."
for f in "$ENTRY_FILE" "$ICON_ICO" "$ICON_PNG" "$ICON_PNG_256" language_plugin; do
  test -e "$f" || { echo "FEHLER: Datei/Ordner fehlt im Repo-Hauptordner: $f"; exit 1; }
done

echo "[2/6] Virtuelle Umgebung einrichten ..."
command -v python3 >/dev/null || { echo "FEHLER: python3 nicht gefunden (Python 3.11 empfohlen)."; exit 1; }
[ -d "$VENV" ] || python3 -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"

echo "[3/6] Abhängigkeiten installieren ..."
python -m pip install --upgrade pip
# Pillow wandelt das PNG-Icon für PyInstaller automatisch in .icns um
pip install pyinstaller pillow
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

echo "[4/6] Import-Test ..."
QT_QPA_PLATFORM=offscreen python -c "import pandora_git_basics; print('Import ok')" \
  || { echo "FEHLER: Import-Test fehlgeschlagen. Programmfehler zuerst beheben."; exit 1; }

echo "[5/6] App bauen ..."
pyinstaller --windowed --noconfirm \
  --name "$APP_NAME" \
  --icon "$ICON_PNG" \
  --osx-bundle-identifier "de.pandora.gitbasics" \
  --add-data "language_plugin/language_packs:language_plugin/language_packs" \
  --hidden-import language_plugin.language_manager \
  "$ENTRY_FILE"

echo "[6/6] DMG erstellen ..."
rm -f "Pandora-Git-Basics-Mac.dmg"
hdiutil create -volname "Pandora Git Basics" \
  -srcfolder "dist/$APP_NAME.app" \
  -ov -format UDZO "Pandora-Git-Basics-Mac.dmg"

test -f "Pandora-Git-Basics-Mac.dmg" || { echo "FEHLER: DMG wurde nicht erzeugt."; exit 1; }
echo
echo "Fertig: Pandora-Git-Basics-Mac.dmg"
echo "Hinweis: Die App ist nicht signiert. Beim ersten Start: Rechtsklick -> Öffnen."
