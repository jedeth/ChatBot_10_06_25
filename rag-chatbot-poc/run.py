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
            logging.FileHandler(log_dir / 'chatbot.log'),
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

def check_dependencies():
    """Vérification des dépendances critiques"""
    try:
        import fastapi
        import chromadb
        import sentence_transformers
        import PyPDF2
        import sqlalchemy
        return True
    except ImportError as e:
        logging.error(f"Dépendance manquante: {e}")
        print(f"❌ Erreur: Dépendance manquante - {e}")
        print("Veuillez exécuter le script d'installation : ./scripts/install.sh")
        return False

def create_directories():
    """Création des répertoires nécessaires à partir de la config"""
    config = load_config()
    directories = [
        config['storage']['documents_path'],
        config['storage']['processed_path'],
        Path(config['database']['path']).parent,
        Path(config['database']['vector_db']['path']).parent,
        'logs'
    ]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logging.info(f"Répertoire créé/vérifié: {directory}")

def check_ollama_status():
    """Vérification du statut d'Ollama au démarrage"""
    logger = logging.getLogger(__name__)
    try:
        import requests
        config = load_config()
        ollama_url = config['llm']['ollama_url']
        response = requests.get(f"{ollama_url}/api/tags", timeout=3)
        if response.status_code == 200:
            logger.info("✅ Ollama détecté et opérationnel")
            models = response.json().get('models', [])
            if models:
                logger.info(f"📋 {len(models)} modèle(s) installé(s): {', '.join([m['name'].split(':')[0] for m in models])}")
            else:
                logger.warning("⚠️ Aucun modèle installé dans Ollama. Utilisez l'interface admin pour en télécharger.")
        else:
            logger.warning("⚠️ Ollama répond mais avec un statut inattendu.")
    except requests.exceptions.RequestException:
        logger.warning("⚠️ Ollama non disponible - Le chatbot fonctionnera en mode simplifié.")
        logger.info("💡 Pour installer Ollama, suivez les instructions sur ollama.ai")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification d'Ollama: {e}")

def main():
    """Fonction principale"""
    print("🚀 RAG Document Chatbot POC - Démarrage")
    print("=" * 50)
    
    # Configuration du logging
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Vérification des dépendances
        if not check_dependencies():
            sys.exit(1)

        # Chargement de la configuration
        config = load_config()
        logger.info("Configuration chargée avec succès")

        # Création des répertoires
        create_directories()

        # Vérification d'Ollama
        check_ollama_status()
        
        # Import et démarrage de l'application web
        from src.web_app import app, run_app
        logger.info(f"Démarrage du serveur sur {config['app']['host']}:{config['app']['port']}")
        print(f"🌐 Serveur démarré: http://{config['app']['host']}:{config['app']['port']}")
        print(f"📚 Interface de chat: http://{config['app']['host']}:{config['app']['port']}/")
        print(f"📤 Interface d'upload: http://{config['app']['host']}:{config['app']['port']}/upload")
        print(f"⚙️ Panel admin: http://{config['app']['host']}:{config['app']['port']}/admin")
        print("\n💡 Conseil: Uploadez d'abord quelques documents pour tester le chat.")
        print("\n🛑 Pour arrêter: Ctrl+C")
        
        # Démarrage du serveur
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