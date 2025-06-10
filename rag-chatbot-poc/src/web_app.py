import os
import time
import logging
from pathlib import Path
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, List

from .document_processor import DocumentProcessor
from .rag_engine import RAGEngine
from .llm_handler import get_llm_handler
from .model_manager import OllamaModelManager
from run import load_config

config = load_config()
logger = logging.getLogger(__name__)

app = FastAPI(title=config['app']['name'])
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

doc_processor = DocumentProcessor()
rag_engine = RAGEngine(config)
llm_handler = get_llm_handler(config)
model_manager = OllamaModelManager(config)

documents_db: Dict[int, Dict] = {}
next_doc_id = 1

@app.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    stats = {"total_documents": len(documents_db), "total_chunks": rag_engine.get_stats()['total_chunks']}
    return templates.TemplateResponse("index.html", {"request": request, "stats": stats})

@app.get("/admin", response_class=HTMLResponse)
async def get_admin_page(request: Request):
    stats = {"total_documents": len(documents_db), "total_chunks": rag_engine.get_stats()['total_chunks']}
    return templates.TemplateResponse("admin.html", {"request": request, "stats": stats, "documents": list(documents_db.values())})

@app.post("/api/chat")
async def api_chat(request: Request):
    data = await request.json()
    query = data.get("message")
    search_results = rag_engine.search(query, n_results=5)
    context = "\n\n".join([res['content'] for res in search_results])
    sources = list(set([res['metadata']['filename'] for res in search_results]))
    response_text = llm_handler.generate_response(context, query)
    return JSONResponse({"response": response_text, "sources": sources})

@app.get("/api/models/status")
async def get_models_status():
    provider = config.get('llm', {}).get('provider', 'simple').lower()
    
    if provider == 'gemini':
        return JSONResponse({
            "provider": "gemini",
            "current_model": llm_handler.get_current_model(),
            "ollama_available": False
        })
    else: # Pour ollama ou simple
        return JSONResponse({
            "provider": provider,
            "ollama_available": model_manager.is_ollama_available(),
            "current_model": llm_handler.get_current_model()
        })

@app.post("/api/models/set-active/{model_name}")
async def set_active_model_endpoint(model_name: str):
    success = model_manager.set_active_model(model_name)
    if success:
        # Recharger la config et ré-instancier le handler pour prendre en compte le changement
        global config, llm_handler
        config = load_config()
        llm_handler = get_llm_handler(config)
        return JSONResponse({"status": "success"})
    else:
        raise HTTPException(status_code=500, detail="Impossible de changer le modèle actif.")

# --- Les autres routes (upload, etc.) restent les mêmes ---

@app.get("/upload", response_class=HTMLResponse)
async def get_upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/api/upload")
async def api_upload_file(file: UploadFile = File(...)):
    global next_doc_id
    upload_dir = Path(config['storage']['documents_path'])
    file_path = upload_dir / file.filename
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        text = doc_processor.extract_text(str(file_path))
        doc_metadata = {"id": next_doc_id, "doc_id": f"doc_{next_doc_id}", "filename": file.filename}
        num_chunks = rag_engine.add_document(doc_id=doc_metadata['doc_id'], text=text, metadata=doc_metadata)
        doc_metadata["chunk_count"] = num_chunks
        documents_db[next_doc_id] = doc_metadata
        next_doc_id += 1
        return JSONResponse({"message": "Fichier traité.", "chunks": num_chunks})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/stats")
async def get_api_stats():
    """Retourne les statistiques de base de l'application."""
    try:
        stats = {
            "total_documents": len(documents_db),
            "total_chunks": rag_engine.get_stats()['total_chunks']
        }
        return JSONResponse(stats)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des stats: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")
        
def run_app():
    import uvicorn
    uvicorn.run(app, host=config['app']['host'], port=config['app']['port'])