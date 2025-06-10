import os
import time
import logging
from pathlib import Path
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, List

# Imports depuis nos modules locaux
from .document_processor import DocumentProcessor
from .rag_engine import RAGEngine
from .llm_handler import get_llm_handler
from .model_manager import OllamaModelManager
from run import load_config # On importe depuis le run.py pour centraliser

# Configuration
config = load_config()
logger = logging.getLogger(__name__)

# Initialisation de l'application FastAPI
app = FastAPI(title=config['app']['name'], version=config['app']['version'])

# Montage des fichiers statiques et des templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialisation des composants principaux
doc_processor = DocumentProcessor()
rag_engine = RAGEngine(config)
llm_handler = get_llm_handler(config)
model_manager = OllamaModelManager(config)

# "Base de données" en mémoire pour les documents (pour ce POC)
# Dans une vraie app, on utiliserait SQLAlchemy avec la DB SQLite
documents_db: Dict[int, Dict] = {}
next_doc_id = 1

# --- Routes pour les pages HTML ---

@app.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    # Logique pour récupérer les stats...
    stats = {"total_documents": len(documents_db), "processed_documents": len(documents_db), "total_chunks": rag_engine.get_stats()['total_chunks'], "total_conversations": 0}
    return templates.TemplateResponse("index.html", {"request": request, "stats": stats})

@app.get("/upload", response_class=HTMLResponse)
async def get_upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def get_admin_page(request: Request):
    # Logique pour les stats et la liste des documents...
    stats = {"total_documents": len(documents_db), "processed_documents": len(documents_db), "total_chunks": rag_engine.get_stats()['total_chunks'], "total_conversations": 0}
    return templates.TemplateResponse("admin.html", {"request": request, "stats": stats, "documents": list(documents_db.values())})

# --- Routes API ---

@app.post("/api/upload")
async def api_upload_file(file: UploadFile = File(...), tags: str = Form("")):
    global next_doc_id
    max_size = config['storage']['max_file_size'] * 1024 * 1024
    if file.size > max_size:
        raise HTTPException(status_code=413, detail=f"Fichier trop volumineux. Taille max: {config['storage']['max_file_size']}MB")

    upload_dir = Path(config['storage']['documents_path'])
    upload_dir.mkdir(exist_ok=True)
    file_path = upload_dir / file.filename
    
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        text = doc_processor.extract_text(str(file_path))
        
        doc_metadata = {
            "id": next_doc_id,
            "doc_id": f"doc_{next_doc_id}",
            "filename": file.filename,
            "file_path": str(file_path),
            "file_type": Path(file.filename).suffix,
            "file_size": file.size,
            "upload_date": time.strftime('%Y-%m-%d %H:%M:%S'),
            "tags": tags,
            "processed": True
        }

        num_chunks = rag_engine.add_document(doc_id=doc_metadata['doc_id'], text=text, metadata={"doc_id": doc_metadata['doc_id'], "filename": file.filename})
        doc_metadata["chunk_count"] = num_chunks
        
        documents_db[next_doc_id] = doc_metadata
        next_doc_id += 1
        
        return JSONResponse({
            "message": f"Fichier '{file.filename}' uploadé et traité avec succès.",
            "chunks": num_chunks
        })

    except Exception as e:
        logger.error(f"Erreur lors de l'upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def api_chat(request: Request):
    data = await request.json()
    query = data.get("message")
    if not query:
        raise HTTPException(status_code=400, detail="Message manquant.")

    start_time = time.time()
    
    # 1. Recherche RAG
    search_results = rag_engine.search(query, n_results=5)
    context = "\n\n".join([res['content'] for res in search_results])
    sources = list(set([res['metadata']['filename'] for res in search_results]))

    # 2. Génération de la réponse
    response_text = llm_handler.generate_response(context, query)
    
    end_time = time.time()
    
    return JSONResponse({
        "response": response_text,
        "sources": sources,
        "response_time": round(end_time - start_time, 2)
    })
    
@app.get("/api/stats")
async def get_api_stats():
    # Ici, vous pourriez avoir une logique plus complexe
    return JSONResponse({
        "total_documents": len(documents_db),
        "total_chunks": rag_engine.get_stats()['total_chunks']
    })

# --- Routes API pour la gestion des modèles ---

@app.get("/api/models/status")
async def get_models_status():
    return JSONResponse({
        "ollama_available": model_manager.is_ollama_available(),
        "current_model": llm_handler.get_current_model(),
        "installed_count": len(model_manager.get_installed_models())
    })

@app.get("/api/models/installed")
async def get_installed_models():
    return JSONResponse({
        "models": model_manager.get_installed_models(),
        "current_model": llm_handler.get_current_model(),
        "ollama_available": model_manager.is_ollama_available()
    })

@app.get("/api/models/available")
async def get_available_models():
    return JSONResponse({
        "ollama_models": model_manager.get_available_models(),
        "ollama_available": model_manager.is_ollama_available()
    })

@app.post("/api/models/install/{model_name}")
async def install_model(model_name: str):
    result = await model_manager.install_model(model_name)
    if not result['success']:
        raise HTTPException(status_code=500, detail=result.get('error', 'Erreur inconnue'))
    return JSONResponse(result)

@app.delete("/api/models/{model_name}")
async def remove_model(model_name: str):
    result = model_manager.remove_model(model_name)
    if not result['success']:
        raise HTTPException(status_code=500, detail=result.get('error', 'Erreur inconnue'))
    return JSONResponse(result)

@app.post("/api/models/set-active/{model_name}")
async def set_active_model(model_name: str):
    success = model_manager.set_active_model(model_name)
    if success:
        if hasattr(llm_handler, 'set_model'):
            llm_handler.set_model(model_name)
        return JSONResponse({"status": "success", "message": f"Modèle actif changé pour {model_name}"})
    else:
        raise HTTPException(status_code=500, detail="Impossible de changer le modèle actif.")

# --- Fonction pour lancer le serveur ---

def run_app():
    import uvicorn
    uvicorn.run(app, host=config['app']['host'], port=config['app']['port'])