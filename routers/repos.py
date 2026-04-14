from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas

router = APIRouter(prefix="/repos", tags=["Repositories"])

@router.get("/", response_model=List[schemas.Repository])
def get_repositories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Repository).offset(skip).limit(limit).all()

@router.get("/{repo_id}", response_model=schemas.Repository)
def get_repository(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(models.Repository).filter(models.Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo

@router.get("/{repo_id}/leaks", response_model=List[schemas.Leak])
def get_repository_leaks(repo_id: int, db: Session = Depends(get_db)):
    leaks = db.query(models.Leak).filter(models.Leak.repository_id == repo_id).all()
    return leaks

@router.get("/leaks/all", response_model=List[schemas.Leak])
def get_all_leaks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Leak).offset(skip).limit(limit).all()
