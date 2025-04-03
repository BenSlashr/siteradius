# Guide Technique de l'API

Ce document détaille l'implémentation de l'API de SiteRadius, expliquant les endpoints, les structures de données et les mécanismes de traitement asynchrone.

## Vue d'ensemble

L'API de SiteRadius est construite avec FastAPI, un framework Python moderne pour le développement d'APIs RESTful. Elle sert d'interface entre le frontend et les composants backend (crawler et analyzer), permettant de lancer des analyses de sites web, de suivre leur progression et de récupérer les résultats.

## Structure de l'API

L'API est implémentée dans le fichier `app.py` et s'articule autour de plusieurs endpoints RESTful.

### Configuration et initialisation

```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
import os
import json
import uuid
from datetime import datetime
import asyncio

from crawler import SiteCrawler
from analyzer import SiteAnalyzer

# Modèles de données
class AnalysisRequest(BaseModel):
    url: HttpUrl
    max_urls: int = 100
    max_depth: int = 3

class AnalysisResponse(BaseModel):
    task_id: str
    status: str

class StatusResponse(BaseModel):
    status: str
    progress: int
    message: str

# Initialisation de l'application
app = FastAPI(
    title="SiteRadius API",
    description="API pour l'analyse de cohésion sémantique des sites web",
    version="1.0.0"
)

# Montage des fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

# Stockage en mémoire des tâches en cours
tasks = {}
```

## Endpoints principaux

### 1. Page d'accueil

```python
@app.get("/")
async def read_root():
    """Renvoie la page d'accueil"""
    return FileResponse("static/index.html")
```

### 2. Lancement d'une analyse

```python
@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_site(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Lance l'analyse d'un site web"""
    # Générer un ID unique pour la tâche
    task_id = str(uuid.uuid4())
    
    # Initialiser le statut de la tâche
    tasks[task_id] = {
        "status": "pending",
        "progress": 0,
        "message": "Initialisation de l'analyse...",
        "url": request.url,
        "max_urls": request.max_urls,
        "max_depth": request.max_depth,
        "start_time": datetime.now().isoformat()
    }
    
    # Lancer l'analyse en arrière-plan
    background_tasks.add_task(
        run_analysis,
        task_id,
        request.url,
        request.max_urls,
        request.max_depth
    )
    
    return {"task_id": task_id, "status": "running"}
```

### 3. Vérification du statut

```python
@app.get("/status/{task_id}", response_model=StatusResponse)
async def get_status(task_id: str):
    """Vérifie le statut d'une tâche d'analyse"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    
    task = tasks[task_id]
    
    return {
        "status": task["status"],
        "progress": task["progress"],
        "message": task["message"]
    }
```

### 4. Récupération des résultats

```python
@app.get("/results/{task_id}")
async def get_results(task_id: str):
    """Récupère les résultats d'une analyse terminée"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    
    task = tasks[task_id]
    
    if task["status"] != "completed":
        raise HTTPException(status_code=202, detail="Analyse en cours")
    
    # Vérifier si le fichier de résultats existe
    result_file = f"results/{task_id}.json"
    if not os.path.exists(result_file):
        raise HTTPException(status_code=404, detail="Résultats non trouvés")
    
    # Charger et renvoyer les résultats
    with open(result_file, "r") as f:
        results = json.load(f)
    
    return results
```

## Traitement asynchrone

Le traitement asynchrone est géré par la fonction `run_analysis` qui est exécutée en arrière-plan :

```python
async def run_analysis(task_id: str, url: str, max_urls: int, max_depth: int):
    """Exécute l'analyse complète en arrière-plan"""
    try:
        # Mettre à jour le statut
        tasks[task_id]["status"] = "running"
        tasks[task_id]["progress"] = 5
        tasks[task_id]["message"] = "Démarrage du crawling..."
        
        # Initialiser le crawler
        crawler = SiteCrawler(url, max_urls=max_urls, max_depth=max_depth)
        
        # Exécuter le crawling
        tasks[task_id]["progress"] = 10
        tasks[task_id]["message"] = "Crawling du site en cours..."
        crawl_results = await crawler.crawl(
            progress_callback=lambda p, m: update_progress(task_id, p * 0.6 + 10, m)
        )
        
        # Mettre à jour le statut
        tasks[task_id]["progress"] = 70
        tasks[task_id]["message"] = "Crawling terminé. Démarrage de l'analyse..."
        
        # Initialiser l'analyzer
        analyzer = SiteAnalyzer()
        
        # Exécuter l'analyse
        tasks[task_id]["message"] = "Analyse sémantique en cours..."
        analysis_results = analyzer.analyze_site(
            crawl_results,
            progress_callback=lambda p, m: update_progress(task_id, p * 0.3 + 70, m)
        )
        
        # Sauvegarder les résultats
        os.makedirs("results", exist_ok=True)
        with open(f"results/{task_id}.json", "w") as f:
            json.dump(analysis_results, f)
        
        # Mettre à jour le statut final
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["progress"] = 100
        tasks[task_id]["message"] = "Analyse terminée"
        tasks[task_id]["end_time"] = datetime.now().isoformat()
        
    except Exception as e:
        # Gérer les erreurs
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["message"] = f"Erreur: {str(e)}"
        print(f"Error in task {task_id}: {e}")
```

### Fonction de mise à jour de la progression

```python
def update_progress(task_id: str, progress: float, message: str):
    """Met à jour la progression d'une tâche"""
    if task_id in tasks:
        tasks[task_id]["progress"] = min(int(progress), 99)  # Max 99% jusqu'à la fin
        tasks[task_id]["message"] = message
```

## Structures de données

