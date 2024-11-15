import faiss
import numpy as np

class VectorStore:
    def __init__(self):
        self.index = faiss.IndexFlatL2(384)
        self.documents = []

    def add_document(self, filepath, embedding):
        vector = np.array([embedding]).astype('float32')
        self.index.add(vector)
        self.documents.append(filepath)

    def search(self, query_embedding, top_k=3):
        D, I = self.index.search(np.array([query_embedding]).astype('float32'), top_k)
        return [self.documents[i] for i in I[0]]
