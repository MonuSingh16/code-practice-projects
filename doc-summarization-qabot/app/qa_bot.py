from models.embeddings import generate_embeddings
from app.vector_store import VectorStore
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import os

vector_store = VectorStore()

gpt_model_path = "models/generative/"
gpt_model = AutoModelForCausalLM.from_pretrained(gpt_model_path)
gpt_tokenizer = AutoTokenizer.from_pretrained(gpt_model_path)
generative_pipeline = pipeline('text-generation', model=gpt_model, tokenizer=gpt_tokenizer)

class QABot:
    def answer_question_stream(self, question):
        question_embedding = generate_embeddings(question)
        relevant_docs = vector_store.search(question_embedding)

        # Construct context from relevant documents
        context = ""
        for doc_path in relevant_docs:
            with open(doc_path, 'r') as file:
                context += file.read() + "\n"

        # Use the generative model to provide an answer using the context
        prompt = f"Context: {context}\nQuestion: {question}\nAnswer:"
        response = generative_pipeline(prompt, max_length=150, do_sample=True)[0]['generated_text'].replace(prompt, '').strip()
        for char in response:
            yield char