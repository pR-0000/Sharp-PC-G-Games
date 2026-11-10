# Versions / Releases

## 0.9.0

FR : galerie animée G850 pour Pocket Vector, Pocket Clash, Pocket Jumper, Pocket Rally et Pocket Depths 2. GIF du LCD émulé intégrés au catalogue et aux guides FR/EN ; outil de capture reproductible avec comparaison des pixels au rendu Z80.

EN: animated G850 gallery for Pocket Vector, Pocket Clash, Pocket Jumper, Pocket Rally and Pocket Depths 2. Emulated-LCD GIFs embedded in the FR/EN catalogue and guides; reproducible capture tool compares pixels against the Z80 renderer.

FR : distribution Intel HEX privilégiée sous l’extension `.ihx`. Binaires, manifestes et outils uniformisés dans `build/g80x/`, `build/g80x-32k/` ou `build/g850/` pour chaque jeu ; exemple graphique dans `examples/build/g80x/`. Catalogue bilingue simplifié, liens et galerie G80X/G850 actualisés.

EN: Intel HEX distribution now uses `.ihx`. Binaries, manifests and tools consistently use each game’s `build/g80x/`, `build/g80x-32k/` or `build/g850/`; the graphics example uses `examples/build/g80x/`. Simplified bilingual catalogue, updated links and G80X/G850 gallery.

FR : Pocket Vector et Pocket Clash disponibles pour G801/G805 avec 32 Kio. Moteurs et BMP partagés, fichiers FR/EN séparés `g80x_32k`, pilotes quatre lignes/sept bits. Vector conserve ses trois courses, sa coupe, sa physique et un vaisseau 23 × 11 ; sol en 2 × 2, HUD natif et minimap 16 × 8. Clash conserve quatre combattants, trois arènes et coupe avec une vue 120 × 21 et treize échelles. Guides, lanceurs, captures g800 et contrôles CPU dédiés. Binaires G850 inchangés.

EN: Pocket Vector and Pocket Clash available for G801/G805 with 32 KiB. Shared engines/BMPs, separate FR/EN `g80x_32k` files and four-row/seven-bit display adapters. Vector retains its three tracks, cup, physics and 23 × 11 ship; 2 × 2 floor, native HUD and 16 × 8 minimap. Clash keeps four fighters, three arenas and cup with a 120 × 21 scene and thirteen scales. Dedicated guides, launchers, g800 captures and CPU checks. G850 binaries unchanged.

FR : Pocket Clash 0.1.1 pour G850 : combat sur plateformes, quatre personnages originaux, double saut, garde, quatre spéciaux et projections liées aux dégâts. Coupe de trois rencontres avec classement, trois arènes et décors BMP modifiables. Graphismes affinés : six poses par combattant, jardin suspendu, temple et pont nocturne, avec détails en périphérie. Neuf tailles de sprites masqués, caméra avec zoom et parallaxe, clavier simultané, démonstration et gel photo. Fichiers FR/EN, guide bilingue, atlas BMP, captures LCD g800 et contrôles CPU.

EN: Pocket Clash 0.1.1 for G850: platform fighting, four original characters, double jump, guarding, four specials and damage-based launch. Three-battle cup with standings, three arenas and editable BMP scenery. Refined artwork: six poses per fighter, hanging garden, temple and night bridge with details near the sides. Nine masked sprite sizes, zoom camera, parallax, simultaneous input, demo and clean photo freeze. FR/EN files, bilingual guide, BMP atlas, g800 LCD captures and CPU checks.

FR : Star Lane 0.2.0, G80X et G850 : tirs, pirates résistants, bouclier rechargeable, combos, secteurs progressifs et gel photo. Cinq couloirs natifs sur G850. Pocket Depths 0.3.0 : campagne de trois étages, garde, interruption des attaques, recul au fusil, ravitaillement aux balises et panneau d’objectifs. Version G850 144 × 40 / 48 rayons ; Lite G801 conservant ces règles sous 5 859 octets grâce aux sprites stockés sans bandes vides. Fichiers FR/EN, guides, lanceurs et captures LCD actualisés.

EN: Star Lane 0.2.0 for G80X/G850: shots, tougher pirates, rechargeable shield, combos, progressive sectors and photo freeze. Five native G850 lanes. Pocket Depths 0.3.0: three-floor campaign, guarding, attack interruption, shotgun knockback, beacon supplies and objective HUD. G850 144 × 40 / 48-ray build; G801 Lite keeps the rules below 5,859 bytes by omitting empty sprite bands. Updated FR/EN files, guides, launchers and LCD photos.

