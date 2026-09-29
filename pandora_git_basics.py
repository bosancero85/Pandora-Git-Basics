#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pandora® The Basics of git
============================
Ein umfassendes, interaktives Git-Cheatsheet als PyQt6 Desktop-Anwendung.

Architektur:
    - LanguageManager    : lädt die 10 Sprachpakete aus language_plugin/language_packs/
    - GitDataManager     : Datenhaltung aller Git-Kategorien/Befehle (ID-basiert, sprachneutral)
    - SidebarNavigation  : Vertikale Kategorie-Navigation inkl. Einstellungen-Button
    - CommandCard        : Wiederverwendbare Befehls-Karte mit Copy-Funktion
    - SettingsDialog     : Eigene Einstellungs-Ansicht mit Sprachauswahl (Hot-Reload)
    - MainWindow         : Hauptfenster, Such-Logik, Stack-Steuerung

Mehrsprachigkeit (10 Sprachen: de, en, es, fr, it, ru, tr, bs, mk, sq):
    - Sprachauswahl unter "⚙️ Einstellungen" in der Sidebar.
    - Hot-Reload: ein Klick auf eine Sprache übersetzt die komplette
      Oberfläche sofort, ganz ohne Neustart der Anwendung.
    - Die gewählte Sprache wird dauerhaft gespeichert
      (~/.config/pandora_git_basics/settings.json) und beim nächsten
      Start automatisch wiederhergestellt.
    - Der komplette Befehlskatalog (182 Befehle) ist auf Deutsch und
      Englisch vollständig übersetzt. Für die übrigen 8 Sprachen ist
      aktuell die komplette Oberfläche (Menüs, Einstellungen, Kategorien)
      übersetzt; fehlende Katalog-Übersetzungen fallen automatisch und
      ohne Fehler auf Deutsch zurück (LanguageManager-Fallback).

Ausführen:
    python pandora_git_basics.py

Voraussetzung:
    pip install PyQt6
