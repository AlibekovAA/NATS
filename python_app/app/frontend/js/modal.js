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
        <div class="terminal-loader">
            <div class="terminal-header">
                <div class="terminal-title">Status</div>
                <div class="terminal-controls">
                    <div class="control close"></div>
                    <div class="control minimize"></div>
                    <div class="control maximize"></div>
                </div>
            </div>
            <div class="text">Loading...</div>
        </div>
    `;
    resultsModal.classList.add('show');
}

export function showSuccessMessage(result) {
    const resultsModal = document.getElementById('results');
    const modalBody = resultsModal.querySelector('.results-modal-body');

    modalBody.innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
    resultsModal.classList.add('show');
}

export function closeResults() {
    const resultsModal = document.getElementById('results');
    resultsModal.classList.remove('show');
}