FR : Pocket Vector 0.6.0 pour PC-G850 : course monochrome à projection de sol Q8.8, trois circuits larges, menu coupe/course libre/démonstration, trois manches de trois tours et classement aux points. Deux adversaires, rebonds, recharge, turbo au deuxième tour et vrille avec inertie. Huit orientations du joueur, vrille à deux rotations complètes, 22 BMP sources modifiables et planche verticale. Sprites 2 bits par pixel et miroirs exacts, HUD 3 × 5, minimap 32 × 16 et sol étendu à la dernière ligne ; noms de circuit réservés aux menus et résultats. Orbite sans vaisseaux, arrivée depuis le bas, grille derrière la ligne et décompte 3/2/1/GO ; premier franchissement sans tour supplémentaire. Adversaires recalibrés selon la longueur des circuits, freinage en virage et turbo dès le deuxième tour. Accélération doublée du joueur et braquage plus direct. Vrille accélérée sur huit images, ligne droite de départ et validation ENTER après relâchement stable. Adversaires environ 14 % plus rapides. Vrille sans dégâts sur les bordures, rebonds conservant l’élan tangent et poussée des adversaires. Cartes compressées LZ : 27 648 / 27 648 octets FR/EN, USER6CFF commun et budget mémoire sous le firmware. Commandes simultanées, pause photo, versions FR/EN et lanceur g800. Include et wrappers G850 indépendants. Captures LCD 144 × 48 et contrôles du programme Z80, dont une coupe complète.

EN: Pocket Vector 0.6.0 for PC-G850: monochrome Q8.8 floor-projected racing, three wide circuits, cup/single race/demonstration menu, three three-lap rounds and points standings. Two opponents, rebounds, recharge, lap-two boost and momentum-preserving spin. Eight player orientations, two complete turns per spin, 22 editable BMP sources and vertical sprite sheet. Two-bit sprite storage and exact mirrors, 3 × 5 HUD, 32 × 16 minimap and floor extended to the last row; course names remain in menus and results. Empty-track orbit, ships arriving from the bottom, grid behind the line and 3/2/1/GO countdown; first crossing does not complete a lap. Opponent pace accounts for circuit length, with corner braking and boosts from lap two. Doubled player acceleration and more direct steering. Faster eight-frame spin, level starting straight and stable ENTER release between results/menu screens. Opponents cruise about 14% faster. Harmless border rebounds during spins, retained tangent momentum and opponent knockback. LZ-compressed maps: 27,648 / 27,648 bytes FR/EN, shared USER6CFF and a memory budget below firmware workspaces. Simultaneous input, photo pause, FR/EN builds and g800 launcher. Independent G850 include and wrappers. 144 × 48 LCD screenshots and actual Z80 program checks, including a complete cup.

FR : Pocket Jumper 0.2.0 et Pocket Depths 2 0.2.0 : versions PC-G850 séparées FR/EN, fenêtre 144 × 40 et HUD natif en haut. Jumper ajoute un niveau de 768 × 64, des décors en parallaxe, une démonstration automatique et une pause photo propre. Depths 2 passe à 48 rayons, avec projection, sprites et arme adaptés. Sources communes, couche IOCS par cible, fichiers G850 identifiables et téléchargements regroupés par modèle. Binaires G80X conservés à l’identique.

EN: Pocket Jumper 0.2.0 and Pocket Depths 2 0.2.0: separate FR/EN PC-G850 builds, 144 × 40 viewport and native top HUD. Jumper adds a 768 × 64 level, parallax scenery, automatic demonstration and clean photo freeze. Depths 2 uses 48 rays, with adapted projection, sprites and weapon. Shared sources, target IOCS layer, identifiable G850 files and model-specific downloads. G80X binaries remain identical.

FR : Quest 0.2.0 pour G850 : carte 18 × 5 en 8 × 8, caméra, graphismes Canon et portraits 16 × 16 ; règles et données communes au G80X. Pocket Invaders 0.3.0 : arène 108 × 48, aliens 9 × 7, commandes simultanées et gel photo TAB. Pocket Runner 0.2.0 : fenêtre 140 × 40, motifs 7 × 8 et gel photo F. Atlas BMP, documentation FR/EN, lanceurs, captures LCD et contrôles CPU des deux cibles. Binaires G80X inchangés.

EN: Quest 0.2.0 for G850: 18 × 5 map of 8 × 8 tiles, camera, Canon artwork and 16 × 16 portraits; rules and data shared with G80X. Pocket Invaders 0.3.0: 108 × 48 arena, 9 × 7 aliens, simultaneous controls and TAB photo freeze. Pocket Runner 0.2.0: 140 × 40 viewport, 7 × 8 patterns and F photo freeze. BMP artwork, FR/EN documentation, launchers, LCD captures and CPU checks for both targets. G80X binaries unchanged.

FR : Pocket Vector 0.7.0 : sprites adverses 15/11 pixels sur la grille, projection et découpage latéral améliorés ; normales de contact issues de la route et des vaisseaux, rebonds avec élan tangent et inertie prolongée, poussée mutuelle hors vrille également. 27 904 octets FR/EN, USER6DFF. Pocket Rally 0.2.0 ajoute une cible G850 144 × 40, HUD au-dessus, défilement au pixel, commandes simultanées et gel photo TAB, avec les règles et circuits communs au G80X. Versions FR/EN et captures LCD.

