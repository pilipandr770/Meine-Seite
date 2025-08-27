"""
Тестовый скрипт для проверки маршрута /crm/submit_task
"""
import requests
import json
import os

# URL вашего API
API_URL = "https://meine-seite.onrender.com/crm/submit_task"

# Тестовые данные
test_data = {
    "project_type": "web-dev",
    "project_name": "Test Project",
    "task_description": "This is a test task description",
    "key_features": "Feature 1, Feature 2",
    "design_preferences": "Minimalistic",
    "platform": "Web",
    "budget": "1000-2000",
    "timeline": "2 weeks",
    "integrations": "None",
    "contact_method": "Email",
    "contact_info": "test@example.com"
}

# Отправка POST-запроса
print(f"Отправка запроса на {API_URL}")
response = requests.post(API_URL, json=test_data)

# Вывод результата
print(f"Код статуса: {response.status_code}")
print("Ответ:")
try:
    print(json.dumps(response.json(), indent=4))
except:
    print(response.text)
