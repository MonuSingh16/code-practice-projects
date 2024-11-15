from app.vector_store import VectorStore
from models.embeddings import generate_embeddings
import os

vector_store = VectorStore()

def process_document(filepath):
    with open(filepath, 'r') as file:
        content = file.read()
    embeddings = generate_embeddings(content)
    vector_store.add_document(filepath, embeddings)
