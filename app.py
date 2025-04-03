from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
import uvicorn
import os
import json
import numpy as np
from typing import Dict, List, Optional
import logging
import time
import argparse
from datetime import datetime
import traceback

from crawler import WebCrawler
from analyzer import SiteAnalyzer

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Custom JSON encoder to handle NumPy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

# Get command line arguments
def get_args():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--max-pages', type=int, default=10000)
        args, _ = parser.parse_known_args()
        return args
    except:
        # Return default values if parsing fails
        class Args:
            max_pages = 10000
        return Args()

app = FastAPI(title="SiteRadius API", description="API pour analyser la cohésion sémantique d'un site web")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create results directory if it doesn't exist
os.makedirs("results", exist_ok=True)

# Create static directory for frontend
os.makedirs("static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Store ongoing tasks
tasks_status = {}

class AnalysisRequest(BaseModel):
    url: HttpUrl
    max_pages: Optional[int] = None
    same_domain_only: bool = True

class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: Optional[float] = None
    message: Optional[str] = None

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.post("/analyze", response_model=dict)
async def analyze_site(request: AnalysisRequest, background_tasks: BackgroundTasks, args: argparse.Namespace = Depends(get_args)):
    """Start a site analysis task."""
    # Use request max_pages if provided, otherwise use command line arg
    max_pages = request.max_pages or args.max_pages
    
    task_id = str(hash(f"{request.url}_{max_pages}"))
    
    # Check if task is already running
    if task_id in tasks_status and tasks_status[task_id]["status"] == "running":
        return {"task_id": task_id, "status": "running"}
    
    # Initialize task status
    tasks_status[task_id] = {
        "status": "running",
        "progress": 0,
        "message": "Starting analysis..."
    }
    
    # Start background task
    background_tasks.add_task(
        run_analysis,
        task_id=task_id,
        url=str(request.url),
        max_pages=max_pages,
        same_domain_only=request.same_domain_only
    )
    
    return {"task_id": task_id, "status": "running"}

@app.get("/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Get the status of a running task."""
    if task_id not in tasks_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task_id,
        **tasks_status[task_id]
    }

@app.get("/results/{task_id}")
async def get_results(task_id: str):
    """Get the results of a completed task."""
    result_file = os.path.join("results", f"results_{task_id}.json")
    
    if not os.path.exists(result_file):
        raise HTTPException(status_code=404, detail="Results not found")
    
    with open(result_file, "r") as f:
        results = json.load(f)
    
    return results

async def run_analysis(task_id, url, max_pages=200, same_domain_only=True):
    """Run the full analysis process."""
    try:
        # Update task status
        tasks_status[task_id] = {
            'status': 'running',
            'progress': 0.1,
            'message': 'Initialisation du crawler...'
        }
        
        # Create crawler instance
        crawler = WebCrawler(
            max_pages=max_pages, 
            same_domain_only=same_domain_only, 
            delay=0.05,  # Reduced delay for faster crawling
            max_workers=20  # Increased workers for more parallelism
        )
        
        # Update task status
        tasks_status[task_id]['progress'] = 0.2
        tasks_status[task_id]['message'] = 'Crawling du site web...'
        
        # Crawl the website - crawl_parallel n'est pas une coroutine async, donc pas de await
        pages_content = crawler.crawl_parallel(url)
        
        # Update task status
        tasks_status[task_id]['progress'] = 0.6
        tasks_status[task_id]['message'] = 'Création des embeddings...'
        
        # Create analyzer instance
        analyzer = SiteAnalyzer()
        
        # Run analysis
        results = analyzer.analyze_site(pages_content)
        
        # Update task status
        tasks_status[task_id]['progress'] = 0.9
        tasks_status[task_id]['message'] = 'Finalisation des résultats...'
        
        # Add metadata to results
        results['metadata'] = {
            'url': url,
            'pages_crawled': len(pages_content),
            'timestamp': datetime.now().isoformat(),
            'max_pages': max_pages
        }
        
        # Save results using the custom NumPy encoder
        result_file = os.path.join("results", f"results_{task_id}.json")
        with open(result_file, "w") as f:
            json.dump(results, f, cls=NumpyEncoder)
        
        # Update task status
        tasks_status[task_id] = {
            'status': 'completed',
            'progress': 1.0,
            'message': 'Analyse terminée'
        }
        
        return results
        
    except Exception as e:
        # Update task status on error
        tasks_status[task_id] = {
            'status': 'failed',
            'progress': 0,
            'message': str(e)
        }
        logging.error(f"Error in analysis: {str(e)}")
        traceback.print_exc()
        raise

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
