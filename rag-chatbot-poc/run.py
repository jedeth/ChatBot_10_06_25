#!/usr/bin/env python3
"""
RAG Document Chatbot POC - Point d'entrée principal
"""
import os
import sys
import logging
import yaml
from pathlib import Path

# Ajout du répertoire src au path Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def setup_logging():
    """Configuration du système de logging"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'chatbot.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Réduction du niveau de logging pour certaines librairies
    logging.getLogger('chromadb').setLevel(logging.WARNING)
    logging.getLogger('sentence_transformers').setLevel(logging.WARNING)
    logging.getLogger('transformers').setLevel(logging.WARNING)

def load_config():
    """Chargement de la configuration"""
    config_path = 'config/config.yaml'
    if Path(config_path).exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    raise FileNotFoundError(f"Le fichier de configuration '{config_path}' est introuvable.")

def create_directories(config: dict):
    """Création des répertoires nécessaires à partir de la config"""
    directories = [
        config['storage']['documents_path'],
        config['storage']['processed_path'],
        Path(config['database']['path']).parent,
        Path(config['database']['vector_db']['path']).parent,
        'logs'
    ]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def check_ollama_status(config: dict):
    """Vérification du statut d'Ollama (uniquement si le provider est ollama)"""
    logger = logging.getLogger(__name__)
    if config.get('llm', {}).get('provider') != 'ollama':
        logger.info("Fournisseur LLM n'est pas Ollama, la vérification du statut est ignorée.")
        return

    logger.info("Vérification du statut d'Ollama...")
    try:
        import requests
        ollama_config = config['llm']['ollama']
        ollama_url = ollama_config['url']
        response = requests.get(f"{ollama_url}/api/tags", timeout=3)
        if response.status_code == 200:
            logger.info("(OK) Ollama détecté et opérationnel")
            models = response.json().get('models', [])
            if models:
                logger.info(f" -> {len(models)} modèle(s) installé(s).")
            else:
                logger.warning("(!) Aucun modèle installé dans Ollama.")
        else:
            logger.warning("(!) Ollama répond mais avec un statut inattendu.")
    except requests.exceptions.RequestException:
        logger.warning("(!) Ollama non disponible.")
    except Exception as e:
        logger.error(f"(X) Erreur lors de la vérification d'Ollama: {e}")

def main():
    """Fonction principale"""
    print("🚀 RAG Document Chatbot POC - Démarrage")
    print("=" * 50)
    
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        config = load_config()
        logger.info("Configuration chargée avec succès")

        create_directories(config)

        check_ollama_status(config)
        
        from src.web_app import app, run_app
        logger.info(f"Démarrage du serveur sur {config['app']['host']}:{config['app']['port']}")
        print(f"🌐 Serveur démarré: http://{config['app']['host']}:{config['app']['port']}")
        
        run_app()

    except KeyboardInterrupt:
        logger.info("Arrêt demandé par l'utilisateur")
        print("\n👋 Arrêt du serveur...")
    except Exception as e:
        logger.error(f"Erreur critique: {e}", exc_info=True)
        print(f"❌ Erreur critique: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()