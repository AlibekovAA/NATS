export function initializeTitleAnimation() {
    const title = document.querySelector('.animated-title span');
    const text = title.textContent;
    title.textContent = '';

    text.split('').forEach((char, i) => {
        const span = document.createElement('span');
        span.textContent = char;
        span.style.setProperty('--char-index', i + 1);
        title.appendChild(span);
    });
}
