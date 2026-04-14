# 🔍 GitHub Leak Scanner

A **FastAPI-based security tool** that automatically scans public GitHub repositories for sensitive information leaks — such as API keys, passwords, and credentials — using regex pattern matching and risk-based scoring.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Installation & Setup](#installation--setup)
- [API Endpoints](#api-endpoints)
- [How the Scanner Works](#how-the-scanner-works)
- [Database Schema](#database-schema)
- [Risk Scoring & Severity](#risk-scoring--severity)
- [Usage Examples](#usage-examples)

---

## 🧭 Overview

Leaked secrets in source code (API keys, database passwords, access tokens) are one of the most common causes of security breaches. **GitHub Leak Scanner** addresses this by providing a REST API that:

1. Accepts a GitHub repository URL.
2. Downloads the repository as a ZIP archive.
3. Scans every relevant source file for sensitive patterns.
4. Stores all findings in a SQLite database with risk scores and severity levels.
5. Exposes query endpoints to retrieve scan results.

The entire scanning process runs **asynchronously in the background** using FastAPI's `BackgroundTasks`, so the API responds immediately while the scan happens behind the scenes.

---

## ✨ Features

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

## 🏗️ Architecture

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

### Request Flow

1. **Client** sends `POST /scan/` with a GitHub repo URL.
2. **Scan Router** creates (or resets) the repository record in the DB with status `PENDING`, then schedules a background task.
3. **Scanner Engine** (`scanner.py`) runs in the background:
   - Downloads the repo as a ZIP from GitHub.
   - Extracts it to a temp directory.
   - Walks through all supported files, matching lines against regex patterns.
   - For each match, calculates a risk score and severity, then saves a `Leak` record.
   - Updates the repo status to `COMPLETED` (or `FAILED` on error).
4. **Client** polls `GET /repos/{id}` or `GET /repos/{id}/leaks` to check results.

---

## 📁 Project Structure

```
github-leak-scanner/
│
├── main.py              # FastAPI application entry point & router registration
├── database.py          # SQLAlchemy engine, session factory, and Base declaration
├── models.py            # ORM models (Repository, Leak) and enums (ScanStatus, SeverityLevel)
├── schemas.py           # Pydantic schemas for request/response validation
├── scanner.py           # Core scanning engine — download, extract, pattern match, score
├── requirements.txt     # Python dependencies
├── scanner.db           # SQLite database file (auto-created at runtime)
│
└── routers/
    ├── scan.py          # POST /scan/ — trigger a new scan
    └── repos.py         # GET /repos/ — query repositories and leaks
```

### File-by-File Breakdown

#### `main.py` — Application Entry Point
- Creates the FastAPI app instance with title `"GitHub Leak Scanner API"`.
- Calls `models.Base.metadata.create_all()` to auto-create database tables on startup.
- Registers the `scan` and `repos` routers.
- Serves a root welcome endpoint at `GET /`.

#### `database.py` — Database Configuration
- Configures a **SQLite** database at `./scanner.db`.
- Uses `check_same_thread=False` to allow multi-threaded access (required for background tasks).
- Provides a `get_db()` dependency that yields a session and ensures cleanup via `finally`.

#### `models.py` — SQLAlchemy ORM Models

Two tables are defined:

| Model | Table | Fields | Purpose |
|---|---|---|---|
| `Repository` | `repositories` | `id`, `url` (unique), `status` | Tracks each scanned repository and its scan state |
| `Leak` | `leaks` | `id`, `repository_id` (FK), `file_path`, `line_number`, `snippet`, `secret_type`, `severity`, `risk_score` | Stores each detected secret with context |

Two enums:
- **`ScanStatus`**: `PENDING` → `SCANNING` → `COMPLETED` / `FAILED`
- **`SeverityLevel`**: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`

#### `schemas.py` — Pydantic Validation Schemas

| Schema | Type | Purpose |
|---|---|---|
| `RepositoryCreate` | Request | Validates incoming scan requests (expects an `HttpUrl`) |
| `Repository` | Response | Full repository data including nested leaks |
| `Leak` | Response | Individual leak finding with all metadata |

All response schemas use `from_attributes = True` to enable ORM-mode serialization.

#### `scanner.py` — Scanning Engine

The heart of the application. It handles:

1. **Pattern Definitions** — Three regex patterns:
   - `AWS_KEY`: Matches AWS access key IDs (`AKIA` prefix + 16 alphanumeric chars).
   - `GENERIC_API_KEY`: Matches `api_key=`, `apikey=`, or `secret=` followed by a quoted token (16+ chars).
   - `DB_PASSWORD`: Matches `password=` or `passwd=` followed by a quoted value.

2. **`fetch_and_scan(repo_id)`** — The main background task:
   - Opens its own DB session (can't share the request's session across threads).
   - Parses `owner/repo` from the GitHub URL using regex.
   - Downloads the ZIP archive (tries `main` branch first, falls back to `master`).
   - Extracts and recursively walks the directory.
   - For each supported file, reads line-by-line and runs all patterns.
   - Creates `Leak` records for every match with calculated risk and severity.

3. **`calculate_risk()`** — Returns a risk score based on secret type:
   - AWS keys → `0.95` (Critical)
   - Generic API keys → `0.80` (High)
   - Everything else → `0.50` (Medium)

4. **`get_severity()`** — Maps risk score to severity level:
   - `≥ 0.9` → `CRITICAL`
   - `≥ 0.7` → `HIGH`
   - `≥ 0.4` → `MEDIUM`
   - `< 0.4` → `LOW`

#### `routers/scan.py` — Scan Trigger Endpoint

- `POST /scan/` — Accepts a JSON body with a `url` field.
  - If the URL is new, creates a `Repository` record with `PENDING` status.
  - If the URL already exists, resets its status to `PENDING` and **deletes all previous leaks** (re-scan).
  - Schedules `fetch_and_scan()` as a `BackgroundTask`.
  - Returns the repository object immediately.

#### `routers/repos.py` — Query Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/repos/` | GET | List all repositories (with pagination: `skip`, `limit`) |
| `/repos/{repo_id}` | GET | Get a single repository by ID (includes nested leaks) |
| `/repos/{repo_id}/leaks` | GET | Get all leaks for a specific repository |
| `/repos/leaks/all` | GET | List all leaks across all repositories (with pagination) |

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Web Framework | [FastAPI](https://fastapi.tiangolo.com/) 0.110.0 |
| ASGI Server | [Uvicorn](https://www.uvicorn.org/) 0.27.1 |
| Validation | [Pydantic](https://docs.pydantic.dev/) 2.6.3 |
| ORM | [SQLAlchemy](https://www.sqlalchemy.org/) 2.0.28 |
| Database | SQLite (via SQLAlchemy) |
| HTTP Client | `urllib.request` (stdlib) |
| Language | Python 3.10+ |

---

## 🚀 Installation & Setup

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

## 📡 API Endpoints

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

## ⚙️ How the Scanner Works

```
GitHub URL  ──▶  Parse owner/repo  ──▶  Download ZIP (main → master fallback)
                                              │
                                              ▼
                                     Extract to temp dir
                                              │
                                              ▼
                                    Walk all supported files
                                   (.py, .js, .json, .env, etc.)
                                              │
                                              ▼
                                  For each line in each file:
                                   ┌─ Match AWS_KEY pattern
                                   ├─ Match GENERIC_API_KEY pattern
                                   └─ Match DB_PASSWORD pattern
                                              │
                                       On match found:
                                              │
                                              ▼
                                   calculate_risk(secret_type)
                                              │
                                              ▼
                                   get_severity(risk_score)
                                              │
                                              ▼
                                   Save Leak record to DB
                                              │
                                              ▼
                                  Update repo status → COMPLETED
```

### Detection Patterns

| Pattern Name | Regex | What it Catches |
|---|---|---|
| `AWS_KEY` | `AKIA[0-9A-Z]{16}` | AWS Access Key IDs (always start with `AKIA`) |
| `GENERIC_API_KEY` | `(?:api_key\|apikey\|secret)[=:]\s*["']([a-zA-Z0-9_\-\.]{16,})["']` | API keys and secrets assigned in code |
| `DB_PASSWORD` | `(?:password\|passwd)[=:]\s*["'](.*?)["']` | Database passwords and credentials |

All patterns are case-insensitive.

---

## 🗄️ Database Schema

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

## 📊 Risk Scoring & Severity

### Risk Score Assignment

| Secret Type | Risk Score | Rationale |
|---|---|---|
| `AWS_KEY` | **0.95** | AWS keys grant direct cloud infrastructure access |
| `GENERIC_API_KEY` | **0.80** | API keys can expose services and data |
| `DB_PASSWORD` | **0.50** | Passwords may be placeholders or dev-only |

### Severity Thresholds

| Risk Score Range | Severity Level |
|---|---|
| `≥ 0.90` | 🔴 **CRITICAL** |
| `0.70 – 0.89` | 🟠 **HIGH** |
| `0.40 – 0.69` | 🟡 **MEDIUM** |
| `< 0.40` | 🟢 **LOW** |

---

## 💡 Usage Examples

### Using `curl`

**Trigger a scan:**
```bash
curl -X POST http://127.0.0.1:8000/scan/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/octocat/Hello-World"}'
```

**Check scan results:**
```bash
curl http://127.0.0.1:8000/repos/1
```

**Get all leaks:**
```bash
curl http://127.0.0.1:8000/repos/leaks/all
```

### Using Python `requests`

```python
import requests
import time

# Trigger scan
response = requests.post(
    "http://127.0.0.1:8000/scan/",
    json={"url": "https://github.com/octocat/Hello-World"}
)
repo = response.json()
print(f"Scan triggered — Repo ID: {repo['id']}, Status: {repo['status']}")

# Poll until complete
while True:
    time.sleep(5)
    result = requests.get(f"http://127.0.0.1:8000/repos/{repo['id']}").json()
    print(f"Status: {result['status']}")
    if result["status"] in ("COMPLETED", "FAILED"):
        break

# Print findings
for leak in result["leaks"]:
    print(f"[{leak['severity']}] {leak['secret_type']} in {leak['file_path']}:{leak['line_number']}")
    print(f"  Snippet: {leak['snippet']}")
    print(f"  Risk: {leak['risk_score']}")
```

---

## 📝 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

**Disclaimer**: This project is for educational and internal security auditing purposes. Always obtain proper authorization before scanning repositories you do not own.

