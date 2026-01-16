let currentMode = 'single';
let reportData = [];

function setMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.mode-option').forEach(opt => opt.classList.remove('active'));
    document.getElementById(mode === 'single' ? 'singleMode' : 'crawlMode').classList.add('active');

    const input = document.getElementById('urlInput');
    if (mode === 'crawl') {
        input.placeholder = "Enter website home URL (e.g., https://example.com)";
        input.rows = 2;
    } else {
        input.placeholder = "Enter URLs here (one per line)\nhttps://example.com\nhttps://ulatus.com";
        input.rows = 5;
    }
}

async function analyze() {
    const urlInput = document.getElementById('urlInput');
    const submitBtn = document.getElementById('submitBtn');
    const loader = document.getElementById('loader');
    const resultsArea = document.getElementById('resultsArea');
    const error = document.getElementById('error');

    const rawInput = urlInput.value.trim();
    if (!rawInput) {
        showError("Please enter at least one URL");
        return;
    }

    // Reset UI
    error.style.display = 'none';
    resultsArea.style.display = 'none';
    loader.style.display = 'block';
    const loaderText = document.getElementById('loaderText');
    if (loaderText) {
        loaderText.innerText = currentMode === 'single' ? "Analyzing Content..." : "Crawling Entire Website...";
    }
    submitBtn.disabled = true;

    try {
        let response;
        if (currentMode === 'single') {
            const urls = rawInput.split('\n').map(u => u.trim()).filter(u => u);
            response = await fetch('/count', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ urls: urls }),
            });
        } else {
            response = await fetch('/crawl', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: rawInput }),
            });
        }

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Analysis failed");

        processAndDisplayResults(data);
    } catch (err) {
        showError(err.message);
    } finally {
        loader.style.display = 'none';
        submitBtn.disabled = false;
    }
}

function processAndDisplayResults(data) {
    const resultsArea = document.getElementById('resultsArea');
    const tableBody = document.getElementById('resultsTableBody');
    const totalCountVal = document.getElementById('totalCountVal');
    const pagesCrawledVal = document.getElementById('pagesCrawledVal');
    const overallLangVal = document.getElementById('overallLangVal');

    tableBody.innerHTML = '';
    let total = 0;
    let pages = 0;
    let langGroup = '-';

    reportData = [];

    if (currentMode === 'single') {
        reportData = data.results;
        data.results.forEach(res => {
            if (res.error) {
                addErrorRow(tableBody, res.url, res.error);
            } else {
                addResultRow(tableBody, res);
                total += res.stats.count;
                pages++;
                langGroup = res.stats.language_group; // Use last for simplicity in single mode
            }
        });
    } else {
        reportData = data.results;
        total = data.aggregate.total_count;
        pages = data.aggregate.pages_crawled;
        langGroup = data.aggregate.primary_group;
        data.results.forEach(res => addResultRow(tableBody, res));
    }

    totalCountVal.innerText = total.toLocaleString();
    pagesCrawledVal.innerText = pages;
    overallLangVal.innerText = langGroup;

    resultsArea.style.display = 'block';
}

function addResultRow(parent, res) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td title="${res.title}">${truncate(res.title || res.url, 40)}</td>
        <td style="font-weight: 600;">${res.stats.count.toLocaleString()}</td>
        <td>${res.stats.type.toUpperCase()}</td>
        <td><a href="${res.url}" target="_blank" style="color: var(--brand-crimson); text-decoration: none;">View ↗</a></td>
    `;
    parent.appendChild(row);
}

function addErrorRow(parent, url, error) {
    const row = document.createElement('tr');
    row.className = 'error-row';
    row.innerHTML = `
        <td>Fetch Failed</td>
        <td>0</td>
        <td>-</td>
        <td title="${error}">${truncate(url, 20)} ⚠</td>
    `;
    parent.appendChild(row);
}

async function exportCSV() {
    if (!reportData.length) return;

    try {
        const response = await fetch('/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(reportData),
        });

        if (!response.ok) throw new Error("Export failed");

        const blob = await response.blob();

        // Proper CSV download trigger
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.setAttribute('download', 'ulatus_linguistic_report.csv');
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

    } catch (err) {
        showError("Failed to download CSV: " + err.message);
    }
}

function truncate(str, len) {
    if (!str) return '';
    return str.length > len ? str.substring(0, len) + '...' : str;
}

function showError(msg) {
    const error = document.getElementById('error');
    error.innerText = msg;
    error.style.display = 'block';
}
