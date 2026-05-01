# RepoShield-Analyzer | GitHub Secret Intelligence

A **FastAPI-powered security tool** designed to automatically detect sensitive information leaks — such as API keys, passwords, and credentials — in public GitHub repositories with  responsive web interface.

---



## Overview

Leaked secrets in source code (AWS keys, database passwords, access tokens) are major security risks. **RepoShield-Analyzer** provides an end-to-end solution to identify these leaks before they are exploited.

The tool downloads repositories, scans them line-by-line using optimized regex patterns, and provides a real-time dashboard to visualize the findings. Everything runs **asynchronously** to ensure a smooth, non-blocking user experience.

---

## Features

| Feature | Description |
|---|---|
| **Premium Web UI** | Modern dark-mode dashboard built with Vanilla HTML/CSS/JS |
| **Regex-based Detection** | Optimized patterns for AWS keys, generic API keys, and credentials |
| **Real-time Status** | Live updates on scan progress via background task polling |
| **Risk Scoring** | Automated calculation of risk (0.0–1.0) based on secret impact |
| **Leak Inspector** | View exact file paths, line numbers, and code snippets of detected leaks |
| **Background Scanning** | Non-blocking execution using FastAPI `BackgroundTasks` |
| **Multi-format Support** | Scans `.py`, `.js`, `.json`, `.env`, `.yml`, `.txt`, and more |

---

## Web Interface

The project now includes a stunning user interface served directly by the FastAPI backend.

- **Dashboard**: Track all your repository scans in one place.
- **Glassmorphism Design**: Modern aesthetics with vibrant gradients and dark mode.
- **Interactive Findings**: Click on any completed scan to open a detailed modal containing all detected leaks.
- **Polling Logic**: The UI automatically refreshes every 5 seconds to keep you updated on active scans.

---


## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/jan08-ux/RepoShield-Analyzer.git
cd RepoShield-Analyzer
```

### 2. Setup Virtual Environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
uvicorn main:app --reload
```

The application will be available at:
- **Web Interface**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/scan/` | Trigger a new repository scan |
| `GET` | `/repos/` | List all scanned repositories |
| `GET` | `/repos/{id}` | Get detailed info for a specific repo |
| `GET` | `/repos/{id}/leaks` | Get all findings for a specific repo |
| `GET` | `/repos/leaks/all` | Global list of all detected leaks |

---

## Risk Scoring & Severity

| Secret Type | Risk Score | Severity Level |
|---|---|---|
| **AWS Access Key** | 0.95 | 🔴 **CRITICAL** |
| **API/Secret Key** | 0.80 | 🟠 **HIGH** |
| **DB Password** | 0.50 | 🟡 **MEDIUM** |
| **Other Credentials** | < 0.40 | 🟢 **LOW** |

---


---

**Disclaimer**: This tool is for educational purposes and internal security auditing. Ensure you have permission to scan repositories that do not belong to you.
