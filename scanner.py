import re
import urllib.request
import zipfile
import tempfile
import os
from sqlalchemy.orm import Session
from models import Leak, SeverityLevel, Repository, ScanStatus

# Regex Patterns
PATTERNS = {
    "AWS_KEY": r"(?i)AKIA[0-9A-Z]{16}",
    "GENERIC_API_KEY": r"(?i)(?:api_key|apikey|secret)[=:]\s*[\"']([a-zA-Z0-9_\-\.]{16,})[\"']",
    "DB_PASSWORD": r"(?i)(?:password|passwd)[=:]\s*[\"'](.*?)[\"']",
}

def calculate_risk(secret_type: str, snippet: str) -> float:
    # Dummy ML detection logic or risk scoring
    if secret_type == "AWS_KEY":
        return 0.95
    elif secret_type == "GENERIC_API_KEY":
        return 0.80
    return 0.50

def get_severity(risk_score: float) -> SeverityLevel:
    if risk_score >= 0.9:
        return SeverityLevel.CRITICAL
    elif risk_score >= 0.7:
        return SeverityLevel.HIGH
    elif risk_score >= 0.4:
        return SeverityLevel.MEDIUM
    return SeverityLevel.LOW

def fetch_and_scan(repo_id: int):
    from database import SessionLocal
    db = SessionLocal()
    repo = None
    try:
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            return
            
        repo.status = ScanStatus.SCANNING
        db.commit()

        # Parse owner and repo from URL
        match = re.search(r"github\.com/([^/]+)/([^/]+)", repo.url)
        if not match:
            repo.status = ScanStatus.FAILED
            db.commit()
            return

        owner, repo_name = match.groups()
        repo_name = repo_name.replace(".git", "")
        # fallback to master if main doesn't work could be added, but assuming main for simplicity
        zip_url = f"https://github.com/{owner}/{repo_name}/archive/refs/heads/main.zip"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "repo.zip")
            opener = urllib.request.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0 LeakScanner/1.0')]
            urllib.request.install_opener(opener)
            
            try:
                urllib.request.urlretrieve(zip_url, zip_path)
            except urllib.error.HTTPError as e:
                # If 'main' branch fails, try 'master' branch
                if e.code == 404:
                    zip_url = f"https://github.com/{owner}/{repo_name}/archive/refs/heads/master.zip"
                    urllib.request.urlretrieve(zip_url, zip_path)
                else:
                    raise e
                
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
                
            # Scan files
            for root, _, files in os.walk(tmpdir):
                for file in files:
                    if file.endswith(('.py', '.js', '.json', '.env', '.yml', '.yaml', '.txt', '.md', '.html')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                                for i, line in enumerate(lines):
                                    for sec_type, pattern in PATTERNS.items():
                                        for match_val in re.finditer(pattern, line):
                                            risk = calculate_risk(sec_type, match_val.group(0))
                                            sev = get_severity(risk)
                                            # Create Leak
                                            leak = Leak(
                                                repository_id=repo.id,
                                                file_path=file_path.replace(tmpdir, ""),
                                                line_number=i + 1,
                                                snippet=line.strip()[:100],  # Limit snippet length
                                                secret_type=sec_type,
                                                severity=sev,
                                                risk_score=risk
                                            )
                                            db.add(leak)
                        except UnicodeDecodeError:
                            pass # Skip binary or non-utf-8 files
            
            repo.status = ScanStatus.COMPLETED
            db.commit()

    except Exception as e:
        print(f"Error scanning {repo.url if repo else repo_id}: {e}")
        if repo:
            repo.status = ScanStatus.FAILED
            db.commit()
    finally:
        db.close()
