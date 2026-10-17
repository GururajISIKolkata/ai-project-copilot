"""
reporter.py - Automated Weekly Executive Report Generator
Synthesizes structured metrics (SQL/Pandas) with unstructured contract/meeting context (FAISS)
to produce an executive-ready weekly status report in Markdown format.
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from analytics import (
    get_project_summary,
    get_completion_stats,
    get_overdue_tasks,
    get_bottlenecks,
    get_upcoming_deadlines
)
from rag_engine import search_similar_documents

load_dotenv()

# ==============================================================================
# 1. LLM CONFIGURATION (Gemini 3.8 Flash)
# ==============================================================================
llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    temperature=0.1,  # Low temperature for factual precision
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

# ==============================================================================
# 2. EXECUTIVE REPORT PROMPT TEMPLATE
# ==============================================================================
WEEKLY_REPORT_PROMPT_TEMPLATE = """You are a Senior Engagement Director at a top-tier management consultancy.
Synthesize the following live project operational data and knowledge base context into a comprehensive, 
highly polished Weekly Executive Status Report.

=======================================================
LIVE OPERATIONAL METRICS (FROM SQL DATABASE):
=======================================================
1. Portfolio Health Summary:
{portfolio_summary}

2. Project Completion Percentages:
{completion_stats}

3. Overdue & Delayed Tasks:
{overdue_tasks}

4. Critical Dependency Bottlenecks:
{bottlenecks}

5. Upcoming Deadlines (Next 7-14 Days):
{upcoming_deadlines}

=======================================================
CONTRACTUAL & GOVERNANCE CONTEXT (FROM KNOWLEDGE BASE):
=======================================================
{contract_context}

=======================================================
INSTRUCTIONS & STRUCTURE:
=======================================================
Generate the report in clean GitHub-Flavored Markdown using these exact sections:

# 📊 WEEKLY EXECUTIVE ENGAGEMENT REPORT
**Reporting Period:** Week Ending {current_date}  
**Portfolio Health:** [Insert Overall Health: On Track / At Risk / Critical]

---

## 1. Executive Snapshot & RAG Status
- Concise narrative of portfolio health and primary operational focus this week.

## 2. Key Accomplishments This Period
- Summary of successfully completed milestones and deliverables.

## 3. Critical Path Slippages & Operational Bottlenecks
- Table or detailed breakdown of delayed deliverables, assigned owners, days late, and downstream impacts.

## 4. Immediate Milestone Horizon (Next 7–14 Days)
- Deliverables due in the upcoming sprint, owners, and readiness posture.

## 5. Contractual & SLA Exposure Analysis
- Synthesis connecting current technical delays to the client's hard go-live date and contractual penalties.

## 6. Recommended Leadership Interventions (Human-in-the-Loop)
- 3 to 4 concrete, actionable recommendations for engagement managers to approve/execute immediately.

Maintain an authoritative, direct, and solutions-oriented consulting tone.
"""

report_prompt = PromptTemplate(
    template=WEEKLY_REPORT_PROMPT_TEMPLATE,
    input_variables=[
        "portfolio_summary",
        "completion_stats",
        "overdue_tasks",
        "bottlenecks",
        "upcoming_deadlines",
        "contract_context",
        "current_date"
    ]
)


# ==============================================================================
# 3. REPORT SYNTHESIS ENGINE
# ==============================================================================
def compile_weekly_report() -> str:
    """
    Pulls structured data from analytics.py + unstructured data from rag_engine.py,
    prompts Gemini, and returns the full Markdown executive report.
    """
    print("📊 1. Pulling live relational data from SQL database via Pandas...")
    
    # 1. Pull metrics
    summary = get_project_summary()
    summary_text = (
        f"Total Active Projects: {summary['total_projects']} | "
        f"On Track: {summary['on_track']} | "
        f"At Risk: {summary['at_risk']} | "
        f"Delayed: {summary['delayed']}"
    )

    stats = get_completion_stats()
    stats_lines = [
        f"- {s['project_name']}: {s['completion_percentage']}% completed ({s['completed_tasks']}/{s['total_tasks']} deliverables)"
        for s in stats
    ]
    completion_text = "\n".join(stats_lines)

    overdue_df = get_overdue_tasks()
    if len(overdue_df) > 0:
        overdue_lines = [
            f"- '{row['title']}' | Owner: {row['owner']} | {row['days_overdue']} days overdue | Priority: {row['priority']}"
            for _, row in overdue_df.iterrows()
        ]
        overdue_text = "\n".join(overdue_lines)
    else:
        overdue_text = "No overdue tasks currently recorded."

    bottlenecks = get_bottlenecks()
    if bottlenecks:
        bottleneck_lines = [f"- {b['risk_message']}" for b in bottlenecks]
        bottleneck_text = "\n".join(bottleneck_lines)
    else:
        bottleneck_text = "No active dependency bottlenecks detected."

    upcoming_df = get_upcoming_deadlines(days_ahead=14)
    if len(upcoming_df) > 0:
        upcoming_lines = [
            f"- '{row['title']}' | Owner: {row['owner']} | Due: {row['deadline'].strftime('%b %d, %Y')} | Status: {row['status']}"
            for _, row in upcoming_df.iterrows()
        ]
        upcoming_text = "\n".join(upcoming_lines)
    else:
        upcoming_text = "No upcoming deadlines in the next 14 days."

    print("📚 2. Querying FAISS vector store for client governance & contractual mandates...")
    # 2. Query RAG knowledge base for governance rules
    contract_docs = search_similar_documents("cutover go-live deadline SLA penalties requirements", k=2)
    contract_text = "\n\n".join([f"[{os.path.basename(doc.metadata.get('source', 'Doc'))}]:\n{doc.page_content.strip()}" for doc in contract_docs])

    print("🤖 3. Synthesizing executive report via Google Gemini 3.8 Flash...")
    current_date_str = datetime.now().strftime("%B %d, %Y")

    # 3. Generate report via LLM
    final_prompt = report_prompt.format(
        portfolio_summary=summary_text,
        completion_stats=completion_text,
        overdue_tasks=overdue_text,
        bottlenecks=bottleneck_text,
        upcoming_deadlines=upcoming_text,
        contract_context=contract_text,
        current_date=current_date_str
    )

    response = llm.invoke(final_prompt)
    report_content = response.content.strip()

    # 4. Save to markdown file for instant viewing/sharing
    output_filename = "weekly_report_latest.md"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"💾 4. Weekly Report saved to: '{output_filename}'")
    return report_content


# ==============================================================================
# 4. TEST HARNESS & DEMO
# ==============================================================================
if __name__ == "__main__":
    print("=" * 65)
    print("       GENERATING AUTOMATED EXECUTIVE WEEKLY STATUS REPORT")
    print("=" * 65)

    report_markdown = compile_weekly_report()
    
    print("\n" + "=" * 65)
    print("📄 PREVIEW OF GENERATED REPORT:")
    print("=" * 65 + "\n")
    print(report_markdown[:1500] + "\n\n[... Full report saved in weekly_report_latest.md ...]")