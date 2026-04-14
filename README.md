# RepoShield Analyzer: Automated GitHub Secret Intelligence


A **FastAPI-based security tool** that automatically scans public GitHub repositories for sensitive information leaks — such as API keys, passwords, and credentials — using regex pattern matching and risk-based scoring.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)

---

## Overview

Leaked secrets in source code (API keys, database passwords, access tokens) are one of the most common causes of security breaches. **GitHub Leak Scanner** addresses this by providing a REST API that:

1. Accepts a GitHub repository URL.
2. Downloads the repository as a ZIP archive.
3. Scans every relevant source file for sensitive patterns.
4. Stores all findings in a SQLite database with risk scores and severity levels.
5. Exposes query endpoints to retrieve scan results.

The entire scanning process runs **asynchronously in the background** using FastAPI's `BackgroundTasks`, so the API responds immediately while the scan happens behind the scenes.

---

## Features

| Feature | Description |
|---|---|
| **Regex-based detection** | Pre-built patterns for AWS keys, generic API keys, and database passwords |
| **Risk scoring** | Each finding receives a risk score (0.0–1.0) based on the secret type |
| **Severity classification** | Findings are classified as `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL` |
| **Background scanning** | Scans run asynchronously — the API returns immediately after triggering |
| **Scan status tracking** | Track scan progress via `PENDING → SCANNING → COMPLETED / FAILED` states |
| **Re-scan support** | Submitting the same URL clears old leaks and starts a fresh scan |
| **Branch fallback** | Automatically tries `master` branch if `main` doesn't exist |
| **Multi-format support** | Scans `.py`, `.js`, `.json`, `.env`, `.yml`, `.yaml`, `.txt`, `.md`, `.html` files |
| **Interactive API docs** | Auto-generated Swagger UI at `/docs` |

---

## Architecture

```
┌─────────────┐       POST /scan        ┌──────────────────┐
│   Client     │ ─────────────────────▶ │   FastAPI App     │
│  (Browser /  │                        │   (main.py)       │
│   curl)      │ ◀───────────────────── │                   │
└─────────────┘   Immediate response    │  ┌─────────────┐  │
                   (repo + PENDING)     │  │ scan.router  │  │
                                        │  └──────┬──────┘  │
                                        │         │         │
                                        │  BackgroundTask   │
                                        │         │         │
                                        │  ┌──────▼──────┐  │
                                        │  │  scanner.py  │──│──▶ GitHub (download ZIP)
                                        │  │  (engine)    │  │
                                        │  └──────┬──────┘  │
                                        │         │         │
                                        │  ┌──────▼──────┐  │
                                        │  │ scanner.db   │  │
                                        │  │  (SQLite)    │  │
                                        │  └─────────────┘  │
                                        └──────────────────┘

                    GET /repos/*
┌─────────────┐  ─────────────────────▶  ┌─────────────────┐
│   Client     │                         │  repos.router    │──▶ Query DB
│              │ ◀─────────────────────  │                  │
└─────────────┘   JSON (repos/leaks)     └─────────────────┘
```



## Project Structure

```
github-leak-scanner/
│
├── main.py              
├── database.py         
├── models.py            
├── schemas.py           
├── scanner.py           
├── requirements.txt   
├── scanner.db           
│
└── routers/
    ├── scan.py          
    └── repos.py         
```

---

##  Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/github-leak-scanner.git
cd github-leak-scanner
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Server

```bash
uvicorn main:app --reload
```

The server starts at **http://127.0.0.1:8000**.

### 5. Open the API Docs

Navigate to **http://127.0.0.1:8000/docs** — FastAPI auto-generates an interactive Swagger UI where you can test all endpoints.

---

## API Endpoints

### Trigger a Scan

```http
POST /scan/
Content-Type: application/json

{
  "url": "https://github.com/owner/repo-name"
}
```

**Response** (immediate):
```json
{
  "id": 1,
  "url": "https://github.com/owner/repo-name",
  "status": "PENDING",
  "leaks": []
}
```

### List All Repositories

```http
GET /repos/?skip=0&limit=100
```

### Get a Specific Repository

```http
GET /repos/1
```

**Response** (after scan completes):
```json
{
  "id": 1,
  "url": "https://github.com/owner/repo-name",
  "status": "COMPLETED",
  "leaks": [
    {
      "id": 1,
      "repository_id": 1,
      "file_path": "/repo-name-main/config.py",
      "line_number": 12,
      "snippet": "AWS_ACCESS_KEY = 'AKIAIOSFODNN7EXAMPLE'",
      "secret_type": "AWS_KEY",
      "severity": "CRITICAL",
      "risk_score": 0.95
    }
  ]
}
```

### Get Leaks for a Repository

```http
GET /repos/1/leaks
```

### Get All Leaks (Global)

```http
GET /repos/leaks/all?skip=0&limit=100
```

---



## Database Schema

```
┌────────────────────────┐       ┌────────────────────────────────┐
│     repositories       │       │            leaks               │
├────────────────────────┤       ├────────────────────────────────┤
│ id      INTEGER (PK)   │───┐   │ id              INTEGER (PK)   │
│ url     STRING (UNIQUE) │   │   │ repository_id   INTEGER (FK)   │
│ status  ENUM           │   └──▶│ file_path       STRING         │
│          (PENDING,     │       │ line_number     INTEGER        │
│           SCANNING,    │       │ snippet         STRING         │
│           COMPLETED,   │       │ secret_type     STRING         │
│           FAILED)      │       │ severity        ENUM           │
└────────────────────────┘       │                 (LOW, MEDIUM,  │
                                 │                  HIGH, CRITICAL)│
                                 │ risk_score      FLOAT          │
                                 └────────────────────────────────┘
```

**Relationship**: One Repository → Many Leaks (one-to-many via `repository_id` foreign key).


---

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

**Disclaimer**: This project is for educational and internal security auditing purposes. Always obtain proper authorization before scanning repositories you do not own.

