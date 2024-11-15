import sys
import os

# Add the root project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from streamlit_chat import message
from app.doc_processor import process_document
from app.qa_bot import QABot
from app.summarizer import Summarizer
import os
import time
import chardet  # For detecting encoding

qa_bot = QABot()
summarizer = Summarizer()

session_state = st.session_state
if "chat_history" not in session_state:
    session_state.chat_history = []

def stream_response(response_generator, output_placeholder):
    response = ""
    for chunk in response_generator:
        response += chunk
        output_placeholder.markdown(response)
        time.sleep(0.05)  # to simulate streaming effect

def detect_encoding(filepath):
    with open(filepath, 'rb') as file:
        result = chardet.detect(file.read(10000))  # Read the first 10KB to detect encoding
    return result['encoding']

def main():
    st.title("Document Summarizer & QA Chatbot")
    st.sidebar.title("Navigation")
    choice = st.sidebar.radio("Go to", ["Upload Document", "Summarize Document", "Ask a Question"])

    if choice == "Upload Document":
        st.header("Upload Document")
        uploaded_file = st.file_uploader("Choose a file", type=["txt", "pdf"])
        if uploaded_file is not None:
            filepath = os.path.join('data/documents', uploaded_file.name)
            with open(filepath, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            process_document(filepath)
            st.success("File uploaded and processed successfully!")

    elif choice == "Summarize Document":
        st.header("Summarize Document")
        filename = st.text_input("Enter the filename of the document to summarize:")
        if st.button("Generate Summary"):
            filepath = os.path.join('data/documents', filename)
            if os.path.exists(filepath):
                encoding = detect_encoding(filepath)
                with open(filepath, 'r', encoding=encoding) as file:
                    content = file.read()
                output_placeholder = st.empty()
                response_generator = summarizer.generate_summary_stream(content)
                stream_response(response_generator, output_placeholder)
            else:
                st.error("File not found. Please upload the document first.")

    elif choice == "Ask a Question":
        st.header("Ask a Question")
        question = st.text_input("Enter your question:")
        if st.button("Get Answer"):
            if question:
                output_placeholder = st.empty()
                response_generator = qa_bot.answer_question_stream(question)
                stream_response(response_generator, output_placeholder)
            else:
                st.error("Please enter a question.")

if __name__ == '__main__':
    main()
