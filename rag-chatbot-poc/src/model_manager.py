import requests
import logging
from typing import Dict, List
from pathlib import Path
import yaml

class OllamaModelManager:
    """Gestionnaire pour les modèles Ollama."""
    def __init__(self, config: Dict):
        self.config = config
        self.base_url = config.get('llm', {}).get('ollama', {}).get('url')
        self.logger = logging.getLogger(__name__)

    def is_ollama_available(self) -> bool:
        if not self.base_url:
            return False
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def get_installed_models(self) -> List[Dict]:
        if not self.is_ollama_available():
            return []
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [{'name': m['name'].split(':')[0], 'full_name': m['name']} for m in data.get('models', [])]
        except Exception as e:
            self.logger.error(f"Erreur de récupération des modèles installés: {e}")
            return []

    def get_available_models(self) -> List[Dict]:
        if not self.is_ollama_available():
            return []
        # Utilise .get() pour un accès sûr
        available_models = self.config.get('llm', {}).get('available_models', []).copy()
        installed_names = [model['name'] for model in self.get_installed_models()]
        for model in available_models:
            model['installed'] = model['name'] in installed_names
        return available_models
    
    def set_active_model(self, model_name: str) -> bool:
        try:
            # Cette fonction modifie directement le fichier config.yaml
            config_path = Path('config/config.yaml')
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # S'assure que la section ollama existe avant de la modifier
            if 'ollama' in config_data.get('llm', {}):
                config_data['llm']['ollama']['model'] = model_name
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
                self.logger.info(f"Modèle actif changé pour : {model_name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Erreur lors du changement de modèle actif : {e}")
            return False