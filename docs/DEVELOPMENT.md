# Développement

**Français** · [English](DEVELOPMENT_EN.md) · [Collection](../README.md#francais)

Les `.ihx` prêts à charger ne demandent aucun outil de développement. Pour modifier un jeu, installer Python 3.10+ et [SjASMPlus](https://github.com/z00m128/sjasmplus), puis construire ses sources depuis la racine du dépôt. Exemple :

```text
python games/star-lane/build_star.py --lang fr --assembler "sjasmplus.exe"
```

Chaque script `games/<jeu>/build_*.py` génère les deux langues. Les options `--target g80x` ou `--target g850` sélectionnent une cible lorsqu’elles sont proposées ; Vector et Clash utilisent `--target g80x-32k` pour les G80X étendus.

Les règles, graphismes sources et scripts de construction accompagnent chaque jeu. `include/` définit les interfaces matérielles ; `lib/` contient les routines assembleur communes et les petits modules Python nécessaires à la construction des sources. Chaque `build/<cible>/manifest.json` indique les tailles, réservations USER et empreintes SHA-256.

Le rendu G80X utilise 120 × 28 pixels utiles, en quatre bandes de sept bits. Le G850 utilise 144 × 48 pixels, en six bandes de huit bits. Les règles sont partagées autant que possible ; la géométrie LCD et le clavier sont adaptés par cible.
