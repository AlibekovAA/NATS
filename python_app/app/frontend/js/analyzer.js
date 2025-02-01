import { initializeTitleAnimation } from './animations.js';
import { initializeModal } from './modal.js';
import { initializeFileHandlers } from './fileHandler.js';

document.addEventListener('DOMContentLoaded', () => {
    initializeTitleAnimation();
    initializeModal();
    initializeFileHandlers();
});