### 1. Requête d'analyse

```python
class AnalysisRequest(BaseModel):
    url: HttpUrl
    max_urls: int = 100
    max_depth: int = 3
```

### 2. Réponse d'analyse

```python
class AnalysisResponse(BaseModel):
    task_id: str
    status: str
```

### 3. Réponse de statut

```python
class StatusResponse(BaseModel):
    status: str
    progress: int
    message: str
```

### 4. Format des résultats

Les résultats sont stockés au format JSON avec la structure suivante :

```json
{
  "site_focus_score": 0.85,
  "site_radius": 0.12,
  "similarity_distribution": [
    {
      "range": [0.0, 0.1],
      "count": 5
    },
    // ...
  ],
  "content_composition": {
    "central_content": {
      "count": 25,
      "percentage": 0.5
    },
    "support_content": {
      "count": 15,
      "percentage": 0.3
    },
    "peripheral_content": {
      "count": 10,
      "percentage": 0.2
    }
  },
  "content_clusters": [
    {
      "url": "https://example.com/page1",
      "topic_alignment": 0.92,
      "info_density": 0.78,
      "category": "central"
    },
    // ...
  ],
  "page_metrics": [
    {
      "url": "https://example.com/page1",
      "similarity": 0.92,
      "content_length": 2500
    },
    // ...
  ],
  "metadata": {
    "url": "https://example.com",
    "pages_crawled": 50,
    "model_used": "all-MiniLM-L6-v2",
    "timestamp": "2025-04-02T15:30:45.123456"
  }
}
```

## Gestion des erreurs

L'API gère plusieurs types d'erreurs :

### 1. Erreurs de validation

FastAPI valide automatiquement les requêtes entrantes grâce aux modèles Pydantic :

```python
# Si l'URL n'est pas valide, FastAPI renvoie une erreur 422
@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_site(request: AnalysisRequest, background_tasks: BackgroundTasks):
    # ...
```

### 2. Erreurs de ressource non trouvée

```python
@app.get("/results/{task_id}")
async def get_results(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    # ...
    
    if not os.path.exists(result_file):
        raise HTTPException(status_code=404, detail="Résultats non trouvés")
    # ...
```

### 3. Erreurs de traitement

Les erreurs survenant pendant l'analyse sont capturées et stockées dans le statut de la tâche :

```python
try:
    # Processus d'analyse
except Exception as e:
    tasks[task_id]["status"] = "failed"
    tasks[task_id]["message"] = f"Erreur: {str(e)}"
    print(f"Error in task {task_id}: {e}")
```

## Documentation interactive

FastAPI génère automatiquement une documentation interactive pour l'API :

- Swagger UI : `/docs`
- ReDoc : `/redoc`

## Optimisations pour les grands sites

Pour gérer efficacement les analyses de grands sites (jusqu'à 10 000 URLs), l'API intègre plusieurs optimisations :

### 1. Traitement asynchrone

L'utilisation de tâches en arrière-plan permet de libérer le serveur web pour traiter d'autres requêtes pendant qu'une analyse est en cours.

### 2. Mises à jour de progression

Les callbacks de progression permettent de suivre l'avancement de l'analyse en temps réel :

```python
crawl_results = await crawler.crawl(
    progress_callback=lambda p, m: update_progress(task_id, p * 0.6 + 10, m)
)
```

### 3. Gestion de la mémoire

Les résultats sont stockés sur disque dès qu'ils sont disponibles pour libérer la mémoire :

```python
with open(f"results/{task_id}.json", "w") as f:
    json.dump(analysis_results, f)
```

## Extension de l'API

L'API peut être étendue de plusieurs façons :

### 1. Nouveaux endpoints

Pour ajouter de nouvelles fonctionnalités :

```python
@app.get("/compare/{task_id1}/{task_id2}")
async def compare_results(task_id1: str, task_id2: str):
    """Compare les résultats de deux analyses"""
    # Implémentation de la comparaison
```

### 2. Authentification

Pour sécuriser l'API :

```python
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Authentification
    
@app.post("/analyze")
async def analyze_site(request: AnalysisRequest, token: str = Depends(oauth2_scheme)):
    # Vérification du token
    # ...
```

### 3. Limites de taux

Pour éviter les abus :

```python
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

X_API_KEY = APIKeyHeader(name="X-API-Key")

rate_limits = {}  # Stockage des limites par clé API

def check_rate_limit(api_key: str = Depends(X_API_KEY)):
    if api_key in rate_limits:
        # Vérifier les limites
        if rate_limits[api_key]["count"] > 10:  # 10 requêtes max
            raise HTTPException(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        rate_limits[api_key]["count"] += 1
    else:
        rate_limits[api_key] = {"count": 1}
    return api_key

@app.post("/analyze")
async def analyze_site(
    request: AnalysisRequest,
    api_key: str = Depends(check_rate_limit)
):
    # ...
```

## Considérations de déploiement

### 1. Serveur de production

Pour un déploiement en production, il est recommandé d'utiliser Uvicorn avec Gunicorn :

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app
```

### 2. Équilibrage de charge

Pour gérer un grand nombre de requêtes, un équilibreur de charge peut être utilisé avec plusieurs instances de l'API.

### 3. Stockage des résultats

Pour une installation à grande échelle, il est recommandé de remplacer le stockage de fichiers par une base de données :

```python
# Exemple avec MongoDB
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.siteradius
results_collection = db.results

async def save_results(task_id, results):
    await results_collection.insert_one({
        "_id": task_id,
        "results": results,
        "timestamp": datetime.now()
    })

async def get_results(task_id):
    return await results_collection.find_one({"_id": task_id})
```
