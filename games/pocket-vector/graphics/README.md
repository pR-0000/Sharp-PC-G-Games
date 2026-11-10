# Sprites BMP / BMP sprites

[Français](#francais) · [English](#english)

<a id="francais"></a>

## Français

Ces **22 BMP sont les sources graphiques utilisées par le jeu**. Les fichiers existants sont lus sans être modifiés par la construction.

| Série | Fichiers BMP |
|---|---|
| Joueur, 23 × 11, orientations disponibles | [Nord](player_north.bmp) · [Nord-ouest](player_north_west.bmp) · [Ouest](player_west.bmp) · [Sud-ouest](player_west_south.bmp) · [Sud](player_south.bmp) · [Sud-est](player_east_south.bmp) · [Est](player_east.bmp) · [Nord-est](player_north_east.bmp) |
| Adversaire A, largeurs en pixels | [3](rival_a_03.bmp) · [5](rival_a_05.bmp) · [7](rival_a_07.bmp) · [9](rival_a_09.bmp) · [11](rival_a_11.bmp) · [15](rival_a_15.bmp) |
| Adversaire B, largeurs en pixels | [3](rival_b_03.bmp) · [5](rival_b_05.bmp) · [7](rival_b_07.bmp) · [9](rival_b_09.bmp) · [11](rival_b_11.bmp) · [15](rival_b_15.bmp) |
| Flammes, 5 × 2 | [0](exhaust_0.bmp) · [1](exhaust_1.bmp) |

La vrille rapide parcourt **Nord, Ouest, Sud, Est deux fois**, soit huit images de jeu au total, sans tourner la caméra. Les huit orientations restent compilées et modifiables. La conduite normale utilise Nord, Nord-ouest et Nord-est. Les images exactement identiques ou symétriques partagent automatiquement leurs données ; un miroir horizontal au rendu reproduit chaque dessin. Une différence d’un seul pixel suffit à conserver une image séparée. Toutes les sources BMP restent disponibles pour l’édition.

[Planche BMP complète](../docs/sprites.bmp) : une pose sous l’autre dans des cellules de **24 × 16 pixels**, dans l’ordre du tableau. [Aperçu agrandi et légendé](../docs/sprites_preview.png) · [Animation de la vrille](../docs/vector_spin_z80.gif).

### Modifier et intégrer

1. Modifier un **BMP individuel de ce dossier**, en conservant ses dimensions.
2. Utiliser **noir `#000000`**, **blanc `#FFFFFF`** et **gris `#808080`**. Le gris signifie **transparent** ; noir et blanc sont opaques. Les gris neutres très clairs, de `#F0F0F0` à `#FFFFFF`, sont interprétés comme blancs à l’import sans modifier le fichier source.
3. Enregistrer sans compression, idéalement en BMP 24 bits. Éviter l’anticrénelage et les redimensionnements interpolés.
4. Reconstruire depuis la racine :

```text
python games/pocket-vector/build_vector.py --lang fr --assembler "chemin/vers/sjasmplus.exe"
```

La construction régénère les planches et les fichiers IHX FR/EN de chaque cible, en conservant les BMP. Les sprites sont compactés sur **deux bits par pixel** (trois états, pas de niveaux de gris LCD). Les petites tailles adverses sont dessinées séparément pour rester lisibles ; elles ne sont pas remplacées automatiquement à partir d’une grande pose.

La planche `docs/sprites.bmp` est un export : la modifier seule ne change pas le jeu. La palette et les dimensions des BMP sources sont contrôlées à la construction.

Code et graphismes : MIT, © 2026 P.RAIMBAULT. [Guide du jeu](../README.md#francais).

---

<a id="english"></a>

## English

These **22 BMP files are the graphics sources used by the game**. Building reads existing files without modifying them. The table above links every source: eight 23 × 11 player views, six sizes for each opponent and two exhaust frames.

The fast spin follows **north, west, south, east twice**: eight game frames total, with no camera rotation. All eight source orientations remain compiled and editable. Normal steering uses north, north-west and north-east. Exactly identical or mirrored frames share data automatically; runtime horizontal mirroring reproduces each drawing. Even a one-pixel difference retains a separate image. Every source BMP remains available for editing.

[Complete BMP sheet](../docs/sprites.bmp) stacks frames vertically in **24 × 16 pixel cells**, in table order. [Enlarged labelled preview](../docs/sprites_preview.png) · [Spin animation](../docs/vector_spin_z80.gif).

### Edit and build

1. Edit an **individual BMP in this folder**, preserving its dimensions.
2. Use **black `#000000`**, **white `#FFFFFF`** and **grey `#808080`**. Grey means **transparent**; black and white are opaque. Neutral near-whites from `#F0F0F0` through `#FFFFFF` are imported as white without changing the source file.
3. Save without compression, preferably as 24-bit BMP. Avoid antialiasing and interpolated resizing.
4. Rebuild from the repository root:

```text
python games/pocket-vector/build_vector.py --lang en --assembler "path/to/sjasmplus.exe"
```

The build updates the sheets and each target’s FR/EN IHX files while preserving the BMPs. Sprites use **two bits per pixel** for three states, not LCD greyscale. Small opponent sizes are authored independently for readability and are not automatically replaced by scaling a large pose.

`docs/sprites.bmp` is an export: editing that sheet alone does not change the game. The build validates source BMP palette and dimensions.

Code and artwork: MIT, © 2026 P.RAIMBAULT. [Game guide](../README.md#english).
