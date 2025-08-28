/**
 * QR Code generator for ROZOOM
 * Uses qrcode.js library to generate QR codes for mobile access
 */

// Функция создания QR-кода
function generateQRCode(url, elementId) {
    if (!document.getElementById(elementId)) {
        console.error(`Element with id ${elementId} not found`);
        return;
    }
    
    // Очистка контейнера
    const element = document.getElementById(elementId);
    element.innerHTML = '';
    
    // Создание QR-кода
    new QRCode(element, {
        text: url,
        width: 128,
        height: 128,
        colorDark: "#ffffff",
        colorLight: "#000000",
        correctLevel: QRCode.CorrectLevel.H
    });
}

// Функция для генерации QR-кода на странице
function setupQRCode() {
    // Генерируем QR-код для текущей страницы
    const currentUrl = window.location.href;
    
    // Создаем контейнер для QR-кода, если его еще нет
    if (!document.getElementById('qrCodeContainer')) {
        const container = document.createElement('div');
        container.className = 'qr-container';
        container.innerHTML = `
            <h3 id="qrTitle"></h3>
            <div id="qrCode" class="qr-code"></div>
            <p class="qr-text" id="qrText"></p>
        `;
        
        // Находим место для вставки QR-кода
        const targetElement = document.querySelector('.page-wrapper') || document.body;
        targetElement.appendChild(container);
    }
    
    // Устанавливаем заголовок и текст в зависимости от языка
    const lang = document.documentElement.lang || 'uk';
    
    const titles = {
        'uk': 'Відскануйте для мобільного доступу',
        'de': 'Scannen Sie für mobilen Zugriff',
        'en': 'Scan for mobile access'
    };
    
    const texts = {
        'uk': 'Відкрийте цю сторінку на своєму мобільному пристрої',
        'de': 'Öffnen Sie diese Seite auf Ihrem Mobilgerät',
        'en': 'Open this page on your mobile device'
    };
    
    document.getElementById('qrTitle').textContent = titles[lang] || titles['en'];
    document.getElementById('qrText').textContent = texts[lang] || texts['en'];
    
    // Генерируем QR-код
    generateQRCode(currentUrl, 'qrCode');
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Проверяем, не мобильное ли устройство (не показываем QR на мобильных)
    if (!(/Mobi|Android/i.test(navigator.userAgent))) {
        // Добавляем библиотеку QRCode.js
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.min.js';
        script.onload = function() {
            setupQRCode();
        };
        document.head.appendChild(script);
    }
    
    // Добавляем класс mobile-optimized для лучшей адаптивности текста
    const textElements = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, li, span');
    textElements.forEach(element => {
        element.classList.add('mobile-optimized');
    });
    
    // Добавляем класс mobile-image для всех изображений
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        img.classList.add('mobile-image');
    });
});
