# RAG Document Chatbot POC

Un chatbot intelligent qui utilise la technologie RAG (Retrieval-Augmented Generation) pour répondre aux questions basées sur vos documents.

## 🚀 Fonctionnalités

-   **Upload de documents**: PDF, Word, Excel, PowerPoint, Texte.
-   **Recherche intelligente**: Utilise des embeddings sémantiques pour trouver les informations les plus pertinentes.
-   **Interface de chat web**: Interface intuitive pour poser des questions et obtenir des réponses.
-   **Panel d'administration**: Pour gérer les documents, voir les statistiques et administrer le système.
-   **Gestion des Modèles LLM**: Interface pour installer, gérer et tester des modèles LLM locaux via Ollama.
-   **Mode dégradé**: Fonctionne en mode simple basé sur des templates si Ollama n'est pas disponible.

## 📋 Prérequis

-   Python 3.8+
-   4GB RAM minimum (8GB+ recommandé, surtout pour les LLMs).
-   2GB d'espace disque libre (plus selon la taille des modèles).
-   (Optionnel mais recommandé) [Ollama](https://ollama.ai/) installé pour la fonctionnalité LLM complète.

## 🛠️ Installation Rapide

1.  **Clonez le projet**:
    ```bash
    git clone <url-du-repo>
    cd rag-chatbot-poc
    ```

2.  **Rendez les scripts exécutables**:
    ```bash
    chmod +x scripts/install.sh
    chmod +x scripts/start.sh
    ```

3.  **Exécutez le script d'installation**:
    Ce script créera un environnement virtuel et installera toutes les dépendances.
    ```bash
    ./scripts/install.sh
    ```

4.  **Démarrez l'application**:
    ```bash
    ./scripts/start.sh
    ```
    (Ou `python run.py` si l'environnement virtuel est déjà activé).

5.  **Ouvrez votre navigateur**: Accédez à [http://localhost:8000](http://localhost:8000).

## 📖 Guide d'utilisation

1.  **Uploadez des documents**: Allez sur la page "Upload" ([http://localhost:8000/upload](http://localhost:8000/upload)) et ajoutez vos fichiers.
2.  **Gérez les modèles (optionnel)**: Allez sur la page "Admin" et cliquez sur "Gestion des Modèles LLM" pour installer et activer un modèle comme `mistral`.
3.  **Discutez avec vos documents**: Retournez sur la page de chat principale et posez des questions sur le contenu des documents que vous avez uploadés.

## ⚙️ Configuration

Le fichier `config/config.yaml` centralise tous les paramètres du projet. Vous pouvez y ajuster les chemins, les modèles, les tailles de chunks, etc.

## 🧠 Architecture Technique

-   **Backend**: FastAPI (framework web asynchrone).
-   **Frontend**: HTML5, Bootstrap 5, JavaScript (vanilla).
-   **Base de données de metadonnées**: SQLite (simple et léger).
-   **Base de données vectorielle**: ChromaDB (pour la recherche de similarité).
-   **Traitement IA/ML**: `sentence-transformers` pour les embeddings, `Ollama` pour la génération de texte par LLM.

## 🐛 Dépannage

-   **Erreur "Dépendance manquante"**: Assurez-vous d'avoir bien activé l'environnement virtuel (`source venv/bin/activate`) et relancez `pip install -r requirements.txt`.
-   **Port déjà utilisé**: Arrêtez le processus qui utilise le port 8000 ou changez le port dans `config/config.yaml`.
-   **Ollama non détecté**: Assurez-vous qu'Ollama est bien installé et en cours d'exécution. Vous pouvez le lancer avec la commande `ollama serve`.

## 🔒 Sécurité

⚠️ **IMPORTANT**: Cette version est un POC (Proof of Concept) destiné au développement et aux tests. **NE PAS UTILISER EN PRODUCTION** sans des mesures de sécurité additionnelles comme l'authentification des utilisateurs, HTTPS, et la protection des API.