"""

import sys
import os
import json
from dataclasses import dataclass, field
from typing import List, Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QObject
from PyQt6.QtGui import QFont, QIcon, QGuiApplication
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QFrame,
    QSizePolicy,
    QSpacerItem,
    QGraphicsDropShadowEffect,
    QDialog,
)

# Erlaubt den Import von language_plugin/, egal von wo das Skript gestartet wird.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from language_plugin.language_manager import LanguageManager  # noqa: E402


# ---------------------------------------------------------------------------
#  SPRACH-SYSTEM (10 Sprachen, Hot-Reload, persistente Auswahl)
# ---------------------------------------------------------------------------

SETTINGS_PATH = os.path.join(
    os.path.expanduser("~"), ".config", "pandora_git_basics", "settings.json"
)


def _load_saved_language() -> Optional[str]:
    """Liest die zuletzt gewählte Sprache aus der Konfigurationsdatei."""
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            return data.get("language")
    except (OSError, json.JSONDecodeError):
        return None


def save_language(code: str) -> None:
    """Speichert die aktuell gewählte Sprache dauerhaft (überlebt einen Neustart)."""
    try:
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as fh:
            json.dump({"language": code}, fh)
    except OSError:
        pass  # Persistenz ist ein Komfortfeature - ein Schreibfehler darf die App nicht stören.


class _LanguageBus(QObject):
    """Globaler Signal-Bus: informiert alle offenen Widgets über einen Sprachwechsel (Hot-Reload)."""

    changed = pyqtSignal()


LANG_BUS = _LanguageBus()
LM = LanguageManager(default_language="de")

_saved_lang = _load_saved_language()
if _saved_lang:
    LM.set_language(_saved_lang)


def set_active_language(code: str) -> bool:
    """Wechselt die Sprache, speichert die Wahl und löst den Hot-Reload aller Widgets aus."""
    if LM.set_language(code):
        save_language(code)
        LANG_BUS.changed.emit()
        return True
    return False


# ---------------------------------------------------------------------------
#  DATENMODELL
# ---------------------------------------------------------------------------

@dataclass
class GitCommand:
    """Repräsentiert einen einzelnen Git-Befehl.

    Titel, Beschreibung und Tipp sind KEINE festen Strings mehr, sondern
    werden bei jedem Zugriff live aus dem aktiven Sprachpaket (LM) über die
    ID nachgeschlagen. Das ist die Grundlage für den Hot-Reload: nach einem
    Sprachwechsel liefern dieselben Objekte sofort neue Texte, ohne dass
    die Datenstruktur neu aufgebaut werden muss.
    """
    id: str  # z. B. "setup.benutzername_festlegen" -> Übersetzungsschlüssel-Präfix
    command: str  # Git-Syntax bleibt unübersetzt (Code-Beispiel)
    has_tip: bool = False

    @property
    def title(self) -> str:
        return LM.tr(f"cmd.{self.id}.title")

    @property
    def description(self) -> str:
        return LM.tr(f"cmd.{self.id}.description")

    @property
    def tip(self) -> Optional[str]:
        if not self.has_tip:
            return None
        return LM.tr(f"cmd.{self.id}.tip")


@dataclass
class GitCategory:
    """Repräsentiert eine Kategorie von Git-Befehlen. Das Label wird live übersetzt."""
    key: str
    icon: str
    commands: List[GitCommand] = field(default_factory=list)

    @property
    def label(self) -> str:
        return LM.tr(f"category.{self.key}.label")


class GitDataManager:
    """
    Zentrale Datenhaltung für alle Git-Kategorien und Befehle.
    Stellt strukturierte Daten für Sidebar, Content-Bereich und Suche bereit.
    """

    def __init__(self):
        self.categories: List[GitCategory] = self._build_data()

    # ------------------------------------------------------------------
    def _build_data(self) -> List[GitCategory]:
        return [
            GitCategory(
                key='setup',
                icon='⚙️',
                commands=[
                    GitCommand('setup.benutzername_festlegen', 'git config --global user.name "Dein Name"', has_tip=True),
                    GitCommand('setup.e_mail_adresse_festlegen', 'git config --global user.email "du@example.com"', has_tip=True),
                    GitCommand('setup.konfiguration_anzeigen', 'git config --list', has_tip=True),
                    GitCommand('setup.globale_config_bearbeiten', 'git config --global --edit', has_tip=False),
                    GitCommand('setup.ssh_schlussel_generieren', 'ssh-keygen -t ed25519 -C "du@example.com"', has_tip=True),
                    GitCommand('setup.standard_editor_setzen', 'git config --global core.editor "code --wait"', has_tip=True),
                    GitCommand('setup.standard_branch_name', 'git config --global init.defaultBranch main', has_tip=False),
                    GitCommand('setup.zeilenenden_normalisieren', 'git config --global core.autocrlf input', has_tip=True),
                    GitCommand('setup.alias_anlegen', 'git config --global alias.co checkout', has_tip=True),
                    GitCommand('setup.git_version_prufen', 'git --version', has_tip=False),
                ],
            ),
            GitCategory(
                key='basics',
                icon='🚀',
                commands=[
                    GitCommand('basics.repository_initialisieren', 'git init', has_tip=False),
                    GitCommand('basics.repository_klonen', 'git clone <url>', has_tip=True),
                    GitCommand('basics.status_prufen', 'git status', has_tip=True),
                    GitCommand('basics.datei_stagen', 'git add <datei>', has_tip=False),
                    GitCommand('basics.alle_anderungen_stagen', 'git add .', has_tip=True),
                    GitCommand('basics.interaktiv_stagen', 'git add -p', has_tip=True),
                    GitCommand('basics.commit_erstellen', 'git commit -m "Aussagekräftige Nachricht"', has_tip=True),
                    GitCommand('basics.letzten_commit_korrigieren', 'git commit --amend -m "Neue Nachricht"', has_tip=True),
                    GitCommand('basics.datei_umbenennen_verschieben', 'git mv <alt> <neu>', has_tip=False),
                    GitCommand('basics.datei_aus_git_entfernen', 'git rm <datei>', has_tip=True),
                    GitCommand('basics.anderungen_pushen', 'git push origin main', has_tip=False),
                    GitCommand('basics.anderungen_pullen', 'git pull origin main', has_tip=True),
                    GitCommand('basics.remote_hinzufugen', 'git remote add origin <url>', has_tip=False),
                    GitCommand('basics.alle_anderungen_stagen_inkl_geloschte', 'git add -A', has_tip=True),
                    GitCommand('basics.stagen_und_committen_in_einem_schritt', 'git commit -am "Nachricht"', has_tip=True),
                    GitCommand('basics.commit_ohne_hooks', 'git commit --no-verify -m "Nachricht"', has_tip=True),
                    GitCommand('basics.bare_repository_erstellen', 'git init --bare', has_tip=False),
                    GitCommand('basics.verzeichnisinhalt_zurucksetzen', 'git restore .', has_tip=True),
                ],
            ),
            GitCategory(
                key='branching',
                icon='🌿',
                commands=[
                    GitCommand('branching.branches_auflisten', 'git branch', has_tip=True),
                    GitCommand('branching.neuen_branch_erstellen', 'git branch <name>', has_tip=False),
                    GitCommand('branching.branch_wechseln_klassisch', 'git checkout <branch>', has_tip=True),
                    GitCommand('branching.branch_wechseln_modern', 'git switch <branch>', has_tip=False),
                    GitCommand('branching.branch_erstellen_wechseln', 'git switch -c <name>', has_tip=True),
                    GitCommand('branching.branch_umbenennen', 'git branch -m <alter-name> <neuer-name>', has_tip=False),
                    GitCommand('branching.branch_mergen', 'git merge <branch>', has_tip=True),
                    GitCommand('branching.merge_ohne_fast_forward', 'git merge --no-ff <branch>', has_tip=True),
                    GitCommand('branching.merge_abbrechen', 'git merge --abort', has_tip=False),
                    GitCommand('branching.gemergte_branches_anzeigen', 'git branch --merged', has_tip=True),
                    GitCommand('branching.branch_loschen', 'git branch -d <name>', has_tip=True),
                    GitCommand('branching.branches_mit_tracking_info', 'git branch -vv', has_tip=False),
                    GitCommand('branching.nicht_gemergte_branches_anzeigen', 'git branch --no-merged', has_tip=False),
                    GitCommand('branching.detached_head_auschecken', 'git switch --detach <commit>', has_tip=True),
                    GitCommand('branching.upstream_verknupfung_entfernen', 'git branch --unset-upstream', has_tip=False),
                    GitCommand('branching.upstream_nachtraglich_setzen', 'git branch --set-upstream-to=origin/<branch>', has_tip=False),
                    GitCommand('branching.squash_merge', 'git merge --squash <branch>', has_tip=True),
                ],
            ),
            GitCategory(
                key='history',
                icon='🔍',
                commands=[
                    GitCommand('history.commit_historie_anzeigen', 'git log', has_tip=False),
                    GitCommand('history.kompakter_graph_log', 'git log --oneline --graph --all', has_tip=True),
                    GitCommand('history.log_mit_vollstandigem_diff', 'git log -p', has_tip=False),
                    GitCommand('history.log_nach_autor_filtern', 'git log --author="Name"', has_tip=False),
                    GitCommand('history.commits_pro_autor_zahlen', 'git shortlog -sn', has_tip=False),
                    GitCommand('history.datei_historie_uber_umbenennungen', 'git log --follow <datei>', has_tip=False),
                    GitCommand('history.anderungen_anzeigen', 'git diff', has_tip=False),
                    GitCommand('history.gestagte_anderungen_anzeigen', 'git diff --staged', has_tip=False),
                    GitCommand('history.branches_vergleichen', 'git diff branch1..branch2', has_tip=False),
                    GitCommand('history.commit_details_anzeigen', 'git show <commit>', has_tip=False),
                    GitCommand('history.commit_statistik_anzeigen', 'git show --stat <commit>', has_tip=False),
                    GitCommand('history.zeilen_autoren_anzeigen', 'git blame <datei>', has_tip=True),
                    GitCommand('history.log_mit_statistik', 'git log --stat', has_tip=False),
                    GitCommand('history.log_nach_zeitraum_filtern', 'git log --since="2 weeks ago" --until="yesterday"', has_tip=True),
                    GitCommand('history.nur_dateinamen_im_diff', 'git diff --name-only', has_tip=False),
                    GitCommand('history.commit_nachrichten_durchsuchen', 'git log --grep="Bugfix"', has_tip=False),
                    GitCommand('history.code_anderungen_durchsuchen_pickaxe', 'git log -S"funktionsname"', has_tip=True),
                    GitCommand('history.wer_hat_wann_was_geandert_kurzform', 'git log --oneline --name-status', has_tip=False),
                ],
            ),
            GitCategory(
                key='stash_reset',
                icon='⚡',
                commands=[
                    GitCommand('stash_reset.anderungen_stashen', 'git stash', has_tip=False),
                    GitCommand('stash_reset.stash_mit_nachricht', 'git stash push -m "Beschreibung"', has_tip=False),
                    GitCommand('stash_reset.stash_wiederherstellen', 'git stash pop', has_tip=True),
                    GitCommand('stash_reset.stash_liste_anzeigen', 'git stash list', has_tip=False),
                    GitCommand('stash_reset.stash_inhalt_anzeigen', 'git stash show -p', has_tip=False),
                    GitCommand('stash_reset.stash_verwerfen', 'git stash drop', has_tip=False),
                    GitCommand('stash_reset.datei_unstagen', 'git reset <datei>', has_tip=False),
                    GitCommand('stash_reset.soft_reset', 'git reset --soft HEAD~1', has_tip=False),
                    GitCommand('stash_reset.hard_reset', 'git reset --hard HEAD~1', has_tip=True),
                    GitCommand('stash_reset.datei_wiederherstellen', 'git restore <datei>', has_tip=False),
                    GitCommand('stash_reset.commit_ruckgangig_machen', 'git revert <commit>', has_tip=True),
                    GitCommand('stash_reset.stash_als_neuen_branch', 'git stash branch <neuer-branch>', has_tip=True),
                    GitCommand('stash_reset.alle_stashes_loschen', 'git stash clear', has_tip=False),
                    GitCommand('stash_reset.mixed_reset_standard', 'git reset --mixed HEAD~1', has_tip=True),
                    GitCommand('stash_reset.bereinigung_testen_trockenlauf', 'git clean -nd', has_tip=True),
                ],
            ),
            GitCategory(
                key='remote',
                icon='🌐',
                commands=[
                    GitCommand('remote.remotes_anzeigen', 'git remote -v', has_tip=False),
                    GitCommand('remote.remote_anderungen_laden', 'git fetch', has_tip=True),
                    GitCommand('remote.alle_remotes_aktualisieren', 'git fetch --all --prune', has_tip=False),
                    GitCommand('remote.branch_mit_tracking_pushen', 'git push -u origin <branch>', has_tip=True),
                    GitCommand('remote.sicher_force_pushen', 'git push --force-with-lease', has_tip=True),
                    GitCommand('remote.remote_branch_loschen', 'git push origin --delete <branch>', has_tip=False),
                    GitCommand('remote.remote_url_andern', 'git remote set-url origin <neue-url>', has_tip=False),
                    GitCommand('remote.remote_entfernen', 'git remote remove <name>', has_tip=False),
                    GitCommand('remote.remote_details_anzeigen', 'git remote show origin', has_tip=False),
                    GitCommand('remote.remote_umbenennen', 'git remote rename origin upstream', has_tip=True),
                    GitCommand('remote.nur_bestimmten_branch_pullen', 'git pull origin <branch> --rebase', has_tip=True),
                ],
            ),
            GitCategory(
                key='tags',
                icon='🏷️',
                commands=[
                    GitCommand('tags.tags_auflisten', 'git tag', has_tip=False),
                    GitCommand('tags.annotiertes_tag_erstellen', 'git tag -a v1.0.0 -m "Release 1.0.0"', has_tip=True),
                    GitCommand('tags.leichtes_tag_erstellen', 'git tag v1.0.0-beta', has_tip=False),
                    GitCommand('tags.tags_zum_remote_pushen', 'git push origin --tags', has_tip=True),
                    GitCommand('tags.zu_tag_wechseln', 'git checkout v1.0.0', has_tip=True),
                    GitCommand('tags.tag_loschen', 'git tag -d v1.0.0-beta', has_tip=True),
                    GitCommand('tags.tags_nach_muster_filtern', 'git tag -l "v1.*"', has_tip=False),
                    GitCommand('tags.nachstgelegenes_tag_ermitteln', 'git describe --tags', has_tip=True),
                ],
            ),
            GitCategory(
                key='advanced',
                icon='🛠️',
                commands=[
                    GitCommand('advanced.rebase_durchfuhren', 'git rebase <branch>', has_tip=True),
                    GitCommand('advanced.interaktiver_rebase', 'git rebase -i HEAD~3', has_tip=True),
                    GitCommand('advanced.rebase_fortsetzen', 'git rebase --continue', has_tip=False),
                    GitCommand('advanced.rebase_abbrechen', 'git rebase --abort', has_tip=False),
                    GitCommand('advanced.cherry_pick', 'git cherry-pick <commit>', has_tip=False),
                    GitCommand('advanced.cherry_pick_abbrechen', 'git cherry-pick --abort', has_tip=False),
                    GitCommand('advanced.reflog_anzeigen', 'git reflog', has_tip=True),
                    GitCommand('advanced.fehlerhaften_commit_suchen', 'git bisect start', has_tip=True),
                    GitCommand('advanced.zusatzliches_arbeitsverzeichnis', 'git worktree add ../hotfix hotfix-branch', has_tip=True),
                    GitCommand('advanced.arbeitsverzeichnis_bereinigen', 'git clean -fd', has_tip=True),
                    GitCommand('advanced.notiz_zu_einem_commit_hinzufugen', 'git notes add -m "Zusatzinfo"', has_tip=False),
                    GitCommand('advanced.leeren_commit_erstellen', 'git commit --allow-empty -m "Trigger CI"', has_tip=False),
                ],
            ),
            GitCategory(
                key='ignore_clean',
                icon='🧹',
                commands=[
                    GitCommand('ignore_clean.gitignore_anlegen', 'echo "*.log" >> .gitignore', has_tip=True),
                    GitCommand('ignore_clean.bereits_getrackte_datei_ignorieren', 'git rm --cached <datei>', has_tip=True),
                    GitCommand('ignore_clean.verzeichnis_rekursiv_aus_tracking_entfer', 'git rm -r --cached <verzeichnis>', has_tip=False),
                    GitCommand('ignore_clean.ignorierte_dateien_anzeigen', 'git status --ignored', has_tip=False),
                    GitCommand('ignore_clean.prufen_warum_eine_datei_ignoriert_wird', 'git check-ignore -v <datei>', has_tip=True),
                    GitCommand('ignore_clean.datei_als_binar_markieren', "echo '*.psd binary' >> .gitattributes", has_tip=False),
                ],
            ),
            GitCategory(
                key='patches',
                icon='📦',
                commands=[
                    GitCommand('patches.diff_in_datei_exportieren', 'git diff > aenderungen.patch', has_tip=False),
                    GitCommand('patches.patch_anwenden', 'git apply aenderungen.patch', has_tip=True),
                    GitCommand('patches.commits_als_patch_serie_exportieren', 'git format-patch origin/main', has_tip=True),
                    GitCommand('patches.patch_serie_anwenden', 'git am < 0001-feature.patch', has_tip=False),
                    GitCommand('patches.snapshot_als_archiv_exportieren', 'git archive --format=zip -o projekt.zip HEAD', has_tip=True),
                ],
            ),
            GitCategory(
                key='submodules',
                icon='🧩',
                commands=[
                    GitCommand('submodules.submodul_hinzufugen', 'git submodule add <url> <pfad>', has_tip=False),
                    GitCommand('submodules.submodule_beim_klonen_laden', 'git clone --recurse-submodules <url>', has_tip=False),
                    GitCommand('submodules.submodule_nachtraglich_initialisieren', 'git submodule update --init --recursive', has_tip=True),
                    GitCommand('submodules.submodule_aktualisieren', 'git submodule update --remote --merge', has_tip=False),
                    GitCommand('submodules.befehl_in_allen_submodulen_ausfuhren', "git submodule foreach 'git status'", has_tip=False),
                    GitCommand('submodules.submodul_entfernen', 'git submodule deinit -f <pfad> && git rm -f <pfad>', has_tip=False),
                    GitCommand('submodules.subtree_hinzufugen', 'git subtree add --prefix=<pfad> <url> main --squash', has_tip=True),
                    GitCommand('submodules.subtree_aktualisieren', 'git subtree pull --prefix=<pfad> <url> main --squash', has_tip=False),
                ],
            ),
            GitCategory(
                key='hooks',
                icon='🪝',
                commands=[
                    GitCommand('hooks.hook_verzeichnis_anzeigen', 'ls -la .git/hooks/', has_tip=True),
                    GitCommand('hooks.pre_commit_hook_aktivieren', 'chmod +x .git/hooks/pre-commit', has_tip=True),
                    GitCommand('hooks.globales_hook_verzeichnis_setzen', 'git config --global core.hooksPath ~/.git-hooks', has_tip=True),
                    GitCommand('hooks.commit_vorlage_einrichten', 'git config --global commit.template ~/.gitmessage', has_tip=False),
                ],
            ),
            GitCategory(
                key='maintenance',
                icon='🧰',
                commands=[
                    GitCommand('maintenance.repository_optimieren', 'git gc', has_tip=True),
                    GitCommand('maintenance.repository_integritat_prufen', 'git fsck', has_tip=False),
                    GitCommand('maintenance.objektanzahl_anzeigen', 'git count-objects -v', has_tip=False),
                    GitCommand('maintenance.nicht_erreichbare_objekte_entfernen', 'git prune', has_tip=True),
                    GitCommand('maintenance.partielles_auschecken_sparse_checkout', 'git sparse-checkout init --cone && git sparse-checkout set <ordner>', has_tip=True),
                    GitCommand('maintenance.flachen_klon_nachtraglich_vervollstandig', 'git fetch --unshallow', has_tip=False),
                ],
            ),
            GitCategory(
                key='lfs',
                icon='🗄️',
                commands=[
                    GitCommand('lfs.git_lfs_aktivieren', 'git lfs install', has_tip=True),
                    GitCommand('lfs.dateityp_per_lfs_verwalten', 'git lfs track "*.psd"', has_tip=True),
                    GitCommand('lfs.lfs_dateien_auflisten', 'git lfs ls-files', has_tip=False),
                    GitCommand('lfs.lfs_inhalte_nachladen', 'git lfs pull', has_tip=True),
                ],
            ),
            GitCategory(
                key='specialtools',
                icon='🧪',
                commands=[
                    GitCommand('specialtools.code_inhalt_durchsuchen', 'git grep "TODO"', has_tip=True),
                    GitCommand('specialtools.konfliktlosungen_merken', 'git config --global rerere.enabled true', has_tip=True),
                    GitCommand('specialtools.repository_als_datei_bundeln', 'git bundle create repo.bundle --all', has_tip=True),
                    GitCommand('specialtools.aus_einem_bundle_klonen', 'git clone repo.bundle projekt', has_tip=False),
                    GitCommand('specialtools.alle_arbeitsverzeichnisse_auflisten', 'git worktree list', has_tip=False),
                    GitCommand('specialtools.arbeitsverzeichnis_entfernen', 'git worktree remove ../hotfix', has_tip=True),
                    GitCommand('specialtools.commit_serien_vergleichen', 'git range-diff main~5..main main~3..main', has_tip=True),
                    GitCommand('specialtools.commit_graph_datei_erzeugen', 'git commit-graph write --reachable', has_tip=False),
                    GitCommand('specialtools.automatische_wartung_einrichten', 'git maintenance start', has_tip=True),
                    GitCommand('specialtools.commit_signatur_prufen', 'git verify-commit <commit>', has_tip=False),
                    GitCommand('specialtools.tag_signatur_prufen', 'git verify-tag v1.0.0', has_tip=False),
                    GitCommand('specialtools.signierten_commit_erstellen', 'git commit -S -m "Nachricht"', has_tip=True),
                    GitCommand('specialtools.objekt_temporar_ersetzen', 'git replace <alter-commit> <neuer-commit>', has_tip=True),
                    GitCommand('specialtools.historie_mit_filter_repo_umschreiben', 'git filter-repo --path secrets.env --invert-paths', has_tip=True),
                    GitCommand('specialtools.automatisiertes_bisect', 'git bisect run ./test.sh', has_tip=True),
                    GitCommand('specialtools.pull_request_text_generieren', 'git request-pull v1.0 origin main', has_tip=False),
                    GitCommand('specialtools.grafische_historie_offnen', 'gitk --all', has_tip=True),
                    GitCommand('specialtools.zugangsdaten_zwischenspeichern', 'git config --global credential.helper cache', has_tip=True),
                ],
            ),
            GitCategory(
                key='plumbing',
                icon='🔧',
                commands=[
                    GitCommand('plumbing.objekt_inhalt_anzeigen', 'git cat-file -p <hash>', has_tip=True),
                    GitCommand('plumbing.blob_objekt_erzeugen', 'git hash-object -w <datei>', has_tip=True),
                    GitCommand('plumbing.verzeichnisbaum_anzeigen', 'git ls-tree -r HEAD', has_tip=False),
                    GitCommand('plumbing.tree_objekt_erstellen', 'git write-tree', has_tip=False),
                    GitCommand('plumbing.tree_objekt_aus_text_erzeugen', 'git mktree', has_tip=True),
                    GitCommand('plumbing.commit_objekt_manuell_erstellen', 'git commit-tree <tree-hash> -p <parent-hash> -m "Nachricht"', has_tip=True),
                    GitCommand('plumbing.referenz_auflosen', 'git rev-parse HEAD', has_tip=True),
                    GitCommand('plumbing.commit_liste_roh_abfragen', 'git rev-list --count HEAD', has_tip=True),
                    GitCommand('plumbing.index_direkt_manipulieren', 'git update-index --add --cacheinfo 100644,<hash>,<pfad>', has_tip=False),
                    GitCommand('plumbing.getrackte_dateien_roh_auflisten', 'git ls-files', has_tip=False),
                    GitCommand('plumbing.anderungen_zwischen_index_und_head', 'git diff-index HEAD', has_tip=False),
                    GitCommand('plumbing.anderungen_zwischen_zwei_trees', 'git diff-tree -p <commit>', has_tip=False),
                    GitCommand('plumbing.symbolische_referenz_lesen_setzen', 'git symbolic-ref HEAD', has_tip=False),
                    GitCommand('plumbing.referenzen_aller_art_auflisten', 'git show-ref', has_tip=False),
                    GitCommand('plumbing.referenzen_formatiert_auflisten', "git for-each-ref --format='%(refname:short) %(objectname)'", has_tip=False),
                    GitCommand('plumbing.gemeinsamen_vorfahren_finden', 'git merge-base branch1 branch2', has_tip=False),
                    GitCommand('plumbing.objekte_zu_paketdatei_bundeln', 'git pack-objects --revs pack < commit-liste.txt', has_tip=False),
                    GitCommand('plumbing.paketdatei_entpacken', 'git unpack-objects < paket.pack', has_tip=False),
                    GitCommand('plumbing.paketdatei_indizieren', 'git index-pack paket.pack', has_tip=False),
                    GitCommand('plumbing.paketdatei_verifizieren', 'git verify-pack -v paket.idx', has_tip=False),
                    GitCommand('plumbing.attribut_einer_datei_prufen', 'git check-attr -a <datei>', has_tip=False),
                    GitCommand('plumbing.git_umgebungsvariable_abfragen', 'git var -l', has_tip=False),
                ],
            ),
        ]
    # ------------------------------------------------------------------
    def get_category(self, key: str) -> Optional[GitCategory]:
        for cat in self.categories:
            if cat.key == key:
                return cat
        return None

    def search(self, query: str) -> List[GitCommand]:
        """Durchsucht Titel, Beschreibung und Befehl aller Kategorien."""
        query = query.strip().lower()
        if not query:
            return []
        results: List[GitCommand] = []
        for cat in self.categories:
            for cmd in cat.commands:
                haystack = f"{cmd.title} {cmd.description} {cmd.command}".lower()
                if query in haystack:
                    results.append(cmd)
        return results


# ---------------------------------------------------------------------------
#  STYLESHEET (Cyberpunk Dark Mode)
# ---------------------------------------------------------------------------

STYLE_SHEET = """
QMainWindow, QWidget#CentralWidget {
    background-color: #0F0F14;
}

