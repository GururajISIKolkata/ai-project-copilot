"""
app.py - Main Streamlit Web Application
Connects SQLite Database, Pandas Analytics, FAISS Vector Search, 
Pydantic Task Extractor, and Gemini RAG into a unified Executive Dashboard.
"""

import os
import json
from datetime import datetime
import streamlit as st
import pandas as pd

# Backend Engine Imports
from database import SessionLocal, Task, PendingApproval, Project
from analytics import (
    get_project_summary,
    get_completion_stats,
    get_overdue_tasks,
    get_bottlenecks,
    get_upcoming_deadlines,
    load_projects,
    load_tasks
)
from rag_engine import ask_project_copilot, load_and_chunk_file, build_vector_store
from ai_agents import (
    extract_tasks_from_transcript,
    stage_extracted_tasks_for_approval,
    summarize_meeting_transcript,
    generate_ai_risk_assessment
)
from reporter import compile_weekly_report

# ==============================================================================
# 1. PAGE CONFIGURATION & STYLING
# ==============================================================================
st.set_page_config(
    page_title="AI Project Copilot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom header styling
st.markdown("""
    <style>
    .main-title {
        font-size: 32px;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 5px;
    }
    .sub-title {
        font-size: 16px;
        color: #64748B;
        margin-bottom: 25px;
    }
    .risk-card {
        background-color: #FEF2F2;
        border-left: 5px solid #EF4444;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)


# ==============================================================================
# 2. SIDEBAR NAVIGATION & SYSTEM HEALTH
# ==============================================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/8644/8644485.png", width=70)
    st.title("AI Operations Copilot")
    st.caption("PwC / Consulting Business Assistant")
    st.divider()

    summary = get_project_summary()
    st.subheader("📌 Portfolio Overview")
    st.write(f"📁 **Active Projects:** {summary['total_projects']}")
    st.write(f"🟢 **On Track:** {summary['on_track']}")
    st.write(f"🟡 **At Risk:** {summary['at_risk']}")
    st.write(f"🔴 **Delayed:** {summary['delayed']}")

    st.divider()
    # Check pending approvals count
    db = SessionLocal()
    pending_count = db.query(PendingApproval).filter(PendingApproval.status == "PENDING").count()
    db.close()

    if pending_count > 0:
        st.warning(f"🔔 **{pending_count} AI actions** waiting for review!")
    else:
        st.success("✅ No pending reviews.")


# ==============================================================================
# 3. MAIN TABBED INTERFACE
# ==============================================================================
st.markdown('<div class="main-title">🚀 AI-Powered Business Operations Copilot</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Autonomous Project Management, Cascading Risk Detection & Governance Intelligence</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Executive Dashboard",
    "💬 Ask AI Copilot (RAG)",
    "📋 Human Approval Queue",
    "📤 Meeting Ingestion",
    "📝 Weekly Executive Report"
])


# ==============================================================================
# TAB 1: EXECUTIVE DASHBOARD
# ==============================================================================
with tab1:
    # 1. KPI Top Cards Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Projects", summary["total_projects"])
    with col2:
        st.metric("On Track", summary["on_track"], delta="Healthy", delta_color="normal")
    with col3:
        st.metric("At Risk", summary["at_risk"], delta="-1 Project", delta_color="inverse")
    with col4:
        overdue_df = get_overdue_tasks()
        st.metric("Overdue Tasks", len(overdue_df), delta=f"{len(overdue_df)} Late", delta_color="inverse")

    st.divider()

    # 2. AI Detected Risks & Cascading Bottlenecks Banner
    bottlenecks = get_bottlenecks()
    if bottlenecks:
        st.subheader("🚨 AI-Detected Cascading Bottlenecks")
        for b in bottlenecks:
            st.markdown(f"""
                <div class="risk-card">
                    <b>⚠ Critical Path Blockage Detected:</b><br>
                    {b['risk_message']}<br>
                    <small>Impact: Downstream deliverable '<b>{b['blocked_task']}</b>' cannot start.</small>
                </div>
            """, unsafe_allow_html=True)

    # 3. Two-Column Layout: Progress & Upcoming Deadlines
    c1, c2 = st.columns([1, 1])

    with c1:
        st.subheader("📈 Project Completion Status")
        stats = get_completion_stats()
        for s in stats:
            st.write(f"**{s['project_name']}**")
            st.progress(s["completion_percentage"] / 100.0)
            st.caption(f"{s['completion_percentage']}% complete ({s['completed_tasks']}/{s['total_tasks']} deliverables)")

    with c2:
        st.subheader("📅 Upcoming Deadlines (Next 14 Days)")
        upcoming = get_upcoming_deadlines(days_ahead=14)
        if len(upcoming) > 0:
            formatted_upcoming = upcoming.copy()
            formatted_upcoming["deadline"] = formatted_upcoming["deadline"].dt.strftime("%b %d, %Y")
            st.dataframe(
                formatted_upcoming[["title", "owner", "priority", "deadline", "status"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No deadlines in the next 14 days.")

    # 4. Overdue Tasks Table
    if len(overdue_df) > 0:
        st.subheader("⚠ Overdue Action Items")
        formatted_overdue = overdue_df.copy()
        formatted_overdue["deadline"] = formatted_overdue["deadline"].dt.strftime("%b %d, %Y")
        st.dataframe(
            formatted_overdue[["title", "owner", "priority", "deadline", "days_overdue"]],
            use_container_width=True,
            hide_index=True
        )


# ==============================================================================
# TAB 2: ASK AI COPILOT (RAG CHAT)
# ==============================================================================
with tab2:
    st.subheader("💬 Ask Project Copilot (RAG Knowledge Engine)")
    st.caption("Ask questions across meeting transcripts, client specifications, SLAs, and security requirements.")

    # Initialize session state for chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! I am your Business Operations Copilot. You can ask me anything about Project Alpha, meeting decisions, security rules, or delivery risks."
            }
        ]

    # Display chat messages from history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "sources" in msg and msg["sources"]:
                st.caption(f"📌 Sources: {', '.join(msg['sources'])}")

    # User input field
    if user_query := st.chat_input("Ask a question (e.g., 'What are our encryption requirements?' or 'What did we decide about the API delay?')"):
        # Display user message
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        # Generate response using RAG
        with st.chat_message("assistant"):
            with st.spinner("Searching project knowledge base..."):
                response_data = ask_project_copilot(user_query)
                st.markdown(response_data["answer"])
                if response_data["sources"]:
                    st.caption(f"📌 Sources: {', '.join(response_data['sources'])}")

        st.session_state.messages.append({
            "role": "assistant",
            "content": response_data["answer"],
            "sources": response_data["sources"]
        })


# ==============================================================================
# TAB 3: HUMAN APPROVAL QUEUE (HITL)
# ==============================================================================
with tab3:
    st.subheader("📋 Human-in-the-Loop Review & Approval Queue")
    st.caption("AI proposes actions extracted from meetings or risk engines. Managers review and sign off before changes affect production.")

    db = SessionLocal()
    pending_items = db.query(PendingApproval).filter(PendingApproval.status == "PENDING").all()

    if not pending_items:
        st.success("🎉 All caught up! No pending AI recommendations to review.")
    else:
        st.info(f"You have **{len(pending_items)} item(s)** awaiting decision:")

        for item in pending_items:
            with st.expander(f"Action: **{item.action_type}** | Source: *{item.source}*", expanded=True):
                details = json.loads(item.details_json)

                colA, colB = st.columns([2, 1])
                with colA:
                    st.markdown(f"**Proposed Task:** {details.get('title', 'N/A')}")
                    st.write(f"👤 **Assignee:** {details.get('owner', 'N/A')}")
                    st.write(f"📅 **Deadline:** {details.get('deadline', 'N/A')} | 🏷 **Priority:** {details.get('priority', 'Medium')}")
                    st.write(f"💡 **AI Reasoning:** {item.ai_reasoning}")

                with colB:
                    st.write("**Manager Decision:**")
                    
                    # Approve Button
                    if st.button("✅ Approve & Create Task", key=f"app_{item.id}", use_container_width=True):
                        # 1. Find target project
                        proj_name = details.get("project_name", "Project Alpha")
                        project_record = db.query(Project).filter(Project.name.ilike(f"%{proj_name}%")).first()
                        target_proj_id = project_record.id if project_record else 1

                        # 2. Create the real task in the tasks table!
                        new_task = Task(
                            project_id=target_proj_id,
                            title=details.get("title"),
                            owner=details.get("owner"),
                            priority=details.get("priority", "Medium"),
                            status="Pending",
                            deadline=datetime.strptime(details.get("deadline"), "%Y-%m-%d")
                        )
                        db.add(new_task)

                        # 3. Mark approval as APPROVED
                        item.status = "APPROVED"
                        db.commit()
                        st.success(f"Task '{details.get('title')}' approved and created!")
                        st.rerun()

                    # Reject Button
                    if st.button("❌ Reject Action", key=f"rej_{item.id}", use_container_width=True):
                        item.status = "REJECTED"
                        db.commit()
                        st.warning("Action rejected.")
                        st.rerun()

    db.close()


# ==============================================================================
# TAB 4: MEETING INGESTION & DOCUMENT UPLOAD
# ==============================================================================
with tab4:
    st.subheader("📤 Ingest New Meeting Transcripts & Project Documents")
    st.caption("Upload text transcripts (.txt) or project specifications (.pdf). The AI will chunk, embed, and extract actionable tasks automatically.")

    uploaded_file = st.file_uploader("Choose a .txt or .pdf document", type=["txt", "pdf"])

    if uploaded_file is not None:
        file_path = os.path.join("sample_data", uploaded_file.name)
        
        # Save file locally
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"File uploaded successfully: `{uploaded_file.name}`")

        col_x, col_y = st.columns(2)
        with col_x:
            if st.button("🤖 1. Extract Tasks & Stage for Approval", use_container_width=True):
                with st.spinner("AI parsing transcript for tasks..."):
                    with open(file_path, "r", encoding="utf-8") as f:
                        text_content = f.read()
                    extracted_list = extract_tasks_from_transcript(text_content)
                    stage_extracted_tasks_for_approval(extracted_list, source_name=uploaded_file.name)
                st.success(f"Extracted and staged {len(extracted_list.tasks)} tasks! Check the 'Human Approval Queue' tab.")

        with col_y:
            if st.button("🧠 2. Index into FAISS Vector Database", use_container_width=True):
                with st.spinner("Chunking & computing vector embeddings..."):
                    build_vector_store()
                st.success("Knowledge base updated! You can now ask questions about this document in Tab 2.")


# ==============================================================================
# TAB 5: WEEKLY EXECUTIVE REPORT
# ==============================================================================
with tab5:
    st.subheader("📝 Automated Executive Status Report")
    st.caption("One-click synthesis combining live SQL analytics, active bottlenecks, and contractual knowledge.")

    if st.button("⚡ Generate Fresh Weekly Report", type="primary"):
        with st.spinner("Synthesizing multi-source executive report via Gemini 3.8 Flash..."):
            report_text = compile_weekly_report()
            st.session_state["latest_report"] = report_text
            st.success("Weekly Report compiled successfully!")

    if "latest_report" in st.session_state:
        st.download_button(
            label="📥 Download Report as Markdown (.md)",
            data=st.session_state["latest_report"],
            file_name=f"weekly_report_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown"
        )
        st.markdown(st.session_state["latest_report"])
    elif os.path.exists("weekly_report_latest.md"):
        with open("weekly_report_latest.md", "r", encoding="utf-8") as f:
            saved_report = f.read()
        st.download_button(
            label="📥 Download Saved Report (.md)",
            data=saved_report,
            file_name="weekly_report_latest.md",
            mime="text/markdown"
        )
        st.markdown(saved_report)