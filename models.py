from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum
from database import Base

class ScanStatus(str, enum.Enum):
    PENDING = "PENDING"
    SCANNING = "SCANNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class SeverityLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True)
    status = Column(Enum(ScanStatus), default=ScanStatus.PENDING)
    
    leaks = relationship("Leak", back_populates="repository")

class Leak(Base):
    __tablename__ = "leaks"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"))
    file_path = Column(String)
    line_number = Column(Integer)
    snippet = Column(String)
    secret_type = Column(String)
    severity = Column(Enum(SeverityLevel), default=SeverityLevel.MEDIUM)
    risk_score = Column(Float, default=0.0)

    repository = relationship("Repository", back_populates="leaks")
