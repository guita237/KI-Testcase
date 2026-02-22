from sentence_transformers import SentenceTransformer
import os

model_name = "paraphrase-multilingual-MiniLM-L12-v2"
model = SentenceTransformer(model_name)

# Le dossier cache par défaut de HuggingFace
from huggingface_hub import hf_hub_download
from transformers.utils import default_cache_path

print("Default cache path:", default_cache_path)
print("Model loaded:", model)
