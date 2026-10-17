"""
seed_data.py - Populates the database with realistic consulting projects and tasks.
"""

from datetime import datetime, timedelta
from database import init_db, SessionLocal, Project, Task, PendingApproval

def seed():
    # 1. Initialize tables
    init_db()
    
    db = SessionLocal()
    
    # Clear existing data to avoid duplicates
    db.query(PendingApproval).delete()
    db.query(Task).delete()
    db.query(Project).delete()
    db.commit()

    now = datetime.now()

    # 2. Create Project 1: Enterprise ERP Upgrade
    proj1 = Project(
        name="Project Alpha: Enterprise ERP Migration",
        client="Bharat Financial Group",   # (was Acme Financial Group)
        status="At Risk",
        start_date=now - timedelta(days=30),
        target_end_date=now + timedelta(days=60),
        budget=250000.0
    )
    
    # Create Project 2: Customer Portal Modernization
    proj2 = Project(
        name="Project Beta: Customer Portal Modernization",
        client="Nexus Healthcare",
        status="On Track",
        start_date=now - timedelta(days=15),
        target_end_date=now + timedelta(days=45),
        budget=180000.0
    )

    db.add_all([proj1, proj2])
    db.commit()

    # 3. Tasks for Project Alpha
    t1 = Task(
        project_id=proj1.id,
        title="Architecture Design & Security Review",
        owner="Sneha Patel",
        priority="High",
        status="Completed",
        deadline=now - timedelta(days=10)
    )
    
    t2 = Task(
        project_id=proj1.id,
        title="Core API Integration",
        owner="Rohan Verma",
        priority="High",
        status="Delayed",
        deadline=now - timedelta(days=4)
    )
    
    db.add_all([t1, t2])
    db.commit()

    t3 = Task(
        project_id=proj1.id,
        title="User Acceptance Testing (UAT)",
        owner="Kavita Iyer",
        priority="High",
        status="In Progress",
        deadline=now + timedelta(days=7),
        depends_on_task_id=t2.id  # Critical dependency on Rohan's task!
    )

    t4 = Task(
        project_id=proj1.id,
        title="Data Migration & Validation",
        owner="Sneha Patel",
        priority="Medium",
        status="Pending",
        deadline=now + timedelta(days=14)
    )

    # 4. Tasks for Project Beta
    t5 = Task(
        project_id=proj2.id,
        title="Frontend Wireframes & Design Approval",
        owner="Arjun Kumar",
        priority="Medium",
        status="Completed",
        deadline=now - timedelta(days=5)
    )
    
    t6 = Task(
        project_id=proj2.id,
        title="Authentication & SSO Integration",
        owner="Arjun Kumar",
        priority="High",
        status="In Progress",
        deadline=now + timedelta(days=10)
    )

    t7 = Task(
        project_id=proj2.id,
        title="Patient Records API Development",
        owner="Priya Sharma",
        priority="High",
        status="Pending",
        deadline=now + timedelta(days=20)
    )

    db.add_all([t3, t4, t5, t6, t7])
    db.commit()

    # 5. Pending Approval Item (AI Suggested)
    pending_item = PendingApproval(
        action_type="CREATE_TASK",
        source="Meeting Transcript: Steering Committee Oct 05",
        details_json='{"project_name": "Project Alpha: Enterprise ERP Migration", "title": "Conduct Emergency API Bug Bash", "owner": "Rohan Verma", "priority": "High", "deadline": "2026-10-12"}',
        ai_reasoning="API Integration is 4 days delayed. Transcript notes team agreed to hold an emergency bug bash session led by Rohan Verma.",
        status="PENDING"
    )

    db.add(pending_item)
    db.commit()
    db.close()
    print("✅ Seed data updated with Indian team members!")

if __name__ == "__main__":
    seed()