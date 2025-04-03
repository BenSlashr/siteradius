# Guide Technique de l'Analyzer

Ce document détaille le fonctionnement du module d'analyse de SiteRadius, responsable de la conversion du contenu textuel en embeddings vectoriels et du calcul des métriques de cohésion sémantique.

## Vue d'ensemble

L'analyzer est le cœur algorithmique de SiteRadius. Il prend en entrée le contenu textuel extrait par le crawler, le convertit en représentations vectorielles (embeddings), puis calcule diverses métriques et visualisations pour évaluer la cohésion sémantique du site web.

## Fonctionnalités principales

- Conversion du texte en embeddings vectoriels
- Calcul du Site Focus Score et du Site Radius
- Génération de la distribution de similarité
- Analyse de la composition du contenu
- Création des clusters de contenu
- Calcul des métriques par page

## Architecture de l'analyzer

L'analyzer est implémenté dans le fichier `analyzer.py` et s'articule autour de la classe principale `SiteAnalyzer`.

### Classe SiteAnalyzer

```python
class SiteAnalyzer:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.embeddings_cache = {}
        
    def load_model(self):
        """Charge le modèle d'embedding"""
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)
        return self.model
```

#### Attributs principaux

- `model_name` : Nom du modèle Sentence Transformer à utiliser
- `model` : Instance du modèle chargé
- `embeddings_cache` : Cache pour éviter de recalculer les embeddings

### Méthodes principales

#### 1. Analyse du site

```python
def analyze_site(self, crawl_results):
    """Méthode principale d'analyse du site"""
    # Charger le modèle
    model = self.load_model()
    
    # Extraire le contenu des pages
    pages = [result for result in crawl_results if result.get('content')]
    
    # Calculer les embeddings pour chaque page
    page_embeddings = []
    for page in pages:
        embedding = self.get_embedding(page['content'])
        if embedding is not None:
            page_embeddings.append({
                'url': page['url'],
                'embedding': embedding,
                'content_length': len(page['content'])
            })
    
    # Calculer le centroïde (représentation du thème central)
    centroid = self.calculate_centroid(page_embeddings)
    
    # Calculer les similarités avec le centroïde
    similarities = []
    for page in page_embeddings:
        sim = self.cosine_similarity(page['embedding'], centroid)
        similarities.append(sim)
        page['similarity'] = sim
    
    # Calculer le Site Focus Score (moyenne des similarités)
    focus_score = np.mean(similarities)
    
    # Calculer le Site Radius (1 - moyenne des similarités)
    radius = 1 - focus_score
    
    # Générer la distribution de similarité
    similarity_distribution = self.generate_similarity_distribution(similarities)
    
    # Analyser la composition du contenu
    content_composition = self.analyze_content_composition(similarities)
    
    # Créer les clusters de contenu
    content_clusters = self.create_content_clusters(page_embeddings, centroid)
    
    # Calculer les métriques par page
    page_metrics = self.calculate_page_metrics(page_embeddings)
    
    # Assembler les résultats
    results = {
        "site_focus_score": float(focus_score),
        "site_radius": float(radius),
        "similarity_distribution": similarity_distribution,
        "content_composition": content_composition,
        "content_clusters": content_clusters,
        "page_metrics": page_metrics,
        "metadata": {
            "url": crawl_results[0]['url'] if crawl_results else "",
            "pages_crawled": len(pages),
            "model_used": self.model_name,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    return results
```

#### 2. Calcul des embeddings

```python
def get_embedding(self, text):
    """Calcule l'embedding pour un texte donné"""
    # Utiliser le cache si disponible
    if text in self.embeddings_cache:
        return self.embeddings_cache[text]
    
    # Limiter la taille du texte pour éviter les problèmes de mémoire
    if len(text) > 10000:
        text = text[:10000]
    
    try:
        # Calculer l'embedding
        embedding = self.model.encode(text)
        
        # Normaliser l'embedding
        normalized_embedding = embedding / np.linalg.norm(embedding)
        
        # Mettre en cache
        self.embeddings_cache[text] = normalized_embedding
        
        return normalized_embedding
    except Exception as e:
        print(f"Error calculating embedding: {e}")
        return None
```

#### 3. Calcul du centroïde

```python
def calculate_centroid(self, page_embeddings):
    """Calcule le centroïde (représentation du thème central)"""
    if not page_embeddings:
        return None
    
    # Extraire les embeddings
    embeddings = [page['embedding'] for page in page_embeddings]
    
    # Calculer la moyenne
    centroid = np.mean(embeddings, axis=0)
    
    # Normaliser
    normalized_centroid = centroid / np.linalg.norm(centroid)
    
    return normalized_centroid
```

#### 4. Génération de la distribution de similarité

