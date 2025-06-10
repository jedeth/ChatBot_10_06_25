# build.py
import PyInstaller.__main__
import os
import shutil

# --- Configuration ---
PROJECT_NAME = "RAG-Chatbot"
ENTRY_POINT_SCRIPT = "run.py"
OUTPUT_FOLDER = "dist"

def build_executable():
    """Lance le processus de création de l'exécutable avec PyInstaller."""
    print("🚀 Démarrage de la création de l'exécutable...")

    # Définition des dossiers à inclure dans l'exécutable.
    # Format pour --add-data: 'source;destination_dans_le_bundle'
    # Le séparateur est ';' sur Windows et ':' sur Mac/Linux.
    separator = ';' if os.name == 'nt' else ':'
    
    data_to_include = [
        f'config{separator}config',
        f'static{separator}static',
        f'templates{separator}templates'
    ]

    # Définition des arguments pour PyInstaller
    pyinstaller_args = [
        ENTRY_POINT_SCRIPT,
        '--noconfirm',  # Ne pas demander de confirmation pour écraser les fichiers
        '--clean',      # Nettoyer les fichiers de cache avant de commencer
        '--onefile',    # Créer un seul fichier .exe
        f'--name={PROJECT_NAME}',  # Nom de l'exécutable final
    ]

    # Ajout des dossiers de données
    for data in data_to_include:
        pyinstaller_args.extend(['--add-data', data])

    # Ajout des imports "cachés" que PyInstaller pourrait manquer
    # C'est souvent nécessaire pour les serveurs web comme FastAPI/Uvicorn
    hidden_imports = [
        'uvicorn.lifespan.on',
        'uvicorn.loops.auto',
        'uvicorn.protocols.http.auto',
    ]
    for lib in hidden_imports:
        pyinstaller_args.extend(['--hidden-import', lib])
        
    # --- Optionnel : Cacher la console ---
    # Pour la version finale, vous pouvez décommenter la ligne suivante.
    # Pour le débogage, il est préférable de garder la console visible.
    # pyinstaller_args.append('--windowed') # ou --noconsole

    print(f"⚙️  Arguments PyInstaller : {' '.join(pyinstaller_args)}")

    # Lancement de PyInstaller
    PyInstaller.__main__.run(pyinstaller_args)

    print("\n✅ Création de l'exécutable terminée !")
    print(f"Vous trouverez '{PROJECT_NAME}.exe' dans le dossier '{OUTPUT_FOLDER}'.")

if __name__ == "__main__":
    build_executable()