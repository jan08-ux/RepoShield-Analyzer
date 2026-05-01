document.addEventListener('DOMContentLoaded', () => {
    const scanBtn = document.getElementById('scanBtn');
    const repoUrlInput = document.getElementById('repoUrl');
    const scanMsg = document.getElementById('scanMsg');
    const reposGrid = document.getElementById('reposGrid');
    const refreshBtn = document.getElementById('refreshBtn');
    const leakModal = document.getElementById('leakModal');
    const closeModal = document.querySelector('.close-modal');
    const leakList = document.getElementById('leakList');
    const modalTitle = document.getElementById('modalTitle');

    // Fetch initial repositories
    fetchRepos();

    // Polling for updates every 5 seconds
    setInterval(fetchRepos, 5000);

    scanBtn.addEventListener('click', async () => {
        const url = repoUrlInput.value.trim();
        if (!url) {
            showMessage('Please enter a GitHub URL', 'error');
            return;
        }

        if (!url.includes('github.com')) {
            showMessage('Invalid GitHub URL', 'error');
            return;
        }

        setLoading(true);
        try {
            const response = await fetch('/scan/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url })
            });

            const data = await response.json();
            if (response.ok) {
                showMessage('Scan started successfully!', 'success');
                repoUrlInput.value = '';
                fetchRepos();
            } else {
                showMessage(data.detail || 'Failed to start scan', 'error');
            }
        } catch (error) {
            showMessage('Connection error', 'error');
        } finally {
            setLoading(false);
        }
    });

    refreshBtn.addEventListener('click', fetchRepos);

    closeModal.onclick = () => leakModal.style.display = 'none';
    window.onclick = (event) => {
        if (event.target == leakModal) leakModal.style.display = 'none';
    };

    async function fetchRepos() {
        try {
            const response = await fetch('/repos/');
            const repos = await response.json();
            renderRepos(repos);
        } catch (error) {
            console.error('Error fetching repos:', error);
        }
    }

    function renderRepos(repos) {
        if (repos.length === 0) {
            reposGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--text-muted);">No scans yet. Start your first scan above!</div>';
            return;
        }

        reposGrid.innerHTML = repos.map(repo => {
            const statusClass = `status-${repo.status.toLowerCase()}`;
            const leakCount = repo.leaks ? repo.leaks.length : 0;
            const repoName = repo.url.split('/').pop() || repo.url;
            
            return `
                <div class="repo-card" data-id="${repo.id}">
                    <div class="repo-header">
                        <div class="repo-info">
                            <h3>${repoName}</h3>
                            <p title="${repo.url}">${repo.url}</p>
                        </div>
                        <span class="status-badge ${statusClass}">${repo.status}</span>
                    </div>
                    <div class="repo-stats">
                        <div class="stat-item">
                            <span class="stat-label">Leaks Found</span>
                            <span class="stat-value ${leakCount > 0 ? 'critical' : ''}">${leakCount}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Risk Level</span>
                            <span class="stat-value" style="color: ${getRiskColor(leakCount)}">${getRiskLabel(leakCount)}</span>
                        </div>
                    </div>
                    <div class="repo-footer">
                        <button class="btn-view" onclick="viewLeaks(${repo.id}, '${repoName}')" ${repo.status !== 'COMPLETED' ? 'disabled' : ''}>
                            ${repo.status === 'COMPLETED' ? 'View Findings' : 'Processing...'}
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    window.viewLeaks = async (repoId, repoName) => {
        modalTitle.innerText = `Findings for ${repoName}`;
        leakList.innerHTML = '<div class="text-center">Loading findings...</div>';
        leakModal.style.display = 'flex';

        try {
            const response = await fetch(`/repos/${repoId}/leaks`);
            const leaks = await response.json();
            
            if (leaks.length === 0) {
                leakList.innerHTML = '<div style="text-align: center; padding: 2rem;">No leaks detected. Great job!</div>';
            } else {
                leakList.innerHTML = leaks.map(leak => `
                    <div class="leak-item">
                        <span class="leak-type">${leak.secret_type}</span>
                        <div class="leak-file"><i class="far fa-file-code"></i> ${leak.file_path} (Line ${leak.line_number})</div>
                        <div class="leak-code"><code>${escapeHtml(leak.snippet)}</code></div>
                    </div>
                `).join('');
            }
        } catch (error) {
            leakList.innerHTML = '<div class="error">Error loading findings</div>';
        }
    };

    function setLoading(loading) {
        if (loading) {
            scanBtn.classList.add('loading');
            scanBtn.disabled = true;
        } else {
            scanBtn.classList.remove('loading');
            scanBtn.disabled = false;
        }
    }

    function showMessage(text, type) {
        scanMsg.innerText = text;
        scanMsg.className = `message ${type}`;
        setTimeout(() => {
            scanMsg.innerText = '';
            scanMsg.className = 'message';
        }, 5000);
    }

    function getRiskColor(count) {
        if (count === 0) return '#10b981';
        if (count < 5) return '#f59e0b';
        return '#ef4444';
    }

    function getRiskLabel(count) {
        if (count === 0) return 'Safe';
        if (count < 5) return 'Medium';
        return 'Critical';
    }

    function escapeHtml(unsafe) {
        return unsafe
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
    }
});
