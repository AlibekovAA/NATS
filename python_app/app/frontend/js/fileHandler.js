import { analyzePcap } from './pcapAnalyzer.js';
import { showErrorMessage } from './modal.js';

export function initializeFileHandlers() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('pcapFile');

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
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    document.getElementById('dropZone').classList.add('drag-over');
}

function unhighlight(e) {
    document.getElementById('dropZone').classList.remove('drag-over');
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const file = dt.files[0];
    handleFile(file);
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    handleFile(file);
    e.target.value = '';
}

function handleFile(file) {
    if (!file) return;

    if (!file.name.endsWith('.pcap')) {
        showErrorMessage('Please select a PCAP file');
        return;
    }

    const maxSize = 1024 * 1024 * 1024;
    if (file.size > maxSize) {
        showErrorMessage('File size exceeds 1GB limit');
        return;
    }

    analyzePcap(file);
}
