import os 
import glob
import re 
import numpy as np
from rank_bm25 import BM25Okapi

class Retriever: 
    def __init__(self, docs_path="docs"):
        self.chunks = []
        self.corpus = []
        self.bm25 = None

        filepaths = glob.glob(os.path.join(docs_path, "*.md"))
        
        for filepath in filepaths:
            file_name = os.path.basename(filepath).replace(".md", "")
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
                self._process_text(text, split_on="\n## ", file_name=file_name)

        tokenized_corpus = [self._tokenize(doc) for doc in self.corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def _tokenize(self, text):
        # 1. lowercase
        # 2. remove all characters that are not letters or numbers
        # 3. split by whitespace
        clean_text = re.sub(r'[^a-z0-9\s]', '', text.lower())
        return clean_text.split()

    def _process_text(self, text, split_on="\n## ", file_name="unknown"):
        sections = text.split(split_on)
        for i, section in enumerate(sections):
            cleaned_section = section.strip()
            if i > 0:
                cleaned_section = "## " + cleaned_section
            
            if not cleaned_section:
                continue

            chunk_id = f"{file_name}::chunk{i}"
            
            self.chunks.append({
                "id": chunk_id,
                "text": cleaned_section,
                "source": file_name
            })
            self.corpus.append(cleaned_section)

    def search(self, query, top_k=3):
        tokenized_query = self._tokenize(query)
        
        doc_scores = self.bm25.get_scores(tokenized_query)
        top_n_indices = np.argsort(doc_scores)[-top_k:][::-1]

        results = []
        for idx in top_n_indices:
            if doc_scores[idx] > 0:
                results.append({
                    "id": self.chunks[idx]["id"],
                    "text": self.chunks[idx]["text"],
                    "source": self.chunks[idx]["source"],
                    "score": doc_scores[idx]
                })
        return results
    
if __name__ == "__main__":
    retriever = Retriever(docs_path="docs")
    query = "return window for unopened beverages"
    results = retriever.search(query, top_k=2)
    for res in results:
        print(f"ID: {res['id']}\nScore: {res['score']:.4f}\nText: {res['text'][:100]}...\n")