QLabel {
    color: #E6E6F0;
}

QLabel#BrandTitle {
    color: #F5F5FF;
    font-size: 20px;
    font-weight: 700;
}

QLabel#BrandMark {
    color: #9D00FF;
}

QLabel#SectionHeading {
    color: #00F0FF;
    font-size: 18px;
    font-weight: 700;
    padding: 4px 0px 12px 0px;
}

QLabel#CardTitle {
    color: #F5F5FF;
    font-size: 15px;
    font-weight: 600;
}

QLabel#CardDescription {
    color: #A8A8C0;
    font-size: 12.5px;
}

QLabel#TipLabel {
    color: #FFD37A;
    font-size: 12px;
}

QLabel#EmptyState {
    color: #5C5C75;
    font-size: 14px;
}

/* Header */
QFrame#Header {
    background-color: #14141C;
    border-bottom: 1px solid #24243A;
}

QLineEdit#SearchBar {
    background-color: #1A1A24;
    border: 1px solid #2A2A3E;
    border-radius: 10px;
    padding: 9px 14px;
    color: #E6E6F0;
    font-size: 13px;
    selection-background-color: #9D00FF;
}

QLineEdit#SearchBar:focus {
    border: 1px solid #9D00FF;
}

/* Sidebar */
QFrame#Sidebar {
    background-color: #14141C;
    border-right: 1px solid #24243A;
}

