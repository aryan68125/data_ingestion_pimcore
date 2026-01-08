from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from db.database import Base

class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    job_id = Column(String, primary_key=True, index=True)
    file_path = Column(String, nullable=False)
    status = Column(String, default="RUNNING")

    total_chunks = Column(Integer, default=0)
    total_records = Column(Integer, default=0)
    total_memory_bytes = Column(Integer, default=0)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class IngestionChunk(Base):
    __tablename__ = "ingestion_chunks"

    id = Column(Integer, primary_key=True)
    job_id = Column(String, ForeignKey("ingestion_jobs.job_id"))
    chunk_index = Column(Integer)
    records_in_chunk = Column(Integer)
    memory_bytes = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())