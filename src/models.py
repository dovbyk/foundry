#This defines our job table 

from sqlalchemy import Column, Integer, String, DateTime, Text
from .database import Base
import datetime

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, index=True, unique=True, nullable=False)
    status = Column(String, default="PENDING") # PENDING, PROCESSING, COMPLETED, FAILED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    result_file_path = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)

