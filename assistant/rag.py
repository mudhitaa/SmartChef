import os
from pathlib import Path
from typing import List, Tuple

import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env
load_dotenv()


class RAGEngine:
    """
    Django-ready RAG engine:
    - SentenceTransformers for embeddings
    - Chroma for vector DB
    - Groq for LLM answer generation
    """

    def __init__(self, data_path: str, persist_dir: str):
        self.data_path = Path(data_path)
        self.persist_dir = persist_dir

        # Embedding model
        self.embed_model_name = "all-MiniLM-L6-v2"
        self.model = SentenceTransformer(self.embed_model_name)

        # Chroma persistent DB
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection("cookbook")

        # Load Groq client
        self.llm = Groq(api_key=os.getenv("GROQ_API_KEY"))

        # If DB is empty, ingest data
        if self.collection.count() == 0:
            print("Chroma empty — building index...")
            self._ingest_all_files()
        else:
            print("Chroma loaded — using existing DB.")

    # ---- Load all .txt files ----
    def _read_text_files(self) -> List[Tuple[str, str]]:
        files = []
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data folder not found: {self.data_path.resolve()}")
        for p in sorted(self.data_path.glob("*.txt")):
            files.append((p.name, p.read_text(encoding="utf-8")))
        return files

    # ---- Chunk text ----
    def _chunk_text(self, text: str, chunk_size=400, overlap=80) -> List[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end == len(text):
                break
            start = end - overlap
        return chunks

    # ---- Ingest all files ----
    def _ingest_all_files(self):
        documents, metadata, ids = [], [], []

        for fname, content in self._read_text_files():
            chunks = self._chunk_text(content)
            for i, c in enumerate(chunks):
                documents.append(c)
                metadata.append({"source": fname, "chunk": i})
                ids.append(f"{fname}-{i}")

        if not documents:
            print("⚠ No documents to index!")
            return

        embeddings = self.model.encode(documents, convert_to_numpy=True).tolist()

        self.collection.add(
            documents=documents,
            metadatas=metadata,
            ids=ids,
            embeddings=embeddings,
        )

        print(f"Ingested {len(documents)} chunks into ChromaDB.")

    # ---- Query Chroma ----
    def query(self, question: str, top_k=5):
        q_emb = self.model.encode(question, convert_to_numpy=True).tolist()
        results = self.collection.query(
            query_embeddings=[q_emb],
            n_results=top_k
        )
        docs = results["documents"][0]
        meta = results["metadatas"][0]
        return docs, meta

    # ---- Full RAG: retrieve + Groq LLM ----
    def answer_question(self, question: str) -> Tuple[str, List[dict]]:
        try:
            docs, meta = self.query(question)
            context = "\n\n".join(docs)

            prompt = f"""

### 💡 Additional Tips
You are SmartChef AI — an expert cooking, nutrition, and allergy-aware recipe assistant. 
You MUST ALWAYS answer in the following structured format:

---

🍽 RECIPE NAME 

📝 Ingredients 
- list ingredients in bullet points

👨‍🍳 Steps
1. numbered steps

⏱ Cooking Time
- Prep Time:
- Cook Time:

🍽 Serving Size

💪 Nutrition Info (approx)
- Calories:
- Protein:
- Carbs:
- Fat:

⚠ Allergy Warnings
Scan the ingredients and context. Mention if the dish may contain:
- nuts
- dairy
- gluten
- soy
- eggs
- shellfish
- sesame
If no allergy risk: write “No common allergens detected.”

🔥 Calorie-Based Suggestions
If the user requests healthy, low-calorie, muscle-building, or gives calorie limits:
- Recommend healthier variations
- Suggest alternatives from the context
- Suggest ingredient substitutions  
If no calorie preference: write “No calorie-specific requests detected.”

💡 Additional Tips
Useful cooking, storage, or serving advice.

---

Use ONLY the cookbook context below. 
If the answer is not fully present in the context, reply:
"I don't have enough information from the cookbook to answer this."

--- CONTEXT ---
{context}

--- USER QUESTION ---
{question}
"""

        # Safely get Groq model from environment, fallback to default
            groq_models = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
            model_to_use = groq_models.split(",")[0].strip()

        
            response = self.llm.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.2
            )
            answer = response.choices[0].message.content
        except Exception as e:
            # Always assign defaults in case of failure
            print(f"Error in answer_question: {e}")
            answer = "Error: Unable to get answer from the AI model. Please check the model and API key."
            meta = []  # fallback to empty list"

        return answer, meta


# ---- Create ONE shared global RAG engine for Django ----
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "rag_data"
CHROMA_DIR = BASE_DIR / "chroma_db"

rag_engine = RAGEngine(
    data_path=DATA_DIR,
    persist_dir=str(CHROMA_DIR)
)


def answer_question(question: str):
    return rag_engine.answer_question(question)
