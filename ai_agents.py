"""
ai_agents.py - Complete AI Extraction, Summarization & Risk Engine
1. Task Extractor: Extracts structured action items into Pydantic schema.
2. Human-in-the-Loop Staging: Stages tasks in SQLite pending_approvals table.
3. Meeting Summarizer: Generates professional 4-section executive memos.
4. Cascading Risk Reasoner: Combines Pandas bottleneck data with RAG document rules.
"""

import os
import json
from typing import List, Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from database import SessionLocal, PendingApproval
from analytics import get_bottlenecks, get_overdue_tasks
from rag_engine import search_similar_documents

load_dotenv()

# ==============================================================================
# 1. LLM SETUP (Gemini 3.8 Flash)
# ==============================================================================
llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    temperature=0.1,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

# ==============================================================================
# 2. PYDANTIC SCHEMAS (STRUCTURED TASKS)
# ==============================================================================
class ExtractedTask(BaseModel):
    """Schema for an individual action item extracted by the AI."""
    title: str = Field(description="Clear title of the task (e.g., 'Lead Emergency API Bug Bash')")
    owner: str = Field(description="Full name of the team member assigned")
    deadline: str = Field(description="Deadline in YYYY-MM-DD format (year 2026)")
    priority: Literal["High", "Medium", "Low"] = Field(default="Medium", description="Urgency level")
    ai_reasoning: str = Field(description="Context and business rationale for this task")


class ExtractedTaskList(BaseModel):
    """Container schema holding multiple extracted tasks."""
    project_name: str = Field(description="Name of the project discussed")
    tasks: List[ExtractedTask] = Field(description="List of concrete action items")


structured_llm = llm.with_structured_output(ExtractedTaskList)

EXTRACTION_PROMPT_TEMPLATE = """You are an expert AI Business Operations Assistant.
Analyze the following meeting transcript and extract all concrete action items, assigned owners, deadlines, and priorities.

Rules:
1. Only extract concrete tasks assigned to a specific person.
2. Infer the date in YYYY-MM-DD format. The current year is 2026.
3. Determine priority based on deliverable criticality.
4. Provide clear reasoning explaining why this task was created.

Transcript Content:
----------------------------------------
{transcript_text}
----------------------------------------
"""

extraction_prompt = PromptTemplate(
    template=EXTRACTION_PROMPT_TEMPLATE,
    input_variables=["transcript_text"]
)
task_extraction_chain = extraction_prompt | structured_llm


def extract_tasks_from_transcript(transcript_text: str) -> ExtractedTaskList:
    """Extracts typed tasks from transcript text."""
    return task_extraction_chain.invoke({"transcript_text": transcript_text})


def stage_extracted_tasks_for_approval(extracted_data: ExtractedTaskList, source_name: str):
    """Stages tasks in SQLite 'pending_approvals' table for manager review."""
    db = SessionLocal()
    staged_count = 0
    try:
        for task in extracted_data.tasks:
            task_payload = {
                "project_name": extracted_data.project_name,
                "title": task.title,
                "owner": task.owner,
                "deadline": task.deadline,
                "priority": task.priority
            }
            approval_entry = PendingApproval(
                action_type="CREATE_TASK",
                source=f"Transcript: {source_name}",
                details_json=json.dumps(task_payload),
                ai_reasoning=task.ai_reasoning,
                status="PENDING"
            )
            db.add(approval_entry)
            staged_count += 1
        db.commit()
        print(f"✅ Successfully staged {staged_count} tasks in 'pending_approvals' queue!")
    except Exception as e:
        db.rollback()
        print(f"❌ Error staging tasks: {e}")
    finally:
        db.close()


# ==============================================================================
# 3. EXECUTIVE MEETING SUMMARIZER
# ==============================================================================
SUMMARY_PROMPT_TEMPLATE = """You are a Senior Engagement Manager at a top-tier management consultancy.
Summarize the following project meeting transcript into a structured, executive-ready briefing memo.

Structure your response using these exact Markdown sections:
### 1. Executive Summary
(2 to 3 sentences capturing the core status and primary takeaway)

### 2. Key Discussion Points
(Bulleted summary of what was debated and analyzed)

### 3. Critical Decisions Made
(Formal agreements reached during the meeting)

### 4. Identified Risks & Impediments
(Blockers, schema issues, timeline risks)

### 5. Agreed Next Steps & Deliverables
(High-level immediate action items)

Transcript:
----------------------------------------
{transcript_text}
----------------------------------------
"""

