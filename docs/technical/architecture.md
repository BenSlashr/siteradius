# Architecture Technique de SiteRadius

Ce document détaille l'architecture technique de SiteRadius, expliquant comment les différents composants interagissent pour analyser la cohésion sémantique des sites web.

## Vue d'ensemble de l'architecture

SiteRadius suit une architecture modulaire avec une séparation claire entre les composants frontend et backend :

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │◄────┤    API      │◄────┤   Backend   │
│  (Browser)  │     │  (FastAPI)  │     │  (Python)   │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
                                        ┌─────────────┐
                                        │  Stockage   │
                                        │  (Fichiers) │
                                        └─────────────┘
```

## Composants principaux

### 1. Frontend (static/)

Le frontend est construit avec des technologies web standard :

- **HTML5** (`index.html`) : Structure de l'interface utilisateur
- **CSS3** (`styles.css`) : Styles et mise en page
- **JavaScript** (`script.js`) : Logique client et visualisations

#### Points clés du frontend :

- Interface utilisateur responsive adaptée aux mobiles et ordinateurs
- Visualisations interactives avec Chart.js
- Communication asynchrone avec l'API via Fetch
- Polling pour les mises à jour de statut des tâches longues

### 2. API (app.py)

L'API est construite avec FastAPI, un framework Python moderne pour les APIs web :

- Endpoints RESTful pour l'analyse, le statut et les résultats
- Gestion asynchrone des requêtes pour de meilleures performances
- Documentation interactive via Swagger UI
- Validation des données d'entrée

### 3. Backend

Le backend est composé de plusieurs modules Python spécialisés :

#### Crawler (crawler.py)

- Exploration asynchrone des sites web
- Respect des règles robots.txt
- Gestion des limites de profondeur et de nombre d'URLs
- Extraction du contenu textuel pertinent

#### Analyzer (analyzer.py)

- Conversion du texte en embeddings vectoriels
- Calcul des métriques de cohésion sémantique
- Génération des visualisations de données
- Analyse des clusters de contenu

#### Utilitaires (utils.py)

- Fonctions d'aide pour le traitement de texte
- Gestion des fichiers et des résultats
- Fonctions mathématiques spécialisées

### 4. Stockage

Les résultats sont stockés dans un format JSON dans le répertoire `results/` :

- Un fichier par analyse avec un UUID unique
- Structure de données standardisée pour les résultats
- Métadonnées incluses (URL, date, paramètres)

## Flux de données

1. **Soumission d'analyse** :
   - L'utilisateur soumet une URL via le frontend
   - L'API crée une tâche et renvoie un ID de tâche
   - Le frontend commence à interroger l'API pour les mises à jour de statut

2. **Processus d'analyse** :
   - Le crawler explore le site et extrait le contenu
   - L'analyzer traite le contenu et calcule les métriques
   - Les résultats sont stockés dans un fichier JSON

3. **Affichage des résultats** :
   - Le frontend récupère les résultats via l'API
   - Les données sont transformées en visualisations
   - L'interface utilisateur est mise à jour avec les résultats

## Diagramme de séquence

```
┌────────┐          ┌────────┐          ┌────────┐          ┌────────┐
│Frontend│          │  API   │          │Crawler │          │Analyzer│
└───┬────┘          └───┬────┘          └───┬────┘          └───┬────┘
    │                   │                   │                   │
    │ POST /analyze     │                   │                   │
    │──────────────────>│                   │                   │
    │                   │                   │                   │
    │ 202 Accepted      │                   │                   │
    │<──────────────────│                   │                   │
    │                   │                   │                   │
    │                   │ start_crawling()  │                   │
    │                   │───────────────────>                   │
    │                   │                   │                   │
    │ GET /status/{id}  │                   │                   │
    │──────────────────>│                   │                   │
    │                   │                   │                   │
    │ 200 {"status": "running"}            │                   │
    │<──────────────────│                   │                   │
    │                   │                   │                   │
    │                   │                   │ crawling_complete │
    │                   │                   │───────────────────>
    │                   │                   │                   │
    │                   │                   │                   │ analyze()
    │                   │<──────────────────────────────────────│
    │                   │                   │                   │
    │ GET /status/{id}  │                   │                   │
    │──────────────────>│                   │                   │
    │                   │                   │                   │
    │ 200 {"status": "completed"}          │                   │
    │<──────────────────│                   │                   │
    │                   │                   │                   │
    │ GET /results/{id} │                   │                   │
    │──────────────────>│                   │                   │
    │                   │                   │                   │
    │ 200 {results}     │                   │                   │
    │<──────────────────│                   │                   │
    │                   │                   │                   │
```

## Considérations techniques

### Performance

- **Crawling asynchrone** : Utilisation d'asyncio et aiohttp pour explorer plusieurs pages simultanément
- **Traitement par lots** : Pour gérer efficacement les grands sites
- **Mise en cache des embeddings** : Pour éviter de recalculer les embeddings pour les mêmes textes

### Extensibilité

L'architecture modulaire permet d'ajouter facilement de nouvelles fonctionnalités :

- Nouveaux modèles d'embedding
- Métriques d'analyse supplémentaires
- Visualisations additionnelles
- Formats d'exportation alternatifs

### Sécurité

- Validation des entrées utilisateur
- Limitation du nombre d'URLs et de la profondeur de crawl
- Respect des règles robots.txt
- Délai entre les requêtes pour éviter de surcharger les serveurs cibles
