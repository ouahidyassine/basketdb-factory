# Performances du rapport

Mesures de l'analyseur de performances de Power BI Desktop, le 18/11/2026 : une actualisation des visuels par page.

- **Requête DAX** : calcul des mesures par le moteur ; « — » quand le visuel n'interroge pas le modèle.
- **Affichage** : dessin du visuel.
- **Autre** : le reste du temps du visuel, surtout l'attente avant son démarrage.

Fichier généré par `powerbi/assets/performance_summary.py` à partir des exports JSON de ce dossier.

## Vue saison

18 visuels affichés en 626 ms au total. Requête DAX la plus lente : 24 ms (Saison la plus faible à domicile).
Temps cumulé des visuels : requête DAX 6 %, affichage 41 %, autre 54 %.

| Visuel | Champs | Requête DAX (ms) | Affichage (ms) | Autre (ms) | Total (ms) |
|---|---|---:|---:|---:|---:|
| pivotTable | season_short ; % ; Taux de victoire (carte de chaleur) | 22 | 323 | 186 | 531 |
| cardVisual | À  domicile | 18 | 144 | 149 | 311 |
| cardVisual | Saisons analysées | 23 | 133 | 151 | 307 |
| cardVisual | Taux de victoire à l'extérieur | 17 | 126 | 163 | 306 |
| cardVisual | Taux de victoire à domicile | 19 | 136 | 149 | 304 |
| cardVisual | Saison la plus faible à domicile | 24 | 115 | 164 | 303 |
| cardVisual | Meilleure saison à domicile | 23 | 118 | 160 | 301 |
| cardVisual | Taux à domicile  - Taux à l'extérieur | 17 | 110 | 173 | 300 |
| cardVisual | Plus faible taux à domicile | 22 | 114 | 161 | 297 |
| cardVisual | Meilleur taux à domicile | 19 | 116 | 137 | 272 |
| donutChart | venue ; Victoires | 24 | 68 | 170 | 262 |
| clusteredBarChart | team_name ; Taux de victoire | 12 | 77 | 173 | 262 |
| lineChart | season_short ; À domicile ; À l'extérieur | 15 | 63 | 182 | 260 |
| cardVisual | Matchs | 15 | 103 | 139 | 257 |
| pageNavigator | — | — | 93 | 33 | 126 |
| slicer | venue | — | 33 | 91 | 124 |
| slicer | season | — | 34 | 88 | 122 |
| slicer | team_name | — | 33 | 88 | 121 |

## Facteurs

17 visuels affichés en 460 ms au total. Requête DAX la plus lente : 26 ms (Facteur ; Taux du facteur).
Temps cumulé des visuels : requête DAX 3 %, affichage 46 %, autre 51 %.

| Visuel | Champs | Requête DAX (ms) | Affichage (ms) | Autre (ms) | Total (ms) |
|---|---|---:|---:|---:|---:|
| cardVisual | En back-to-back | 16 | 215 | 181 | 412 |
| cardVisual | Taux de victoire à l'extérieur | 9 | 216 | 184 | 409 |
| cardVisual | Taux de victoire en back-to-back | 8 | 209 | 191 | 408 |
| cardVisual | Taux de victoire avec plus de repos | 6 | 211 | 188 | 405 |
| cardVisual | Matchs en back-to-back à l'extérieur | 15 | 182 | 193 | 390 |
| cardVisual | Victoires en meilleure forme que l'adversaire | 16 | 180 | 192 | 388 |
| cardVisual | Taux en back-to-back à l'extérieur | 7 | 189 | 190 | 386 |
| pivotTable | venue ; Repos ; Taux de victoire | 14 | 227 | 143 | 384 |
| cardVisual | Écart forme vs 50 % | 9 | 180 | 180 | 369 |
| donutChart | result ; Matchs (équipe) | 17 | 63 | 197 | 277 |
| clusteredBarChart | Facteur ; Taux du facteur | 26 | 54 | 195 | 275 |
| lineChart | season_short ; En back-to-back ; Hors back-to-back | 16 | 59 | 199 | 274 |
| cardVisual | Taux de victoire à domicile | 7 | 95 | 171 | 273 |
| pageNavigator | — | — | 106 | 30 | 136 |
| slicer | venue | — | 63 | 70 | 133 |
| slicer | season | — | 62 | 68 | 130 |
| slicer | team_name | — | 61 | 67 | 128 |

## Face-à-face

17 visuels affichés en 492 ms au total. Requête DAX la plus lente : 21 ms (result ; Matchs (équipe)).
Temps cumulé des visuels : requête DAX 2 %, affichage 41 %, autre 57 %.

| Visuel | Champs | Requête DAX (ms) | Affichage (ms) | Autre (ms) | Total (ms) |
|---|---|---:|---:|---:|---:|
| cardVisual | Victoires | 7 | 198 | 225 | 430 |
| cardVisual | Écart moyen | 15 | 192 | 221 | 428 |
| cardVisual | Défaites | 8 | 184 | 235 | 427 |
| cardVisual | Victoires | 6 | 191 | 228 | 425 |
| cardVisual | Matchs (équipe) | 6 | 191 | 226 | 423 |
| cardVisual | Date de la plus large victoire | 11 | 166 | 244 | 421 |
| cardVisual | Bilan | 9 | 168 | 243 | 420 |
| cardVisual | Taux de victoire | 9 | 184 | 207 | 400 |
| pivotTable | season_short ; % ; Taux de victoire (carte de chaleur) | 20 | 209 | 171 | 400 |
| donutChart | result ; Matchs (équipe) | 21 | 61 | 248 | 330 |
| cardVisual | Plus large victoire | 9 | 114 | 204 | 327 |
| clusteredColumnChart | season_short ; Écart moyen | 8 | 73 | 245 | 326 |
| lineChart | date_day ; Équipe ; Adversaire | 10 | 66 | 248 | 324 |
| pageNavigator | — | — | 121 | 38 | 159 |
| slicer | season | — | 71 | 85 | 156 |
| slicer | team_name | — | 70 | 83 | 153 |
| slicer | opponent_name | — | 70 | 82 | 152 |
