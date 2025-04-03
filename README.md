# SiteRadius

Un outil d'analyse de cohésion sémantique pour sites web qui calcule le "Site Focus Score" et le "Site Radius".

![SiteRadius Dashboard](docs/images/dashboard.png)

## Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Fonctionnalités](#fonctionnalités)
- [Architecture technique](#architecture-technique)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [API](#api)
- [Structure du projet](#structure-du-projet)
- [Visualisations](#visualisations)
- [Optimisations](#optimisations)
- [Dépannage](#dépannage)
- [Contribution](#contribution)

## Vue d'ensemble

SiteRadius est un outil d'analyse qui évalue la cohésion sémantique d'un site web en calculant deux métriques principales :

1. **Site Focus Score** : Mesure à quel point le contenu du site est aligné sur un thème central. Des scores plus élevés indiquent une meilleure cohésion thématique.

2. **Site Radius** : Mesure la distance moyenne des pages par rapport au thème central. Des valeurs plus basses indiquent un contenu plus cohérent.

L'outil utilise des techniques avancées de traitement du langage naturel (NLP) pour convertir le contenu textuel en vecteurs d'embeddings, puis analyse les relations sémantiques entre ces vecteurs.

## Fonctionnalités

- **Crawling de sites web** : Exploration automatique des sites avec gestion des limites de profondeur et de nombre d'URLs
- **Extraction de contenu** : Isolation du contenu textuel pertinent des pages web
- **Analyse sémantique** : Conversion du texte en embeddings vectoriels via sentence-transformers
- **Métriques de cohésion** : Calcul du Site Focus Score et du Site Radius
- **Visualisations avancées** :
  - Jauges interactives pour les métriques principales
  - Distribution de similarité du contenu
  - Composition du contenu par catégorie
  - Clusters de contenu (alignement topique vs densité d'information)
- **Interface utilisateur moderne** : Dashboard responsive avec visualisations interactives
- **API RESTful** : Points d'accès pour l'intégration avec d'autres systèmes

## Architecture technique

### Backend
- **Python 3.10** : Langage principal pour la compatibilité avec les bibliothèques NLP
- **FastAPI** : Framework API haute performance
- **BeautifulSoup4** : Extraction de contenu HTML
- **Sentence-Transformers** : Génération d'embeddings vectoriels
- **NumPy/SciPy/Scikit-learn** : Calculs mathématiques et analyses
- **asyncio/aiohttp** : Crawling asynchrone pour de meilleures performances

### Frontend
- **HTML5/CSS3/JavaScript** : Interface utilisateur
- **Chart.js** : Visualisations interactives
- **Fetch API** : Communication avec le backend

## Installation

### Prérequis
- Python 3.10 ou supérieur
- pip (gestionnaire de paquets Python)
- Navigateur web moderne

### Étapes d'installation

1. Clonez le dépôt :
```bash
git clone https://github.com/votre-username/siteradius.git
cd siteradius
```

2. Créez un environnement virtuel (recommandé) :
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate
```

3. Installez les dépendances :
```bash
pip install -r requirements.txt
```

## Configuration

Le fichier `config.py` contient les paramètres configurables :

- `MAX_URLS` : Nombre maximum d'URLs à crawler (par défaut : 10000)
- `MAX_DEPTH` : Profondeur maximale du crawl (par défaut : 5)
- `CRAWL_DELAY` : Délai entre les requêtes (par défaut : 0.1 seconde)
- `MODEL_NAME` : Modèle d'embedding à utiliser (par défaut : "all-MiniLM-L6-v2")
- `RESULTS_DIR` : Répertoire de stockage des résultats (par défaut : "./results")

## Utilisation

### Application standalone

Lancez l'application principale :
```bash
python main.py
```

Puis accédez à l'interface via votre navigateur à l'adresse : http://localhost:8000

### API seule

Pour démarrer uniquement l'API :
```bash
uvicorn app:app --reload
```

Documentation interactive de l'API : http://localhost:8000/docs

## API

L'API RESTful expose les endpoints suivants :

### POST /analyze
Lance l'analyse d'un site web.

**Paramètres :**
```json
{
  "url": "https://example.com",
  "max_urls": 100,
  "max_depth": 3
}
```

**Réponse :**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running"
}
```

### GET /status/{task_id}
Vérifie le statut d'une tâche d'analyse.

**Réponse :**
```json
{
  "status": "completed",
  "progress": 100,
  "message": "Analyse terminée"
}
```

### GET /results/{task_id}
Récupère les résultats d'une analyse terminée.

**Réponse :**
```json
{
  "site_focus_score": 0.85,
  "site_radius": 0.12,
  "similarity_distribution": [...],
  "content_composition": {...},
  "content_clusters": [...],
  "page_metrics": [...]
}
```

## Structure du projet

```
siteradius/
├── app.py              # Application FastAPI
├── main.py             # Point d'entrée principal
├── config.py           # Configuration globale
├── crawler.py          # Logique de crawling
├── analyzer.py         # Analyse sémantique
├── utils.py            # Fonctions utilitaires
├── requirements.txt    # Dépendances
├── results/            # Résultats d'analyse stockés
├── static/             # Fichiers statiques frontend
│   ├── index.html      # Page principale
│   ├── styles.css      # Styles CSS
│   ├── script.js       # JavaScript frontend
│   └── images/         # Images et icônes
└── docs/               # Documentation
    └── images/         # Images pour la documentation
```

## Visualisations

### Jauges de métriques
Les jauges affichent le Site Focus Score et le Site Radius avec un design moderne et intuitif. L'aiguille indique la valeur actuelle sur un arc semi-circulaire avec un dégradé de couleurs.

### Distribution de similarité
Un histogramme montrant comment les pages se répartissent selon leur similarité au thème central du site.

### Composition du contenu
Répartition des pages en trois catégories :
- **Contenu central** (similarité > 0.8) : pages fortement alignées sur le thème principal
- **Contenu de support** (similarité 0.6-0.8) : pages modérément alignées
- **Contenu périphérique** (similarité < 0.6) : pages faiblement alignées

### Clusters de contenu
Un graphique à nuage de points représentant chaque page selon deux dimensions :
1. **Alignement topique** (axe X) : degré d'alignement avec le thème central
2. **Densité d'information** (axe Y) : richesse informationnelle de la page

## Optimisations

SiteRadius est optimisé pour analyser des sites web de grande taille :

- **Crawling parallèle** : Utilisation d'asyncio pour explorer plusieurs pages simultanément
- **Gestion de la mémoire** : Traitement par lots pour les grands sites
- **Mise en cache** : Stockage intermédiaire des résultats pour éviter les recalculs
- **Traitement vectorisé** : Utilisation de NumPy pour des calculs mathématiques efficaces

## Dépannage

### Problèmes courants

1. **Erreur "ModuleNotFoundError"** :
   - Vérifiez que toutes les dépendances sont installées : `pip install -r requirements.txt`

2. **Erreur de mémoire lors de l'analyse de grands sites** :
   - Réduisez le nombre maximum d'URLs dans la configuration
   - Augmentez la mémoire disponible pour Python

3. **Crawling bloqué par le site** :
   - Augmentez le délai entre les requêtes dans config.py
   - Vérifiez si le site utilise des protections anti-bot

4. **Visualisations non affichées** :
   - Vérifiez la console du navigateur pour les erreurs JavaScript
   - Assurez-vous que les données sont correctement formatées dans l'API

## Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Forkez le dépôt
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/ma-fonctionnalite`)
3. Committez vos changements (`git commit -m 'Ajout de ma fonctionnalité'`)
4. Poussez vers la branche (`git push origin feature/ma-fonctionnalite`)
5. Ouvrez une Pull Request