QPushButton#NavButton {
    text-align: left;
    background-color: transparent;
    color: #B8B8CC;
    border: none;
    border-radius: 10px;
    padding: 11px 14px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton#NavButton:hover {
    background-color: #1F1F2E;
    color: #F5F5FF;
}

QPushButton#NavButton:checked {
    background-color: #221033;
    color: #00F0FF;
    border-left: 3px solid #9D00FF;
    font-weight: 700;
}

/* Content area */
QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

QScrollBar:vertical {
    background: #14141C;
    width: 10px;
    margin: 0px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #2E2E45;
    min-height: 30px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #9D00FF;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    height: 0px;
}

/* Command Card */
QFrame#CommandCard {
    background-color: #16161F;
    border: 1px solid #24243A;
    border-radius: 14px;
}

QFrame#CommandCard:hover {
    border: 1px solid #3A2A5E;
}

QFrame#TerminalBox {
    background-color: #0B0B10;
    border: 1px solid #2A2A3E;
    border-radius: 8px;
}

QLabel#TerminalText {
    color: #00F0FF;
    font-family: "Fira Code", "Consolas", monospace;
    font-size: 13px;
}

QFrame#TipBox {
    background-color: #1E1A0F;
    border: 1px solid #4A3D1A;
    border-radius: 8px;
}

