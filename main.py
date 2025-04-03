#!/usr/bin/env python3
"""
SiteRadius - Outil d'analyse de cohésion sémantique pour sites web

Ce script permet de lancer l'application SiteRadius qui analyse la cohésion sémantique
d'un site web en calculant le Site Focus Score et le Site Radius.
"""

import os
import argparse
import logging
import sys

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_directories():
    """Crée les répertoires nécessaires s'ils n'existent pas."""
    os.makedirs("static", exist_ok=True)
    os.makedirs("results", exist_ok=True)

def parse_arguments():
    """Parse les arguments de ligne de commande."""
    parser = argparse.ArgumentParser(description="SiteRadius - Outil d'analyse de cohésion sémantique pour sites web")
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Adresse IP du serveur')
    parser.add_argument('--port', type=int, default=8000, help='Port du serveur')
    parser.add_argument('--reload', action='store_true', help='Activer le rechargement automatique')
    parser.add_argument('--max-pages', type=int, default=100, help='Nombre maximum de pages à crawler (défaut: 100)')
    return parser.parse_args()

def check_dependencies():
    """Vérifie que les dépendances nécessaires sont installées."""
    try:
        import uvicorn
        from fastapi import FastAPI
        import numpy as np
        from bs4 import BeautifulSoup
        import requests
        
        # Vérification optionnelle de sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            logging.info("Toutes les dépendances sont correctement installées.")
            return True
        except ImportError:
            logging.warning("sentence-transformers n'est pas installé. L'analyse sémantique ne fonctionnera pas.")
            return False
            
    except ImportError as e:
        logging.error(f"Dépendance manquante: {e}")
        logging.error("Veuillez installer les dépendances requises avec: pip install -r requirements.txt")
        return False

def main():
    """Fonction principale pour lancer l'application."""
    # Création des répertoires nécessaires
    create_directories()
    
    # Vérification des dépendances
    if not check_dependencies():
        logging.error("Certaines dépendances sont manquantes. L'application peut ne pas fonctionner correctement.")
        choice = input("Voulez-vous continuer quand même? (o/n): ")
        if choice.lower() != 'o':
            sys.exit(1)
    
    # Parsing des arguments
    args = parse_arguments()
    
    try:
        import uvicorn
        # Affichage du message de démarrage
        logging.info(f"Démarrage de SiteRadius sur http://{args.host}:{args.port}")
        logging.info("Appuyez sur CTRL+C pour arrêter le serveur")
        
        # Lancement du serveur
        uvicorn.run(
            "app:app",
            host=args.host,
            port=args.port,
            reload=args.reload
        )
    except Exception as e:
        logging.error(f"Erreur lors du démarrage du serveur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
