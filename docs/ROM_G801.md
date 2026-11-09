# Routines du firmware PC-G805

**Français** · [English](ROM_G801_EN.md) · [IOCS](../include/sharp-pc-g8xx.inc)

Ces définitions décrivent le **profil de firmware PC-G805**. Les points d’entrée internes dépendent de la révision. Les anciens noms `PCG801_*` et l’alias `sharp_pc_g801.inc` sont conservés pour compatibilité des sources ; ils ne signifient pas que les firmwares des différents modèles sont identiques. Aucune ROM n’est distribuée.

## LCD / IOCS

D = ligne 0–3 ; E = colonne de caractère 0–23. Les motifs comprennent cinq colonnes de sept bits par cellule ; B compte les colonnes de pixels. Limiter les motifs à la ligne et utiliser B ≥ 1. Les wrappers préservant les registres sont dans [pcg801_runtime.asm](../lib/pcg801_runtime.asm).

| IOCS | Adresse | Paramètres |
|---|---|---|
| `PCG_IOCS_PUTC` | BE62h | A = ASCII, DE = cell |
| `PCG_IOCS_PATTERN` | BFD0h | HL = source, B = width, DE = cell |
| `PCG_IOCS_PATTERN_READ` | BD00h | HL = destination, B = width, DE = cell |
| `PCG_IOCS_STRING` | BFF1h | HL = text, B = length, DE = cell; wraps/scrolls |
| `PCG_IOCS_REPEAT` | BFEEh | A = character, B = count, DE = cell; stops at bottom |
| `PCG_IOCS_SCROLL` | BFEBh | Scroll |
| `PCG_IOCS_STATUS` | BFE8h | Status indicators |
| `PCG_IOCS_LCD_ENABLE` | BFD3h | Display enable, command 3Fh |
| `PCG_IOCS_KEY_SCAN` | BE53h | A = raw key |

L’animation ALL RESET alterne un cadre de caractères pleins avec des espaces et un motif de pixels restauré. Les commandes LCD 3Eh/3Fh désactivent/activent l’affichage ; elles ne règlent pas le contraste. Les jeux utilisent un clignotement ou une inversion logicielle pour les dégâts. Ne pas appliquer les commandes de contraste G850 à ce contrôleur.

## SIO

| IOCS | Adresse | Contrat |
|---|---|---|
| `PCG_IOCS_SIO_OPEN` | BCE8h | Initialize serial I/O |
| `PCG_IOCS_SIO_CLOSE` | BCEBh | Close serial I/O |
| `PCG_IOCS_SIO_TX` | BFAFh | A = byte; wait CS; carry = BREAK |
| `PCG_IOCS_SIO_RX` | BCE2h | Assert RS, receive A; carry = error |
| `PCG_IOCS_SIO_RX_NEXT` | BCE5h | Receive without asserting RS |
| `PCG_IOCS_SIO_PUTS` | BFB2h | NUL-terminated text |
| `PCG_IOCS_SIO_NEWLINE` | BCEEh | Build line ending at HL; no transmission |

TX/RX préservent BC/DE/HL mais utilisent les registres alternatifs. Erreurs RX : A=0 BREAK, A=1 fin de trame/ligne non libérée, A=2 parité. Un NUL reçu correctement donne A=0 avec carry nul. RX attend un octet ou BREAK et reste bloquant. TX attend CS ; conserver le contrôle de flux matériel.

Réglages : 78EDh (vitesse), 78EEh (format), 78EFh (EOF) ; état en 78ECh. Sauvegarder puis restaurer les réglages du firmware autour d’un programme. Les masques 01/02/04/08/10h sélectionnent 300/600/1200/2400/4800 bauds. Format : bit 7 = 8 bits, bit 6 = parité active, bit 5 = parité paire, bit 4 = deux stops. Le masque 10h de l’état sélectionne RX brut sans conversion CR/LF. L’include nomme également les ports et miroirs RAM associés.

## BEEP

La routine en banque 01 à E71Fh prend A=délai de hauteur, DE=nombre de sons et BC=cycles par son. Une valeur A plus grande allonge la période ; ce n’est pas une note MIDI. BC=0 ou DE=0 ne produit pas d’oscillation. Utiliser le wrapper de changement de banque [pcg801_rom.asm](../lib/pcg801_rom.asm), plutôt qu’appeler directement une adresse paginée.

```asm
    INCLUDE "sharp-pc-g8xx.inc"
    ld a,7
    ld de,1
    ld bc,100
    call pcg801_rom_beep
    ; ... program return ...
    INCLUDE "pcg801_rom.asm"
```

Le wrapper préserve BC/DE/HL ; AF est indéfini. BREAK peut interrompre le son mais le nettoyage remet carry à zéro. La routine oscille les bits 6/7 du port 18h, dont XOUT. Elle suppose un buzzer installé, s’appelle hors interruption et hors transfert série/cassette, et demande la cohérence normale du miroir de banque.

[g800](https://ver0.sakura.ne.jp/pc/) · [Include](../include/sharp-pc-g8xx.inc) · [Development](DEVELOPMENT.md)
