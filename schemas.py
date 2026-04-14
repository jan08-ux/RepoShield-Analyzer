from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from models import ScanStatus, SeverityLevel

class RepositoryCreate(BaseModel):
    url: HttpUrl

class LeakBase(BaseModel):
    file_path: str
    line_number: int
    snippet: str
    secret_type: str
    severity: SeverityLevel
    risk_score: float

class Leak(LeakBase):
    id: int
    repository_id: int

    class Config:
        from_attributes = True

class Repository(BaseModel):
    id: int
    url: HttpUrl
    status: ScanStatus
    leaks: List[Leak] = []

    class Config:
        from_attributes = True
