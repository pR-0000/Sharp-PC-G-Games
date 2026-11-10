# Piste, références et niveaux de gris / Track, references and greyscale

[Français](#francais) · [English](#english)

<a id="francais"></a>

## Français

### Une piste qui laisse piloter

La largeur utile du circuit de référence est passée de **7,8 à 11 unités**, soit **+41 %**. Les bordures d’une unité se trouvent à l’extérieur de cette surface. Le [plan BMP](docs/track.bmp) et les maquettes utilisent cette même géométrie. La carte de collision renvoyée par `build_track()` suit également cette largeur.

Le premier jeu devrait conserver cette largeur confortable dans les virages, ralentir progressivement sur les accotements et éviter de transformer chaque contact en arrêt brutal. Le paramètre `--road-half-width` permet d’essayer d’autres largeurs dans les maquettes ; il ne change pas le nombre de pixels calculés par le noyau.

### Ce que montrent les sources de G-KART

L’auteur distribue bien les **sources et le binaire** dans [gkart20120728.zip](https://ver0.sakura.ne.jp/g800/gkart20120728.zip), depuis sa [page G850](https://ver0.sakura.ne.jp/g800/). L’archive contient notamment `geo.asm`, `game.asm`, `move.asm`, les circuits BMP et `mktbl.c`.

L’examen du code montre trois idées utiles :

- `mktbl.c` prépare huit tables de coordonnées de 24 × 24 points, complétées par les symétries des quadrants. Cela échange de la mémoire contre les calculs pendant la course.
- `geo.asm` développe chaque échantillon en un motif de **6 × 2 pixels** et écrit directement vers le LCD. Les tons de ce rendu sont des **trames spatiales**, sans alternance temporelle dans cette boucle.
- `game.asm` espace les lectures des groupes clavier par les calculs du jeu et traite séparément piste, terrain ralentissant et collisions.

Le jeu constitue donc une référence concrète pour le G850, sans démontrer la cadence du noyau de cette étude. Le rendu retenu utilise le parcours Q8.8 par lignes, les chiffres à résolution native et des vaisseaux indépendants. Un pilote LCD direct et la composition dans l’ordre des pages sont les premières optimisations à étudier.

Les principaux fichiers assembleur portent une notice à deux clauses de type BSD, © 2012 maruhiro. Une éventuelle adaptation devra conserver leur notice et leurs conditions. Aucun code ni graphisme G-KART n’est intégré à cette étude.

### Direction graphique

[QL-Zero](https://github.com/pR-0000/QL-Zero) inspire la silhouette arrière du vaisseau, le cockpit, les deux propulseurs et la lisibilité des bordures. Le nouveau [sprite natif de 19 × 11 pixels](docs/ship.bmp) est redessiné pour cet écran ; les pixels et les assets couleur QL ne sont pas importés. Les chiffres restent noirs et blancs et le décor laisse une route claire.

### Niveaux de gris : la RAM suffit, le rafraîchissement demande un pilote

L’auteur fournit aussi un [exemple à quatre nuances](https://ver0.sakura.ne.jp/g800/4scales.zip). `4scales.asm` envoie alternativement deux plans compressés au contrôleur 40h/41h, avec des attentes inégales et réglables. C’est une alternance temporelle, différente des trames de G-KART. Son README prévient que l’émulateur ne reproduit pas fidèlement le résultat.

Pour une image de jeu non compressée en 144 × 48 :

| Organisation en RAM | Octets |
|---|---:|
| Une image monochrome | 864 |
| Deux plans pour une image à nuances | 1728 |
| Deux images à nuances, chacune avec deux plans | 3456 |

Deux plans alternés avec le même temps d’exposition permettent noir, blanc et un gris moyen. Des durées pondérées permettent quatre niveaux théoriques ; le résultat dépend de la réponse du LCD et demande un réglage sur le modèle réel. Ces octets s’ajoutent à la carte, au programme et à son état.

La préparation du prochain décor et l’alternance des plans sont deux tâches distinctes. **Il ne faut pas recalculer le sol à chaque alternance.** Le pilote doit réafficher les plans terminés à cadence régulière, même si le prochain décor prend une centaine de millisecondes à produire. Alterner seulement à la cadence du jeu ferait clignoter l’image.

La voie IOCS de référence n’est pas adaptée à ce service : dans le modèle g800, un transfert complet coûte environ 147 480 cycles, soit 18,4 ms à 8 MHz. À 60 transferts/s, ce service dépasserait déjà à lui seul le budget CPU. Ce calcul n’est ni une fréquence de gris recommandée ni une mesure sur machine. Un pilote direct est beaucoup moins coûteux en principe, mais ses attentes LCD et sa cadence stable restent à mesurer.

Décision proposée : **monochrome par défaut pendant la course**, puis option de gris expérimentale avec pilote rapide et répartition du calcul en petites tranches. Une zone grisée limitée, ou un écran de titre statique, constitue une première étape moins coûteuse. Garder aussi une image monochrome nette pour les photos : une exposition courte peut capturer un seul plan ou des bandes.

Cette étude n’installe pas de gestionnaire d’interruption et ne modifie pas l’état du LCD. L’implémentation du gris devra préserver la pile, les registres, le défilement et l’état des interruptions du firmware, et être validée sur un PC-G850.

---

<a id="english"></a>

## English

### Room to drive

The reference road’s usable width is now **11 world units instead of 7.8**, an increase of **41%**. One-unit borders sit outside this area. The [BMP map](docs/track.bmp), concept images and collision map returned by `build_track()` share this geometry.

The first game should retain generous corners, slow down progressively on shoulders and avoid abrupt stops on every contact. `--road-half-width` allows further concept comparisons without changing the kernel’s sample count.

### What G-KART’s source shows

The author distributes **source and binary** in [gkart20120728.zip](https://ver0.sakura.ne.jp/g800/gkart20120728.zip), linked from the [G850 page](https://ver0.sakura.ne.jp/g800/). It contains `geo.asm`, `game.asm`, `move.asm`, BMP circuits and `mktbl.c`.

Three useful ideas emerge from the code:

- `mktbl.c` prepares eight 24 × 24 coordinate tables and uses quadrant symmetry, trading memory for runtime work.
- `geo.asm` expands samples into **6 × 2 pixel** patterns and writes directly to the LCD. These shades are **spatial dithering**, without temporal alternation in that loop.
- `game.asm` separates keyboard-group reads with game calculations and distinguishes road, slowing terrain and wall collisions.

This is a concrete G850 reference, not a benchmark of this study’s kernel. The chosen renderer uses Q8.8 scanlines, native-resolution digits and independent ships. Direct LCD output and page-order composition are the first optimisation candidates.

The main assembly files carry a two-clause BSD-style notice, © 2012 maruhiro. Any future adaptation must retain its notice and conditions. No G-KART code or artwork is integrated here.

### Art direction

[QL-Zero](https://github.com/pR-0000/QL-Zero) inspires the rear silhouette, cockpit, twin engines and readable road edges. The new [19 × 11 native sprite](docs/ship.bmp) is drawn for this display; QL pixels and colour assets are not imported. Digits stay monochrome and the road remains clear.

### Greyscale: enough RAM, but a dedicated refresh driver is needed

The author also provides a [four-shade example](https://ver0.sakura.ne.jp/g800/4scales.zip). `4scales.asm` alternates two compressed planes through ports 40h/41h, with unequal adjustable waits. This is temporal modulation, unlike G-KART’s dithering. Its README warns that emulation does not accurately reproduce the display.

For uncompressed 144 × 48 game images:

| RAM arrangement | Bytes |
|---|---:|
| One monochrome image | 864 |
| Two planes for one shaded image | 1728 |
| Two shaded images, two planes each | 3456 |

Equal plane exposure provides black, white and a middle grey. Weighted exposure allows four theoretical levels; actual shades depend on the LCD and need hardware calibration. These buffers come in addition to the program, world map and game state.

Rendering the next scene and alternating the completed planes are separate jobs. **Do not recalculate the floor for each alternation.** The driver needs regular refresh even when preparing the next scene takes around a hundred milliseconds. Alternating only at game frame rate would flicker.

The reference IOCS path does not fit that service: g800 models a full upload at roughly 147,480 cycles, or 18.4 ms at 8 MHz. At 60 uploads/s, refresh alone would exceed the CPU budget. This is neither a recommended greyscale rate nor a hardware measurement. Direct output should be much cheaper, but LCD wait times and stable cadence still need measurement.

Proposed approach: **monochrome racing by default**, followed by experimental greyscale with a fast driver and rendering split into small work slices. A limited shaded area or static title screen is a cheaper first step. Keep a crisp monochrome photo option too: short camera exposures can capture a single plane or bands.

This study installs no interrupt handler and changes no LCD state. A greyscale implementation must preserve firmware stack, registers, scrolling and interrupt state, and be validated on a PC-G850.
