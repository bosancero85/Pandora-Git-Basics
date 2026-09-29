# Pandora® The Basics of git

Interaktives Git-Cheatsheet als Desktop-Anwendung (PyQt6): 182 Befehle in 16 Kategorien, mit Suche,
Ein-Klick-Kopieren und Profi-Tipps. Läuft komplett offline und in 10 Sprachen.

Landingpage: https://bosancero85.github.io/Pandora-Git-Basics/

## Funktionen

- **182 Befehle in 16 Kategorien**: Setup, Grundlagen, Branching, Verlauf, Stash und Reset, Remote, Tags, Fortgeschrittenes, Ignore und Clean, Patches, Submodule, Hooks, Wartung, LFS, Spezialwerkzeuge und Plumbing
- **Suche** nach Stichworten wie `rebase`, `stash` oder `commit`
- **Kopieren mit einem Klick** in die Zwischenablage
- **Profi-Tipps** zu vielen Befehlen (89 von 182)
- **10 Sprachen** mit Umschaltung ohne Neustart: Deutsch, English, Español, Français, Italiano, Русский, Türkçe, Bosanski, Македонски, Shqip
- Die gewählte Sprache wird gespeichert und beim nächsten Start wiederhergestellt

Der Befehlskatalog ist auf Deutsch und Englisch vollständig übersetzt. In den übrigen acht Sprachen ist die
Oberfläche übersetzt, Befehlstexte erscheinen dort auf Deutsch.

## Downloads

Die fertigen Programme liegen unter **Releases**:

| System  | Datei                                |
|---------|--------------------------------------|
| Windows | `Pandora-Git-Basics-Win.exe`         |
| macOS   | `Pandora-Git-Basics-Mac.dmg`         |
| Linux   | `Pandora-Git-Basics-Linux.AppImage`  |

Die Programme sind nicht signiert. Unter Windows kann SmartScreen warnen, unter macOS hilft
Rechtsklick → Öffnen, unter Linux vorher `chmod +x Pandora-Git-Basics-Linux.AppImage`.

Die ausführliche Schritt-für-Schritt-Hilfe steht in [anleitung.md](anleitung.md).

## Aus dem Quellcode starten

Voraussetzung: Python 3.10 oder neuer. Der Ordner `language_plugin/` muss neben
`pandora_git_basics.py` liegen.

```bash
git clone https://github.com/bosancero85/Pandora-Git-Basics.git
cd Pandora-Git-Basics
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python pandora_git_basics.py
```

## Selbst bauen

Die Build-Skripte liegen im Hauptordner neben `pandora_git_basics.py` und brauchen Python 3.11.
Jedes Skript baut nur für das System, auf dem es läuft.

| System  | Befehl               | Ergebnis                             |
|---------|----------------------|--------------------------------------|
| Windows | `build_windows.bat`  | `dist\Pandora-Git-Basics-Win.exe`    |
| macOS   | `./build_macos.sh`   | `Pandora-Git-Basics-Mac.dmg`         |
| Linux   | `./build_linux.sh`   | `Pandora-Git-Basics-Linux.AppImage`  |

## Automatischer Release über GitHub

Tag pushen, z. B. `git tag v0.1.0 && git push origin v0.1.0`. Der Workflow
`.github/workflows/release.yml` baut alle drei Dateien und hängt sie an das Release.
Ohne Tag lässt er sich unter Actions → *Build & Release Pandora Git Basics* → *Run workflow*
manuell starten; die Dateien liegen dann als Artifacts am Lauf.

## Neue Sprache hinzufügen

Eine Datei `language_plugin/language_packs/<code>_<LAND>/<code>.json` mit einem `_meta`-Block
(`code`, `name`, `flag`) anlegen. Die Sprache erscheint automatisch unter Einstellungen.
Für gebaute Programme muss danach neu gebaut werden.

## Lizenz

MIT, siehe `LICENCE`.
