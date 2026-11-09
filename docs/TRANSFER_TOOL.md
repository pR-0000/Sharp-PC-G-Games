# Sharp PC-G Link

**Français** · [English](TRANSFER_TOOL_EN.md) · [Chargement](LOADING.md)

**Sharp PC-G Link** est l’utilitaire de transfert séparé. Le télécharger depuis [son dépôt GitHub](https://github.com/pR-0000/Sharp-PC-G-Link), puis suivre son README. La [version Windows autonome](https://github.com/pR-0000/Sharp-PC-G-Link/releases/latest) se lance avec **Sharp PC-G Link.exe**, sans Python. Avec Python 3.10+ et Tkinter, lancer **Sharp PC-G Link.pyw**, à la racine de son dossier. Il propose d’installer pyserial dans un environnement local si nécessaire.

Autre installation depuis le dossier de l’utilitaire :

```text
python -m pip install -r requirements.txt
python -m sharp_link
```

Utiliser **Envoyer ASM** pour les fichiers HEX/BIN des jeux. Le [guide de chargement](LOADING.md) donne la réservation USER de chaque jeu. Les exemples BASIC sont dans `examples/basic/` du dépôt de l’utilitaire. Langue et paramètres série sont conservés dans son fichier INI local.
