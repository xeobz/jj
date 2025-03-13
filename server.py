from flask import Flask, request, jsonify
import pandas as pd
import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

app = Flask(__name__)

# Авторизация Google Drive
gauth = GoogleAuth()
gauth.LoadCredentialsFile("credentials.json")
drive = GoogleDrive(gauth)

# Все возможные поля
FIELDS = [
    "Основная идея марафона", "Ключевые тезисы", "Формат марафона", "Целевая аудитория", 
    "Призывы к действию (CTA)", "Ключевые выгоды", "Ссылка на документ (Сегментация)", "Цена курса", 
    "Рассрочка", "Используем чат-бот VK / канал VK / группу VK", 
    "Используем чат-бот WhatsApp / канал WhatsApp / группу WhatsApp", 
    "Используем чат-бот TG / канал TG / группу TG", "Тип основной площадки", 
    "Ссылка на лендинг (LP)", "Ссылка на лендинг (ГТ)", "Группа в Telegram (Зарегистрировались)", 
    "Группа в Telegram (Подписались)", "Группа в Telegram (Купили)", "Тип виджета", "Ссылка на виджет", 
    "Ссылка на оплату", "Ссылка на вебинарную комнату (Bizon365)", 
    "Ссылка на процесс рассылки в Getкурс", "Сценарий воронки продаж (Excel файл, генерируется автоматически по шаблону)", 
    "Формат презентации", "Ссылка на дизайн и визуальный стиль", "Ссылка на файл", 
    "Ответственный за проверку", "Комментарии по итоговой проверке", "Готово к запуску?"
]

@app.route('/generate_excel', methods=['GET'])
def generate_excel():
    try:
        # Получаем параметры из URL
        request_data = request.args.to_dict()

        # Формируем данные: если параметр не передан, оставляем пустое значение
        data = {field: request_data.get(field, "") for field in FIELDS}

        # Создаем DataFrame
        df = pd.DataFrame(list(data.items()), columns=["Поле", "Значение"])
        file_path = "output.xlsx"
        df.to_excel(file_path, index=False)

        # Загружаем файл в Google Drive
        file_drive = drive.CreateFile({"title": "output.xlsx"})
        file_drive.SetContentFile(file_path)
        file_drive.Upload()

        # Открываем доступ к файлу и получаем ссылку
        file_drive.InsertPermission({'type': 'anyone', 'value': 'anyone', 'role': 'reader'})
        file_link = file_drive['alternateLink']

        return jsonify({"file_url": file_link})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