QPushButton#CopyButton {
    background-color: #221033;
    color: #C9A6FF;
    border: 1px solid #3A2A5E;
    border-radius: 7px;
    padding: 6px 12px;
    font-size: 11.5px;
    font-weight: 600;
}

QPushButton#CopyButton:hover {
    background-color: #2E1745;
    color: #F5F5FF;
}

QPushButton#CopyButton[copied="true"] {
    background-color: #0F2E1E;
    color: #4CFFA0;
    border: 1px solid #1E5C3C;
}
"""


# ---------------------------------------------------------------------------
#  SIDEBAR NAVIGATION
# ---------------------------------------------------------------------------

class SidebarNavigation(QFrame):
    """Vertikale Navigation zur Auswahl einer Git-Kategorie."""

    category_selected = pyqtSignal(str)
    settings_requested = pyqtSignal()

    def __init__(self, categories: List[GitCategory], parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(240)

        self._categories = categories
        self._buttons: dict[str, QPushButton] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 18, 12, 18)
        layout.setSpacing(4)

        self._nav_heading = QLabel(LM.tr("ui.sidebar.heading"))
        self._nav_heading.setStyleSheet(
            "color:#5C5C75; font-size:11px; font-weight:700; "
            "letter-spacing:1px; padding:4px 10px 10px 10px;"
        )
        layout.addWidget(self._nav_heading)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(4)

        for cat in categories:
            btn = QPushButton(f"  {cat.icon}   {cat.label}")
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(40)
            btn.clicked.connect(lambda _checked, k=cat.key: self._on_clicked(k))
            nav_layout.addWidget(btn)
            self._buttons[cat.key] = btn

        nav_layout.addStretch(1)
        scroll.setWidget(nav_container)
        layout.addWidget(scroll, stretch=1)

        self._settings_btn = QPushButton(LM.tr("ui.sidebar.settings_button"))
        self._settings_btn.setObjectName("NavButton")
        self._settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._settings_btn.setMinimumHeight(38)
        self._settings_btn.clicked.connect(self.settings_requested.emit)
        layout.addWidget(self._settings_btn)

        self._footer = QLabel(LM.tr("ui.sidebar.footer"))
        self._footer.setStyleSheet("color:#3A3A52; font-size:10.5px; padding:6px 10px;")
        layout.addWidget(self._footer)

    def _on_clicked(self, key: str):
        self.set_active(key)
        self.category_selected.emit(key)

    def set_active(self, key: str):
        for k, btn in self._buttons.items():
            btn.setChecked(k == key)

    def retranslate_ui(self):
        """Hot-Reload: aktualisiert alle sichtbaren Sidebar-Texte in der neuen Sprache."""
        self._nav_heading.setText(LM.tr("ui.sidebar.heading"))
        self._settings_btn.setText(LM.tr("ui.sidebar.settings_button"))
        self._footer.setText(LM.tr("ui.sidebar.footer"))
        for cat in self._categories:
            btn = self._buttons.get(cat.key)
            if btn is not None:
                btn.setText(f"  {cat.icon}   {cat.label}")


# ---------------------------------------------------------------------------
#  COMMAND CARD
# ---------------------------------------------------------------------------

class CommandCard(QFrame):
    """Wiederverwendbare Karte zur Darstellung eines einzelnen Git-Befehls."""

    def __init__(self, cmd: GitCommand, parent=None):
        super().__init__(parent)
        self.setObjectName("CommandCard")
        self._command_text = cmd.command

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(22)
        shadow.setOffset(0, 4)
        shadow.setColor(Qt.GlobalColor.black)
        self.setGraphicsEffect(shadow)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 16, 18, 16)
        outer.setSpacing(10)

        # Title
        title = QLabel(cmd.title)
        title.setObjectName("CardTitle")
        outer.addWidget(title)

        # Description
        desc = QLabel(cmd.description)
        desc.setObjectName("CardDescription")
        desc.setWordWrap(True)
        outer.addWidget(desc)

        # Terminal box + copy button row
        term_row = QHBoxLayout()
        term_row.setSpacing(10)

        terminal_box = QFrame()
        terminal_box.setObjectName("TerminalBox")
        term_inner = QHBoxLayout(terminal_box)
        term_inner.setContentsMargins(12, 8, 12, 8)

        prompt = QLabel("$")
        prompt.setStyleSheet("color:#9D00FF; font-family:'Fira Code','Consolas',monospace; font-weight:700;")
        term_inner.addWidget(prompt)

        term_text = QLabel(cmd.command)
        term_text.setObjectName("TerminalText")
        term_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        term_inner.addWidget(term_text)
        term_inner.addStretch(1)

        term_row.addWidget(terminal_box, stretch=1)

        self.copy_btn = QPushButton(LM.tr("ui.copy_button.default"))
        self.copy_btn.setObjectName("CopyButton")
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.setFixedWidth(100)
        self.copy_btn.clicked.connect(self._on_copy)
        term_row.addWidget(self.copy_btn)

        outer.addLayout(term_row)

        # Optional Pro-Tip
        if cmd.tip:
            tip_box = QFrame()
            tip_box.setObjectName("TipBox")
            tip_layout = QHBoxLayout(tip_box)
            tip_layout.setContentsMargins(12, 8, 12, 8)
            tip_label = QLabel(LM.tr("ui.tip_prefix", tip=cmd.tip))
            tip_label.setObjectName("TipLabel")
            tip_label.setWordWrap(True)
            tip_layout.addWidget(tip_label)
            outer.addWidget(tip_box)

    def _on_copy(self):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self._command_text)

        self.copy_btn.setText(LM.tr("ui.copy_button.copied"))
        self.copy_btn.setProperty("copied", "true")
        self.copy_btn.style().unpolish(self.copy_btn)
        self.copy_btn.style().polish(self.copy_btn)

        QTimer.singleShot(1400, self._reset_copy_button)

    def _reset_copy_button(self):
        self.copy_btn.setText(LM.tr("ui.copy_button.default"))
        self.copy_btn.setProperty("copied", "false")
        self.copy_btn.style().unpolish(self.copy_btn)
        self.copy_btn.style().polish(self.copy_btn)


# ---------------------------------------------------------------------------
#  CONTENT PAGE (Liste von CommandCards mit Scroll)
# ---------------------------------------------------------------------------

class CommandListPage(QScrollArea):
    """Scrollbare Seite mit einer Überschrift und mehreren CommandCards."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(28, 24, 28, 28)
        self._layout.setSpacing(14)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.setWidget(self._container)

        self._heading = QLabel("")
        self._heading.setObjectName("SectionHeading")
        self._layout.addWidget(self._heading)

        self._empty_state = QLabel(LM.tr("ui.empty_state"))
        self._empty_state.setObjectName("EmptyState")
        self._empty_state.setVisible(False)
        self._layout.addWidget(self._empty_state)

    def set_content(self, heading: str, commands: List[GitCommand]):
        self._heading.setText(heading)
        self._empty_state.setText(LM.tr("ui.empty_state"))

        # Vorhandene Cards entfernen (alles außer heading/empty_state)
        while self._layout.count() > 2:
            item = self._layout.takeAt(2)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not commands:
            self._empty_state.setVisible(True)
            return

        self._empty_state.setVisible(False)
        for cmd in commands:
            card = CommandCard(cmd)
            self._layout.addWidget(card)


