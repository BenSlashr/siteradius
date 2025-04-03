from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import logging
from tqdm import tqdm
import gc  # Pour la gestion de la mémoire

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SiteAnalyzer:
    def __init__(self, model_name="all-MiniLM-L6-v2", batch_size=32):
        """Initialize the analyzer with a sentence transformer model."""
        try:
            self.model = SentenceTransformer(model_name)
        except Exception as e:
            logging.warning(f"Error loading model {model_name}: {e}")
            logging.info("Trying with a different model...")
            self.model = SentenceTransformer('paraphrase-MiniLM-L3-v2')
        
        self.embeddings = {}
        self.central_embedding = None
        self.site_focus_score = None
        self.site_radius = None
        self.batch_size = batch_size
        
    def _chunk_text(self, text, chunk_size=512, overlap=100):
        """Split text into chunks of approximately chunk_size characters with overlap."""
        if len(text) <= chunk_size:
            return [text]
            
        chunks = []
        start = 0
        while start < len(text):
            # Find a good breaking point (space) near the chunk_size
            end = min(start + chunk_size, len(text))
            if end < len(text):
                # Try to find the last space within the chunk
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            chunks.append(text[start:end].strip())
            start = end - overlap if end - overlap > start else end
            
        return chunks
    
    def create_embeddings(self, pages_content):
        """Create embeddings for all pages content."""
        logging.info("Creating embeddings for all pages...")
        
        all_chunks = []
        url_to_chunks = {}
        
        # Process each page into chunks
        for url, content in tqdm(pages_content.items(), desc="Chunking text"):
            chunks = self._chunk_text(content)
            url_to_chunks[url] = (len(all_chunks), len(chunks))  # Store (start_idx, count)
            all_chunks.extend(chunks)
        
        # Create embeddings for all chunks in batches to manage memory
        logging.info(f"Creating embeddings for {len(all_chunks)} text chunks...")
        
        # Utiliser des batches pour gérer la mémoire avec de grands sites
        all_embeddings = []
        for i in tqdm(range(0, len(all_chunks), self.batch_size), desc="Batches"):
            batch = all_chunks[i:i + self.batch_size]
            batch_embeddings = self.model.encode(batch, show_progress_bar=False)
            all_embeddings.append(batch_embeddings)
            
            # Libérer la mémoire après chaque batch
            if i % (self.batch_size * 10) == 0:
                gc.collect()
        
        # Concaténer tous les embeddings
        all_embeddings = np.vstack(all_embeddings)
        
        # Organiser les embeddings par URL
        for url, (start_idx, count) in url_to_chunks.items():
            page_embeddings = all_embeddings[start_idx:start_idx + count]
            # Utiliser la moyenne des embeddings pour représenter la page entière
            self.embeddings[url] = np.mean(page_embeddings, axis=0)
        
        # Libérer la mémoire
        del all_embeddings
        gc.collect()
        
        logging.info(f"Created embeddings for {len(self.embeddings)} pages.")
        return self.embeddings
    
    def calculate_central_embedding(self):
        """Calculate the central embedding (semantic center) of the site."""
        if not self.embeddings:
            raise ValueError("No embeddings available. Run create_embeddings first.")
            
        # Use the mean of all page embeddings as the central embedding
        all_embeddings = np.array(list(self.embeddings.values()))
        self.central_embedding = np.mean(all_embeddings, axis=0)
        return self.central_embedding
    
    def calculate_site_focus_score(self):
        """Calculate the site focus score based on cosine similarity to central embedding."""
        if self.central_embedding is None:
            self.calculate_central_embedding()
            
        similarities = []
        for url, embedding in self.embeddings.items():
            similarity = cosine_similarity([embedding], [self.central_embedding])[0][0]
            similarities.append(similarity)
            
        # Site focus score is the average similarity to the central embedding
        self.site_focus_score = np.mean(similarities)
        return self.site_focus_score
    
    def calculate_site_radius(self):
        """Calculate the site radius (average distance from central embedding)."""
        if self.central_embedding is None:
            self.calculate_central_embedding()
            
        distances = []
        for url, embedding in self.embeddings.items():
            # Convert similarity to distance (1 - similarity)
            distance = 1 - cosine_similarity([embedding], [self.central_embedding])[0][0]
            distances.append(distance)
            
        # Site radius is the average distance from the central embedding
        self.site_radius = np.mean(distances)
        return self.site_radius
    
    def analyze_site(self, pages_content):
        """Run full analysis on the site content."""
        self.create_embeddings(pages_content)
        self.calculate_central_embedding()
        focus_score = self.calculate_site_focus_score()
        radius = self.calculate_site_radius()
        
        # Get page-level metrics for detailed analysis
        page_metrics = {}
        
        # Pour calculer la distribution de similarité
        similarity_distribution = {
            "0.0-0.1": 0, "0.1-0.2": 0, "0.2-0.3": 0, "0.3-0.4": 0, "0.4-0.5": 0,
            "0.5-0.6": 0, "0.6-0.7": 0, "0.7-0.8": 0, "0.8-0.9": 0, "0.9-1.0": 0
        }
        
        # Pour calculer la composition du contenu
        content_composition = {
            "core": 0,      # Pages très similaires au centre (>0.8)
            "supporting": 0, # Pages moyennement similaires (0.6-0.8)
            "peripheral": 0  # Pages peu similaires (<0.6)
        }
        
        # Pour la visualisation des clusters
        content_clusters = []
        
        # Traiter les pages par lots pour économiser la mémoire
        urls = list(self.embeddings.keys())
        for i in range(0, len(urls), 100):
            batch_urls = urls[i:i+100]
            for url in batch_urls:
                embedding = self.embeddings[url]
                similarity = cosine_similarity([embedding], [self.central_embedding])[0][0]
                distance = 1 - similarity
                
                # Calculer une métrique d'information density (approximation)
                # Basée sur la norme du vecteur d'embedding
                information_density = np.linalg.norm(embedding) / 10  # Normalisé pour l'affichage
                information_density = min(max(information_density, 0), 1)  # Limiter entre 0 et 1
                
                page_metrics[url] = {
                    "similarity": similarity,
                    "distance": distance,
                    "information_density": information_density
                }
                
                # Ajouter les données pour la visualisation des clusters
                category = "core" if similarity >= 0.8 else "supporting" if similarity >= 0.6 else "peripheral"
                content_clusters.append({
                    "url": url,
                    "x": similarity,  # Alignement topique (plus élevé = plus aligné)
                    "y": information_density,  # Densité d'information
                    "category": category
                })
                
                # Mettre à jour la distribution de similarité
                bucket = min(int(similarity * 10), 9)
                bucket_key = f"{bucket/10:.1f}-{(bucket+1)/10:.1f}"
                similarity_distribution[bucket_key] += 1
                
                # Mettre à jour la composition du contenu
                if similarity >= 0.8:
                    content_composition["core"] += 1
                elif similarity >= 0.6:
                    content_composition["supporting"] += 1
                else:
                    content_composition["peripheral"] += 1
        
        # Calculer les pourcentages pour la composition du contenu
        total_pages = len(urls)
        content_composition_percentages = {
            "core_percent": round((content_composition["core"] / total_pages) * 100, 1),
            "supporting_percent": round((content_composition["supporting"] / total_pages) * 100, 1),
            "peripheral_percent": round((content_composition["peripheral"] / total_pages) * 100, 1)
        }
        
        results = {
            "site_focus_score": focus_score,
            "site_radius": radius,
            "page_metrics": page_metrics,
            "similarity_distribution": similarity_distribution,
            "content_composition": {
                "counts": content_composition,
                "percentages": content_composition_percentages
            },
            "content_clusters": content_clusters
        }
        
        return results
