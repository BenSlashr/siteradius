# Guide Technique du Frontend

Ce document détaille l'implémentation du frontend de SiteRadius, expliquant la structure, les composants et les visualisations de l'interface utilisateur.

## Vue d'ensemble

Le frontend de SiteRadius est une interface web moderne qui permet aux utilisateurs de soumettre des sites à analyser et de visualiser les résultats de l'analyse de cohésion sémantique. Il est construit avec des technologies web standard (HTML, CSS, JavaScript) et utilise Chart.js pour les visualisations interactives.

## Structure des fichiers

Le frontend est organisé dans le répertoire `static/` avec la structure suivante :

```
static/
├── index.html      # Structure HTML principale
├── styles.css      # Styles CSS
├── script.js       # Logique JavaScript
└── images/         # Images et icônes
```

## Composants principaux

### 1. Page HTML (index.html)

La page HTML définit la structure de l'interface utilisateur avec plusieurs sections :

- Formulaire d'analyse
- Section de chargement
- Affichage des résultats
  - Informations du site
  - Métriques principales (jauges)
  - Visualisations (distribution, composition, clusters)
  - Tableau des métriques par page

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SiteRadius - Analyse de cohésion sémantique</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <h1>SiteRadius</h1>
        <p>Analyse de cohésion sémantique pour sites web</p>
    </header>
    
    <main>
        <!-- Formulaire d'analyse -->
        <section class="input-section">
            <form id="analysis-form">
                <!-- Champs du formulaire -->
            </form>
        </section>
        
        <!-- Section de chargement -->
        <section id="loading-section">
            <!-- Indicateur de progression -->
        </section>
        
        <!-- Affichage des résultats -->
        <section id="results-section">
            <!-- Informations du site -->
            <div class="site-info">
                <!-- Détails du site -->
            </div>
            
            <!-- Métriques principales -->
            <div class="metrics-container">
                <!-- Jauges -->
            </div>
            
            <!-- Visualisations -->
            <div class="visualizations">
                <!-- Graphiques -->
            </div>
            
            <!-- Tableau des métriques -->
            <div class="table-container">
                <!-- Tableau des pages -->
            </div>
        </section>
    </main>
    
    <footer>
        <!-- Pied de page -->
    </footer>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation"></script>
    <script src="script.js"></script>
</body>
</html>
```

### 2. Styles CSS (styles.css)

Le fichier CSS définit l'apparence visuelle de l'interface avec plusieurs sections :

- Variables globales (couleurs, espacements)
- Styles de base (typographie, mise en page)
- Formulaire d'analyse
- Indicateur de chargement
- Jauges de métriques
- Visualisations
- Tableau des résultats
- Styles responsives

```css
:root {
    --primary-color: #4a6fa5;
    --secondary-color: #6c757d;
    --accent-color: #17a2b8;
    --success-color: #28a745;
    --warning-color: #ffc107;
    --danger-color: #dc3545;
    --light-color: #f8f9fa;
    --dark-color: #343a40;
    --text-color: #212529;
    --border-radius: 8px;
    --box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* Styles de base */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background-color: #f5f7fa;
    margin: 0;
    padding: 0;
}

/* Styles spécifiques pour les jauges */
.gauge-container {
    position: relative;
    width: 220px;
    height: 120px;
    margin: 0 auto 20px;
}

.gauge-arc {
    position: absolute;
    width: 220px;
    height: 110px;
    border-radius: 110px 110px 0 0;
    bottom: 0;
    left: 0;
    overflow: hidden;
    box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.1);
}

