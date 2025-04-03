document.addEventListener('DOMContentLoaded', () => {
    // DOM elements
    const analysisForm = document.getElementById('analysis-form');
    const inputSection = document.querySelector('.input-section');
    const loadingSection = document.getElementById('loading-section');
    const resultsSection = document.getElementById('results-section');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const statusMessage = document.getElementById('status-message');
    const newAnalysisBtn = document.getElementById('new-analysis-btn');
    const siteUrl = document.getElementById('site-url');
    const pagesInfo = document.getElementById('pages-info');
    const focusGauge = document.getElementById('focus-gauge');
    const focusValue = document.getElementById('focus-value');
    const radiusGauge = document.getElementById('radius-gauge');
    const radiusValue = document.getElementById('radius-value');
    const pageMetricsBody = document.getElementById('page-metrics-body');
    
    // Composition info elements
    const compositionInfoBtn = document.getElementById('composition-info-btn');
    const compositionInfoText = document.getElementById('composition-info-text');
    
    // Chart variables
    let similarityDistributionChart = null;

    // Current task state
    let currentTaskId = null;
    let pollingInterval = null;

    // Form submission
    analysisForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const url = document.getElementById('url').value;
        const maxPages = document.getElementById('max-pages').value;
        const sameDomain = document.getElementById('same-domain').checked;
        
        // Show loading section
        inputSection.classList.add('hidden');
        loadingSection.classList.remove('hidden');
        resultsSection.classList.add('hidden');
        
        // Reset progress
        updateProgress(0, 'Initialisation de l\'analyse...');
        
        try {
            // Start analysis
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    url: url,
                    max_pages: parseInt(maxPages),
                    same_domain_only: sameDomain
                })
            });
            
            const data = await response.json();
            
            if (data.task_id) {
                currentTaskId = data.task_id;
                // Start polling for task status
                startPolling(currentTaskId);
            } else {
                throw new Error('No task ID received');
            }
        } catch (error) {
            console.error('Error starting analysis:', error);
            updateProgress(0, `Erreur: ${error.message}`);
            setTimeout(() => {
                loadingSection.classList.add('hidden');
                inputSection.classList.remove('hidden');
            }, 3000);
        }
    });
    
    // New analysis button
    newAnalysisBtn.addEventListener('click', () => {
        resultsSection.classList.add('hidden');
        inputSection.classList.remove('hidden');
    });
    
    // Composition info button
    if (compositionInfoBtn) {
        compositionInfoBtn.addEventListener('click', () => {
            compositionInfoText.classList.toggle('hidden');
        });
    }
    
    // Start polling for task status
    function startPolling(taskId) {
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }
        
        pollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/task/${taskId}`);
                const data = await response.json();
                
                if (data.status === 'running') {
                    const progress = data.progress || 0;
                    updateProgress(progress * 100, data.message || 'Analyse en cours...');
                } else if (data.status === 'completed') {
                    updateProgress(100, 'Analyse terminée!');
                    clearInterval(pollingInterval);
                    setTimeout(() => {
                        fetchResults(taskId);
                    }, 1000);
                } else if (data.status === 'failed') {
                    updateProgress(0, `Erreur: ${data.message || 'Une erreur est survenue'}`);
                    clearInterval(pollingInterval);
                    setTimeout(() => {
                        loadingSection.classList.add('hidden');
                        inputSection.classList.remove('hidden');
                    }, 3000);
                }
            } catch (error) {
                console.error('Error polling task status:', error);
            }
        }, 1000);
    }
    
    // Update progress bar and message
    function updateProgress(percent, message) {
        progressFill.style.width = `${percent}%`;
        progressText.textContent = `${Math.round(percent)}%`;
        statusMessage.textContent = message;
    }
    
    // Fetch and display results
    async function fetchResults(taskId) {
        try {
            const response = await fetch(`/results/${taskId}`);
            const data = await response.json();
            
            // Display results
            displayResults(data);
            
            // Show results section
            loadingSection.classList.add('hidden');
            resultsSection.classList.remove('hidden');
        } catch (error) {
            console.error('Error fetching results:', error);
            updateProgress(0, `Erreur: ${error.message}`);
            setTimeout(() => {
                loadingSection.classList.add('hidden');
                inputSection.classList.remove('hidden');
            }, 3000);
        }
    }
    
    // Display results in the UI
    function displayResults(data) {
        // Update site info
        const url = data.metadata?.url || 'Unknown site';
        const pagesCrawled = data.metadata?.pages_crawled || 0;
        
        siteUrl.textContent = url;
        pagesInfo.textContent = `${pagesCrawled} pages analysées`;
        
        // Update focus score gauge
        const focusScore = data.site_focus_score || 0;
        const focusFill = document.getElementById('focus-fill');
        focusValue.textContent = focusScore.toFixed(3);
        updateGauge(focusFill, focusScore);
        
        // Update radius gauge
        const radius = data.site_radius || 0;
        const radiusFill = document.getElementById('radius-fill');
        radiusValue.textContent = radius.toFixed(3);
        updateGauge(radiusFill, radius);
        
        // Update content composition section if available
        if (data.content_composition) {
            updateContentComposition(data.content_composition);
        }
        
        // Update similarity distribution chart if available
        if (data.similarity_distribution) {
            updateSimilarityDistribution(data.similarity_distribution);
        }
        
        // Update content clusters visualization if available
        if (data.content_clusters) {
            updateContentClusters(data.content_clusters, focusScore);
        }
        
        // Update page metrics table
        pageMetricsBody.innerHTML = '';
        
        if (data.page_metrics) {
            // Sort pages by similarity (descending)
            const sortedPages = Object.entries(data.page_metrics)
                .sort((a, b) => b[1].similarity - a[1].similarity);
            
            sortedPages.forEach(([url, metrics]) => {
                const row = document.createElement('tr');
                
                const urlCell = document.createElement('td');
                urlCell.textContent = formatUrl(url);
                urlCell.title = url;
                
                const similarityCell = document.createElement('td');
                similarityCell.textContent = metrics.similarity.toFixed(3);
                
                const distanceCell = document.createElement('td');
                distanceCell.textContent = metrics.distance.toFixed(3);
                
                row.appendChild(urlCell);
                row.appendChild(similarityCell);
                row.appendChild(distanceCell);
                
                pageMetricsBody.appendChild(row);
            });
        }
    }
    
    // Update content composition section
    function updateContentComposition(compositionData) {
        const coreCount = document.getElementById('core-count');
        const corePercent = document.getElementById('core-percent');
        const supportingCount = document.getElementById('supporting-count');
        const supportingPercent = document.getElementById('supporting-percent');
        const peripheralCount = document.getElementById('peripheral-count');
        const peripheralPercent = document.getElementById('peripheral-percent');
        
        if (coreCount && compositionData.counts) {
            coreCount.textContent = `${compositionData.counts.core} pages`;
            supportingCount.textContent = `${compositionData.counts.supporting} pages`;
            peripheralCount.textContent = `${compositionData.counts.peripheral} pages`;
        }
        
        if (corePercent && compositionData.percentages) {
            corePercent.textContent = `${compositionData.percentages.core_percent}% du site`;
            supportingPercent.textContent = `${compositionData.percentages.supporting_percent}% du site`;
            peripheralPercent.textContent = `${compositionData.percentages.peripheral_percent}% du site`;
        }
    }
    
    // Update similarity distribution chart
    function updateSimilarityDistribution(distributionData) {
        const ctx = document.getElementById('similarity-distribution-chart');
        
        if (!ctx) return;
        
        // Destroy previous chart if exists
        if (similarityDistributionChart) {
            similarityDistributionChart.destroy();
        }
        
        // Prepare data for chart
        const labels = Object.keys(distributionData);
        const data = Object.values(distributionData);
        
        // Create chart
        similarityDistributionChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Nombre de pages',
                    data: data,
                    backgroundColor: '#4a6fa5',
                    borderColor: '#3a5a8c',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Nombre de Pages'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Similarité au Centre du Site'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Distribution de la Similarité du Contenu'
                    }
                }
            }
        });
    }
    
    // Create content clusters visualization
    function updateContentClusters(clustersData, focusScore) {
        const ctx = document.getElementById('content-clusters-chart');
        
        if (!ctx) return;
        
        // Destroy previous chart if exists
        if (window.contentClustersChart) {
            window.contentClustersChart.destroy();
        }
        
        // Prepare data for scatter plot
        const datasets = [
            {
                label: 'Contenu Central',
                data: [],
                backgroundColor: '#28a745',
                pointRadius: 6,
                pointHoverRadius: 8
            },
            {
                label: 'Contenu de Support',
                data: [],
                backgroundColor: '#ffa500',
                pointRadius: 6,
                pointHoverRadius: 8
            },
            {
                label: 'Contenu Périphérique',
                data: [],
                backgroundColor: '#dc3545',
                pointRadius: 6,
                pointHoverRadius: 8
            }
        ];
        
        // Organize data by category
        clustersData.forEach(point => {
            const dataPoint = {
                x: point.x,
                y: point.y,
                url: point.url
            };
            
            if (point.category === 'core') {
                datasets[0].data.push(dataPoint);
            } else if (point.category === 'supporting') {
                datasets[1].data.push(dataPoint);
            } else {
                datasets[2].data.push(dataPoint);
            }
        });
        
        // Create chart
        window.contentClustersChart = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        min: 0,
                        max: 1,
                        title: {
                            display: true,
                            text: 'Alignement Topique (Plus élevé = Plus Aligné avec le Thème du Site)'
                        },
                        grid: {
                            color: 'rgba(200, 200, 200, 0.2)'
                        }
                    },
                    y: {
                        min: 0,
                        max: 1,
                        title: {
                            display: true,
                            text: 'Densité d\'Information (Approximative)'
                        },
                        grid: {
                            color: 'rgba(200, 200, 200, 0.2)'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: `Clusters de Contenu (Score Focus: ${focusScore.toFixed(2)})`,
                        font: {
                            size: 16
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const point = context.raw;
                                const url = formatUrl(point.url);
                                return [
                                    `URL: ${url}`,
                                    `Alignement: ${point.x.toFixed(2)}`,
                                    `Densité: ${point.y.toFixed(2)}`
                                ];
                            }
                        }
                    },
                    annotation: {
                        annotations: {
                            line1: {
                                type: 'line',
                                xMin: 0.8,
                                xMax: 0.8,
                                borderColor: 'rgba(150, 150, 150, 0.5)',
                                borderWidth: 1,
                                borderDash: [6, 6],
                                label: {
                                    display: false
                                }
                            },
                            line2: {
                                type: 'line',
                                xMin: 0.6,
                                xMax: 0.6,
                                borderColor: 'rgba(150, 150, 150, 0.5)',
                                borderWidth: 1,
                                borderDash: [6, 6],
                                label: {
                                    display: false
                                }
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Update gauge visualization
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
    
    // Format URL for display
    function formatUrl(url) {
        try {
            const urlObj = new URL(url);
            let path = urlObj.pathname;
            
            // Truncate path if too long
            if (path.length > 30) {
                path = path.substring(0, 27) + '...';
            }
            
            return path === '/' ? urlObj.hostname : `${urlObj.hostname}${path}`;
        } catch (e) {
            return url;
        }
    }
});