EN: Pocket Vector 0.7.0: 15/11-pixel opponents on the grid, improved projection and side clipping; road/ship contact normals, tangential rebounds and longer-lived inertia, mutual knockback outside spins as well. 27,904 bytes FR/EN, USER6DFF. Pocket Rally 0.2.0 adds a G850 144 × 40 target, top HUD, pixel scrolling, simultaneous controls and TAB photo freeze, sharing rules and circuits with G80X. FR/EN builds and LCD captures.

## 0.8.1

FR : README français/anglais réunis pour la collection et les huit jeux, navigation par langue et liens directs vers Sharp PC-G Link. Archive de distribution avec contrôles des fichiers, graphismes, manifestes et liens.

EN: Combined French/English READMEs for the collection and all eight games, language navigation and direct links to Sharp PC-G Link. Distribution archive with file, artwork, manifest and link checks.

## 0.8.0

FR : Pocket Rally 0.1.0, course vue de dessus : deux circuits, deux adversaires, trois tours, seize orientations, accélérateur/frein, contrôle simultané et caméra anticipée. Tilemapper 4 × 4 avec défilement au pixel sur deux axes, circuits RLE, caches de lignes et fragments graphiques décalés. Versions FR/EN, plans BMP, guides et lanceur g800.

EN: Pocket Rally 0.1.0, overhead racing: two circuits, two opponents, three laps, sixteen headings, throttle/brake, simultaneous controls and look-ahead camera. A 4 × 4 tilemapper with two-axis pixel scrolling, RLE circuits, row caches and shifted graphic fragments. FR/EN builds, BMP layouts, guides and g800 launcher.

## 0.7.1

FR : Pocket Jumper 0.1.1 : flèches et ESPACE/HAUT simultanés, saut déclenché à la pression et raccourcis Z/X conservés. Atlas BMP éditable, plan de niveau en couleurs, carte complète, guide bilingue des motifs et import de cartes 8 × 8.

EN: Pocket Jumper 0.1.1: simultaneous arrows and SPACE/UP, jump press detection and retained Z/X shortcuts. Editable BMP atlas, colour level layout, complete map, bilingual sprite guide and 8 × 8 map import.

## 0.7.0

FR : Pocket Jumper 0.1.0 : plateformes au pixel, sprites 12 × 12, défilement, sauts avec élan, pièces, blocs bonus, ennemis et point de reprise. Versions FR/EN, guides et lanceur g800. Documentation publique recentrée sur les jeux et leur utilisation.

EN: Pocket Jumper 0.1.0: pixel platforming, 12 × 12 sprites, scrolling, momentum-based jumping, coins, bonus blocks, enemies and checkpoint. FR/EN builds, guides and g800 launcher. Public documentation focused on games and usage.

## 0.6.0

FR : Pocket Runner : trois niveaux originaux, échelles, cordes, gardes, trous temporaires et caméra verticale.

EN: Pocket Runner: three original levels, ladders, ropes, guards, temporary holes and vertical scrolling.

## 0.5.0

FR : Pocket Depths 2 : raycaster DDA Q8.8 calculé sur Z80, 32 orientations et sprites projetés.

EN: Pocket Depths 2: Z80 runtime Q8.8 DDA raycaster, 32 headings and projected sprites.

## 0.4.0

FR : Pocket Invaders : arène 90 × 28 et panneau latéral. Pocket Depths : portes avec cadre et poignée.

EN: Pocket Invaders: 90 × 28 arena and sidebar. Pocket Depths: framed doors with handles.

## 0.3.0

FR : Pocket Invaders ajouté. Cœur clignotant après les dégâts dans Pocket Depths.

EN: Added Pocket Invaders. Blinking heart after damage in Pocket Depths.

## 0.2.0–0.2.1

FR : Pocket Depths complète/Lite, niveaux modulaires, orientation et pas latéral. Include Sharp partagé et routines de firmware. Utilitaire de transfert séparé dans Sharp-PC-G-Link.

EN: Pocket Depths full/Lite, modular levels, compass and strafing. Shared Sharp include and firmware routines. Transfer utility separated into Sharp-PC-G-Link.

## 0.1.0–0.1.2

FR : Quest et Star Lane, guides FR/EN, Pocket Depths initial, lancement BASIC et atlas de Quest éditable. Quest 0.1.6 allonge de 20 % le délai de frappe ; équipements +1 puis +2.

EN: Quest and Star Lane, FR/EN guides, initial Pocket Depths, BASIC launch and editable Quest atlas. Quest 0.1.6 lengthens typing time by 20%; equipment progresses from +1 to +2.