/* Styles responsives */
@media (max-width: 768px) {
    .metrics-container {
        flex-direction: column;
    }
    
    .gauge-container {
        width: 180px;
        height: 100px;
    }
}
```

### 3. Logique JavaScript (script.js)

Le fichier JavaScript gère l'interactivité de l'interface et la communication avec l'API :

- Gestion du formulaire d'analyse
- Communication avec l'API backend
- Polling pour les mises à jour de statut
- Affichage des résultats
- Création et mise à jour des visualisations

```javascript
document.addEventListener('DOMContentLoaded', () => {
    // Éléments DOM
    const analysisForm = document.getElementById('analysis-form');
    const inputSection = document.querySelector('.input-section');
    const loadingSection = document.getElementById('loading-section');
    const resultsSection = document.getElementById('results-section');
    
    // Gestionnaire de soumission du formulaire
    analysisForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Récupérer les valeurs du formulaire
        const formData = new FormData(analysisForm);
        const url = formData.get('url');
        const maxUrls = formData.get('max_urls');
        const maxDepth = formData.get('max_depth');
        
        // Préparer les données pour l'API
        const data = {
            url: url,
            max_urls: parseInt(maxUrls),
            max_depth: parseInt(maxDepth)
        };
        
        // Afficher la section de chargement
        inputSection.style.display = 'none';
        loadingSection.style.display = 'block';
        resultsSection.style.display = 'none';
        
        try {
            // Envoyer la requête à l'API
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                // Démarrer le polling pour les mises à jour de statut
                startPolling(result.task_id);
            } else {
                // Afficher l'erreur
                alert(`Erreur: ${result.detail}`);
                inputSection.style.display = 'block';
                loadingSection.style.display = 'none';
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Une erreur est survenue lors de la communication avec le serveur.');
            inputSection.style.display = 'block';
            loadingSection.style.display = 'none';
        }
    });
    
    // Autres fonctions...
});
```

## Visualisations

### 1. Jauges de métriques

Les jauges affichent le Site Focus Score et le Site Radius avec un design moderne et intuitif :

```javascript
function updateGauge(gaugeElement, value) {
    // Identifier quelle jauge nous mettons à jour
    const isFocus = gaugeElement.id === 'focus-fill';
    const valueElement = document.getElementById(isFocus ? 'focus-value' : 'radius-value');
    
    // Mettre à jour la valeur affichée
    valueElement.textContent = value.toFixed(3);
    
    // Calculer l'angle de rotation pour l'aiguille (0 à 180 degrés)
    // 0 = -90 degrés (gauche), 1 = 90 degrés (droite)
    const angle = -90 + (value * 180);
    
    // Appliquer la rotation à l'aiguille
    gaugeElement.style.transform = `translateX(-50%) rotate(${angle}deg)`;
}
```

### 2. Distribution de similarité

Un histogramme montrant comment les pages se répartissent selon leur similarité au thème central :

```javascript
function updateSimilarityDistribution(distributionData) {
    const ctx = document.getElementById('similarity-chart').getContext('2d');
    
    // Préparer les données pour Chart.js
    const labels = distributionData.map(d => `${d.range[0].toFixed(1)}-${d.range[1].toFixed(1)}`);
    const data = distributionData.map(d => d.count);
    
    // Créer le graphique
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Nombre de pages',
                data: data,
                backgroundColor: 'rgba(74, 111, 165, 0.7)',
                borderColor: 'rgba(74, 111, 165, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Nombre de pages'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Similarité au thème central'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Distribution de similarité du contenu'
                },
                tooltip: {
                    callbacks: {
                        title: (tooltipItems) => {
                            const item = tooltipItems[0];
                            const range = distributionData[item.dataIndex].range;
                            return `Similarité: ${range[0].toFixed(1)} - ${range[1].toFixed(1)}`;
                        }
                    }
                }
            }
        }
    });
}
```

### 3. Composition du contenu

Visualisation de la répartition des pages par catégorie :

```javascript
function updateContentComposition(compositionData) {
    const centralContent = compositionData.central_content;
    const supportContent = compositionData.support_content;
    const peripheralContent = compositionData.peripheral_content;
    
    // Mettre à jour les compteurs
    document.getElementById('central-count').textContent = centralContent.count;
    document.getElementById('support-count').textContent = supportContent.count;
    document.getElementById('peripheral-count').textContent = peripheralContent.count;
    
    // Mettre à jour les pourcentages
    document.getElementById('central-percent').textContent = 
        `${(centralContent.percentage * 100).toFixed(1)}%`;
    document.getElementById('support-percent').textContent = 
        `${(supportContent.percentage * 100).toFixed(1)}%`;
    document.getElementById('peripheral-percent').textContent = 
        `${(peripheralContent.percentage * 100).toFixed(1)}%`;
    
    // Mettre à jour les barres de progression
    document.getElementById('central-bar').style.width = 
        `${centralContent.percentage * 100}%`;
    document.getElementById('support-bar').style.width = 
        `${supportContent.percentage * 100}%`;
    document.getElementById('peripheral-bar').style.width = 
        `${peripheralContent.percentage * 100}%`;
}
```

### 4. Clusters de contenu

Un graphique à nuage de points représentant chaque page selon deux dimensions :

```javascript
function updateContentClusters(clustersData, focusScore) {
    const ctx = document.getElementById('clusters-chart').getContext('2d');
    
    // Préparer les données par catégorie
    const centralData = [];
    const supportData = [];
    const peripheralData = [];
    const urls = [];
    
    clustersData.forEach(item => {
        const point = {
            x: item.topic_alignment,
            y: item.info_density
        };
        
        urls.push(item.url);
        
        if (item.category === 'central') {
            centralData.push(point);
        } else if (item.category === 'support') {
            supportData.push(point);
        } else {
            peripheralData.push(point);
        }
    });
    
    // Créer le graphique
    const clustersChart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: 'Contenu central',
                    data: centralData,
                    backgroundColor: 'rgba(40, 167, 69, 0.7)',
                    borderColor: 'rgba(40, 167, 69, 1)',
                    borderWidth: 1,
                    pointRadius: 6,
                    pointHoverRadius: 8
                },
                {
                    label: 'Contenu de support',
                    data: supportData,
                    backgroundColor: 'rgba(255, 193, 7, 0.7)',
                    borderColor: 'rgba(255, 193, 7, 1)',
                    borderWidth: 1,
                    pointRadius: 6,
                    pointHoverRadius: 8
                },
                {
                    label: 'Contenu périphérique',
                    data: peripheralData,
                    backgroundColor: 'rgba(220, 53, 69, 0.7)',
                    borderColor: 'rgba(220, 53, 69, 1)',
                    borderWidth: 1,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Alignement topique'
                    },
                    min: 0,
                    max: 1
                },
                y: {
                    title: {
                        display: true,
                        text: 'Densité d\'information'
                    },
                    min: 0,
                    max: 1
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Clusters de contenu'
                },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const index = context.dataIndex;
                            const datasetIndex = context.datasetIndex;
                            const url = urls[index + datasetIndex * centralData.length];
                            return [
                                `URL: ${formatUrl(url)}`,
                                `Alignement: ${context.parsed.x.toFixed(3)}`,
                                `Densité: ${context.parsed.y.toFixed(3)}`
                            ];
                        }
                    }
                },
                annotation: {
                    annotations: {
                        focusLine: {
                            type: 'line',
                            xMin: focusScore,
                            xMax: focusScore,
                            yMin: 0,
                            yMax: 1,
                            borderColor: 'rgba(74, 111, 165, 0.7)',
                            borderWidth: 2,
                            borderDash: [5, 5],
                            label: {
                                content: `Focus Score: ${focusScore.toFixed(3)}`,
                                enabled: true,
                                position: 'top'
                            }
                        }
                    }
                }
            }
        }
    });
}
```

## Communication avec l'API

### 1. Soumission d'analyse

```javascript
async function submitAnalysis(url, maxUrls, maxDepth) {
    const response = await fetch('/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            url: url,
            max_urls: maxUrls,
            max_depth: maxDepth
        })
    });
    
    return await response.json();
}
```

### 2. Vérification du statut

```javascript
async function checkStatus(taskId) {
    const response = await fetch(`/status/${taskId}`);
    return await response.json();
}
```

### 3. Récupération des résultats

```javascript
async function fetchResults(taskId) {
    const response = await fetch(`/results/${taskId}`);
    
    if (response.ok) {
        const data = await response.json();
        displayResults(data);
        
        // Masquer la section de chargement et afficher les résultats
        loadingSection.style.display = 'none';
        resultsSection.style.display = 'block';
    } else {
        // Gérer les erreurs
        setTimeout(() => {
            fetchResults(taskId);
        }, 3000);
    }
}
```

## Optimisations pour l'expérience utilisateur

### 1. Feedback visuel pendant le chargement

```javascript
function updateProgress(percent, message) {
    const progressBar = document.querySelector('.progress-fill');
    const statusMessage = document.getElementById('status-message');
    
    progressBar.style.width = `${percent}%`;
    statusMessage.textContent = message;
}
```

### 2. Formatage des URLs pour l'affichage

```javascript
function formatUrl(url) {
    // Supprimer le protocole
    let formatted = url.replace(/^https?:\/\//, '');
    
    // Limiter la longueur
    if (formatted.length > 40) {
        formatted = formatted.substring(0, 37) + '...';
    }
    
    return formatted;
}
```

### 3. Tri des tableaux de résultats

```javascript
function setupTableSorting() {
    const tableHeaders = document.querySelectorAll('.sortable');
    
    tableHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const table = header.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            const column = header.dataset.column;
            const isNumeric = header.dataset.type === 'numeric';
            const direction = header.classList.contains('asc') ? -1 : 1;
            
            // Trier les lignes
            rows.sort((a, b) => {
                const aValue = a.querySelector(`td[data-column="${column}"]`).textContent;
                const bValue = b.querySelector(`td[data-column="${column}"]`).textContent;
                
                if (isNumeric) {
                    return direction * (parseFloat(aValue) - parseFloat(bValue));
                } else {
                    return direction * aValue.localeCompare(bValue);
                }
            });
            
            // Mettre à jour la direction du tri
            tableHeaders.forEach(h => h.classList.remove('asc', 'desc'));
            header.classList.add(direction === 1 ? 'asc' : 'desc');
            
            // Réorganiser les lignes
            rows.forEach(row => tbody.appendChild(row));
        });
    });
}
```

## Considérations de design

### 1. Responsive design

L'interface s'adapte à différentes tailles d'écran grâce à des media queries :

```css
@media (max-width: 768px) {
    .metrics-container {
        flex-direction: column;
    }
    
    .gauge-container {
        width: 180px;
        height: 100px;
    }
    
    .visualizations {
        flex-direction: column;
    }
}
```

### 2. Accessibilité

L'interface respecte les bonnes pratiques d'accessibilité :

- Contraste des couleurs suffisant
- Structure HTML sémantique
- Textes alternatifs pour les éléments visuels
- Navigation au clavier possible

### 3. Performance

Pour optimiser les performances du frontend :

- Chargement asynchrone des scripts
- Utilisation de requestAnimationFrame pour les animations
- Optimisation des sélecteurs CSS
- Minimisation des reflows et repaints
