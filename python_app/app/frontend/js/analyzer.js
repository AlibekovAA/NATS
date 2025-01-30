document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('pcapFile');
    const uploadStatus = document.getElementById('uploadStatus');

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    dropZone.addEventListener('drop', handleDrop, false);
    fileInput.addEventListener('change', handleFileSelect, false);

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight(e) {
        dropZone.classList.add('drag-over');
    }

    function unhighlight(e) {
        dropZone.classList.remove('drag-over');
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const file = dt.files[0];
        handleFile(file);
    }

    function handleFileSelect(e) {
        const file = e.target.files[0];
        handleFile(file);
    }

    function handleFile(file) {
        if (!file) return;

        if (!file.name.endsWith('.pcap')) {
            showErrorMessage('Пожалуйста, выберите PCAP файл');
            return;
        }

        analyzePcap(file);
    }

    async function analyzePcap(file) {
        showLoadingMessage();
        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/analyze-network', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                showSuccessMessage(result);
            } else {
                showErrorMessage(result.detail || 'Ошибка анализа файла');
            }
        } catch (error) {
            showErrorMessage('Ошибка анализа файла');
            console.error('Ошибка анализа:', error);
        }
    }
});

function showErrorMessage(message) {
    const resultsDiv = document.getElementById('results');
    const uploadStatus = document.getElementById('uploadStatus');

    uploadStatus.innerHTML = '';
    resultsDiv.innerHTML = `
        <div class="error-message">
            <p>${message}</p>
        </div>
    `;
}

function showLoadingMessage() {
    const resultsDiv = document.getElementById('results');
    const uploadStatus = document.getElementById('uploadStatus');

    uploadStatus.innerHTML = 'Анализ файла...';
    resultsDiv.innerHTML = `
        <div class="loading">
            <p>Идет анализ пакетов...</p>
        </div>
    `;
}

function showSuccessMessage(result) {
    const resultsDiv = document.getElementById('results');
    const uploadStatus = document.getElementById('uploadStatus');

    uploadStatus.innerHTML = 'Анализ завершен';
    resultsDiv.innerHTML = `
        <div class="success-message">
            <h2>Результаты анализа</h2>
        </div>
        <pre>${JSON.stringify(result, null, 2)}</pre>
    `;
}
