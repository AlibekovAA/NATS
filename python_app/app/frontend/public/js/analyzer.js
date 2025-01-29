async function analyzePcap() {
    const fileInput = document.getElementById('pcapFile');

    if (!fileInput.files.length) {
        showError('Please select a file');
        return;
    }

    const file = fileInput.files[0];
    if (!file.name.endsWith('.pcap')) {
        showError('Please select a PCAP file');
        return;
    }

    showLoading();

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/analyze-network', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            showResults(result);
        } else {
            showError(result.detail || 'Error analyzing file');
        }
    } catch (error) {
        showError('Error analyzing file');
        console.error('Analysis error:', error);
    }
}

function showError(message) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = `
        <div class="error-message">
            <p>${message}</p>
        </div>
    `;
}

function showLoading() {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = `
        <div class="loading">
            <p>Analyzing packet data...</p>
        </div>
    `;
}

function showResults(result) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = `
        <div class="success-message">
            <h2>Analysis Results</h2>
        </div>
        <pre>${JSON.stringify(result, null, 2)}</pre>
    `;
}