summary_prompt = PromptTemplate(
    template=SUMMARY_PROMPT_TEMPLATE,
    input_variables=["transcript_text"]
)

def summarize_meeting_transcript(transcript_text: str) -> str:
    """Generates an executive-level structured meeting summary memo."""
    formatted_prompt = summary_prompt.format(transcript_text=transcript_text)
    response = llm.invoke(formatted_prompt)
    return response.content.strip()


# ==============================================================================
# 4. MULTI-SOURCE CASCADING RISK REASONER
# ==============================================================================
RISK_SYNTHESIS_PROMPT = """You are an AI Risk & Governance Consultant.
Analyze the following live project health data:

1. SQL Database Analytics (Overdue Tasks & Dependency Bottlenecks):
----------------------------------------
{analytics_context}
----------------------------------------

2. Relevant Client Contract & Compliance Constraints (From Knowledge Base):
----------------------------------------
{contract_context}
----------------------------------------

Synthesize an Executive Risk Advisory Report.
Include:
- Impact Analysis: How the technical delays in SQL affect downstream testing and the client's hard go-live date.
- Contractual & SLA Exposure: What financial or governance penalties are at risk.
- Recommended Tactical Interventions: 3 concrete managerial steps to mitigate the delays.

Be direct, analytical, and professional."""

risk_prompt = PromptTemplate(
    template=RISK_SYNTHESIS_PROMPT,
    input_variables=["analytics_context", "contract_context"]
)

def generate_ai_risk_assessment() -> str:
    """
    Combines:
    1. Structured analytics from Pandas (bottlenecks, days late)
    2. Unstructured contractual rules from FAISS (penalties, cutover dates)
    3. LLM reasoning to synthesize a strategic risk briefing.
    """
    # 1. Pull hard numbers from Pandas
    bottlenecks = get_bottlenecks()
    overdue_df = get_overdue_tasks()

    analytics_lines = []
    if len(overdue_df) > 0:
        for _, row in overdue_df.iterrows():
            analytics_lines.append(
                f"- OVERDUE TASK: '{row['title']}' (Owner: {row['owner']}) is {row['days_overdue']} days late. Priority: {row['priority']}."
            )
    if bottlenecks:
        for b in bottlenecks:
            analytics_lines.append(f"- BOTTLENECK: {b['risk_message']}")

    analytics_context = "\n".join(analytics_lines) if analytics_lines else "No overdue tasks or bottlenecks."

    # 2. Pull contractual and go-live rules from FAISS vector store
    contract_docs = search_similar_documents("go-live deadline penalties cutover criteria SLA", k=2)
    contract_context = "\n\n".join([doc.page_content.strip() for doc in contract_docs])

    # 3. Feed both sources into Gemini LLM
    final_prompt = risk_prompt.format(
        analytics_context=analytics_context,
        contract_context=contract_context
    )
    response = llm.invoke(final_prompt)
    return response.content.strip()


# ==============================================================================
# 5. TEST HARNESS & DEMO
# ==============================================================================
if __name__ == "__main__":
    print("=" * 65)
    print("          TESTING AI MEETING SUMMARIZER & RISK REASONER")
    print("=" * 65)

    # Load sample transcript
    with open("sample_data/meeting_transcript_oct05.txt", "r", encoding="utf-8") as f:
        transcript = f.read()

    # Test 1: Executive Meeting Summary
    print("\n📝 1. GENERATING EXECUTIVE MEETING MEMO...")
    print("-" * 60)
    summary_memo = summarize_meeting_transcript(transcript)
    print(summary_memo)

    # Test 2: Multi-Source Risk Assessment (Pandas + FAISS + Gemini)
    print("\n" + "=" * 65)
    print("🚨 2. GENERATING MULTI-SOURCE EXECUTIVE RISK ADVISORY...")
    print("-" * 60)
    risk_advisory = generate_ai_risk_assessment()
    print(risk_advisory)
    print("\n" + "=" * 65)