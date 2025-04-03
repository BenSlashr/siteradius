# Guide Technique du Crawler

Ce document détaille le fonctionnement du crawler de SiteRadius, responsable de l'exploration des sites web et de l'extraction de leur contenu.

## Vue d'ensemble

Le crawler est un composant essentiel de SiteRadius qui explore récursivement un site web, extrait le contenu textuel des pages et prépare les données pour l'analyse sémantique. Il est conçu pour être efficace, respectueux des ressources du serveur cible et capable de gérer des sites de grande taille.

## Fonctionnalités principales

- Exploration asynchrone des sites web
- Extraction du contenu textuel pertinent
- Respect des règles robots.txt
- Gestion des limites de profondeur et de nombre d'URLs
- Détection et normalisation des URLs
- Filtrage du contenu non pertinent

## Architecture du crawler

Le crawler est implémenté dans le fichier `crawler.py` et s'articule autour de la classe principale `SiteCrawler`.

### Classe SiteCrawler

```python
class SiteCrawler:
    def __init__(self, start_url, max_urls=100, max_depth=3, delay=0.1):
        self.start_url = start_url
        self.max_urls = max_urls
        self.max_depth = max_depth
        self.delay = delay
        self.visited_urls = set()
        self.queue = asyncio.Queue()
        self.results = []
        self.session = None
        self.robots_parser = None
```

#### Attributs principaux

- `start_url` : URL de départ pour le crawl
- `max_urls` : Nombre maximum d'URLs à explorer
- `max_depth` : Profondeur maximale d'exploration
- `delay` : Délai entre les requêtes (en secondes)
- `visited_urls` : Ensemble des URLs déjà visitées
- `queue` : File d'attente asynchrone pour les URLs à explorer
- `results` : Liste des résultats (contenu extrait)
- `session` : Session HTTP asynchrone
- `robots_parser` : Parser pour les fichiers robots.txt

### Méthodes principales

#### 1. Initialisation du crawl

```python
async def init_crawl(self):
    """Initialise la session HTTP et le parser robots.txt"""
    self.session = aiohttp.ClientSession()
    await self.init_robots_parser()
    await self.queue.put((self.start_url, 0))  # (url, depth)
```

#### 2. Crawling principal

```python
async def crawl(self):
    """Méthode principale de crawling"""
    await self.init_crawl()
    workers = [asyncio.create_task(self.worker()) for _ in range(10)]
    await self.queue.join()
    for w in workers:
        w.cancel()
    await self.session.close()
    return self.results
```

#### 3. Worker asynchrone

```python
async def worker(self):
    """Worker qui traite les URLs de la queue"""
    while True:
        url, depth = await self.queue.get()
        try:
            if len(self.visited_urls) >= self.max_urls:
                self.queue.task_done()
                continue
                
            if url in self.visited_urls:
                self.queue.task_done()
                continue
                
            self.visited_urls.add(url)
            
            if not self.is_allowed_by_robots(url):
                self.queue.task_done()
                continue
            
            # Respecter le délai entre les requêtes
            await asyncio.sleep(self.delay)
            
            # Récupérer et traiter la page
            html = await self.fetch_url(url)
            if html:
                content = self.extract_content(html)
                if content:
                    self.results.append({
                        "url": url,
                        "content": content,
                        "depth": depth
                    })
                
                # Ajouter les liens trouvés à la queue si la profondeur le permet
                if depth < self.max_depth:
                    links = self.extract_links(html, url)
                    for link in links:
                        if link not in self.visited_urls:
                            await self.queue.put((link, depth + 1))
        except Exception as e:
            print(f"Error processing {url}: {e}")
        finally:
            self.queue.task_done()
```

#### 4. Extraction de contenu

```python
def extract_content(self, html):
    """Extrait le contenu textuel pertinent d'une page HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Supprimer les éléments non pertinents
    for element in soup.select('script, style, nav, footer, header, aside'):
        element.decompose()
    
    # Extraire le texte du contenu principal
    main_content = soup.select_one('main, article, #content, .content')
    if main_content:
        text = main_content.get_text(separator=' ', strip=True)
    else:
        text = soup.body.get_text(separator=' ', strip=True)
    
    # Nettoyer le texte
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text if len(text) > 100 else None  # Ignorer les pages avec trop peu de contenu
```

#### 5. Extraction de liens

```python
def extract_links(self, html, base_url):
    """Extrait et normalise les liens d'une page HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        
        # Normaliser l'URL
        full_url = urljoin(base_url, href)
        
        # Vérifier si l'URL est dans le même domaine
        if self.is_same_domain(full_url, self.start_url):
            # Nettoyer l'URL (supprimer fragments, paramètres de requête, etc.)
            clean_url = self.clean_url(full_url)
            if clean_url:
                links.append(clean_url)
    
    return links
```

## Optimisations pour les grands sites

Pour gérer efficacement les sites de grande taille (jusqu'à 10 000 URLs), le crawler intègre plusieurs optimisations :

### 1. Crawling asynchrone

L'utilisation d'`asyncio` et `aiohttp` permet de traiter plusieurs pages simultanément, réduisant considérablement le temps d'exploration.

```python
# Création de plusieurs workers asynchrones
workers = [asyncio.create_task(self.worker()) for _ in range(10)]
```

### 2. Gestion de la mémoire

Pour éviter les problèmes de mémoire avec les grands sites, le crawler :

- Limite la taille du texte extrait
- Utilise des structures de données efficaces (ensembles pour les URLs visitées)
- Nettoie les objets BeautifulSoup après utilisation

### 3. Respect des serveurs cibles

Pour éviter de surcharger les serveurs cibles :

- Délai configurable entre les requêtes
- Respect des règles robots.txt
- Limitation du nombre de workers parallèles

## Traitement des erreurs

Le crawler est conçu pour être robuste face aux erreurs courantes :

- Timeout des requêtes HTTP
- Pages inaccessibles ou erreurs 404
- Contenu malformé ou non standard
- Redirections infinies

Chaque erreur est gérée individuellement sans interrompre le processus global de crawling.

## Extension du crawler

Le crawler peut être étendu de plusieurs façons :

### Ajout de nouveaux extracteurs de contenu

Pour supporter des types de sites spécifiques :

```python
def extract_content_for_blog(self, html):
    """Extracteur spécialisé pour les blogs"""
    # Implémentation spécifique
```

### Support de l'authentification

Pour explorer des sites nécessitant une authentification :

```python
async def login(self, login_url, username, password):
    """Authentification sur le site cible"""
    # Implémentation de l'authentification
```

### Extraction de métadonnées supplémentaires

Pour enrichir l'analyse avec des métadonnées :

```python
def extract_metadata(self, html):
    """Extrait les métadonnées de la page"""
    # Extraction des balises meta, Open Graph, etc.
```

## Considérations de performance

- Le crawler peut traiter environ 10-20 pages par seconde (selon la configuration)
- Pour un site de 10 000 URLs, le temps d'exploration est d'environ 10-15 minutes
- La consommation mémoire reste stable même pour les grands sites grâce au traitement asynchrone
