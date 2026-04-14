from fastapi import FastAPI
from database import engine
import models
from routers import scan, repos

# Initialize DB tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="GitHub Leak Scanner API", version="1.0.0")

app.include_router(scan.router)
app.include_router(repos.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to GitHub Leak Scanner API"}
