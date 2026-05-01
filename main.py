from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import engine
import models
from routers import scan, repos
import os

# Initialize DB tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="RepoShield-Analyzer API", version="1.0.0")

# Mount static files
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(scan.router)
app.include_router(repos.router)

@app.get("/")
def read_root():
    return FileResponse("static/index.html")
