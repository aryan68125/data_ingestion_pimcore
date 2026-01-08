from sqlalchemy.orm import Session
from db.models import IngestionJob, IngestionChunk

def create_job(db: Session, job_id: str, file_path: str):
    job = IngestionJob(
        job_id=job_id,
        file_path=file_path,
        status="RUNNING"
    )
    db.add(job)
    db.commit()
    return job


def add_chunk(
    db: Session,
    job_id: str,
    chunk_index: int,
    records: int,
    memory_bytes: int
):
    chunk = IngestionChunk(
        job_id=job_id,
        chunk_index=chunk_index,
        records_in_chunk=records,
        memory_bytes=memory_bytes
    )
    db.add(chunk)

    job = db.query(IngestionJob).filter_by(job_id=job_id).first()
    job.total_chunks += 1
    job.total_records += records
    job.total_memory_bytes += memory_bytes

    db.commit()


def mark_job_completed(db: Session, job_id: str):
    job = db.query(IngestionJob).filter_by(job_id=job_id).first()
    job.status = "COMPLETED"
    db.commit()
