# Développement

**Français** · [English](DEVELOPMENT_EN.md) · [Collection](../README.md)

Construire depuis la racine avec Python 3.10+ et SjASMPlus. Les deux langues sont générées :

```text
python tools/build_all.py --lang fr --assembler "sjasmplus.exe"
```

La variable `SJASMPLUS` ou PATH peut aussi désigner l’assembleur. BIN, Intel HEX et manifestes accompagnent chaque jeu ; symboles et listings sont générés localement. Après modification des sources, reconstruire également les binaires distribués.

## Organisation des cibles

Conserver **un dépôt unique, organisé par jeu** : `games/<jeu>/` contient ses règles, graphismes sources et documentation bilingue. `include/` et `lib/` regroupent les contrats et pilotes matériels par profil. Les différences de LCD et de clavier appartiennent à cette couche ; les règles et circuits restent communs autant que possible.

Lorsqu’un jeu reçoit plusieurs versions, ajouter `targets/g850/`, `targets/g815/` ou `targets/g80x-32k/` dans son dossier pour les adaptations, et un sous-dossier `build/<cible>/` par famille. Identifier aussi la cible dans les noms téléchargés, par exemple `clash_g850_FR.ihx` et `clash_g80x_32k_FR.ihx`. Cette disposition s’applique aussi aux jeux à cible unique. Distribuer les fichiers `.ihx` et `.bin` avec leur manifeste ; ne pas conserver de doublon à la racine de `build/`.

Le manifeste de chaque cible doit donner le modèle, la RAM minimale, la géométrie, l’origine, la réservation USER, le point d’entrée, la langue et les empreintes. Le README principal sert de catalogue avec une [matrice de compatibilité](COMPATIBILITY.md) ; les archives de release peuvent regrouper les jeux par cible et besoin mémoire. La présence d’un CPU Z80 ou d’un connecteur commun ne remplace pas la validation du profil.

## Vérifications automatisées

Quest, Pocket Invaders, Pocket Runner, Pocket Rally, Pocket Jumper, Pocket Depths 1/2 et Star Lane utilisent `include/game_platform.inc` et `lib/game_runtime.asm` : seules les interfaces IOCS publiques sont partagées. La version G850 ne reçoit aucun pointeur système interne G805. Leurs constructions génèrent G80X et G850 ; `--target g850` ou `--target g80x` limite la cible. Les versions G850 sont dans `games/<jeu>/build/g850/`, les versions G80X sont dans `games/<jeu>/build/g80x/`.

```text
python -m pip install -r tests/requirements.txt
python tools/check_publication.py --lang fr
python -m unittest discover -s tests -p "test_*.py"
python tests/check_programs.py --lang fr
python games/star-lane/check_star.py --lang fr
python games/star-lane/check_g850.py --lang fr
python games/pocket-depths/check_g850.py --lang fr
python games/quest/check_quest.py --lang fr
python games/quest/check_tiles.py --lang fr
python games/pocket-depths/check_depths.py --lang fr
python games/pocket-depths-2/check_depths2.py --lang fr
python games/pocket-invaders/check_invaders.py --lang fr
python games/pocket-runner/check_runner.py --lang fr
python games/pocket-rally/check_rally.py --lang fr
python games/pocket-vector/check_vector.py --lang fr
python games/pocket-clash/check_clash.py --lang fr
python tests/check_g80x32_ports.py --lang fr
python tests/check_g850_backend.py --lang fr --assembler "sjasmplus.exe"
python games/pocket-jumper/check_jumper.py --lang fr
python games/pocket-jumper/check_assets.py --lang fr --assembler "sjasmplus.exe"
python games/pocket-jumper/check_g850.py --lang fr
python games/pocket-depths-2/check_g850.py --lang fr
python games/quest/check_g850.py --lang fr
python games/pocket-invaders/check_g850.py --lang fr
python games/pocket-runner/check_g850.py --lang fr
python games/pocket-rally/check_g850.py --lang fr
```

Le contrôle de publication vérifie les liens et ancres des README, les empreintes des manifestes, la correspondance BIN/IHX, les checksums et les réservations mémoire. Il utilise uniquement Python standard et s’exécute aussi avant la création de l’archive. Les vérifications CPU exécutent les binaires Z80 avec des contrats IOCS simulés et nécessitent `z80==1.2.0`. Cette dépendance n’est nécessaire ni pour assembler ni pour jouer.

## Graphismes

Le format de pixels utilise **480 octets** : quatre bandes de 120 colonnes, avec sept bits utiles par octet. Le point `(x,y)` est à `120*(y//7)+x`, masque `1<<(y%7)`. Envoyer chaque bande par `PCG_IOCS_PATTERN`, avec D=ligne, E=colonne de caractère et B=nombre de colonnes de pixels. Le LCD physique conserve ses interstices entre cellules. Les chiffres du panneau peuvent utiliser la police native de la ROM.

Voir `games/pocket-jumper/render.asm` pour la composition des sprites avec découpage, `games/pocket-depths-2/raycaster.asm` pour le DDA en virgule fixe et `include/sharp-pc-g8xx.inc` pour les contrats IOCS.

Le [profil de développement G850](G850.md#francais) utilise un tampon distinct de 864 octets et l’include `sharp_pc_g850.inc`. [Pocket Vector](../games/pocket-vector/README.md#francais) est un prototype jouable sur ce profil. L’[étude du moteur](../designs/pocket-vector/README.md#francais) détaille la projection au sol et ses budgets de calcul.

## g800

```text
python tools/play_jumper.py --lang fr --emulator "g800.exe"
```

Le même principe s’applique à `play_quest.py`, `play_rally.py`, `play_runner.py`, `play_invaders.py`, `play_star.py`, `play_depths.py` et `play_depths2.py`. `play_clash.py` / `play_vector.py` sélectionne le profil PC-G850. Ajouter `--lite` pour Depths Lite. g800 s’installe séparément. Les lanceurs utilisent les IOCS simulés sans ROM. Les outils de capture Windows facultatifs nécessitent `tools/requirements-capture.txt` et ne capturent que le LCD.

Pour Quest, Invaders, Runner, Rally, Jumper, Star Lane et Depths 1/2, ajouter **`--model PC-G850`** au lanceur. `python tools/capture_g850_games.py --lang fr --emulator "g800.exe"` produit leurs captures LCD et vérifie les pixels des fenêtres de jeu et des portraits de combat contre le tampon calculé par le programme Z80. Les situations de capture sont préparées ; les fichiers temporaires de capture ne remplacent jamais les programmes distribués.

## Archive de publication

```text
python tools/package_collection.py --lang fr
```

Crée un ZIP et son fichier SHA-256 dans `../deliverables/`, en excluant environnements, préférences personnelles, caches et rapports locaux.


Pocket Vector et Pocket Clash : `--target g80x-32k` construit ou lance le profil 32 Kio ; `--target g850` conserve le profil natif. Les constructions sans sélecteur génèrent les deux profils. Les fichiers G850 sont dans `build/g850/`. [Chargement G80X 32 Ko](G80X_32K.md#francais).


## Animations de la galerie

```text
python tools/capture_animations.py --lang fr --emulator "g800.exe"
```

Produit les cinq GIF G850 depuis les binaires distribués : Vector, Clash, Jumper, Rally et Depths 2. `--game jumper` sélectionne un seul jeu. Chaque image passe par g800 et ses pixels graphiques sont comparés à l’exécution Z80. Les compteurs utilisent la police native ; la cadence du GIF est une présentation indicative. Les captures temporaires et rapports restent hors distribution.
