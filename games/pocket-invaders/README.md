# Pocket Invaders 0.2.0

[Français](#francais) · [English](#english)

<a id="francais"></a>

## Français

[Collection](../../README.md#francais)

Un jeu d’arcade original en assembleur Z80 pour **Sharp PC-G801 / PC-G805** : deux rangées de huit envahisseurs animés, projectiles au pixel, trois abris destructibles et vagues successives. Les ennemis accélèrent lorsque leur nombre diminue. Trois vies, protection temporaire après un coup, explosions et record conservé tant que le programme reste en RAM.

![Scène de Pocket Invaders rendue dans g800](docs/invaders_fr_g800.png)

Captures LCD : **g800**.

### Terrain et panneau — 0.2.0

L’arène utilise désormais **90 × 28 points**, contre 120 × 21 auparavant. Score, vague, vies et nombre d’ennemis sont regroupés à droite, avec une séparation verticale. Les aliens démarrent à y=1 au lieu de y=8 ; les tirs peuvent traverser la première ligne. Les limites de déplacement, l’espacement des aliens et les abris sont adaptés à la nouvelle largeur.

### Charger sur le Sharp

[Français — HEX](build/invaders_FR.hex) · [English — HEX](build/invaders_EN.hex) · [Français — BIN](build/invaders_FR.bin) · [English — BIN](build/invaders_EN.bin)

1. Sauvegarder les programmes à conserver. Régler **TEXT → Sio → Format** sur **4800 / 8N1, RS/CS, CR LF, EOF 1A**, puis ENTER. Choisir les mêmes valeurs dans Sharp PC-G Link.
2. Depuis BASIC/RUN : **MON → USER0BFF → R**, chaque commande suivie d’ENTER.
3. Sélectionner le HEX dans **Envoyer ASM**, attendre la fin du transfert, puis saisir **G100** sur le Sharp.

Après réservation et chargement, **CALL &H100** depuis BASIC lance aussi le jeu. Le binaire FR occupe **2 666 octets**, l’anglais **2 653 octets** ; ils tiennent dans la mémoire du G801 sans extension. Ils remplacent le précédent programme à 0100h.

### Commandes et règles

| Touche | Action |
|---|---|
| ENTER / ESPACE à l’accueil | Commencer |
| ← / → ou A / D | Déplacer le vaisseau ; maintenir pour continuer |
| ESPACE / ENTER en jeu | Tirer ; maintenir pour répéter |
| F | Activer/désactiver le tir automatique ; indicateur A dans le panneau |
| P | Pause / reprise |
| M | Aide / retour |
| R | Recommencer ; conserver le record |
| Q / BREAK | Quitter vers l’appelant |

Le clavier renvoie une touche à la fois : le tir automatique permet de se déplacer en continu tout en tirant. Les tirs amis et ennemis endommagent les abris ; ceux-ci sont réparés à la vague suivante. Chaque ennemi vaut **10 points**. Le score est plafonné à **9 999**, le compteur de vagues à **99**. Si les envahisseurs atteignent la ligne du vaisseau ou si les trois vies sont perdues, la partie se termine. Le score utilise les chiffres classiques de la ROM Sharp ; le cœur et les sprites sont dessinés par le jeu.

### Construire et essayer dans g800

```text
python games/pocket-invaders/build_invaders.py --lang fr --assembler "chemin/vers/sjasmplus.exe"
python games/pocket-invaders/check_invaders.py --lang fr
python tools/play_invaders.py --lang fr --emulator "chemin/vers/g800.exe"
```

Sources : [invaders.asm](invaders.asm) et [render.asm](render.asm). Le constructeur utilise Python standard et SjASMPlus ; les tests seulement nécessitent `z80==1.2.0`. Aucun émulateur ni ROM n’est distribué.

© 2026 P.RAIMBAULT — [licence MIT](../../LICENSE.txt). Code et graphismes originaux ; aucune ressource d’un jeu commercial n’est incorporée.

---

<a id="english"></a>

## English

[Collection](../../README.md#english)

An original Z80 arcade game for **Sharp PC-G801 / PC-G805**: two rows of eight animated invaders, pixel projectiles, three destructible shields and successive waves. Enemies speed up as fewer remain. Three lives, brief protection after a hit, explosions and a best score retained while the program stays in RAM.

![Pocket Invaders rendered in g800](docs/invaders_en_g800.png)

LCD screenshots: **g800**.

### Arena and panel — 0.2.0

The arena now uses **90 × 28 pixels**, previously 120 × 21. Score, wave, lives and remaining enemies are grouped on the right, behind a vertical divider. Aliens start at y=1 instead of y=8; shots can cross the first display row. Movement limits, alien spacing and shields fit the new width.

### Load on Sharp

[French — HEX](build/invaders_FR.hex) · [English — HEX](build/invaders_EN.hex) · [French — BIN](build/invaders_FR.bin) · [English — BIN](build/invaders_EN.bin)

1. Back up programs you want to keep. Set **TEXT → Sio → Format** to **4800 / 8N1, RS/CS, CR LF, EOF 1A**, then ENTER. Use matching settings in Sharp PC-G Link.
2. From BASIC/RUN: **MON → USER0BFF → R**, confirming each command with ENTER.
3. Select the HEX using **Send ASM**, wait for transfer to finish, then run **G100** on Sharp.

After reservation and loading, **CALL &H100** from BASIC also starts the game. French occupies **2,666 bytes**, English **2,653 bytes**; both fit an unexpanded G801. Loading replaces the previous program at 0100h.

### Controls and rules

| Key | Action |
|---|---|
| ENTER / SPACE on title screen | Start |
| ← / → or A / D | Move; hold to continue |
| SPACE / ENTER in game | Fire; hold to repeat |
| F | Toggle automatic fire; A indicator in HUD |
| P | Pause / resume |
| M | Help / return |
| R | Restart; retain best score |
| Q / BREAK | Return to caller |

The keyboard reports one key at a time: automatic fire lets you keep moving while shooting. Friendly and enemy shots damage shields, which are repaired between waves. Each alien earns **10 points**. Score caps at **9,999**, wave number at **99**. Reaching the ship line or losing all three lives ends the game. Score digits use Sharp’s standard ROM font; the heart and sprites are drawn by the game.

### Build and try in g800

```text
python games/pocket-invaders/build_invaders.py --lang en --assembler "path/to/sjasmplus.exe"
python games/pocket-invaders/check_invaders.py --lang en
python tools/play_invaders.py --lang en --emulator "path/to/g800.exe"
```

Sources: [invaders.asm](invaders.asm) and [render.asm](render.asm). Building needs standard Python and SjASMPlus; only tests require `z80==1.2.0`. No emulator or ROM is distributed.

© 2026 P.RAIMBAULT — [MIT license](../../LICENSE.txt). Original code and graphics; no commercial-game assets are incorporated.
