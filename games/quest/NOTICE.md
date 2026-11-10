# Provenance de Quest

**Français** · [English](NOTICE_EN.md)

Ce portage dérive du **[Canon X-07 Quest](https://github.com/pR-0000/Canon_X-07_RPG)**. `upstream.json` conserve les empreintes des sources utilisées.

La carte, les textes, les statistiques et une partie des routines Z80 proviennent de ce jeu. Les routines Sharp, les motifs 5 × 7, la représentation compacte de l'état et les outils/tests de portage ont été ajoutés pour cette adaptation. La cible G850 reprend aussi les 23 graphismes 8 × 8 de l’atlas Canon, conservé dans `targets/g850/tiles.bmp` ; les portraits sont agrandis à partir de cet atlas. La musique et le pilote sonore Canon ne sont pas inclus.

Les éléments repris de Quest restent soumis aux conditions de leur auteur ; ce portage ne présume aucun changement de licence du jeu d'origine. La licence MIT du dépôt concerne les nouveaux outils et composants Sharp, sous réserve de ces éléments hérités.

Les adresses et contrats IOCS Sharp proviennent des sources publiques de g800 et de z88dk, détaillées dans le [guide de compatibilité](../../docs/COMPATIBILITY.md) et dans `include/sharp_pc_g801.inc` à la racine. Les outils SjASMPlus, z80, g800 et SDL conservent leurs licences et ne sont pas redistribués dans l'archive.
