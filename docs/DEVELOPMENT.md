# Développement

**Français** · [English](DEVELOPMENT_EN.md) · [Collection](../README.md)

Construire depuis la racine avec Python 3.10+ et SjASMPlus. Les deux langues sont générées :

```text
python tools/build_all.py --lang fr --assembler "sjasmplus.exe"
```

La variable `SJASMPLUS` ou PATH peut aussi désigner l’assembleur. BIN, Intel HEX et manifestes accompagnent chaque jeu ; symboles et listings sont générés localement. Après modification des sources, reconstruire également les binaires distribués.

## Vérifications automatisées

```text
python -m pip install -r tests/requirements.txt
python tools/check_publication.py --lang fr
python -m unittest discover -s tests -p "test_*.py"
python tests/check_programs.py --lang fr
python games/quest/check_quest.py --lang fr
python games/quest/check_tiles.py --lang fr
python games/pocket-depths/check_depths.py --lang fr
python games/pocket-depths-2/check_depths2.py --lang fr
python games/pocket-invaders/check_invaders.py --lang fr
python games/pocket-runner/check_runner.py --lang fr
python games/pocket-rally/check_rally.py --lang fr
python games/pocket-jumper/check_jumper.py --lang fr
python games/pocket-jumper/check_assets.py --lang fr --assembler "sjasmplus.exe"
```

Le contrôle de publication vérifie les liens et ancres des README, les empreintes des manifestes, la correspondance BIN/HEX, les checksums et les réservations mémoire. Il utilise uniquement Python standard et s’exécute aussi avant la création de l’archive. Les vérifications CPU exécutent les binaires Z80 avec des contrats IOCS simulés et nécessitent `z80==1.2.0`. Cette dépendance n’est nécessaire ni pour assembler ni pour jouer.

## Graphismes

Le format de pixels utilise **480 octets** : quatre bandes de 120 colonnes, avec sept bits utiles par octet. Le point `(x,y)` est à `120*(y//7)+x`, masque `1<<(y%7)`. Envoyer chaque bande par `PCG_IOCS_PATTERN`, avec D=ligne, E=colonne de caractère et B=nombre de colonnes de pixels. Le LCD physique conserve ses interstices entre cellules. Les chiffres du panneau peuvent utiliser la police native de la ROM.

Voir `games/pocket-jumper/render.asm` pour la composition des sprites avec découpage, `games/pocket-depths-2/raycaster.asm` pour le DDA en virgule fixe et `include/sharp-pc-g8xx.inc` pour les contrats IOCS.

## g800

```text
python tools/play_jumper.py --lang fr --emulator "g800.exe"
```

Le même principe s’applique à `play_rally.py`, `play_runner.py`, `play_invaders.py`, `play_depths.py` et `play_depths2.py`. Ajouter `--lite` pour Depths Lite. g800 s’installe séparément. Les lanceurs utilisent les IOCS simulés sans ROM. Les outils de capture Windows facultatifs nécessitent `tools/requirements-capture.txt` et ne capturent que le LCD.

## Archive de publication

```text
python tools/package_collection.py --lang fr
```

Crée un ZIP et son fichier SHA-256 dans `../deliverables/`, en excluant environnements, préférences personnelles, caches et rapports locaux.
