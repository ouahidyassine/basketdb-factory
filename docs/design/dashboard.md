# Dashboard : spécification

Canevas de 1280 × 720 px, grille de 8 px, marges de 24 px, espacement de 16 px. Les 3 pages partagent le même fond (`powerbi/assets/backgrounds/page.png`), généré par `powerbi/assets/generate_background.py`.

## Les cartes

| Carte | x | y | Largeur | Hauteur |
|---|---|---|---|---|
| En-tête | 24 | 24 | 1232 | 64 |
| Indicateur 1 | 24 | 104 | 296 | 104 |
| Indicateur 2 | 336 | 104 | 296 | 104 |
| Indicateur 3 | 648 | 104 | 296 | 104 |
| Indicateur 4 | 960 | 104 | 296 | 104 |
| Visuel principal | 24 | 224 | 728 | 472 |
| Visuel secondaire | 768 | 224 | 488 | 472 |

Un visuel se place **8 px à l'intérieur** de sa carte : position (x + 8, y + 8), taille (largeur − 16, hauteur − 16).

## Les pages

| Page | Question | Indicateurs | Visuel principal | Visuel secondaire |
|---|---|---|---|---|
| Vue saison | Comment évolue l'avantage du terrain ? | Matchs, victoires à domicile, victoires à l'extérieur, avantage du terrain | Domicile et extérieur par saison | Classement des équipes par taux de victoire |
| Facteurs d'avant-match | Quel facteur pèse le plus ? | Domicile, plus de repos, back-to-back, meilleure forme | Les facteurs comparés à la ligne des 50 % | Taux de victoire selon le repos et le lieu, en carte de chaleur |
| Face-à-face | Comment une équipe s'en sort-elle contre une autre ? | Confrontations, victoires de l'équipe, victoires de l'adversaire, écart moyen | Résultats des confrontations par saison | Forme comparée des deux équipes |

## Couleurs

Orange `#F97316` pour ce qui est mis en avant, gris `#64748B` pour ce qui sert de comparaison. Fond de page `#0B0F14`, fond des cartes `#121821`, bordure `#1F2A37`.
