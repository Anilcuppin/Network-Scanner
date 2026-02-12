document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        
        // Update active nav link
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        link.classList.add('active');
        
        // Show corresponding section
        const section = link.dataset.section;
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
        document.getElementById(`${section}-section`).classList.add('active');
        
        // Load history if navigating to history section
        if (section === 'history') {
            loadHistory();
        }
    });
});

// ===================================
// SCAN FUNCTIONALITY
// ===================================
const scanBtn = document.getElementById('scan-btn');
const networkInput = document.getElementById('network-input');
const loading = document.getElementById('loading');
const resultsPanel = document.getElementById('results-panel');
const hostsGrid = document.getElementById('hosts-grid');
const hostsCount = document.getElementById('hosts-count');
const scannedNetwork = document.getElementById('scanned-network');

scanBtn.addEventListener('click', async () => {
    const network = networkInput.value.trim();
    
    // Show loading, hide results
    loading.classList.remove('hidden');
    resultsPanel.classList.add('hidden');
    scanBtn.disabled = true;
    scanBtn.querySelector('.btn-text').textContent = 'SCANNING...';
    
    try {
        const response = await fetch('/api/scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ network: network || null })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayResults(data);
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Network error: ' + error.message);
    } finally {
        loading.classList.add('hidden');
        scanBtn.disabled = false;
        scanBtn.querySelector('.btn-text').textContent = 'INITIATE SCAN';
    }
});

// ===================================
// DISPLAY RESULTS
// ===================================
function displayResults(data) {
    scannedNetwork.textContent = data.network;
    hostsCount.textContent = data.total;
    
    // Clear previous results
    hostsGrid.innerHTML = '';
    
    // Display hosts
    if (data.online_hosts.length === 0) {
        hostsGrid.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🔍</div><p>No online hosts found</p></div>';
    } else {
        data.online_hosts.forEach((host, index) => {
            const card = document.createElement('div');
            card.className = 'host-card';
            card.style.animationDelay = `${index * 0.05}s`;
            card.innerHTML = `
                <div class="host-icon">💻</div>
                <div class="host-ip">${host}</div>
                <div class="host-status">● Online</div>
            `;
            hostsGrid.appendChild(card);
        });
    }
    
    resultsPanel.classList.remove('hidden');
    
    // Smooth scroll to results
    setTimeout(() => {
        resultsPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}

// ===================================
// HISTORY FUNCTIONALITY
// ===================================
async function loadHistory() {
    const historyList = document.getElementById('history-list');
    historyList.innerHTML = '<div class="loading"><p>Loading history...</p></div>';
    
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        if (data.success) {
            displayHistory(data.scans);
        } else {
            historyList.innerHTML = '<div class="empty-state"><div class="empty-state-icon">❌</div><p>Error loading history</p></div>';
        }
    } catch (error) {
        historyList.innerHTML = '<div class="empty-state"><div class="empty-state-icon">❌</div><p>Network error</p></div>';
    }
}

function displayHistory(scans) {
    const historyList = document.getElementById('history-list');
    
    if (scans.length === 0) {
        historyList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📊</div>
                <p>No scan history yet. Start your first scan!</p>
            </div>
        `;
        return;
    }
    
    historyList.innerHTML = '';
    
    scans.forEach((scan, index) => {
        const item = document.createElement('div');
        item.className = 'history-item';
        item.style.animationDelay = `${index * 0.1}s`;
        
        const hostsChips = scan.online_hosts.map(host => 
            `<span class="host-chip">${host}</span>`
        ).join('');
        
        item.innerHTML = `
            <div class="history-header">
                <div>
                    <div class="history-time">📅 ${scan.timestamp}</div>
                    <div class="history-network">🌐 ${scan.network_cidr}</div>
                </div>
                <div>
                    <button class="delete-btn" onclick="deleteScan(${scan.id})">Delete</button>
                </div>
            </div>
            <div style="color: var(--text-secondary); margin-bottom: 0.5rem;">
                <strong>${scan.total_hosts}</strong> online host${scan.total_hosts !== 1 ? 's' : ''}
            </div>
            <div class="history-hosts">${hostsChips}</div>
        `;
        
        historyList.appendChild(item);
    });
}

// ===================================
// DELETE SCAN
// ===================================
async function deleteScan(scanId) {
    if (!confirm('Are you sure you want to delete this scan?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/delete/${scanId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            loadHistory(); // Reload history
        } else {
            alert('Error deleting scan: ' + data.error);
        }
    } catch (error) {
        alert('Network error: ' + error.message);
    }
}

// ===================================
// KEYBOARD SHORTCUTS
// ===================================
networkInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        scanBtn.click();
    }
});

// ===================================
// INITIALIZE
// ===================================
document.addEventListener('DOMContentLoaded', () => {
    console.log('NetScan initialized');
});