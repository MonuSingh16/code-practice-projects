from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer
import os
import time
import urllib.error

def retry_download(func):
    """Decorator to retry a function up to 3 times if it fails."""
    def wrapper(*args, **kwargs):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except urllib.error.URLError as e:
                if attempt < max_retries - 1:
                    print(f"Error occurred: {e}. Retrying download ({attempt + 1}/{max_retries})...")
                    time.sleep(5)
                else:
                    print(f"Failed to download after {max_retries} attempts.")
                    raise
    return wrapper

@retry_download
def download_transformer_model(model_name, model_path):
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model.save_pretrained(model_path)
    tokenizer.save_pretrained(model_path)

@retry_download
def download_generative_model(model_name, model_path):
    model = AutoModelForCausalLM.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model.save_pretrained(model_path)
    tokenizer.save_pretrained(model_path)

@retry_download
def download_embedding_model(model_name, model_path):
    model = SentenceTransformer(model_name)
    model.save(model_path)

def download_models():
    # Define model paths
    summarizer_model_path = "models/summarizer/"
    embedding_model_path = "models/embeddings/"
    gpt_model_path = "models/generative/"

    # Create directories if they do not exist
    os.makedirs(summarizer_model_path, exist_ok=True)
    os.makedirs(embedding_model_path, exist_ok=True)
    os.makedirs(gpt_model_path, exist_ok=True)

    # Download summarizer model and tokenizer
    print("Downloading summarizer model...")
    download_transformer_model("facebook/bart-large-cnn", summarizer_model_path)

    # Download embedding model
    print("Downloading embedding model...")
    download_embedding_model('all-MiniLM-L6-v2', embedding_model_path)

    # Download generative model (GPT-like model)
    print("Downloading generative model...")
    download_generative_model("gpt2", gpt_model_path)

if __name__ == "__main__":
    download_models()
