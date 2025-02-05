export function initializeModal() {
    const resultsModal = document.getElementById('results');
    const closeButton = resultsModal.querySelector('.close-button');

    resultsModal.addEventListener('click', (e) => {
        if (e.target === resultsModal) {
            closeResults();
        }
    });

    closeButton.addEventListener('click', () => {
        closeResults();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && resultsModal.classList.contains('show')) {
            closeResults();
        }
    });
}

export function showErrorMessage(message) {
    const resultsModal = document.getElementById('results');
    const modalBody = resultsModal.querySelector('.results-modal-body');

    modalBody.innerHTML = `
        <div class="error-message">
            <p>${message}</p>
        </div>
    `;
    resultsModal.classList.add('show');
}

export function showLoadingMessage() {
    const resultsModal = document.getElementById('results');
    const modalBody = resultsModal.querySelector('.results-modal-body');

    modalBody.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading...</p>
        </div>
    `;
    resultsModal.classList.add('show');
}

export function showSuccessMessage(result) {
    const resultsModal = document.getElementById('results');
    const modalBody = resultsModal.querySelector('.results-modal-body');

    const uniqueIPs = {
        sources: [...new Set(result.packets.map(p => p.source_ip))],
        destinations: [...new Set(result.packets.map(p => p.destination_ip))]
    };

    const summaryView = {
        summary: result.summary,
        unique_ips: {
            sources: uniqueIPs.sources,
            destinations: uniqueIPs.destinations
        }
    };

    modalBody.innerHTML = `
        <div class="view-controls">
            <label class="switch">
                <input type="checkbox" id="viewToggle">
                <span class="slider"></span>
            </label>
            <span class="view-label">Подробный отчет</span>
        </div>
        <div class="results-content">
            <pre class="summary-view">${JSON.stringify(summaryView, null, 2)}</pre>
            <pre class="detailed-view" style="display: none">${JSON.stringify(result, null, 2)}</pre>
        </div>
    `;

    const viewToggle = modalBody.querySelector('#viewToggle');
    const summaryViewEl = modalBody.querySelector('.summary-view');
    const detailedViewEl = modalBody.querySelector('.detailed-view');

    viewToggle.addEventListener('change', () => {
        summaryViewEl.style.display = viewToggle.checked ? 'none' : 'block';
        detailedViewEl.style.display = viewToggle.checked ? 'block' : 'none';
    });

    resultsModal.classList.add('show');
}

export function closeResults() {
    const resultsModal = document.getElementById('results');
    resultsModal.classList.remove('show');
}
