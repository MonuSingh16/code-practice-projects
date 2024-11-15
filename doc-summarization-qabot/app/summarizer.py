from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
import os

summarizer_model_path = "models/summarizer/"
summarizer_model = AutoModelForSeq2SeqLM.from_pretrained(summarizer_model_path)
summarizer_tokenizer = AutoTokenizer.from_pretrained(summarizer_model_path)

summarizer_pipeline = pipeline('summarization', model=summarizer_model, tokenizer=summarizer_tokenizer)

class Summarizer:
    def generate_summary_stream(self, filepath):
        with open(filepath, 'r') as file:
            content = file.read()
        summary = summarizer_pipeline(content, max_length=100, min_length=25, do_sample=False)
        for char in summary[0]['summary_text']:
            yield char