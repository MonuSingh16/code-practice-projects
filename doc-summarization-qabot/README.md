# Document Summarizer & QA Chatbot
This project allows users to upload a document, generate a summary of the document, and ask specific questions using the document as a knowledge source. The application uses FAISS for VectorDB and llama_index/langchain for the question-answering bot.

## Setup
1. Install dependencies: `pip install -r dependencies/requirements.txt`
2. Download required models: `python download_models.py`
3. Run the application: `streamlit run app/main.py`
4. Use the Streamlit interface to upload documents, summarize, and ask questions.