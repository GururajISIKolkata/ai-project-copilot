from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Float
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()
class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    client = Column(String(100), nullable=False)
    status = Column(String(50), default="On Track")
    start_date = Column(DateTime, default=datetime.utcnow)
    target_end_date = Column(DateTime, nullable=False)
    budget = Column(Float, default=0.0)

    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(200), nullable=False)
    owner = Column(String(100), nullable=False)
    priority = Column(String(20), default="Medium")
    status = Column(String(50), default="Pending")
    deadline = Column(DateTime, nullable=False)
    depends_on_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)

    project = relationship("Project", back_populates="tasks")
    dependency = relationship("Task", remote_side=[id])


class PendingApproval(Base):
    __tablename__ = "pending_approvals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action_type = Column(String(50), nullable=False)
    source = Column(String(100), nullable=False)
    details_json = Column(Text, nullable=False)
    ai_reasoning = Column(Text, nullable=True)
    status = Column(String(20), default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)

DATABASE_URL = "sqlite:///project_copilot.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully: project_copilot.db")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()           