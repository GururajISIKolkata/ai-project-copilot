import pandas as pd
from datetime import datetime, timedelta
from database import engine

def load_projects():
    """Load all projects from the database into a Pandas DataFrame."""
    df = pd.read_sql("SELECT * FROM projects", engine)
    return df


def load_tasks():
    """Load all tasks from the database into a Pandas DataFrame."""
    df = pd.read_sql("SELECT * FROM tasks", engine)
    # Convert deadline column from string to proper datetime format
    df["deadline"] = pd.to_datetime(df["deadline"])
    return df

def get_project_summary():
    """
    Returns a summary of project health:
    - Total projects
    - How many are On Track, At Risk, Delayed, Completed
    """
    df = load_projects()

    summary = {
        "total_projects": len(df),
        "on_track": len(df[df["status"] == "On Track"]),
        "at_risk": len(df[df["status"] == "At Risk"]),
        "delayed": len(df[df["status"] == "Delayed"]),
        "completed": len(df[df["status"] == "Completed"]),
    }

    return summary

def get_overdue_tasks():
    """
    Finds tasks that are PAST their deadline and NOT completed.
    A task is overdue when: deadline < today AND status != 'Completed'
    """
    df = load_tasks()
    now = datetime.now()

    overdue = df[
        (df["deadline"] < now) &           # Deadline has passed
        (df["status"] != "Completed")       # But task is NOT done
    ].copy()

    # Calculate how many days each task is overdue
    overdue["days_overdue"] = (now - overdue["deadline"]).dt.days

    return overdue[["id", "title", "owner", "priority", "deadline", "days_overdue"]]

def get_bottlenecks():
    """
    Finds tasks that are BLOCKED because the task they depend on is delayed.
    
    Example:
    Task 3 (UAT Testing) depends on Task 2 (API Integration)
    Task 2 is DELAYED
    Therefore Task 3 is BLOCKED — this is a bottleneck!
    """
    df = load_tasks()

    # Get only tasks that have a dependency (depends_on_task_id is not empty)
    dependent_tasks = df[df["depends_on_task_id"].notna()].copy()

    bottlenecks = []

    for _, task in dependent_tasks.iterrows():
        # Find the task that this task depends on
        dependency_id = int(task["depends_on_task_id"])
        parent_task = df[df["id"] == dependency_id]

        if parent_task.empty:
            continue

        parent = parent_task.iloc[0]

        # Check if the parent task is delayed or overdue
        is_parent_delayed = parent["status"] == "Delayed"
        is_parent_overdue = (
            parent["deadline"] < datetime.now() and 
            parent["status"] != "Completed"
        )

        if is_parent_delayed or is_parent_overdue:
            days_late = (datetime.now() - parent["deadline"]).days
            bottlenecks.append({
                "blocked_task": task["title"],
                "blocked_owner": task["owner"],
                "waiting_on_task": parent["title"],
                "waiting_on_owner": parent["owner"],
                "days_late": days_late,
                "risk_message": (
                    f"'{task['title']}' is BLOCKED because "
                    f"'{parent['title']}' (owned by {parent['owner']}) "
                    f"is {days_late} days overdue."
                )
            })

    return bottlenecks

def get_upcoming_deadlines(days_ahead=7):
    """
    Finds tasks with deadlines in the next N days that are NOT completed.
    Default: next 7 days.
    """
    df = load_tasks()
    now = datetime.now()
    future = now + timedelta(days=days_ahead)

    upcoming = df[
        (df["deadline"] >= now) &              # Deadline is in the future
        (df["deadline"] <= future) &            # But within the next N days
        (df["status"] != "Completed")           # And not already done
    ]

    return upcoming[["id", "title", "owner", "priority", "deadline", "status"]]

def get_completion_stats():
    """
    For each project, calculates what percentage of tasks are completed.
    """
    df = load_tasks()
    projects = load_projects()

    stats = []
    for _, project in projects.iterrows():
        project_tasks = df[df["project_id"] == project["id"]]
        total = len(project_tasks)

        if total == 0:
            continue

        completed = len(project_tasks[project_tasks["status"] == "Completed"])
        percentage = round((completed / total) * 100, 1)

        stats.append({
            "project_name": project["name"],
            "total_tasks": total,
            "completed_tasks": completed,
            "completion_percentage": percentage
        })

    return stats

if __name__ == "__main__":
    print("=" * 60)
    print("       PROJECT ANALYTICS REPORT")
    print("=" * 60)

    # 1. Project Summary
    print("\n--- Project Health Summary ---")
    summary = get_project_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # 2. Overdue Tasks
    print("\n--- Overdue Tasks ---")
    overdue = get_overdue_tasks()
    if len(overdue) > 0:
        for _, task in overdue.iterrows():
            print(f"  ⚠ {task['title']} | Owner: {task['owner']} | {task['days_overdue']} days overdue")
    else:
        print("  ✅ No overdue tasks!")

    # 3. Bottlenecks
    print("\n--- Dependency Bottlenecks ---")
    bottlenecks = get_bottlenecks()
    if bottlenecks:
        for b in bottlenecks:
            print(f"  🔴 {b['risk_message']}")
    else:
        print("  ✅ No bottlenecks detected!")

    # 4. Upcoming Deadlines
    print("\n--- Upcoming Deadlines (Next 7 Days) ---")
    upcoming = get_upcoming_deadlines()
    if len(upcoming) > 0:
        for _, task in upcoming.iterrows():
            print(f"  📅 {task['title']} | Owner: {task['owner']} | Due: {task['deadline'].strftime('%b %d')}")
    else:
        print("  No upcoming deadlines in the next 7 days.")

    # 5. Completion Stats
    print("\n--- Project Completion ---")
    stats = get_completion_stats()
    for s in stats:
        bar = "█" * int(s["completion_percentage"] // 10) + "░" * (10 - int(s["completion_percentage"] // 10))
        print(f"  {s['project_name']}")
        print(f"    [{bar}] {s['completion_percentage']}% ({s['completed_tasks']}/{s['total_tasks']} tasks)")

    print("\n" + "=" * 60)


