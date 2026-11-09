# Effet de dégâts

**Français** · [English](CONTRAST_EN.md) · [Jeu](../README.md)

Pocket Depths utilise un **bref négatif logiciel du décor**, suivi de deux clignotements du cœur lors d’un dégât. Les chiffres de santé et de munitions restent lisibles. Le réglage physique du contraste ne change pas.

L’animation ALL RESET alterne caractères et motifs de pixels ; ce n’est pas un réglage logiciel du contraste. Voir la [référence du firmware G805](../../../docs/ROM_G801.md). Les commandes de contraste LCD G850 ne doivent pas être appliquées aux contrôleurs G801/G805.

Pour modifier l’effet, voir `hurt_flash` dans `depths.asm`, puis `invert_buffer` et `.flash_wait` dans `render.asm`. Le masque XOR 7Fh inverse les sept bits utiles de chaque colonne. Aucun port LCD n’est directement utilisé.
