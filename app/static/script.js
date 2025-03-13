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

    const recordButton = document.getElementById("recordButton");
    const messagesDiv = document.getElementById("messages");

    let mediaRecorder;
    let audioChunks = [];

    recordButton.addEventListener("click", async () => {
        console.log("🎤 Кнопку мікрофона натиснуто");

        if (!mediaRecorder || mediaRecorder.state === "inactive") {
            try {
                console.log("🎤 Запит на доступ до мікрофона...");
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.ondataavailable = event => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = async () => {
                    console.log("🎤 Запис завершено, обробка аудіо...");
                    const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
                    audioChunks = [];

                    const formData = new FormData();
                    formData.append("audio", audioBlob, "voice_message.webm");

                    console.log("📤 Відправляємо файл на сервер...", formData);

                    messagesDiv.innerHTML += `<p><strong>Ви (голос):</strong> 🎤 Обробка...</p>`;

                    try {
                        const response = await fetch("/chatbot/voice", {
                            method: "POST",
                            body: formData
                        });

                        console.log("📩 Отримано відповідь:", response);

                        const data = await response.json();
                        if (data.error) {
                            console.error("❌ Помилка сервера:", data.error);
                            messagesDiv.innerHTML += `<p><strong>Помилка:</strong> ${data.error}</p>`;
                        } else {
                            console.log("✅ Отримано текст:", data.transcription);
                            console.log("🤖 Відповідь бота:", data.response);
                            messagesDiv.innerHTML += `<p><strong>Ви (голос):</strong> ${data.transcription}</p>`;
                            messagesDiv.innerHTML += `<p><strong>Бот:</strong> ${data.response}</p>`;
                        }
                    } catch (error) {
                        console.error("❌ Помилка відправки голосу:", error);
                        messagesDiv.innerHTML += `<p><strong>Помилка:</strong> Не вдалося отримати відповідь.</p>`;
                    }
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                };

                mediaRecorder.start();
                console.log("🎙️ Почався запис...");
                recordButton.textContent = "⏹️"; // Змінюємо кнопку на стоп
            } catch (error) {
                console.error("❌ Помилка доступу до мікрофона:", error);
            }
        } else {
            mediaRecorder.stop();
            console.log("🛑 Запис зупинено");
            recordButton.textContent = "🎤"; // Повертаємо іконку мікрофона
        }
    });
});

