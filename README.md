# Sharp PC-G Games

Collection **0.9.0** · [Français](#francais) · [English](#english)

<a id="francais"></a>

## Français

Dix jeux Z80 pour **Sharp PC-G801 / PC-G805 et PC-G850**, en français et en anglais. Fichiers prêts à charger, graphismes modifiables et sources assembleur inclus. Aucun assembleur ni dump ROM n’est nécessaire pour jouer.

### Les jeux

| Jeu et guide | Principe |
|---|---|
| [Pocket Vector](games/pocket-vector/README.md#francais) | Course futuriste en perspective : trois circuits, turbo, vrille et coupe. |
| [Pocket Clash](games/pocket-clash/README.md#francais) | Combat sur plateformes : quatre personnages, trois arènes et classement. |
| [Sharp PC-G Quest](games/quest/README.md#francais) | RPG avec exploration, équipement, cinq boss et défis de frappe. |
| [Pocket Jumper](games/pocket-jumper/README.md#francais) | Plateformes au pixel, sauts avec élan et nuages en parallaxe. |
| [Pocket Depths 2](games/pocket-depths-2/README.md#francais) | FPS à raycaster DDA : murs texturés, portes, clé et sentinelles. |
| [Pocket Rally](games/pocket-rally/README.md#francais) | Course vue de dessus, deux circuits et défilement au pixel. |
| [Pocket Runner](games/pocket-runner/README.md#francais) | Trois niveaux : échelles, cordes, or et pièges pour les gardes. |
| [Pocket Invaders](games/pocket-invaders/README.md#francais) | Arcade : envahisseurs animés, vagues et abris destructibles. |
| [Pocket Depths](games/pocket-depths/README.md#francais) | FPS à trois étages, trois armes et cartes modulaires ; édition Lite. |
| [Star Lane](games/star-lane/README.md#francais) | Shoot’em up : pirates, bouclier rechargeable et combos. |

Quest est issu de [Canon X-07 Quest](https://github.com/pR-0000/Canon_X-07_RPG).

![Pocket Vector — PC-G850, g800 LCD](games/pocket-vector/docs/vector_g850_race_g800.gif)

![Pocket Clash — PC-G850, g800 LCD](games/pocket-clash/docs/clash_g850_battle_g800.gif)

![Pocket Jumper — PC-G850, g800 LCD](games/pocket-jumper/docs/jumper_g850_scroll_g800.gif)

![Pocket Rally — PC-G850, g800 LCD](games/pocket-rally/docs/rally_g850_scroll_g800.gif)

![Pocket Depths 2 — PC-G850, g800 LCD](games/pocket-depths-2/docs/depths2_g850_turn_g800.gif)

[Galerie des captures](docs/DEMONSTRATION.md). Animations et captures montrent uniquement le LCD émulé, sans bordure de fenêtre. La cadence des GIF est indicative.

### Choisir le bon fichier

**Privilégier les fichiers `.ihx`** : format Intel HEX avec adresses de chargement et sommes de contrôle. `.hex` est une autre extension du même format ; les `.bin` restent disponibles pour les autres outils. FR/EN indique la langue.

Chaque jeu suit la même organisation :

```text
games/<game>/build/
  g80x/       G801/G805, écran à cellules
  g80x-32k/   G801/G805 avec 32 Kio (Vector et Clash)
  g850/       G850, écran graphique 144 × 48
```

Seuls les profils disponibles sont présents. **Les binaires G850 et G80X sont différents.** La compatibilité G815 et G850S/V/VS n’est pas présumée : voir les [modèles ciblés](docs/COMPATIBILITY.md).

<a id="g80x-francais"></a>

### G80X — G801/G805

Les versions ci-dessous tiennent sur G801 de 8 Kio **sauf Pocket Depths complète**, destinée au G805 ; choisir Lite sur G801.

| Jeu | Français | English | USER |
|---|---|---|---|
| Sharp PC-G Quest | [FR](games/quest/build/g80x/quest_FR.ihx) | [EN](games/quest/build/g80x/quest_EN.ihx) | `USER17E2` |
| Pocket Jumper | [FR](games/pocket-jumper/build/g80x/jumper_FR.ihx) | [EN](games/pocket-jumper/build/g80x/jumper_EN.ihx) | `USER14FF` |
| Pocket Depths 2 | [FR](games/pocket-depths-2/build/g80x/depths2_FR.ihx) | [EN](games/pocket-depths-2/build/g80x/depths2_EN.ihx) | `USER13FF` |
| Pocket Rally | [FR](games/pocket-rally/build/g80x/rally_FR.ihx) | [EN](games/pocket-rally/build/g80x/rally_EN.ihx) | `USER17E2` |
| Pocket Runner | [FR](games/pocket-runner/build/g80x/runner_FR.ihx) | [EN](games/pocket-runner/build/g80x/runner_EN.ihx) | `USER0FFF` |
| Pocket Invaders | [FR](games/pocket-invaders/build/g80x/invaders_FR.ihx) | [EN](games/pocket-invaders/build/g80x/invaders_EN.ihx) | `USER0BFF` |
| Pocket Depths (G805) | [FR](games/pocket-depths/build/g80x/depths_FR.ihx) | [EN](games/pocket-depths/build/g80x/depths_EN.ihx) | `USER19FF` |
| Pocket Depths Lite | [FR](games/pocket-depths/build/g80x/depths_lite_FR.ihx) | [EN](games/pocket-depths/build/g80x/depths_lite_EN.ihx) | `USER17E2` |
| Star Lane | [FR](games/star-lane/build/g80x/star_lane_FR.ihx) | [EN](games/star-lane/build/g80x/star_lane_EN.ihx) | `USER09FF` |

<a id="g80x-32k-francais"></a>

### G80X — 32 Kio de RAM

**32 Kio doivent être reconnus par le firmware.** Sur G801 étendu, cocher l’extension RAM dans Sharp PC-G Link 1.8.1 ou ultérieure. [Guide mémoire](docs/G80X_32K.md#francais).

| Jeu | Français | English | USER |
|---|---|---|---|
| Pocket Vector | [FR](games/pocket-vector/build/g80x-32k/vector_g80x_32k_FR.ihx) | [EN](games/pocket-vector/build/g80x-32k/vector_g80x_32k_EN.ihx) | `USER6BFF` |
| Pocket Clash | [FR](games/pocket-clash/build/g80x-32k/clash_g80x_32k_FR.ihx) | [EN](games/pocket-clash/build/g80x-32k/clash_g80x_32k_EN.ihx) | `USER59FF` |

<a id="g850-francais"></a>

### PC-G850

| Jeu | Français | English | USER |
|---|---|---|---|
| Pocket Vector | [FR](games/pocket-vector/build/g850/vector_FR.ihx) | [EN](games/pocket-vector/build/g850/vector_EN.ihx) | `USER6DFF` |
| Pocket Clash | [FR](games/pocket-clash/build/g850/clash_g850_FR.ihx) | [EN](games/pocket-clash/build/g850/clash_g850_EN.ihx) | `USER55FF` |
| Sharp PC-G Quest | [FR](games/quest/build/g850/quest_g850_FR.ihx) | [EN](games/quest/build/g850/quest_g850_EN.ihx) | `USER1FFF` |
| Pocket Jumper | [FR](games/pocket-jumper/build/g850/jumper_g850_FR.ihx) | [EN](games/pocket-jumper/build/g850/jumper_g850_EN.ihx) | `USER19FF` |
| Pocket Depths 2 | [FR](games/pocket-depths-2/build/g850/depths2_g850_FR.ihx) | [EN](games/pocket-depths-2/build/g850/depths2_g850_EN.ihx) | `USER16FF` |
| Pocket Rally | [FR](games/pocket-rally/build/g850/rally_g850_FR.ihx) | [EN](games/pocket-rally/build/g850/rally_g850_EN.ihx) | `USER19FF` |
| Pocket Runner | [FR](games/pocket-runner/build/g850/runner_g850_FR.ihx) | [EN](games/pocket-runner/build/g850/runner_g850_EN.ihx) | `USER11FF` |
| Pocket Invaders | [FR](games/pocket-invaders/build/g850/invaders_g850_FR.ihx) | [EN](games/pocket-invaders/build/g850/invaders_g850_EN.ihx) | `USER0DFF` |
| Pocket Depths | [FR](games/pocket-depths/build/g850/depths_g850_FR.ihx) | [EN](games/pocket-depths/build/g850/depths_g850_EN.ihx) | `USER1EFF` |
| Star Lane | [FR](games/star-lane/build/g850/star_lane_g850_FR.ihx) | [EN](games/star-lane/build/g850/star_lane_g850_EN.ihx) | `USER0BFF` |

### Charger et jouer

Utiliser une interface série Sharp compatible et [Sharp PC-G Link](https://github.com/pR-0000/Sharp-PC-G-Link), disponible en [version Windows autonome](https://github.com/pR-0000/Sharp-PC-G-Link/releases/latest).

1. Sauvegarder les programmes à conserver. Sélectionner le modèle réel dans Link.
2. Régler Link et **TEXT → Sio → Format** de façon identique : **4800 bauds / 8N1 / RS/CS / CR LF / EOF 1A**, puis valider avec ENTER.
3. Depuis BASIC/RUN, saisir **MON**, la commande **USER** du tableau correspondant, puis **R** ; valider chaque commande.
4. Choisir le `.ihx` et cliquer sur **Envoyer ASM**. Attendre la fin de réception sur le Sharp.
5. Saisir **G100**. Après chargement, **CALL &H100** lance aussi le jeu depuis BASIC. **Q / BREAK** quitte.

Charger un autre jeu remplace le code et son état à 0100h. En cas d’erreur ou de retour immédiat de `R`, revérifier **TEXT → Sio → Format**. [Chargement et dépannage](docs/LOADING.md) · [Lancement BASIC](docs/BASIC_CALL.md).

### Modifier et construire

Installer Python 3.10+ et [SjASMPlus](https://github.com/z00m128/sjasmplus). Depuis la racine du dépôt :

```text
python tools/build_all.py --lang fr --assembler "sjasmplus.exe"
```

La construction produit les deux langues pour toutes les cibles disponibles. Chaque `manifest.json` indique les tailles, commandes USER et empreintes SHA-256 des fichiers de sa cible. [Guide développeur](docs/DEVELOPMENT.md).

© 2026 P.RAIMBAULT. Jeux et outils originaux : [MIT](LICENSE.txt), [traduction française](LICENSE_FR.txt). Voir la [notice de Quest](games/quest/NOTICE.md) pour les éléments hérités. Aucune ROM Sharp ni exécutable tiers inclus. Projet indépendant, sans affiliation à Sharp.

---

<a id="english"></a>

## English

Ten Z80 games for **Sharp PC-G801 / PC-G805 and PC-G850**, in French and English. Ready-to-load files, editable graphics and assembly sources are included. No assembler or ROM dump is needed to play.

### Games

| Game and guide | Gameplay |
|---|---|
| [Pocket Vector](games/pocket-vector/README.md#english) | Perspective racing: three tracks, boost, spin attack and cup. |
| [Pocket Clash](games/pocket-clash/README.md#english) | Platform fighting: four characters, three arenas and standings. |
| [Sharp PC-G Quest](games/quest/README.md#english) | RPG with exploration, equipment, five bosses and typing challenges. |
| [Pocket Jumper](games/pocket-jumper/README.md#english) | Pixel platforming, momentum-based jumps and parallax clouds. |
| [Pocket Depths 2](games/pocket-depths-2/README.md#english) | DDA-raycast FPS: textured walls, doors, a key and sentinels. |
| [Pocket Rally](games/pocket-rally/README.md#english) | Overhead racing, two tracks and pixel scrolling. |
| [Pocket Runner](games/pocket-runner/README.md#english) | Three levels with ladders, ropes, gold and traps for guards. |
| [Pocket Invaders](games/pocket-invaders/README.md#english) | Arcade: animated invaders, waves and destructible shelters. |
| [Pocket Depths](games/pocket-depths/README.md#english) | Three-floor FPS, three weapons and modular maps; Lite edition. |
| [Star Lane](games/star-lane/README.md#english) | Shoot ’em up: pirates, rechargeable shield and combos. |

Quest is based on [Canon X-07 Quest](https://github.com/pR-0000/Canon_X-07_RPG).

![Pocket Vector — PC-G850, g800 LCD](games/pocket-vector/docs/vector_g850_race_g800.gif)

![Pocket Clash — PC-G850, g800 LCD](games/pocket-clash/docs/clash_g850_battle_g800.gif)

![Pocket Jumper — PC-G850, g800 LCD](games/pocket-jumper/docs/jumper_g850_scroll_g800.gif)

![Pocket Rally — PC-G850, g800 LCD](games/pocket-rally/docs/rally_g850_scroll_g800.gif)

![Pocket Depths 2 — PC-G850, g800 LCD](games/pocket-depths-2/docs/depths2_g850_turn_g800.gif)

[Screenshot gallery](docs/DEMONSTRATION_EN.md). Animations and screenshots show only the emulated LCD, without window borders. GIF timing is illustrative.

### Choose the correct file

**Use `.ihx` files**: Intel HEX with load addresses and checksums. `.hex` is another extension for the same format; `.bin` files remain available for other tools. FR/EN select the language.

Each game uses the same layout:

```text
games/<game>/build/
  g80x/       G801/G805, cell-based LCD
  g80x-32k/   G801/G805 with 32 KiB (Vector and Clash)
  g850/       G850, 144 × 48 graphical LCD
```

Only supported profiles are present. **G850 and G80X binaries are different.** G815 and G850S/V/VS compatibility is not assumed: see [target models](docs/COMPATIBILITY_EN.md).

<a id="g80x-english"></a>

### G80X — G801/G805

All builds below fit a stock 8 KiB G801 **except full Pocket Depths**, which targets G805; choose Lite on G801.

| Game | French | English | USER |
|---|---|---|---|
| Sharp PC-G Quest | [FR](games/quest/build/g80x/quest_FR.ihx) | [EN](games/quest/build/g80x/quest_EN.ihx) | `USER17E2` |
| Pocket Jumper | [FR](games/pocket-jumper/build/g80x/jumper_FR.ihx) | [EN](games/pocket-jumper/build/g80x/jumper_EN.ihx) | `USER14FF` |
| Pocket Depths 2 | [FR](games/pocket-depths-2/build/g80x/depths2_FR.ihx) | [EN](games/pocket-depths-2/build/g80x/depths2_EN.ihx) | `USER13FF` |
| Pocket Rally | [FR](games/pocket-rally/build/g80x/rally_FR.ihx) | [EN](games/pocket-rally/build/g80x/rally_EN.ihx) | `USER17E2` |
| Pocket Runner | [FR](games/pocket-runner/build/g80x/runner_FR.ihx) | [EN](games/pocket-runner/build/g80x/runner_EN.ihx) | `USER0FFF` |
| Pocket Invaders | [FR](games/pocket-invaders/build/g80x/invaders_FR.ihx) | [EN](games/pocket-invaders/build/g80x/invaders_EN.ihx) | `USER0BFF` |
| Pocket Depths (G805) | [FR](games/pocket-depths/build/g80x/depths_FR.ihx) | [EN](games/pocket-depths/build/g80x/depths_EN.ihx) | `USER19FF` |
| Pocket Depths Lite | [FR](games/pocket-depths/build/g80x/depths_lite_FR.ihx) | [EN](games/pocket-depths/build/g80x/depths_lite_EN.ihx) | `USER17E2` |
| Star Lane | [FR](games/star-lane/build/g80x/star_lane_FR.ihx) | [EN](games/star-lane/build/g80x/star_lane_EN.ihx) | `USER09FF` |

<a id="g80x-32k-english"></a>

### G80X — 32 KiB RAM

**32 KiB must be recognized by the firmware.** For an expanded G801, enable the RAM expansion option in Sharp PC-G Link 1.8.1 or later. [Memory guide](docs/G80X_32K.md#english).

| Game | French | English | USER |
|---|---|---|---|
| Pocket Vector | [FR](games/pocket-vector/build/g80x-32k/vector_g80x_32k_FR.ihx) | [EN](games/pocket-vector/build/g80x-32k/vector_g80x_32k_EN.ihx) | `USER6BFF` |
| Pocket Clash | [FR](games/pocket-clash/build/g80x-32k/clash_g80x_32k_FR.ihx) | [EN](games/pocket-clash/build/g80x-32k/clash_g80x_32k_EN.ihx) | `USER59FF` |

<a id="g850-english"></a>

### PC-G850

| Game | French | English | USER |
|---|---|---|---|
| Pocket Vector | [FR](games/pocket-vector/build/g850/vector_FR.ihx) | [EN](games/pocket-vector/build/g850/vector_EN.ihx) | `USER6DFF` |
| Pocket Clash | [FR](games/pocket-clash/build/g850/clash_g850_FR.ihx) | [EN](games/pocket-clash/build/g850/clash_g850_EN.ihx) | `USER55FF` |
| Sharp PC-G Quest | [FR](games/quest/build/g850/quest_g850_FR.ihx) | [EN](games/quest/build/g850/quest_g850_EN.ihx) | `USER1FFF` |
| Pocket Jumper | [FR](games/pocket-jumper/build/g850/jumper_g850_FR.ihx) | [EN](games/pocket-jumper/build/g850/jumper_g850_EN.ihx) | `USER19FF` |
| Pocket Depths 2 | [FR](games/pocket-depths-2/build/g850/depths2_g850_FR.ihx) | [EN](games/pocket-depths-2/build/g850/depths2_g850_EN.ihx) | `USER16FF` |
| Pocket Rally | [FR](games/pocket-rally/build/g850/rally_g850_FR.ihx) | [EN](games/pocket-rally/build/g850/rally_g850_EN.ihx) | `USER19FF` |
| Pocket Runner | [FR](games/pocket-runner/build/g850/runner_g850_FR.ihx) | [EN](games/pocket-runner/build/g850/runner_g850_EN.ihx) | `USER11FF` |
| Pocket Invaders | [FR](games/pocket-invaders/build/g850/invaders_g850_FR.ihx) | [EN](games/pocket-invaders/build/g850/invaders_g850_EN.ihx) | `USER0DFF` |
| Pocket Depths | [FR](games/pocket-depths/build/g850/depths_g850_FR.ihx) | [EN](games/pocket-depths/build/g850/depths_g850_EN.ihx) | `USER1EFF` |
| Star Lane | [FR](games/star-lane/build/g850/star_lane_g850_FR.ihx) | [EN](games/star-lane/build/g850/star_lane_g850_EN.ihx) | `USER0BFF` |

### Load and play

Use a compatible Sharp serial adapter and [Sharp PC-G Link](https://github.com/pR-0000/Sharp-PC-G-Link), available as a [standalone Windows release](https://github.com/pR-0000/Sharp-PC-G-Link/releases/latest).

1. Back up programs to keep. Select the actual Sharp model in Link.
2. Match Link and **TEXT → Sio → Format**: **4800 baud / 8N1 / RS/CS / CR LF / EOF 1A**, then confirm with ENTER.
3. From BASIC/RUN, enter **MON**, the **USER** command from the matching table, then **R**; confirm each command.
4. Select the `.ihx` file and click **Send ASM**. Wait for reception to finish on the Sharp.
5. Enter **G100**. After loading, **CALL &H100** also starts the game from BASIC. **Q / BREAK** quits.

Loading another game replaces the code and its state at 0100h. If reception fails or `R` returns immediately, recheck **TEXT → Sio → Format**. [Loading and troubleshooting](docs/LOADING_EN.md) · [BASIC launch](docs/BASIC_CALL_EN.md).

### Modify and build

Install Python 3.10+ and [SjASMPlus](https://github.com/z00m128/sjasmplus). From the repository root:

```text
python tools/build_all.py --lang en --assembler "sjasmplus.exe"
```

Builds both languages for all available targets. `manifest.json` records sizes, USER commands and SHA-256 hashes beside each target’s files. [Developer guide](docs/DEVELOPMENT_EN.md).

© 2026 P.RAIMBAULT. Original games and tools: [MIT](LICENSE.txt). See [Quest’s notice](games/quest/NOTICE_EN.md) for inherited material. No Sharp ROM or third-party executable is included. Independent project, unaffiliated with Sharp.
