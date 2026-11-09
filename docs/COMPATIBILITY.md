# Modèles ciblés et mémoire

**Français** · [English](COMPATIBILITY_EN.md) · [Collection](../README.md)

La collection cible les **PC-G801 / PC-G805** et leur écran de quatre lignes via les IOCS Sharp. Cette cible ne s’étend pas à toutes les machines portant le nom PC-G ou utilisant le même connecteur. Les PC-G81X, G820/G830 et G850 demandent une adaptation à leur firmware et leur affichage.

| Jeu | Cible | Réservation |
|---|---|---|
| Sharp PC-G80X Quest | PC-G801 / PC-G805 | `USER17E2` |
| Pocket Rally | PC-G801 / PC-G805 | `USER17E2` |
| Pocket Jumper | PC-G801 / PC-G805 | `USER14FF` |
| Pocket Runner | PC-G801 / PC-G805 | `USER0FFF` |
| Pocket Depths 2 | PC-G801 / PC-G805 | `USER13FF` |
| Pocket Depths | PC-G805 | `USER19FF` |
| Pocket Invaders | PC-G801 / PC-G805 | `USER0BFF` |
| Star Lane | PC-G801 / PC-G805 | `USER05FF` |
| Pocket Depths Lite | PC-G801 / PC-G805 | `USER17E2` |

Les programmes commencent en **0100h** et incluent leurs données de travail et leurs tampons. La limite de réservation retenue pour le G801 est **17E2h**, soit **5 859 octets** à partir de 0100h. Pocket Depths complète dépasse ce budget ; utiliser la Lite sur G801. Chaque manifeste donne les tailles exactes et empreintes SHA-256. Les points d’entrée internes du firmware documentés séparément concernent le profil G805.

[IOCS](../include/sharp-pc-g8xx.inc) · [g800](https://ver0.sakura.ne.jp/pc/) · [z88dk](https://github.com/z88dk/z88dk/tree/master/libsrc/target/g800)
