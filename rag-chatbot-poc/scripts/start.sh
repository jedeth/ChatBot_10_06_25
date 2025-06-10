#!/bin/bash
echo "🚀 Démarrage du RAG Document Chatbot POC"
echo "========================================"

# Vérification de l'environnement virtuel
if [ ! -d "venv" ]; then
    echo "❌ Environnement virtuel non trouvé. Avez-vous exécuté ./scripts/install.sh ?"
    exit 1
fi

# Activation de l'environnement virtuel
echo "🔧 Activation de l'environnement virtuel..."
source venv/bin/activate

# Vérification d'Ollama
if ! pgrep -x "ollama" > /dev/null
then
    echo "⚠️  Le service Ollama ne semble pas être en cours d'exécution."
    echo "   Le chatbot démarrera en mode simplifié."
    echo "   Pour une expérience complète, lancez 'ollama serve' dans un terminal séparé."
fi


# Démarrage de l'application
echo "🐍 Lancement de l'application Python..."
python run.py