# ---------------------------------------------------------------------------
#  SETTINGS-DIALOG (eigene UI, keine Standard-QMessageBox/-Dialoge)
# ---------------------------------------------------------------------------

class LanguageOptionButton(QPushButton):
    """Eine einzelne, wählbare Sprachzeile (Flagge + Name) in der Settings-Ansicht."""

    def __init__(self, code: str, name: str, flag: str, parent=None):
        super().__init__(parent)
        self.code = code
        self.setObjectName("LanguageOption")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(46)
        self.setText(f"  {flag}   {name}   ({code})")
        self.setStyleSheet(
            "text-align:left; font-size:13.5px; font-weight:600; border-radius:10px;"
        )


class SettingsDialog(QDialog):
    """
    Eigene, ins Pandora-Design eingebettete Einstellungs-Ansicht.

    Enthält aktuell die Sprachauswahl für alle 10 verfügbaren Sprachen.
    Ein Klick auf eine Sprache wechselt sofort (Hot-Reload) - der Dialog
    bleibt dabei offen, damit der Effekt direkt sichtbar ist, und läuft
    nicht-modal, damit auch das Hauptfenster im Hintergrund sofort
    mitübersetzt wird.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsDialog")
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.setMinimumWidth(380)
        self.setStyleSheet(
            """
            QDialog#SettingsDialog { background-color: #14141C; }
            QLabel#SettingsTitle { color:#F5F5FF; font-size:17px; font-weight:700; }
            QLabel#SettingsSection { color:#00F0FF; font-size:11px; font-weight:700;
                letter-spacing:1px; padding-top:6px; }
            QLabel#SettingsHint { color:#6C6C85; font-size:11px; }
            QPushButton#LanguageOption { background-color:#1A1A24; color:#B8B8CC;
                border:1px solid #2A2A3E; }
            QPushButton#LanguageOption:hover { background-color:#1F1F2E; color:#F5F5FF; }
            QPushButton#LanguageOption:checked { background-color:#221033; color:#00F0FF;
                border:1px solid #9D00FF; font-weight:700; }
            QPushButton#SettingsClose { background-color:#221033; color:#C9A6FF;
                border:1px solid #3A2A5E; border-radius:8px; padding:8px 16px;
                font-size:12.5px; font-weight:600; }
            QPushButton#SettingsClose:hover { background-color:#2E1745; color:#F5F5FF; }
            """
        )

        self._buttons: dict[str, LanguageOptionButton] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 22, 24, 20)
        outer.setSpacing(6)

        self._title = QLabel(LM.tr("ui.settings.title"))
        self._title.setObjectName("SettingsTitle")
        outer.addWidget(self._title)

        self._section = QLabel(LM.tr("ui.settings.language_section"))
        self._section.setObjectName("SettingsSection")
        outer.addWidget(self._section)

        lang_container = QWidget()
        lang_layout = QVBoxLayout(lang_container)
        lang_layout.setContentsMargins(0, 4, 0, 4)
        lang_layout.setSpacing(6)

        for code, meta in LM.available_languages().items():
            btn = LanguageOptionButton(code, meta.get("name", code.upper()), meta.get("flag", ""))
            btn.setChecked(code == LM.current_language)
            btn.clicked.connect(lambda _checked, c=code: self._on_language_clicked(c))
            lang_layout.addWidget(btn)
            self._buttons[code] = btn

        outer.addWidget(lang_container)

        self._hint = QLabel(LM.tr("ui.settings.language_hint"))
        self._hint.setObjectName("SettingsHint")
        self._hint.setWordWrap(True)
        outer.addWidget(self._hint)

        self._fallback_note = QLabel(LM.tr("ui.settings.fallback_note"))
        self._fallback_note.setObjectName("SettingsHint")
        self._fallback_note.setWordWrap(True)
        outer.addWidget(self._fallback_note)

        close_row = QHBoxLayout()
        close_row.addStretch(1)
        self._close_btn = QPushButton(LM.tr("ui.settings.close_button"))
        self._close_btn.setObjectName("SettingsClose")
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.clicked.connect(self.close)
        close_row.addWidget(self._close_btn)
        outer.addLayout(close_row)

        LANG_BUS.changed.connect(self.retranslate_ui)

    def _on_language_clicked(self, code: str):
        set_active_language(code)  # löst LANG_BUS.changed aus -> retranslate_ui überall
        for c, btn in self._buttons.items():
            btn.setChecked(c == code)

    def retranslate_ui(self):
        self.setWindowTitle(LM.tr("ui.settings.title"))
        self._title.setText(LM.tr("ui.settings.title"))
        self._section.setText(LM.tr("ui.settings.language_section"))
        self._hint.setText(LM.tr("ui.settings.language_hint"))
        self._fallback_note.setText(LM.tr("ui.settings.fallback_note"))
        self._close_btn.setText(LM.tr("ui.settings.close_button"))
        for code, btn in self._buttons.items():
            btn.setChecked(code == LM.current_language)

    def closeEvent(self, event):
        try:
            LANG_BUS.changed.disconnect(self.retranslate_ui)
        except TypeError:
            pass
        super().closeEvent(event)


# ---------------------------------------------------------------------------
#  MAIN WINDOW
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(LM.tr("ui.window_title"))
        self.resize(1180, 760)
        self.setMinimumSize(920, 600)

        self.data_manager = GitDataManager()
        self._current_category_key = self.data_manager.categories[0].key
        self._settings_dialog: Optional[SettingsDialog] = None

        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_header())

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar = SidebarNavigation(self.data_manager.categories)
        self.sidebar.category_selected.connect(self._on_category_selected)
        self.sidebar.settings_requested.connect(self._open_settings)
        body_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self._pages: dict[str, CommandListPage] = {}

        for cat in self.data_manager.categories:
            page = CommandListPage()
            page.set_content(f"{cat.icon}  {cat.label}", cat.commands)
            self.stack.addWidget(page)
            self._pages[cat.key] = page

        # Zusätzliche Such-Ergebnis-Seite
        self.search_page = CommandListPage()
        self.stack.addWidget(self.search_page)
        self._pages["__search__"] = self.search_page

        body_layout.addWidget(self.stack, stretch=1)
        root_layout.addWidget(body, stretch=1)

        self.sidebar.set_active(self._current_category_key)
        self.stack.setCurrentWidget(self._pages[self._current_category_key])

        LANG_BUS.changed.connect(self.retranslate_ui)

    # ------------------------------------------------------------------
    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(76)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(18)

        self.brand = QLabel()
        self.brand.setObjectName("BrandTitle")
        self.brand.setText(LM.tr("ui.brand_title_html"))
        layout.addWidget(self.brand)

        self._total_commands = sum(len(c.commands) for c in self.data_manager.categories)
        self.counter = QLabel(LM.tr("ui.header.counter", count=self._total_commands))
        self.counter.setStyleSheet("color:#5C5C75; font-size:12px; font-weight:600;")
        layout.addWidget(self.counter)

        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("SearchBar")
        self.search_bar.setPlaceholderText(LM.tr("ui.header.search_placeholder"))
        self.search_bar.setFixedWidth(420)
        self.search_bar.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_bar)

        return header

    # ------------------------------------------------------------------
    def _on_category_selected(self, key: str):
        self._current_category_key = key
        self.search_bar.blockSignals(True)
        self.search_bar.clear()
        self.search_bar.blockSignals(False)
        self.stack.setCurrentWidget(self._pages[key])

    def _on_search_changed(self, text: str):
        text = text.strip()
        if not text:
            self.stack.setCurrentWidget(self._pages[self._current_category_key])
            self.sidebar.set_active(self._current_category_key)
            return

        results = self.data_manager.search(text)
        heading = LM.tr("ui.search.results_heading", query=text, count=len(results))
        self.search_page.set_content(heading, results)
        self.stack.setCurrentWidget(self.search_page)
        self.sidebar.set_active("")  # keine Kategorie aktiv während der Suche

    # ------------------------------------------------------------------
    def _open_settings(self):
        if self._settings_dialog is None:
            self._settings_dialog = SettingsDialog(self)
        self._settings_dialog.show()
        self._settings_dialog.raise_()
        self._settings_dialog.activateWindow()

    def retranslate_ui(self):
        """Wird bei jedem Sprachwechsel über LANG_BUS ausgelöst (Hot-Reload ohne Neustart)."""
        self.setWindowTitle(LM.tr("ui.window_title"))
        self.brand.setText(LM.tr("ui.brand_title_html"))
        self.counter.setText(LM.tr("ui.header.counter", count=self._total_commands))
        self.search_bar.setPlaceholderText(LM.tr("ui.header.search_placeholder"))

        self.sidebar.retranslate_ui()

        # Alle Kategorie-Seiten mit dem neu übersetzten Inhalt neu befüllen.
        for cat in self.data_manager.categories:
            page = self._pages.get(cat.key)
            if page is not None:
                page.set_content(f"{cat.icon}  {cat.label}", cat.commands)

        # Aktuelle Ansicht (Kategorie oder aktive Suche) neu anzeigen.
        current_text = self.search_bar.text().strip()
        if current_text:
            self._on_search_changed(current_text)
        else:
            self.stack.setCurrentWidget(self._pages[self._current_category_key])
            self.sidebar.set_active(self._current_category_key)


# ---------------------------------------------------------------------------
#  ENTRY POINT
# ---------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Pandora® The Basics of git")

    default_font = QFont("Segoe UI", 10)
    app.setFont(default_font)

    app.setStyleSheet(STYLE_SHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
