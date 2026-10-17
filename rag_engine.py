"""
rag_engine.py - Complete RAG (Retrieval-Augmented Generation) Engine
1. Ingests & chunks documents (PDF/TXT)
2. Embeds into FAISS vector database (Sentence-Transformers)
3. Retrieves relevant context
4. Synthesizes executive answers with citations using Google Gemini 2.5 Flash
"""

import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

# Load environment variables from .env file (reads GOOGLE_API_KEY)
load_dotenv()

# ==============================================================================
# 1. CONFIGURATION & MODELS SETUP
# ==============================================================================
FAISS_INDEX_PATH = "faiss_index"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# 1. Local CPU Embedding Model (Free)
print("⏳ Initializing local embedding model...")
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
print("✅ Local embedding model ready!")

# 2. Cloud LLM Brain: Google Gemini 2.5 Flash (Free tier, fast & smart)
# Temperature = 0.1 ensures responses are strictly factual, not creative/random
llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    temperature=0.1,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

# ==============================================================================
# 2. DOCUMENT LOADING & CHUNKING
# ==============================================================================
def load_and_chunk_file(file_path, chunk_size=500, chunk_overlap=50):
    """Loads a text or PDF document and splits it into searchable chunks."""
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith(".txt"):
        loader = TextLoader(file_path, encoding="utf-8")
    else:
        raise ValueError(f"Unsupported format: {file_path}")

    raw_docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = splitter.split_documents(raw_docs)
    return chunks


# ==============================================================================
# 3. VECTOR STORE CREATION & PERSISTENCE (FAISS)
# ==============================================================================
def build_vector_store(sample_data_dir="sample_data"):
    """Chunks all documents in sample_data and saves them to local FAISS index."""
    all_chunks = []
    if not os.path.exists(sample_data_dir):
        return None

    for filename in os.listdir(sample_data_dir):
        if filename.endswith(".txt") or filename.endswith(".pdf"):
            full_path = os.path.join(sample_data_dir, filename)
            chunks = load_and_chunk_file(full_path)
            all_chunks.extend(chunks)

    if not all_chunks:
        return None

    vector_db = FAISS.from_documents(all_chunks, embeddings)
    vector_db.save_local(FAISS_INDEX_PATH)
    return vector_db


def get_vector_store():
    """Loads existing FAISS index or builds a new one if missing."""
    if os.path.exists(FAISS_INDEX_PATH):
        return FAISS.load_local(
            FAISS_INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
    return build_vector_store()


def search_similar_documents(query, k=3):
    """Retrieves top 'k' most relevant document chunks from FAISS."""
    vector_db = get_vector_store()
    if not vector_db:
        return []
    return vector_db.similarity_search(query, k=k)


# ==============================================================================
# 4. RAG GENERATION: ASK PROJECT COPILOT
# ==============================================================================
# Prompt Template that instructs Gemini how to behave like a consulting assistant
RAG_PROMPT_TEMPLATE = """You are an AI Business Operations Copilot assisting a project management and consulting team.

Answer the user's question accurately using ONLY the provided document context below.
If the answer cannot be found in the context, state clearly: "Based on the available project documents, this information is not mentioned."
Do NOT invent or assume facts outside the context.
Keep your response professional, structured, and concise.

Context from Project Documents:
----------------------------------------
{context}
----------------------------------------

User Question: {question}

Executive Answer:"""

rag_prompt = PromptTemplate(
    template=RAG_PROMPT_TEMPLATE,
    input_variables=["context", "question"]
)

def ask_project_copilot(question, top_k=3):
    """
    Complete RAG Pipeline:
    1. Retrieves top_k relevant chunks from FAISS
    2. Builds the context string with document filenames
    3. Prompts Google Gemini LLM
    4. Returns the synthesized answer along with list of sources
    """
    # 1. Retrieve relevant chunks
    matched_docs = search_similar_documents(question, k=top_k)
    
    if not matched_docs:
        return {
            "answer": "No project documents found in the database. Please ingest documents first.",
            "sources": []
        }

    # 2. Format context with source attribution
    context_parts = []
    sources = set()
    for doc in matched_docs:
        source_name = os.path.basename(doc.metadata.get("source", "Document"))
        sources.add(source_name)
        context_parts.append(f"[{source_name}]:\n{doc.page_content.strip()}")

    formatted_context = "\n\n".join(context_parts)

    # 3. Create the prompt and call Gemini LLM
    final_prompt = rag_prompt.format(context=formatted_context, question=question)
    response = llm.invoke(final_prompt)

    return {
        "answer": response.content.strip(),
        "sources": list(sources)
    }


# ==============================================================================
# 5. TESTING THE COMPLETE RAG SYSTEM
# ==============================================================================
if __name__ == "__main__":
    print("=" * 65)
    print("       TESTING COMPLETE RAG QUESTION-ANSWERING SYSTEM")
    print("=" * 65)

    test_questions = [
        "What did the team decide to do regarding the API delay in Project Alpha?",
        "What are the encryption and data privacy rules for Acme/Bharat Financial?",
        "What is the budget for Project Beta?"  # Trick question: not in the documents!
    ]

    for q in test_questions:
        print("\n" + "-" * 60)
        print(f"❓ QUESTION: {q}")
        print("-" * 60)
        
        result = ask_project_copilot(q)
        print(f"\n💡 AI COPILOT ANSWER:\n{result['answer']}")
        print(f"\n📌 Cited Sources: {', '.join(result['sources'])}")

    print("\n" + "=" * 65)