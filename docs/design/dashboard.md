# Dashboard : spécification

Canevas Power BI de 1280 × 720 px (16:9), grille de 8 px, marges de 16 px. Chaque page a son propre fond, généré par `powerbi/assets/generate_background.py` à partir de `powerbi/assets/dashboard_layout.py` : la grille, les titres, les sous-titres explicatifs et les icônes vivent dans le fond, les visuels Power BI sont posés par-dessus, transparents et sans titre.

## Principes

| Principe | Application |
|---|---|
| Une couleur a une fonction | Orange `#F97316` pour ce qui est mis en avant, gris `#64748B` pour la comparaison |
| Chaque carte explique sa lecture | Un titre, un sous-titre qui dit comment lire, une icône ; un encadré « Comment lire » dans la carte principale |
| Une hiérarchie stable | En-tête (marque, segments, navigation), carte principale, indicateurs, analyses |
| Aucune marque protégée | Logo, icônes et terrain dessinés au trait, sans logo ni photo NBA |

## Couleurs

| Rôle | Couleur |
|---|---|
| Fond de page et wallpaper | `#090C11` |
| Cartes | dégradé `#141B26` → `#0D1219`, bordure orange à 25 % |
| Carte principale | dégradé `#4F210C` → `#111823`, bordure et halo orange |
| Texte principal / secondaire | `#F1F5F9` / `#8090A6` |

## Régénérer les fonds et les positions

```bash
python powerbi/assets/generate_background.py              # un PNG par page
python powerbi/assets/generate_background.py --positions  # tableaux ci-dessous
```

Dans Power BI : **Format page** → **Canvas background** → image de la page, **Image fit : Fill**, transparence 0 % ; **Wallpaper** `#090C11`.

## Positions des visuels

Deux sources, selon l'état de la page :

- page construite : positions **relevées dans le rapport**, avec `python powerbi/assets/report_positions.py "<nom de la page>"` ;
- page à construire : positions **cibles**, données par la grille, avec `python powerbi/assets/generate_background.py --positions`.

### Vue saison

| Visuel | Champs | x | y | Largeur | Hauteur |
|---|---|---|---|---|---|
| pageNavigator | — | 924 | 25 | 336 | 40 |
| slicer | venue | 776 | 41 | 120 | 32 |
| slicer | season | 472 | 42 | 120 | 32 |
| slicer | team_name | 624 | 42 | 120 | 32 |
| cardVisual | Meilleur taux à domicile | 650 | 136 | 272 | 60 |
| cardVisual | Plus faible taux à domicile | 976 | 136 | 272 | 60 |
| cardVisual | Taux à domicile  - Taux à l'extérieur | 32 | 142 | 272 | 104 |
| cardVisual | Meilleure saison à domicile | 650 | 184 | 272 | 22 |
| cardVisual | Saison la plus faible à domicile | 976 | 184 | 272 | 22 |
| donutChart | venue ; Victoires | 1024 | 254 | 240 | 192 |
| cardVisual | Matchs | 76 | 270 | 80 | 44 |
| cardVisual | Taux de victoire à domicile | 220 | 270 | 80 | 44 |
| cardVisual | Taux de victoire à l'extérieur | 364 | 270 | 80 | 44 |
| cardVisual | Saisons analysées | 494 | 270 | 80 | 44 |
| pivotTable | season_short ; % ; Taux de victoire (carte de chaleur) | 624 | 272 | 370 | 144 |
| cardVisual | À  domicile | 1064 | 300 | 160 | 96 |
| clusteredBarChart | team_name ; Taux de victoire | 32 | 428 | 560 | 268 |
| lineChart | season_short ; À domicile ; À l'extérieur | 640 | 500 | 608 | 196 |

### Facteurs d'avant-match

| Zone | Visuel | Champs | x | y | Largeur | Hauteur |
|---|---|---|---|---|---|---|
| segment_1 | Slicer (Dropdown) | dim_season[season] | 472 | 42 | 120 | 32 |
| segment_2 | Slicer (Dropdown) | dim_team[team_name] | 624 | 42 | 120 | 32 |
| segment_3 | Slicer (Dropdown) | fact_team_game[venue] | 776 | 42 | 120 | 32 |
| navigation | Page navigator | Pages visibles du rapport | 924 | 28 | 336 | 40 |
| principal | Card (new) | [Taux de victoire en meilleure forme] | 32 | 152 | 272 | 104 |
| mini_1 | Card (new) | [Taux de victoire à domicile] | 76 | 270 | 80 | 44 |
| mini_2 | Card (new) | [Taux de victoire avec plus de repos] | 220 | 270 | 80 | 44 |
| mini_3 | Card (new) | [Taux de victoire en back-to-back] | 364 | 270 | 80 | 44 |
| mini_4 | Card (new) | [Taux de victoire à l'extérieur] | 508 | 270 | 80 | 44 |
| kpi | Card (new) | [Écart forme vs 50 %] | 640 | 148 | 272 | 60 |
| a_la_une | Card (new) | [Taux en back-to-back à l'extérieur] | 960 | 148 | 168 | 60 |
| chaleur | Matrix | Lignes rest_bucket ; colonnes venue ; [Taux de victoire] | 640 | 284 | 320 | 140 |
| anneau | Donut chart | Légende result ; [Matchs (équipe)] ; filtre is_back_to_back = True | 1056 | 284 | 192 | 140 |
| barres | Clustered bar chart | Facteurs[Facteur] ; [Taux du facteur] | 32 | 428 | 560 | 268 |
| courbes | Line chart | season ; [Taux de victoire en back-to-back], [Taux de victoire hors back-to-back] | 640 | 500 | 608 | 196 |

### Face-à-face

| Zone | Visuel | Champs | x | y | Largeur | Hauteur |
|---|---|---|---|---|---|---|
| segment_1 | Slicer (Dropdown) | dim_team[team_name] | 472 | 42 | 120 | 32 |
| segment_2 | Slicer (Dropdown) | dim_opponent[opponent_name] | 624 | 42 | 120 | 32 |
| segment_3 | Slicer (Dropdown) | dim_season[season] | 776 | 42 | 120 | 32 |
| navigation | Page navigator | Pages visibles du rapport | 924 | 28 | 336 | 40 |
| principal | Card (new) | [Bilan] | 32 | 152 | 272 | 104 |
| mini_1 | Card (new) | [Matchs (équipe)] | 76 | 270 | 80 | 44 |
| mini_2 | Card (new) | [Victoires] | 220 | 270 | 80 | 44 |
| mini_3 | Card (new) | [Défaites] | 364 | 270 | 80 | 44 |
| mini_4 | Card (new) | [Écart moyen] | 508 | 270 | 80 | 44 |
| kpi | Card (new) | [Taux de victoire] | 640 | 148 | 272 | 60 |
| a_la_une | Card (new) | [Plus large victoire] | 960 | 148 | 168 | 60 |
| chaleur | Matrix | Lignes venue ; colonnes season_short ; [Taux de victoire] | 640 | 284 | 320 | 140 |
| anneau | Donut chart | Légende result ; [Matchs (équipe)] | 1056 | 284 | 192 | 140 |
| barres | Clustered column chart | season ; [Écart moyen] | 32 | 428 | 560 | 268 |
| courbes | Line chart | game_date ; [Forme de l'équipe], [Forme de l'adversaire] | 640 | 500 | 608 | 196 |
