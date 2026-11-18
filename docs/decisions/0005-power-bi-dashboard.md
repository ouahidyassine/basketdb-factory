# ADR 0005 — Dashboard Power BI

- Statut : accepté
- Date : 2026-11-18

## Contexte

Gold expose un schéma en étoile, reconstruit chaque jour par dbt. Le dashboard doit répondre à la question du projet de façon lisible et interactive, rester versionné et relu en pull request comme le reste du code, et ne jamais pouvoir modifier l'entrepôt.

## Décision

- **Mode import** depuis PostgreSQL (`localhost:5433`, base `basketdb`), avec le rôle `powerbi_reader`, limité à la lecture du schéma `gold` ; les droits sont posés par `+grants` dans dbt, donc reposés à chaque reconstruction des tables.
- **Format PBIP** : modèle sémantique en TMDL, rapport en PBIR (un fichier JSON par page et par visuel) ; cache et réglages locaux ignorés par Git ; fins de ligne fixées et images déclarées binaires dans `.gitattributes`.
- **Modèle** : les tables de Gold importées telles quelles ; relation inactive vers `dim_team` pour l'adversaire, activée par `USERELATIONSHIP` ; `dim_opponent` pour filtrer l'équipe et son adversaire indépendamment ; `dim_date` marquée comme table de dates, Auto date/time désactivé.
- **Libellés calculés dans dbt**, pas dans Power BI : `venue`, `result`, `rest_bucket` et `season_short` sont des colonnes de Gold, couvertes par des tests `accepted_values` et `not_null`.
- **Mesures DAX** regroupées dans `_Mesures` ; mesures de présentation séparées des mesures de calcul ; comparaison des facteurs par une table déconnectée `Facteurs` et une mesure `SWITCH` ; filtre de page sur les saisons terminées.
- **Design généré** : les fonds de page (grille de 8 px, titres, sous-titres explicatifs, icônes) sont produits par un script Python à partir d'une spécification qui vérifie la grille ; les visuels sont transparents et sans titre ; les positions réelles sont relevées dans le PBIR et reportées dans la documentation. Aucun logo ni photo NBA.
- **Interactions** en mode filtre plutôt qu'en surbrillance ; sur Face-à-face, segments Équipe et Adversaire en sélection unique et non synchronisés avec les autres pages.
- **Vérification** : les mesures sont rapprochées de requêtes SQL sur Gold (page `Contrôles`) ; les performances sont mesurées avec l'analyseur de Power BI Desktop et résumées par un script.

## Alternatives écartées

- **DirectQuery** : chaque visuel interrogerait PostgreSQL à chaque interaction, pour des données qui ne changent qu'une fois par jour.
- **Un fichier `.pbix`** : binaire, sans diff lisible ni relecture possible en pull request.
- **Le rôle propriétaire de l'entrepôt** : Power BI aurait des droits d'écriture sur tous les schémas.
- **Des colonnes calculées dans Power BI** pour les libellés : une logique métier hors de dbt, sans test.
- **Auto date/time** : une table de dates cachée par colonne de date, et un modèle plus lourd.
- **Titres et textes posés à la main dans Power BI** : des dizaines d'objets à aligner, et un design impossible à régénérer.
- **Publication sur le service Power BI** : licence et passerelle de données nécessaires pour actualiser depuis un PostgreSQL local ; hors du périmètre de la v1.0.
- **Signets, info-bulles et page d'extraction** : reportés en v1.1, les trois pages répondent déjà à la question.

## Conséquences

- Le modèle et le rapport se relisent en pull request comme du code ; un fond de page se régénère en une commande.
- Les données du rapport datent de la dernière actualisation dans Power BI Desktop, faite à la main.
- Le PBIR se modifie aussi par script, à condition que Power BI soit fermé : il réécrit ses fichiers à chaque enregistrement.
- Chaque page s'affiche en moins de 0,7 s, et aucune requête DAX ne dépasse 26 ms ; le temps restant est le dessin des visuels.
- Un nouveau libellé, ou une nouvelle catégorie, passe par dbt et ses tests avant d'apparaître dans le rapport.
