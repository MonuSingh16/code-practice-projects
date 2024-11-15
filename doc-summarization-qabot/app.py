# Adapted from https://docs.streamlit.io/knowledge-base/tutorials/build-conversational-apps#build-a-simple-chatbot-gui-with-streaming

import os
import base64
import gc
import random
import tempfile
import time
import uuid

import streamlit as st
from llama_index import VectorStoreIndex, SimpleDirectoryReader, ServiceContext
from llama_index.llms import LLMPredictor
from langchain.vectorstores import FAISS
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

if "id" not in st.session_state:
    st.session_state.id = uuid.uuid4()
    st.session_state.file_cache = {}

session_id = st.session_state.id

@st.cache_resource
def load_llm():
    # Load a local model, assuming it's stored at a specific path
    local_model_path = "./models/generative"  # Update with your local model path
    tokenizer = AutoTokenizer.from_pretrained(local_model_path)
    model = AutoModelForCausalLM.from_pretrained(local_model_path)
    llm_pipeline = pipeline("text-generation", model=model, tokenizer=tokenizer, max_length=512)
    llm_predictor = LLMPredictor(llm_pipeline)
    return llm_predictor

@st.cache_resource
def load_service_context(llm_predictor):
    # Create a ServiceContext to be used in VectorStoreIndex
    service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor)
    return service_context

@st.cache_resource
def load_embedding_model():
    # Load embeddings from a local model
    local_embedding_model_path = "./models/embeddings"  # Update with your local model path
    embed_model = HuggingFaceEmbeddings(model_name=local_embedding_model_path)
    return embed_model

def reset_chat():
    st.session_state.messages = []
    st.session_state.context = None
    gc.collect()

def display_pdf(file):
    # Opening file from file path
    st.markdown("### PDF Preview")
    base64_pdf = base64.b64encode(file.read()).decode("utf-8")

    # Embedding PDF in HTML
    pdf_display = f"""<iframe src="data:application/pdf;base64,{base64_pdf}" width="400" height="100%" type="application/pdf"
                        style="height:100vh; width:100%"
                    >
                    </iframe>"""

    # Displaying File
    st.markdown(pdf_display, unsafe_allow_html=True)

def summarize_document(index, llm):
    # Summarize the document using the LLM through LlamaIndex
    summary_prompt = "Please provide a concise summary of the following document:"
    summary = index.query(summary_prompt)
    return summary.response

with st.sidebar:
    st.header(f"Add your documents!")
    
    uploaded_file = st.file_uploader("Choose your `.pdf` file", type="pdf")

    if uploaded_file:
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                file_path = os.path.join(temp_dir, uploaded_file.name)
                
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                file_key = f"{session_id}-{uploaded_file.name}"
                st.write("Indexing your document...")

                if file_key not in st.session_state.get('file_cache', {}):

                    if os.path.exists(temp_dir):
                        loader = SimpleDirectoryReader(input_dir=temp_dir, required_exts=[".pdf"], recursive=True)
                    else:
                        st.error('Could not find the file you uploaded, please check again...')
                        st.stop()
                    
                    docs = loader.load_data()

                    # setup llm predictor & service context
                    llm_predictor = load_llm()
                    service_context = load_service_context(llm_predictor)
                    embed_model = load_embedding_model()
                    
                    # Creating an index over loaded data using FAISS
                    vector_store = FAISS.from_documents(docs, embed_model)
                    index = VectorStoreIndex.from_vector_store(vector_store, service_context=service_context)
                    
                    # Cache the file information
                    st.session_state.file_cache[file_key] = {
                        'index': index,
                        'docs': docs
                    }

                    # Summarize the document
                    st.write("Generating document summary...")
                    summary = summarize_document(index, llm_predictor)
                    st.session_state.file_cache[file_key]['summary'] = summary
                    st.success("Document indexed and summarized successfully!")
                    st.markdown("### Document Summary")
                    st.markdown(summary)
                else:
                    st.write("Document already indexed.")
                    summary = st.session_state.file_cache[file_key].get('summary')
                    if summary:
                        st.markdown("### Document Summary")
                        st.markdown(summary)
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

def main():
    st.title("Local LLM with LlamaIndex and FAISS")
    reset_button = st.button("Reset Chat", on_click=reset_chat)
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # Handle user input
    user_input = st.text_input("You: ", key="input")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Get response from the model
        llm_predictor = load_llm()
        index = st.session_state.file_cache.get(f"{session_id}-{uploaded_file.name}", {}).get('index')
        if index:
            # Query the index and generate response
            response = index.query(user_input)
            st.session_state.messages.append({"role": "bot", "content": response.response})
        else:
            st.warning("Please upload and index a document first.")

    # Display conversation history
    for message in st.session_state.messages:
        if message['role'] == 'user':
            st.text_area("You", value=message['content'], height=40, key=str(random.random()))
        else:
            st.text_area("Bot", value=message['content'], height=40, key=str(random.random()))

if __name__ == "__main__":
    main()
