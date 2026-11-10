# Modèles ciblés et mémoire

**Français** · [English](COMPATIBILITY_EN.md) · [Collection](../README.md)

Les versions distribuées ciblent les **PC-G801 / PC-G805**, avec **Pocket Clash, Pocket Vector, Pocket Jumper, Pocket Depths 2, Quest, Pocket Invaders, Pocket Runner, Pocket Rally, Star Lane et Pocket Depths pour PC-G850**. Choisir le fichier destiné au modèle et à sa RAM. Un appel IOCS commun peut permettre à certains programmes simples de fonctionner sur plusieurs modèles ; la compatibilité de tous les jeux ne s’en déduit pas. Les pilotes LCD, le clavier, les espaces système et la géométrie doivent correspondre au profil visé.

### Trois profils d’affichage

| Profil | Écran utile | Tampon logiciel | État dans cette collection |
|---|---|---:|---|
| G80X / E200 à cellules | 24 × 4 cellules de 5 × 7, soit 120 × 28 points adressables, avec interstices physiques | 480 octets, quatre bandes de sept bits | Versions G801/G805 ; autres modèles à vérifier |
| PC-G815 | 144 × 32 points continus | 576 octets | Profil distinct à développer |
| PC-G850 | 144 × 48 points continus | 864 octets | Pocket Clash, Pocket Vector, Jumper, Depths 2, Quest, Invaders, Runner, Rally, Star Lane, Depths ; variantes S/V/VS à vérifier séparément |

Le G815 n’est donc pas un G850 à quatre lignes de texte identiques : il a une hauteur graphique et un contrôleur différents. Les G80X peuvent déjà dessiner des motifs et des sprites ; leur limite visible vient des interstices entre cellules. Les [sources originales de g800](https://ver0.sakura.ne.jp/pc/g800src.0.11.4.tgz), notamment `g800.h`, `iocs.c` et `io.c`, distinguent explicitement ces trois profils.

La [page de logiciels de maruhiro](https://ver0.sakura.ne.jp/g800/) est un catalogue commun, avec une liste de modèles pour chaque logiciel. G-KART vise les G850/S/V/VS ; Pocket BlackJack propose des versions G850 et E200. Le titre de la page ne garantit pas un binaire universel.

**Pocket Vector et Pocket Clash pour G80X 32 Ko sont disponibles.** Leurs profils ciblent G801/G805 avec une extension reconnue par le firmware ; leur rendu utilise les cellules 5 × 7. Une extension de RAM ne transforme pas le LCD en celui d’un G850. Voir le [guide G80X 32 Ko](G80X_32K.md#francais).

### Versions disponibles

| Jeu | Cible | Réservation |
|---|---|---|
| Pocket Clash, prototype | PC-G850 | `USER55FF` |
| Pocket Vector, prototype | PC-G850 | `USER6DFF` |
| Pocket Vector G80X 32K | PC-G801 / PC-G805, 32 Kio / KiB | `USER6BFF` |
| Pocket Clash G80X 32K | PC-G801 / PC-G805, 32 Kio / KiB | `USER59FF` |
| Pocket Jumper G850 | PC-G850 | `USER19FF` |
| Pocket Depths 2 G850 | PC-G850 | `USER16FF` |
| Quest G850 | PC-G850 | `USER1FFF` |
| Pocket Invaders G850 | PC-G850 | `USER0DFF` |
| Pocket Runner G850 | PC-G850 | `USER11FF` |
| Pocket Rally G850 | PC-G850 | `USER19FF` |
| Star Lane G850 | PC-G850 | `USER0BFF` |
| Pocket Depths G850 | PC-G850 | `USER1EFF` |
| Sharp PC-G80X Quest | PC-G801 / PC-G805 | `USER17E2` |
| Pocket Rally | PC-G801 / PC-G805 | `USER17E2` |
| Pocket Jumper | PC-G801 / PC-G805 | `USER14FF` |
| Pocket Runner | PC-G801 / PC-G805 | `USER0FFF` |
| Pocket Depths 2 | PC-G801 / PC-G805 | `USER13FF` |
| Pocket Depths | PC-G805 | `USER19FF` |
| Pocket Invaders | PC-G801 / PC-G805 | `USER0BFF` |
| Star Lane | PC-G801 / PC-G805 | `USER09FF` |
| Pocket Depths Lite | PC-G801 / PC-G805 | `USER17E2` |

Les programmes commencent en **0100h** et incluent leurs données de travail et leurs tampons. La limite de réservation retenue pour le G801 est **17E2h**, soit **5 859 octets** à partir de 0100h. Pocket Depths complète dépasse ce budget ; utiliser la Lite sur G801. Chaque manifeste donne les tailles exactes et empreintes SHA-256. Les points d’entrée internes du firmware documentés séparément concernent le profil G805.

[IOCS](../include/sharp-pc-g8xx.inc) · [g800](https://ver0.sakura.ne.jp/pc/) · [z88dk](https://github.com/z88dk/z88dk/tree/master/libsrc/target/g800)
