# Charger les jeux

**Français** · [English](LOADING_EN.md) · [Collection](../README.md)

Ce parcours concerne les **PC-G801, PC-G805 et PC-G850**. Un même connecteur ne garantit pas les mêmes routines ROM sur les autres modèles.

**Pocket Vector et Pocket Clash sur G80X 32 Ko :** utiliser leurs fichiers `g80x_32k` et respectivement **USER6BFF** / **USER59FF**. Sur G801 étendu, activer **Extension RAM 32 Ko (G80X)** dans PC-G Link. [Guide et limites mémoire](G80X_32K.md#francais).

## Préparer le PC et la liaison

Utiliser une interface série prévue pour Sharp PC-G, avec **RTS/CTS** et les polarités adaptées. Un câble RS-232 à tensions positives/négatives ne se branche pas directement sur le connecteur Sharp. Pour une interface FTDI configurée pour ces machines, l'inversion TXD/RXD/RTS#/CTS# doit déjà être programmée dans l'EEPROM ; le logiciel ne le fait pas.

Installer **Sharp PC-G Link** depuis le [dépôt Sharp-PC-G-Link](https://github.com/pR-0000/Sharp-PC-G-Link). Voir [son installation](TRANSFER_TOOL.md). Choisir le port de l'adaptateur ; le [pilote FTDI VCP](https://ftdichip.com/drivers/vcp-drivers/) peut être nécessaire. Les préférences INI restent dans le dossier de l'utilitaire.

## Régler le Sharp

Dans **TEXT → Sio → Format**, puis sur le PC :

| Paramètre | Valeur conseillée |
|---|---|
| Débit | 4800 bauds |
| Data bit | 8 |
| Parity | none / aucune |
| Stop bit | 1 |
| Protocole | RS/CS ; RTS/CTS imposé côté PC |
| End of line | CR LF |
| End of file | 1A |

Valider les modifications sur le Sharp. Le bouton **Conseillés : 4800 / 8N1** règle le PC, pas le Sharp. Les valeurs initiales sont **1200 / 7N1** ; elles restent utilisables si les deux côtés correspondent.

## Recevoir le programme machine

Sauvegarder d'abord le contenu utile du Sharp. Depuis BASIC en mode RUN, saisir :

```text
MON
USER17E2
R
```

Cette réservation correspond à Quest dans les deux langues. Pour Star Lane, remplacer `USER17E2` par `USER09FF` ; pour le test de motifs, par `USER01FF` ; pour **Pocket Depths sur G805, par `USER19FF`**. Les nombres du moniteur sont hexadécimaux.

Dans **Sharp PC-G Link**, choisir le modèle réel, puis le fichier sous **Assembleur → Parcourir** :

- Quest (**G801/G805**) : `games/quest/build/g80x/quest_FR.ihx` ou `quest_EN.ihx`.
- Quest (**PC-G850**, `USER1FFF`) : `games/quest/build/g850/quest_g850_FR.ihx` / `quest_g850_EN.ihx`.
- Pocket Invaders (**PC-G850**, `USER0DFF`) : `games/pocket-invaders/build/g850/invaders_g850_FR.ihx` / `invaders_g850_EN.ihx`.
- Pocket Runner (**PC-G850**, `USER11FF`) : `games/pocket-runner/build/g850/runner_g850_FR.ihx` / `runner_g850_EN.ihx`.
- Pocket Rally (**PC-G850**, `USER19FF`): `games/pocket-rally/build/g850/rally_g850_FR.ihx` / `rally_g850_EN.ihx`.
- Pocket Clash (**PC-G850**, `USER55FF`): `games/pocket-clash/build/g850/clash_g850_FR.ihx` / `clash_g850_EN.ihx`.
- Pocket Vector (**PC-G850**, `USER6DFF`) : `games/pocket-vector/build/g850/vector_FR.ihx` ou `vector_EN.ihx`.
- Pocket Jumper (**PC-G850**, `USER19FF`) : `games/pocket-jumper/build/g850/jumper_g850_FR.ihx` / `jumper_g850_EN.ihx`.
- Pocket Depths 2 (**PC-G850**, `USER16FF`) : `games/pocket-depths-2/build/g850/depths2_g850_FR.ihx` / `depths2_g850_EN.ihx`.
- Star Lane (**PC-G850**, `USER0BFF`) : `games/star-lane/build/g850/star_lane_g850_FR.ihx` / `star_lane_g850_EN.ihx`.
- Pocket Depths (**PC-G850**, `USER1EFF`) : `games/pocket-depths/build/g850/depths_g850_FR.ihx` / `depths_g850_EN.ihx`.
- Star Lane : `games/star-lane/build/g80x/star_lane_FR.ihx` ou `star_lane_EN.ihx`.
- Pocket Rally (**G801/G805**, `USER17E2`) : `games/pocket-rally/build/g80x/rally_FR.ihx` / `rally_EN.ihx`.
- Pocket Jumper (**G801/G805**, `USER14FF`) : `games/pocket-jumper/build/g80x/jumper_FR.ihx` / `jumper_EN.ihx`.
- Pocket Runner (**G801/G805**, `USER0FFF`) : `games/pocket-runner/build/g80x/runner_FR.ihx` ou `runner_EN.ihx`.
- Pocket Depths (**sélectionner PC-G805**) : `games/pocket-depths/build/g80x/depths_FR.ihx` ou `depths_EN.ihx`.
- Pocket Depths Lite (**G801/G805**, `USER17E2`) : `games/pocket-depths/build/g80x/depths_lite_FR.ihx` ou `depths_lite_EN.ihx`.
- Pocket Depths 2 (**G801/G805**, `USER13FF`) : `games/pocket-depths-2/build/g80x/depths2_FR.ihx` ou `depths2_EN.ihx`.
- Test de motifs : `examples/build/g80x/glyph_demo_FR.ihx` ou `glyph_demo_EN.ihx`.

Cliquer sur **Envoyer ASM** après avoir préparé la réception avec `R`. Attendre la fin côté Sharp, puis saisir :

```text
G100
```

Tous ces programmes sont assemblés pour **0100h**. Les IHX contiennent leurs adresses ; pour un BIN, choisir **Chargement BIN = 0100**, **Entrée = 0100**. Changer le champ ne reloge pas le programme. Ne pas ajouter soi-même EOF 1A. **Q ou BREAK** quitte le jeu ; dans Quest, Q s'utilise sur la carte.

## Lancer depuis BASIC après le chargement

Utiliser **`CALL &H100`** en BASIC RUN après la réservation USER et la réception du code. Cette commande lance le code déjà en RAM ; elle ne charge pas un fichier. Le programme doit conserver la pile et terminer par RET. Voir le [guide BASIC](BASIC_CALL.md).

## Si la réception échoue

- **« Octets émis »** décrit l'émission côté PC, sans acquittement du fichier par le Sharp. Vérifier la fin de réception et le lancement sur la machine. CTS peut être actif alors que la réception n'est pas ouverte.
- **I/O DEVICE ERROR / ERROR 10** : vérifier le mode de réception, la trame, RS/CS, le câblage et les inversions FTDI. Pour un jeu assembleur, utiliser **MON → R**, pas **TEXT → Sio → Load** ni l'instruction BASIC `LOAD`.
- Si **FRE affiche environ 64 ko sur un G801 de 8 ko**, sauvegarder ce qui reste récupérable, faire **RESET** et répondre **Y** à **MEMORY CLEAR O.K. ?**. Cela efface la mémoire ; ne le faire que pour une situation incohérente. Recontrôler ensuite les réglages série.
- Le **test de motifs** et Star Lane permettent de vérifier le chargement et les appels graphiques avant un programme plus volumineux.

## Les exemples BASIC

Pour les listings de `examples/basic/` (Sharp-PC-G-Link), utiliser **Envoyer BASIC**, recevoir avec **TEXT → Sio → Load**, ouvrir **TEXT → Edit**, puis convertir avec **TEXT → Basic → Basic←text**, avant **RUN**. Cette conversion remplace le BASIC présent. Ce parcours est différent du chargement machine des jeux de la collection.

Références : [readrom, paramètres et commandes du moniteur](https://github.com/fu-sen/readrom), [émetteur SIO de z88dk](https://github.com/z88dk/z88dk/blob/master/examples/g800/send.py). Les réservations USER ci-dessus proviennent des binaires de cette collection, pas de celles du programme readrom.
