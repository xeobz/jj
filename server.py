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

@app.route('/generate_excel', methods=['GET'])
def generate_excel():
    try:
        # Получаем все параметры запроса
        data = request.args.to_dict()
        if not data:
            return jsonify({"error": "Нет данных"}), 400

        # Создаем Excel
        df = pd.DataFrame(list(data.items()), columns=["Поле", "Значение"])
        file_path = "output.xlsx"
        df.to_excel(file_path, index=False)

        # Загружаем файл на Google Drive
        file_drive = drive.CreateFile({"title": "output.xlsx"})
        file_drive.SetContentFile(file_path)
        file_drive.Upload()

        # Открываем доступ и получаем ссылку
        file_drive.InsertPermission({'type': 'anyone', 'value': 'anyone', 'role': 'reader'})
        file_link = file_drive['alternateLink']

        return jsonify({"file_url": file_link})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
