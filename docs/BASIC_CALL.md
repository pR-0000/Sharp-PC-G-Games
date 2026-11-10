# Lancer du code machine depuis BASIC

**Français** · [English](BASIC_CALL_EN.md) · [Chargement](LOADING.md)

La commande de cette famille Sharp est **CALL adresse**, par exemple pour les jeux assemblés en 0100h :

```text
CALL &H100
```

`CALL 256` désigne la même adresse en décimal. Il faut avoir réservé la zone avec USER et chargé le programme au préalable dans MON → R. Revenir en BASIC/RUN sans réinitialiser la mémoire, puis effectuer l'appel. CALL ne charge pas de fichier ; la commande EXEC du Canon X-07 n'est pas à transposer.

Un petit programme BASIC peut aussi servir de lanceur :

```basic
10 CALL &H100
20 END
```

Le programme machine doit conserver une pile valide et revenir par RET. Pocket Depths conserve aussi BC, DE, HL, IX et IY. Les commandes G100 depuis MON et CALL &H100 depuis BASIC partagent le point d'entrée ; la sortie revient à l'appelant utilisé.

Référence : [CALL dans la documentation PC-E200/G de fu-sen](https://github.com/fu-sen/SHARP-POCKET-COMPUTER-BASIC/blob/master/CALL.txt). Les adresses d'entrée des jeux restent celles de leurs manifestes.
