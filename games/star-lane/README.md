# Star Lane

[Français](#francais) · [English](#english)

<a id="francais"></a>

## Français

[Collection](../../README.md#francais)

Déplacer le vaisseau entre trois couloirs, éviter les astéroïdes et ramasser les étoiles. Trois vies ; chaque avancée vaut un point, chaque étoile 25 points. Le score est plafonné à 9999. Les graphismes sont des motifs logiciels de 5 × 7 pixels.

![Star Lane dans g800](docs/star_lane_g800.png)

### Chargement

Fichiers : [français](../../build/star_lane_FR.hex), [anglais](../../build/star_lane_EN.hex), ou leurs variantes BIN. Régler la liaison en 4800 / 8N1 / RS/CS, puis depuis BASIC :

```text
MON
USER05FF
R
```

Envoyer avec **Assembleur → Envoyer ASM** dans Sharp PC-G Link, attendre la réception, puis `G100`. Origine et entrée BIN : 0100h. [Guide complet](../../docs/LOADING.md).

| Touche | Action |
|---|---|
| ENTER / ESPACE | Démarrer, rejouer |
| ↑ / ↓, W ou Z / S | Changer de couloir |
| P | Pause / reprise |
| R | Nouvelle partie |
| Q / BREAK | Retour au moniteur |

Relâcher entre deux déplacements. Trois vies et une courte invulnérabilité après une collision. Pendant la pause, P, R et les sorties restent actifs.

### Sources

`star_lane.asm` utilise `include/sharp_pc_g801.inc` et `lib/pcg801_runtime.asm`. Les deux langues sont construites par `python tools/build_all.py --lang fr` depuis la racine, avec SjASMPlus dans PATH ou l'option `--assembler`. La constante `STEP_POLLS`, 48 par défaut, règle le nombre de lectures clavier par avancée : l'augmenter ralentit le jeu.

Taille FR : 1195 octets ; EN : 1192 octets, état et buffers compris. La pile du moniteur est conservée et la sortie se fait par RET. Licence MIT, © 2026 P.RAIMBAULT.

---

<a id="english"></a>

## English

[Collection](../../README.md#english)

Move a ship between three lanes, avoid asteroids and collect stars. Three lives; each world step adds one point and each star adds 25. Score is capped at 9999. Graphics use custom software 5 × 7 patterns.

![Star Lane in g800](docs/star_lane_g800.png)

### Loading

Files: [French](../../build/star_lane_FR.hex), [English](../../build/star_lane_EN.hex), or matching BIN files. Set 4800 / 8N1 / RS/CS, then enter from BASIC:

```text
MON
USER05FF
R
```

Use **Assembly → Send ASM** in Sharp PC-G Link, wait for reception to finish, then enter `G100`. BIN origin and entry are 0100h. [Full guide](../../docs/LOADING_EN.md).

| Key | Action |
|---|---|
| ENTER / SPACE | Start, replay |
| ↑ / ↓, W or Z / S | Change lane |
| P | Pause / resume |
| R | New game |
| Q / BREAK | Return to monitor |

Release between moves. A hit grants brief invulnerability. P, R and exit keys remain active during pause.

### Sources

`star_lane.asm` uses `include/sharp_pc_g801.inc` and `lib/pcg801_runtime.asm`. Build both languages from the repository root with `python tools/build_all.py --lang en`, using SjASMPlus in PATH or `--assembler`. `STEP_POLLS`, default 48, sets keyboard scans per world step; increase it to slow the game. Physical-device timing remains to be checked.

FR size: 1195 bytes; EN: 1192 bytes, including state and buffers. The game retains the monitor stack and exits with RET. MIT license, © 2026 P.RAIMBAULT.
