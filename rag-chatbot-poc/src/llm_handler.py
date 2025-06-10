import requests
import logging
from typing import Dict, Optional

class SimpleLLMHandler:
    """Gestionnaire LLM simplifié qui fonctionne sans Ollama, basé sur des templates."""
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def generate_response(self, context: str, query: str) -> str:
        self.logger.info("Génération de réponse avec le SimpleLLMHandler (mode template).")
        if not context or len(context.strip()) < 10:
            return (
                "Je n'ai pas trouvé d'informations pertinentes dans les documents "
                "pour répondre à votre question. Pourriez-vous reformuler ou "
                "vérifier que les documents appropriés ont été téléchargés ?"
            )
        
        response = f"""Basé sur les documents disponibles, voici un extrait pertinent :

"{context[:800]}..."

Cette information provient des documents que vous avez fournis. Si vous souhaitez plus de détails, n'hésitez pas à poser une question plus précise."""
        return response

    def get_current_model(self) -> str:
        return "Template Simple"

class EnhancedOllamaLLMHandler:
    """Gestionnaire LLM amélioré qui interagit avec Ollama."""
    def __init__(self, config: Dict):
        self.config = config['llm']
        self.base_url = self.config['ollama_url']
        self.current_model = self.config['default_model']
        self.logger = logging.getLogger(__name__)

    def is_available(self) -> bool:
        """Vérifie si le service Ollama est accessible."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def get_current_model(self) -> str:
        return self.current_model

    def set_model(self, model_name: str):
        self.logger.info(f"Changement du modèle LLM actif pour : {model_name}")
        self.current_model = model_name

    def generate_response(self, context: str, query: str) -> str:
        self.logger.info(f"Génération de réponse avec Ollama et le modèle : {self.current_model}")
        
        prompt = self._build_prompt(context, query)
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.current_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.config['temperature'],
                        "num_predict": self.config['max_tokens'],
                    }
                },
                timeout=60
            )
            response.raise_for_status() # Lève une exception pour les codes d'erreur HTTP
            
            result = response.json()
            return result.get("response", "").strip()
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération avec Ollama ({self.current_model}): {e}")
            return "Désolé, une erreur est survenue lors de la communication avec le modèle de langage. Le système va utiliser une réponse simple."

    def _build_prompt(self, context: str, query: str) -> str:
        """Construit un prompt optimisé pour un RAG."""
        return f"""[INST] Tu es un assistant intelligent spécialisé dans l'analyse de documents. Ta tâche est de répondre à la question de l'utilisateur en te basant EXCLUSIVEMENT sur le contexte fourni. Ne fais aucune supposition et n'utilise pas de connaissances externes. Si l'information n'est pas dans le contexte, dis-le clairement.

Contexte des documents :
---
{context}
---

Question de l'utilisateur : "{query}"

Ta réponse doit être précise, concise et directement issue du contexte. [/INST]
"""

def get_llm_handler(config: Dict):
    """Factory pour obtenir le bon gestionnaire LLM."""
    logger = logging.getLogger(__name__)
    ollama_handler = EnhancedOllamaLLMHandler(config)
    if ollama_handler.is_available():
        logger.info(f"✅ Le service Ollama est disponible. Utilisation du modèle : {ollama_handler.get_current_model()}")
        return ollama_handler
    else:
        logger.warning("⚠️ Le service Ollama n'est pas disponible. Passage en mode de réponse simplifié.")
        return SimpleLLMHandler(config)