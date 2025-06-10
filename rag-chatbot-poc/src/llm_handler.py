import requests
import logging
from typing import Dict
import os
import google.generativeai as genai

# --- GESTIONNAIRE SIMPLE (FALLBACK) ---
class SimpleLLMHandler:
    def __init__(self, config: Dict):
        self.logger = logging.getLogger(__name__)
    def get_current_model(self) -> str:
        return "Template Simple"
    def generate_response(self, context: str, query: str) -> str:
        self.logger.info("Génération de réponse avec le SimpleLLMHandler (mode template).")
        if not context or len(context.strip()) < 10:
            return "Je n'ai pas trouvé d'informations pertinentes dans les documents."
        return f"""Basé sur les documents, voici un extrait : "{context[:800]}..." """

# --- GESTIONNAIRE POUR GEMINI ---
class GeminiAPIHandler:
    def __init__(self, config: Dict):
        self.logger = logging.getLogger(__name__)
        self.config = config['llm']['gemini']
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Clé API Gemini non trouvée. Définissez la variable d'environnement GEMINI_API_KEY.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.config['model'])
        self.logger.info(f"Gestionnaire Gemini initialisé avec le modèle : {self.config['model']}")
    def get_current_model(self) -> str:
        return self.config['model']
    def generate_response(self, context: str, query: str) -> str:
        prompt = f"""Instructions : Tu es un assistant intelligent. Réponds à la question en te basant uniquement sur le contexte fourni. Si l'information n'est pas dans le contexte, dis-le clairement.

Contexte :
---
{context}
---

Question : "{query}"
"""
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            self.logger.error(f"Erreur avec l'API Gemini: {e}")
            return "Désolé, une erreur est survenue avec l'API Gemini."
    def set_model(self, model_name: str): pass

# --- GESTIONNAIRE POUR OLLAMA ---
class EnhancedOllamaLLMHandler:
    def __init__(self, config: Dict):
        self.logger = logging.getLogger(__name__)
        ollama_cfg = config['llm']['ollama']
        self.base_url = ollama_cfg['url']
        self.current_model = ollama_cfg['model']
        self.temperature = ollama_cfg['temperature']
        self.max_tokens = ollama_cfg['max_tokens']
    def get_current_model(self) -> str:
        return self.current_model
    def set_model(self, model_name: str):
        self.current_model = model_name
    def is_available(self) -> bool:
        try:
            requests.get(f"{self.base_url}/api/tags", timeout=3)
            return True
        except requests.RequestException:
            return False
    def generate_response(self, context: str, query: str) -> str:
        prompt = f"""[INST] Tu es un assistant intelligent. Réponds à la question en te basant EXCLUSIVEMENT sur le contexte fourni. Si l'information n'est pas dans le contexte, dis-le clairement.

Contexte :
---
{context}
---

Question : "{query}" [/INST]
"""
        try:
            response = requests.post(f"{self.base_url}/api/generate", json={"model": self.current_model, "prompt": prompt, "stream": False, "options": {"temperature": self.temperature, "num_predict": self.max_tokens}}, timeout=180)
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except requests.exceptions.ReadTimeout:
            return "Désolé, la génération a pris trop de temps (timeout)."
        except Exception as e:
            return f"Désolé, erreur de communication avec Ollama: {e}"

# --- LA FACTORY (L'USINE QUI CHOISIT) ---
def get_llm_handler(config: Dict):
    logger = logging.getLogger(__name__)
    provider = config.get('llm', {}).get('provider', 'simple').lower()

    if provider == 'gemini':
        logger.info("Choix du fournisseur LLM : Gemini")
        try:
            return GeminiAPIHandler(config)
        except Exception as e:
            logger.error(f"Échec de l'initialisation de Gemini: {e}")
            logger.warning("Passage au mode de réponse simplifié.")
            return SimpleLLMHandler(config)

    elif provider == 'ollama':
        logger.info("Choix du fournisseur LLM : Ollama")
        try:
            ollama_handler = EnhancedOllamaLLMHandler(config)
            if ollama_handler.is_available():
                logger.info(f"Service Ollama disponible. Modèle utilisé : {ollama_handler.get_current_model()}")
                return ollama_handler
            else:
                logger.warning("Service Ollama non disponible.")
                raise ConnectionError("Ollama non disponible")
        except Exception as e:
            logger.error(f"Échec de l'initialisation d'Ollama: {e}")
            logger.warning("Passage au mode de réponse simplifié.")
            return SimpleLLMHandler(config)
            
    else:
        logger.info("Fournisseur non reconnu. Passage au mode de réponse simplifié.")
        return SimpleLLMHandler(config)