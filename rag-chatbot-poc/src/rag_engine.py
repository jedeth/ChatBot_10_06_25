import chromadb
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging
from typing import List, Dict

class RAGEngine:
    def __init__(self, config: dict):
        self.logger = logging.getLogger(__name__)
        self.config = config['embedding']
        db_config = config['database']['vector_db']
        
        self.client = chromadb.PersistentClient(path=db_config['path'])
        self.collection = self.client.get_or_create_collection(name=db_config['collection_name'])
        
        self.logger.info(f"Chargement du modèle d'embedding: {self.config['model_name']}")
        self.embedding_model = SentenceTransformer(self.config['model_name'])
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config['chunk_size'],
            chunk_overlap=self.config['chunk_overlap']
        )
        self.logger.info("Moteur RAG initialisé.")

    def add_document(self, doc_id: str, text: str, metadata: dict) -> int:
        self.logger.info(f"Découpage et embedding du document ID: {doc_id}")
        chunks = self.text_splitter.split_text(text)
        if not chunks:
            self.logger.warning(f"Aucun chunk de texte n'a pu être créé pour le document {doc_id}.")
            return 0
            
        embeddings = self.embedding_model.encode(chunks, show_progress_bar=False)
        
        num_chunks = len(chunks)
        ids = [f"{doc_id}_{i}" for i in range(num_chunks)]
        metadatas = [{**metadata, "chunk_id": i} for i in range(num_chunks)]
        
        self.collection.add(
            documents=chunks,
            embeddings=embeddings.tolist(),
            metadatas=metadatas,
            ids=ids
        )
        self.logger.info(f"{num_chunks} chunks ajoutés à la base de données vectorielle pour le document {doc_id}.")
        return num_chunks

    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        self.logger.info(f"Recherche de la requête : '{query[:50]}...'")
        query_embedding = self.embedding_model.encode([query])
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results
        )
        
        # Formater les résultats pour être plus utilisables
        formatted_results = []
        if results and results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    "content": doc,
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i]
                })
        return formatted_results

    def delete_document(self, doc_id: str):
        self.logger.info(f"Suppression des chunks associés au document ID: {doc_id}")
        self.collection.delete(where={"doc_id": doc_id})

    def get_stats(self):
        count = self.collection.count()
        return {"total_chunks": count}