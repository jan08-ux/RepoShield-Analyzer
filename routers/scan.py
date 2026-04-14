from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from scanner import fetch_and_scan

router = APIRouter(prefix="/scan", tags=["Scanner"])

@router.post("/", response_model=schemas.Repository)
def trigger_scan(repo_in: schemas.RepositoryCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    url_str = str(repo_in.url)
    
    # Check if exists
    db_repo = db.query(models.Repository).filter(models.Repository.url == url_str).first()
    if not db_repo:
        db_repo = models.Repository(url=url_str, status=models.ScanStatus.PENDING)
        db.add(db_repo)
        db.commit()
        db.refresh(db_repo)
    else:
        db_repo.status = models.ScanStatus.PENDING
        # Clear old leaks
        db.query(models.Leak).filter(models.Leak.repository_id == db_repo.id).delete()
        db.commit()

    background_tasks.add_task(fetch_and_scan, db_repo.id)
    return db_repo
