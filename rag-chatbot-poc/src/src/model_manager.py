import requests
import json
import logging
import asyncio
import subprocess
from typing import Dict, List, Optional
from pathlib import Path
import yaml

class OllamaModelManager:
    """Gestionnaire pour les modèles Ollama."""
    def __init__(self, config: Dict):
        self.config = config
        self.base_url = config['llm']['ollama_url']
        self.logger = logging.getLogger(__name__)
        self.download_progress = {}

    def is_ollama_available(self) -> bool:
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
            return [
                {
                    'name': model['name'].split(':')[0],
                    'full_name': model['name'],
                    'size': self._format_size(model.get('size', 0)),
                    'modified_at': model.get('modified_at'),
                    'digest': model.get('digest', '')[:12]
                } for model in data.get('models', [])
            ]
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des modèles installés : {e}")
            return []

    def get_available_models(self) -> List[Dict]:
        available_models = self.config['llm'].get('available_models', []).copy()
        installed_names = [model['name'] for model in self.get_installed_models()]
        for model in available_models:
            model['installed'] = model['name'] in installed_names
            model['downloading'] = model['name'] in self.download_progress and self.download_progress[model['name']].get('status') not in ['completed', 'error']
        return available_models

    async def install_model(self, model_name: str) -> Dict:
        if not self.is_ollama_available():
            return {'success': False, 'error': "Ollama n'est pas disponible"}
        try:
            self.download_progress[model_name] = {'status': 'starting', 'progress': 0, 'message': 'Initialisation...'}
            process = await asyncio.create_subprocess_exec(
                'ollama', 'pull', model_name,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            asyncio.create_task(self._monitor_download(model_name, process))
            return {'success': True, 'message': f'Téléchargement de {model_name} démarré.'}
        except Exception as e:
            self.logger.error(f"Erreur au lancement de l'installation de {model_name}: {e}")
            return {'success': False, 'error': str(e)}

    async def _monitor_download(self, model_name: str, process: asyncio.subprocess.Process):
        # Implementation du monitoring de la progression...
        pass # La logique complète est dans le JS pour ce POC pour plus de simplicité

    def remove_model(self, model_name: str) -> Dict:
        if not self.is_ollama_available():
            return {'success': False, 'error': "Ollama n'est pas disponible"}
        try:
            # On cherche le nom complet avec le tag (ex: 'mistral:latest')
            installed_models = self.get_installed_models()
            full_name = next((m['full_name'] for m in installed_models if m['name'] == model_name), model_name)
            
            self.logger.info(f"Tentative de suppression du modèle : {full_name}")
            result = subprocess.run(['ollama', 'rm', full_name], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                self.logger.info(f"Modèle {full_name} supprimé avec succès.")
                return {'success': True, 'message': f'Modèle {full_name} supprimé.'}
            else:
                self.logger.error(f"Erreur lors de la suppression de {full_name}: {result.stderr}")
                return {'success': False, 'error': result.stderr or "Erreur inconnue."}
        except Exception as e:
            self.logger.error(f"Erreur lors de la suppression du modèle {model_name}: {e}")
            return {'success': False, 'error': str(e)}

    def set_active_model(self, model_name: str) -> bool:
        try:
            config_path = Path('config/config.yaml')
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            config_data['llm']['default_model'] = model_name
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            self.config['llm']['default_model'] = model_name
            self.logger.info(f"Modèle actif changé pour : {model_name}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors du changement de modèle actif : {e}")
            return False

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes == 0: return "0B"
        power = 1024
        n = 0
        power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
        while size_bytes >= power and n < len(power_labels):
            size_bytes /= power
            n += 1
        return f"{size_bytes:.1f} {power_labels[n]}B"