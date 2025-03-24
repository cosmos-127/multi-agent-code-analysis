# File for SQLAlchemy models

from sqlalchemy import Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.sql import func
from database import Base

class CodeAnalysisResult(Base):
    __tablename__ = "code_analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    complexity_score = Column(Integer)
    analysis_report = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
