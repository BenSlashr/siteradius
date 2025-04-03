# Guide d'installation détaillé

Ce document fournit des instructions détaillées pour installer et configurer SiteRadius dans différents environnements.

## Prérequis

### Système d'exploitation
SiteRadius est compatible avec :
- Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)
- macOS (Monterey 12+)
- Windows 10/11 avec WSL2 (recommandé) ou nativement

### Dépendances système
- Python 3.10 ou supérieur (Python 3.13 peut présenter des problèmes de compatibilité avec certaines bibliothèques)
- pip (gestionnaire de paquets Python)
- git (pour cloner le dépôt)
- Navigateur web moderne (Chrome, Firefox, Safari, Edge)

### Matériel recommandé
- CPU : 4 cœurs ou plus
- RAM : 8 Go minimum, 16 Go recommandé pour l'analyse de grands sites
- Espace disque : 2 Go minimum

## Installation pas à pas

### 1. Installation de Python

#### Sur Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip
```

#### Sur macOS (avec Homebrew)
```bash
brew install python@3.10
```

#### Sur Windows
Téléchargez et installez Python 3.10 depuis [python.org](https://www.python.org/downloads/)

### 2. Clonage du dépôt

```bash
git clone https://github.com/votre-username/siteradius.git
cd siteradius
```

### 3. Création d'un environnement virtuel

```bash
python3.10 -m venv venv
```

### 4. Activation de l'environnement virtuel

#### Sur Linux/macOS
```bash
source venv/bin/activate
```

#### Sur Windows
```bash
venv\Scripts\activate
```

### 5. Installation des dépendances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Si vous rencontrez des problèmes avec certaines bibliothèques, essayez d'installer les dépendances une par une :

```bash
pip install fastapi uvicorn
pip install sentence-transformers
pip install beautifulsoup4 aiohttp
pip install numpy scipy scikit-learn
```

### 6. Vérification de l'installation

```bash
python -c "import sentence_transformers; import fastapi; import numpy; print('Installation réussie!')"
```

Si cette commande s'exécute sans erreur, l'installation est réussie.

## Configuration

### Configuration de base

Le fichier `config.py` contient les paramètres configurables. Vous pouvez le modifier selon vos besoins :

```python
# Paramètres de crawling
MAX_URLS = 10000  # Nombre maximum d'URLs à crawler
MAX_DEPTH = 5     # Profondeur maximale du crawl
CRAWL_DELAY = 0.1 # Délai entre les requêtes (secondes)

# Paramètres d'analyse
MODEL_NAME = "all-MiniLM-L6-v2"  # Modèle d'embedding à utiliser

# Paramètres de stockage
RESULTS_DIR = "./results"  # Répertoire de stockage des résultats
```

### Configuration avancée

#### Utilisation d'un modèle d'embedding personnalisé

Si vous souhaitez utiliser un modèle d'embedding personnalisé :

1. Téléchargez le modèle depuis Hugging Face
2. Placez-le dans un répertoire `models/`
3. Mettez à jour `config.py` :

```python
MODEL_NAME = "./models/mon-modele-personnalise"
```

#### Configuration du serveur

Pour modifier le port d'écoute ou l'interface réseau, créez un fichier `.env` :

```
HOST=0.0.0.0
PORT=8080
WORKERS=4
```

## Démarrage de l'application

### Mode développement

```bash
python main.py
```

Ou pour démarrer uniquement l'API :

```bash
uvicorn app:app --reload
```

### Mode production

Pour un déploiement en production, utilisez Gunicorn (Linux/macOS) :

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 app:app
```

Sur Windows, utilisez hypercorn :

```bash
pip install hypercorn
hypercorn app:app -b 0.0.0.0:8000
```

## Installation avec Docker

### Prérequis
- Docker
- Docker Compose (optionnel)

### Création du Dockerfile

Créez un fichier `Dockerfile` à la racine du projet :

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Création du docker-compose.yml (optionnel)

```yaml
version: '3'

services:
  siteradius:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./results:/app/results
    restart: unless-stopped
```

### Construction et démarrage du conteneur

#### Avec Docker

```bash
docker build -t siteradius .
docker run -p 8000:8000 siteradius
```

#### Avec Docker Compose

```bash
docker-compose up -d
```

## Dépannage

### Problèmes courants et solutions

#### 1. Erreur lors de l'installation des dépendances

**Problème** : `ERROR: Could not build wheels for sentence-transformers`

**Solution** :
```bash
pip install --upgrade pip setuptools wheel
pip install sentence-transformers
```

#### 2. Erreur de mémoire lors de l'analyse

**Problème** : `MemoryError` ou `OutOfMemoryError`

**Solutions** :
- Réduisez `MAX_URLS` dans `config.py`
- Augmentez la mémoire swap
- Utilisez un modèle d'embedding plus léger

#### 3. Problèmes avec Python 3.13

**Problème** : Incompatibilités avec certaines bibliothèques

**Solution** : Utilisez Python 3.10 qui est plus compatible avec toutes les dépendances

#### 4. Le crawler est bloqué par certains sites

**Problème** : Certains sites bloquent le crawler

**Solutions** :
- Augmentez `CRAWL_DELAY` dans `config.py`
- Ajoutez des en-têtes HTTP personnalisés dans `crawler.py`

```python
headers = {
    "User-Agent": "Mozilla/5.0 (compatible; SiteRadiusBot/1.0; +https://example.com/bot)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

async def fetch_url(self, url):
    try:
        async with self.session.get(url, headers=headers, timeout=30) as response:
            # ...
```

## Mise à jour

Pour mettre à jour SiteRadius vers la dernière version :

```bash
# Désactiver l'environnement virtuel si actif
deactivate

# Sauvegarder les résultats et configurations personnalisées
cp -r results results_backup
cp config.py config.py.backup

# Mettre à jour le code
git pull

# Réactiver l'environnement virtuel
source venv/bin/activate  # ou venv\Scripts\activate sur Windows

# Mettre à jour les dépendances
pip install -r requirements.txt --upgrade

# Restaurer les configurations personnalisées si nécessaire
# (comparez d'abord les fichiers pour voir les changements)
```

## Installation pour le développement

Si vous souhaitez contribuer au développement de SiteRadius :

```bash
# Cloner le dépôt
git clone https://github.com/votre-username/siteradius.git
cd siteradius

# Créer et activer un environnement virtuel
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sur Windows

# Installer les dépendances de développement
pip install -r requirements-dev.txt

# Installer le package en mode développement
pip install -e .
```

### Outils de développement recommandés

- **VS Code** avec les extensions :
  - Python
  - Pylance
  - ESLint
  - Prettier
- **PyCharm** (alternative)
- **pytest** pour les tests
- **black** pour le formatage du code
- **isort** pour trier les imports
- **flake8** pour l'analyse statique

### Exécution des tests

```bash
pytest tests/
```

### Vérification du style de code

```bash
black --check .
isort --check-only .
flake8 .
```
