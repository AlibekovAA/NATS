import { showLoadingMessage, showErrorMessage, showSuccessMessage } from './modal.js';

export async function analyzePcap(file) {
    showLoadingMessage();
    try {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch('/analyze-network', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error analyzing file');
        }

        const result = await response.json();
        showSuccessMessage(result);
    } catch (error) {
        console.error('Error analyzing:', error);
        showErrorMessage(error.message || 'Error occurred while analyzing the file');
    }
}
