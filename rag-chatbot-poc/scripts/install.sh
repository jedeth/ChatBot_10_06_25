#!/bin/bash
echo "🚀 Installation du RAG Document Chatbot POC"
echo "============================================="

# Vérification de Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé. Veuillez l'installer avant de continuer."
    exit 1
fi
echo "✅ Python 3 détecté: $(python3 --version)"

# Création de l'environnement virtuel
if [ ! -d "venv" ]; then
    echo "📦 Création de l'environnement virtuel dans ./venv..."
    python3 -m venv venv
else
    echo "📦 Environnement virtuel déjà existant."
fi

# Activation de l'environnement virtuel
echo "🔧 Activation de l'environnement virtuel..."
source venv/bin/activate

# Mise à jour de pip
echo "⬆️  Mise à jour de pip..."
pip install --upgrade pip > /dev/null

# Installation des dépendances
echo "📚 Installation des dépendances Python depuis requirements.txt..."
if pip install -r requirements.txt; then
    echo "✅ Dépendances installées avec succès."
else
    echo "❌ Erreur lors de l'installation des dépendances."
    exit 1
fi

# Création des répertoires nécessaires (sera fait par run.py mais on s'assure)
echo "📁 Création de la structure des répertoires..."
mkdir -p data/documents data/processed data/database logs

# Vérification optionnelle d'Ollama
echo "🤖 Vérification d'Ollama (optionnel mais recommandé)..."
if command -v ollama &> /dev/null; then
    echo "✅ Ollama est installé."
    echo "💡 Pensez à lancer 'ollama serve' dans un autre terminal si ce n'est pas déjà fait."
    echo "💡 Pour une meilleure expérience, installez un modèle : 'ollama pull mistral'"
else
    echo "⚠️  Ollama n'est pas détecté. Le chatbot fonctionnera en mode simplifié."
    echo "   Pour une expérience complète, installez Ollama en suivant les instructions sur https://ollama.ai/"
    echo "   Après l'installation, lancez : 'ollama pull mistral'"
fi

echo ""
echo "🎉 Installation terminée avec succès!"
echo ""
echo "Pour démarrer le système, utilisez le script :"
echo "   ./scripts/start.sh"
echo ""
echo "Ou activez manuellement l'environnement et lancez le serveur :"
echo "   source venv/bin/activate"
echo "   python run.py"
echo ""