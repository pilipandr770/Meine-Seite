document.addEventListener("DOMContentLoaded", function() {
    const userInput = document.getElementById("userInput");
    const messagesDiv = document.getElementById("messages");
    const sendButton = document.getElementById("sendButton");
    const recordButton = document.getElementById("recordButton");

    let mediaRecorder;
    let audioChunks = [];

    // 🔹 Відправка текстового повідомлення
    async function sendMessage() {
        if (!userInput.value.trim()) return;

        const userMessage = userInput.value;
        messagesDiv.innerHTML += `<p><strong>Ви:</strong> ${userMessage}</p>`;
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

    if (sendButton) {
        sendButton.addEventListener("click", sendMessage);
    }

    if (userInput) {
        userInput.addEventListener("keypress", function (e) {
            if (e.key === "Enter") {
                sendMessage();
            }
        });
    }

    // 🔹 Обробка голосового повідомлення
    if (recordButton) {
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

                        messagesDiv.innerHTML += `<p><strong>Ви (голос):</strong> 🎤 Обробка...</p>`;

                        try {
                            const response = await fetch("/chatbot/voice", {
                                method: "POST",
                                body: formData
                            });

                            const data = await response.json();

                            if (data.error) {
                                console.error("❌ Помилка сервера:", data.error);
                                messagesDiv.innerHTML += `<p><strong>Помилка:</strong> ${data.error}</p>`;
                            } else {
                                console.log("✅ Розпізнано:", data.transcription);
                                console.log("🤖 Відповідь:", data.response);
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
                    recordButton.textContent = "⏹️"; // Стоп
                } catch (error) {
                    console.error("❌ Помилка доступу до мікрофона:", error);
                }
            } else {
                mediaRecorder.stop();
                console.log("🛑 Запис зупинено");
                recordButton.textContent = "🎤"; // Мікрофон знову
            }
        });
    }
});
