document.addEventListener("DOMContentLoaded", function() {
    // Відтворення відео при завантаженні сторінки
    const introVideo = document.getElementById("intro-video");
    if (introVideo) {
        introVideo.play();
    }

    // Функція для відправки повідомлення в чаті
    async function sendMessage() {
        const userInput = document.getElementById("userInput");
        const messagesDiv = document.getElementById("messages");
        
        if (!userInput.value.trim()) return;
        
        messagesDiv.innerHTML += `<p><strong>Ви:</strong> ${userInput.value}</p>`;
        const userMessage = userInput.value;
        userInput.value = "";
        
        try {
            const response = await fetch("/chatbot", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userMessage })
            });
            
            const data = await response.json();
            messagesDiv.innerHTML += `<p><strong>Бот:</strong> ${data.response || "Помилка!"}</p>`;
        } catch (error) {
            messagesDiv.innerHTML += `<p><strong>Помилка:</strong> Не вдалося отримати відповідь.</p>`;
        }
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
    
    document.getElementById("sendButton").addEventListener("click", sendMessage);
});
