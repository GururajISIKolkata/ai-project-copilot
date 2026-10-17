# 🚀 AI-Powered Project Management & Business Operations Copilot

An enterprise-grade AI Operations Assistant built for management consulting teams (e.g., PwC, Deloitte, McKinsey) to autonomously monitor client engagements, extract structured tasks from meeting transcripts, detect cascading schedule bottlenecks, and generate board-level weekly executive reports—all backed by a strict **Human-in-the-Loop** verification architecture.

---

## 🎯 Executive Summary & Problem Statement

In enterprise consulting engagements, project managers lose 10–15 hours every week on operational overhead:
- Manually parsing meeting transcripts and client emails for action items.
- Manually tracking deliverable dependencies and calculating milestone slippage in spreadsheets.
- Searching across disparate compliance documents and SLAs to answer partner questions.
- Spending Friday afternoons manually compiling multi-stream weekly status reports.

### The Solution: A Hybrid "Deterministic Analytics + Probabilistic AI" Architecture
Unlike generic chatbots that hallucinate dates and risk numbers, this system implements a **two-tier architecture**:
1. **Deterministic Analytics Engine (Pandas + SQLite):** Hard numbers (deadlines, completion rates, and cascading task bottlenecks) are calculated mathematically with zero hallucinations.
2. **Unstructured Knowledge Engine (FAISS + Sentence-Transformers + Gemini 3.8 Flash):** Unstructured transcripts and client compliance specifications are indexed into high-dimensional vector space for semantic retrieval and structured task extraction.
3. **Human-in-the-Loop Governance:** AI-extracted tasks and recommendations are staged in a `pending_approvals` quarantine table. A human manager reviews and signs off on every action before production project data is modified.

---

## 🏛️ System Architecture

```text
                    ┌─────────────────────────────────────────┐
                    │          Streamlit Web Dashboard        │
                    │   (KPIs, RAG Chat, Approval Queue, UI)  │
                    └────────────────────┬────────────────────┘
                                         │
                         ┌───────────────┴───────────────┐
                         ▼                               ▼
        ┌────────────────────────────────┐ ┌────────────────────────────────┐
        │   Deterministic Engine         │ │    Unstructured RAG Engine     │
        │   • Pandas Analytics           │ │    • FAISS Vector Store        │
        │   • Cascading Bottleneck Logic │ │    • Sentence-Transformers     │
        │   • Milestone & Deadline Math  │ │    • Semantic Search on Docs   │
        └───────────────┬────────────────┘ └───────────────┬────────────────┘
                        │                                  │
                        ▼                                  ▼
        ┌────────────────────────────────┐ ┌────────────────────────────────┐
        │      SQLite Relational DB      │ │     Google Gemini 3.8 Flash    │
        │   • Projects Table             │ │   • Pydantic Structured Output │
        │   • Tasks & Dependencies       │ │   • Meeting Summarization      │
        │   • Pending Approvals Queue    │ │   • Weekly Report Synthesis    │
        └───────────────┬────────────────┘ └───────────────┬────────────────┘
                        │                                  │
                        └─────────────────┬────────────────┘
                                          ▼
                        ┌──────────────────────────────────┐
                        │     Human Approval Layer         │
                        │ (Manager Reviews & Approves Plan)│
                        └──────────────────────────────────┘
```

---

## 🛠️ 100% Free Open-Source Tech Stack

| Layer | Technology | Role in System |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Core application runtime |
| **Database & ORM** | SQLite & SQLAlchemy 2.0 | Relational models for projects, deliverables, dependencies, and approval queues |
| **Data Analytics** | Pandas 2.2 | High-speed tabular analytics, milestone tracking, cascading bottleneck detection |
| **Embeddings** | Sentence-Transformers (`all-MiniLM-L6-v2`) | Local CPU vectorization of documents into 384-dimensional space (₹0 cost) |
| **Vector Database** | FAISS (Meta AI) | Fast similarity indexing and retrieval for RAG |
| **LLM Orchestration** | LangChain & Google Gemini 3.8 Flash | Pydantic structured output extraction, anti-hallucination Q&A, report generation |
| **Web Frontend** | Streamlit | Reactive multi-tab dashboard with live metrics, chat interface, and approval queue |

---

## ✨ Key System Capabilities

### 1. 📊 Executive Dashboard (Deterministic Analytics)
- Real-time portfolio health snapshot (Total Projects, On Track, At Risk, Overdue items).
- Visual deliverable completion progress bars per project.
- **Cascading Bottleneck Engine:** Automatically flags when a delayed upstream task (e.g., *Core API Integration*) blocks downstream milestones (e.g., *User Acceptance Testing*).

### 2. 💬 Anti-Hallucination RAG Knowledge Engine
- Converts meeting transcripts and client security specifications into 500-character overlapping chunks.
- Performs Cosine Similarity vector search to retrieve grounded context.
- Answers natural language partner questions with **exact source document citations**.
- Strict anti-hallucination guardrail: Explicitly reports when requested facts are absent from ingested documents.

### 3. 🤖 AI Task Extraction with Pydantic
- Parses unstructured meeting transcripts into strict, typed JSON data structures (`ExtractedTaskList`).
- Automatically resolves contextual dates (e.g., converts *"submit report by Friday"* to the exact calendar date `2026-10-09`).
- Assigns priority based on critical-path urgency.

### 4. 📋 Human-in-the-Loop Approval Queue
- AI-extracted tasks are quarantined in a `pending_approvals` table.
- Engagement managers review the AI's reasoning and click **`[✅ Approve & Create Task]`** or **`[❌ Reject Action]`**.
- Prevents autonomous AI hallucination from corrupting production databases.

### 5. 📝 One-Click Weekly Executive Status Report
- Multi-stream synthesis combining live SQL metrics with contractual governance constraints.
- Formulates a publication-ready 6-section consulting status memo in 5 seconds.
- Integrated one-click Markdown download.

---

## 🚀 Quickstart & Local Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/ai-project-copilot.git
cd ai-project-copilot
```

### 2. Set Up Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Key
Create a `.env` file in the project root:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
```
*(Get a free key in 60 seconds at aistudio.google.com)*

### 5. Initialize Database & Seed Consulting Data
```bash
python seed_data.py
```

### 6. Launch the Interactive Web Dashboard
```bash
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser!

---

## 💼 Alignment with Management Consulting Requirements (PwC / Big 4)

| Consulting Competency | Technical Implementation in This Project |
| :--- | :--- |
| **AI Fluency** | Hybrid RAG architecture + Pydantic structured output + local vector search |
| **Human-AI Collaboration** | Quarantined approval workflow ensuring human sign-off before database updates |
| **Data Analytics** | Pandas-powered bottleneck detection and milestone slippage math |
| **Knowledge Management** | Semantic document indexing across transcripts, SLAs, and compliance specs |
| **Executive Reporting** | Automated multi-source synthesis producing board-ready status memos |