```python
def generate_similarity_distribution(self, similarities):
    """Génère la distribution des similarités"""
    # Définir les intervalles (0.0-0.1, 0.1-0.2, ..., 0.9-1.0)
    bins = np.linspace(0, 1, 11)
    
    # Calculer l'histogramme
    hist, bin_edges = np.histogram(similarities, bins=bins)
    
    # Formater les résultats
    distribution = []
    for i in range(len(hist)):
        distribution.append({
            "range": [float(bin_edges[i]), float(bin_edges[i+1])],
            "count": int(hist[i])
        })
    
    return distribution
```

#### 5. Analyse de la composition du contenu

```python
def analyze_content_composition(self, similarities):
    """Analyse la composition du contenu par catégorie"""
    # Définir les seuils pour chaque catégorie
    central_threshold = 0.8
    support_threshold = 0.6
    
    # Compter les pages dans chaque catégorie
    central_content = sum(1 for sim in similarities if sim >= central_threshold)
    support_content = sum(1 for sim in similarities if central_threshold > sim >= support_threshold)
    peripheral_content = sum(1 for sim in similarities if sim < support_threshold)
    
    # Calculer les pourcentages
    total = len(similarities)
    composition = {
        "central_content": {
            "count": central_content,
            "percentage": central_content / total if total > 0 else 0
        },
        "support_content": {
            "count": support_content,
            "percentage": support_content / total if total > 0 else 0
        },
        "peripheral_content": {
            "count": peripheral_content,
            "percentage": peripheral_content / total if total > 0 else 0
        }
    }
    
    return composition
```

#### 6. Création des clusters de contenu

```python
def create_content_clusters(self, page_embeddings, centroid):
    """Crée les clusters de contenu basés sur l'alignement topique et la densité d'information"""
    clusters = []
    
    for page in page_embeddings:
        # Alignement topique = similarité avec le centroïde
        topic_alignment = page['similarity']
        
        # Densité d'information (approximation basée sur la longueur du contenu)
        # Normaliser entre 0 et 1 avec une fonction sigmoïde
        content_length = page['content_length']
        info_density = 2 / (1 + math.exp(-content_length / 5000)) - 1
        
        # Déterminer la catégorie
        if topic_alignment >= 0.8:
            category = "central"
        elif topic_alignment >= 0.6:
            category = "support"
        else:
            category = "peripheral"
        
        clusters.append({
            "url": page['url'],
            "topic_alignment": float(topic_alignment),
            "info_density": float(info_density),
            "category": category
        })
    
    return clusters
```

## Fondements mathématiques

### Similarité cosinus

La similarité cosinus est la mesure principale utilisée pour évaluer la proximité sémantique entre les pages :

```
similarity(A, B) = (A · B) / (||A|| * ||B||)
```

où :
- A · B est le produit scalaire des vecteurs
- ||A|| et ||B|| sont les normes des vecteurs

### Site Focus Score

Le Site Focus Score est calculé comme la moyenne des similarités de toutes les pages avec le centroïde :

```
focus_score = (1/n) * Σ similarity(page_i, centroid)
```

### Site Radius

Le Site Radius est calculé comme le complément du Site Focus Score :

```
radius = 1 - focus_score
```

## Optimisations pour les grands sites

Pour gérer efficacement les sites de grande taille, l'analyzer intègre plusieurs optimisations :

### 1. Cache d'embeddings

Les embeddings sont mis en cache pour éviter de recalculer les mêmes textes :

```python
def get_embedding(self, text):
    # Utiliser le cache si disponible
    if text in self.embeddings_cache:
        return self.embeddings_cache[text]
    # ...
```

### 2. Traitement par lots

Pour les grands sites, les embeddings sont calculés par lots pour optimiser l'utilisation du GPU/CPU :

```python
def batch_encode(self, texts, batch_size=32):
    """Encode les textes par lots"""
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        embeddings = self.model.encode(batch)
        all_embeddings.extend(embeddings)
    return all_embeddings
```

### 3. Limitation de la taille des textes

Pour éviter les problèmes de mémoire, la taille des textes est limitée :

```python
if len(text) > 10000:
    text = text[:10000]
```

## Extension de l'analyzer

L'analyzer peut être étendu de plusieurs façons :

### Nouveaux modèles d'embedding

Pour utiliser d'autres modèles d'embedding :

```python
def load_custom_model(self, model_path):
    """Charge un modèle personnalisé"""
    self.model = SentenceTransformer(model_path)
    return self.model
```

### Métriques supplémentaires

Pour ajouter de nouvelles métriques d'analyse :

```python
def calculate_topic_diversity(self, page_embeddings):
    """Calcule la diversité thématique du site"""
    # Implémentation de la métrique
```

### Visualisations additionnelles

Pour créer de nouvelles visualisations :

```python
def generate_topic_network(self, page_embeddings):
    """Génère un réseau de thèmes interconnectés"""
    # Implémentation de la visualisation
```

## Considérations de performance

- L'analyzer peut traiter environ 100-200 pages par minute (selon la configuration)
- Pour un site de 10 000 URLs, le temps d'analyse est d'environ 50-100 minutes
- La consommation mémoire est principalement déterminée par la taille du modèle d'embedding (typiquement 200-500 MB)
