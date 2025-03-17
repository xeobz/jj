import requests
import json
import xlsxwriter
import os
import uuid
from flask import Flask

# Настройки API Bitrix24
BITRIX_URL = "https://inwork.bitrix24.ru/rest/8/fjtuc0gmxac1ife0"
BITRIX_FOLDER_ID = "666"  # ID папки "Отчеты"
BITRIX_SMART_PROCESS_ID = 1042  # ID смарт-процесса
BITRIX_ITEM_LIST_URL = f"{BITRIX_URL}/crm.item.list"
BITRIX_ITEM_UPDATE_URL = f"{BITRIX_URL}/crm.item.update"
BITRIX_DISK_UPLOAD_URL = f"{BITRIX_URL}/disk.folder.uploadfile"
BITRIX_PROCESSED_FIELD = "ufCrm8_1742219108820"  # Название поля-флага

# Стадия для обработки сделок
TARGET_STAGE_ID = "DT1042_12:UC_SJ9G5V"

# Поле для ссылки на загруженный файл
BITRIX_FILE_FIELD = "ufCrm8_1742191229853"

# Соответствие ключей и заголовков Excel
FIELD_MAPPING = {
    "ufCrm8_1741618281": "Основная идея марафона",
    "ufCrm8_1741770367567": "Ключевые тезисы",
    "ufCrm8_1741618429801": "Формат марафона",
    "ufCrm8_1741619600776": "Целевая аудитория",
    "ufCrm8_1741619632910": "Призывы к действию (CTA)",
    "ufCrm8_1741619613925": "Ключевые выгоды",
    "ufCrm8_1741771440298": "Ссылка на документ (Сегментация)",
    "ufCrm8_1741619666379": "Цена курса",
    "ufCrm8_1741619708814": "Рассрочка",
    "ufCrm8_1741775905327": "Используем чат-бот VK / канал VK / группу VK",
    "ufCrm8_1741775945725": "Используем чат-бот WhatsApp / канал WhatsApp / группу WhatsApp",
    "ufCrm8_1741775887372": "Используем чат-бот TG / канал TG / группу TG",
    "ufCrm8_1741776999985": "Тип основной площадки",
    "ufCrm8_1741777554858": "Ссылка на лендинг (LP)",
    "ufCrm8_1741777568783": "Ссылка на лендинг (ГТ)",
    "ufCrm8_1741618948304": "Группа в Telegram (Зарегистрировались)",
    "ufCrm8_1741777058373": "Группа в Telegram (Подписались)",
    "ufCrm8_1741618995420": "Группа в Telegram (Купили)",
    "ufCrm8_1741619856822": "Тип виджета",
    "ufCrm8_1741777239028": "Ссылка на виджет",
    "ufCrm8_1741771524820": "Ссылка на оплату",
    "ufCrm8_1741777265704": "Ссылка на вебинарную комнату (Bizon365)",
    "ufCrm8_1741778046357": "Ссылка на процесс рассылки в Getкурс",
    "ufCrm8_1741619470239": "Сценарий воронки продаж",
    "ufCrm8_1741620131859": "Формат презентации",
    "ufCrm8_1741620163224": "Ссылка на дизайн",
    "ufCrm8_1741620139873": "Ссылка на файл",
    "ufCrm8_1741620290": "Ответственный за проверку",
    "ufCrm8_1741620328349": "Комментарии по проверке",
    "ufCrm8_1741620350428": "Готово к запуску?"
}

# Функция для получения ФИО пользователя по ID
def get_user_name(user_id):
    if not user_id:
        return "Не назначен"

    response = requests.get(f"{BITRIX_URL}/user.get", params={"ID": user_id})
    data = response.json()

    if "result" in data and data["result"]:
        user = data["result"][0]
        return f"{user.get('NAME', '')} {user.get('LAST_NAME', '')}".strip()

    return f"ID: {user_id}"  # Если пользователь не найден, оставляем ID


def process_field_value(field, value):
    if value is None:
        return ""  # Если значение None, возвращаем пустую строку

    if isinstance(value, list):  # Обрабатываем множественные поля
        value = [str(v) for v in value]  # Приводим все элементы к строковому виду

    if field == "ufCrm8_1741620290":  # Ответственный за проверку (ФИО)
        if isinstance(value, int):
            return get_user_name(value)
        elif isinstance(value, list):
            return "\n".join(get_user_name(v) for v in value if v)  # Проверяем, что v не None

    if field == "ufCrm8_1741618429801":  # Формат марафона
        return "Бесплатный" if value == 44 else "Продающий" if value == 46 else str(value)

    elif field == "ufCrm8_1741619708814":  # Рассрочка
        return "Да" if value == 68 else "Нет"

    elif field == "ufCrm8_1741775887372":  # Используем чат-бот TG
        return "Нет" if value == 112 else "Да"

    elif field == "ufCrm8_1741775945725":  # Используем чат-бот WhatsApp
        return "Нет" if value == 120 else "Да"

    elif field == "ufCrm8_1741775905327":  # Используем чат-бот VK
        return "Да" if value == 114 else "Нет"

    elif field == "ufCrm8_1741776999985":  # Тип основной площадки (множественное поле)
        mapping = {122: "Лендинг (LP)"}
        if isinstance(value, list):  
            return "\n".join(mapping.get(int(v), "Лендинг (ГТ)") for v in value if v)
        return mapping.get(int(value), "Лендинг (ГТ)")

    elif field == "ufCrm8_1741619856822":  # Тип виджета
        mapping = {78: "Внешний", 82: "Чат-бот", 80: "Форма заявки"}  
        if isinstance(value, list):  
            return "\n".join(mapping.get(int(v), "Форма заявки") for v in value if v)
        return mapping.get(int(value), "Форма заявки")

    elif field == "ufCrm8_1741620131859":  # Формат презентации
        return "PDF" if value == 90 else "PowerPoint" if value == 92 else "Google Slides"

    elif field == "ufCrm8_1741620350428":  # Готово к запуску?
        return "Да" if value == 106 else "Нет" if value == 108 else "На доработке"

    return str(value)  # Все остальные поля просто конвертируем в строку




# Получение сделок
def get_target_deals():
    response = requests.get(BITRIX_ITEM_LIST_URL, params={"entityTypeId": BITRIX_SMART_PROCESS_ID})
    data = response.json()

    if "result" in data and "items" in data["result"]:
        deals = [item for item in data["result"]["items"] if item.get("stageId") == TARGET_STAGE_ID]
        print(f"Найдено {len(deals)} сделок на стадии {TARGET_STAGE_ID}")
        return deals
    else:
        print("Ошибка API:", data.get("error_description", "Неизвестная ошибка"))
        return []

def create_excel_file(item_data, item_id):
    unique_id = uuid.uuid4().hex[:8]  # Генерация уникального 8-символьного идентификатора
    file_name = f"element_{item_id}_{unique_id}.xlsx"
    workbook = xlsxwriter.Workbook(file_name)
    worksheet = workbook.add_worksheet()

    # Формат ячеек: перенос текста + автоширина
    cell_format = workbook.add_format({'text_wrap': True, 'valign': 'top'})  # Перенос строк и выравнивание по верху

    worksheet.write(0, 0, "Поле")
    worksheet.write(0, 1, "Значение")

    row = 1
    for field, title in FIELD_MAPPING.items():
        value = item_data.get(field, "")
        processed_value = process_field_value(field, value)  # Применяем обработку значений

        # Приводим к строке перед вызовом count(), если это не строка
        processed_value_str = str(processed_value)

        # Запись значений в Excel с переносом текста
        worksheet.write(row, 0, title)
        worksheet.write(row, 1, processed_value_str, cell_format)

        # Автоувеличение высоты строки в зависимости от количества строк
        line_count = processed_value_str.count("\n") + 1
        worksheet.set_row(row, line_count * 15)  # Примерная высота строки

        row += 1

    # Автоширина для колонки A (название полей)
    worksheet.set_column(0, 0, 30)  
    # Автоширина для колонки B (значения)
    worksheet.set_column(1, 1, 50)  

    workbook.close()
    print(f"✅ Файл {file_name} создан.")
    return file_name



# Получение uploadUrl из Bitrix24
def get_upload_url():
    response = requests.post(BITRIX_DISK_UPLOAD_URL, json={"id": BITRIX_FOLDER_ID})
    response_data = response.json()

    if "result" in response_data and "uploadUrl" in response_data["result"]:
        return response_data["result"]["uploadUrl"]
    else:
        print("❌ Ошибка: не удалось получить uploadUrl:", response_data)
        return None

# Загрузка файла в Bitrix24
def upload_to_bitrix(file_name):
    upload_url = get_upload_url()
    if not upload_url:
        return None, None

    with open(file_name, "rb") as file:
        response = requests.post(upload_url, files={"file": file})
        response_data = response.json()

    if "result" in response_data:
        file_id = response_data["result"].get("ID")
        file_url = response_data["result"].get("DETAIL_URL", "")

        if file_url:
            print(f"✅ Файл загружен: {file_url}, ID: {file_id}")
            return file_url, file_id

    print("❌ Ошибка загрузки файла:", response_data)
    return None, None

# Обновление сделки ссылкой на файл
def update_item_with_file_link(item_id, file_url):
    if not file_url:
        print(f"❌ Ошибка: Пустой URL файла для сделки {item_id}. Пропускаем обновление.")
        return

    response = requests.post(BITRIX_ITEM_UPDATE_URL, json={
        "entityTypeId": BITRIX_SMART_PROCESS_ID,
        "id": item_id,
        "fields": {BITRIX_FILE_FIELD: file_url}
    })

    if response.json().get("result"):
        print(f"✅ Сделка {item_id} обновлена ссылкой на файл.")
    else:
        print(f"❌ Ошибка обновления сделки {item_id}:", response.json())

def process_deal(item_id):
    """Обрабатывает конкретную сделку по её ID"""
    if not item_id:
        print("❌ Ошибка: item_id не передан.")
        return

    try:
        item_id = int(item_id)
    except ValueError:
        print("❌ Ошибка: item_id должен быть числом.")
        return

    print(f"🔄 Запрос данных по сделке {item_id}...")

    response = requests.get(BITRIX_ITEM_LIST_URL, params={"entityTypeId": BITRIX_SMART_PROCESS_ID, "filter[id]": str(item_id)})
    data = response.json()

    # Логируем ответ Bitrix24 API
    print("🔍 Ответ от Bitrix24:", json.dumps(data, indent=2, ensure_ascii=False))

    if "result" in data and "items" in data["result"] and data["result"]["items"]:
        deal = data["result"]["items"][0]
        processed_flag = deal.get(BITRIX_PROCESSED_FIELD, "")

        if processed_flag == "1":
            print(f"⚠ Сделка {item_id} уже обработана. Пропускаем...")
            return

        file_name = create_excel_file(deal, item_id)
        file_url, _ = upload_to_bitrix(file_name)

        if file_url:
            update_item_with_file_link(item_id, file_url)
            set_processed_flag(item_id)
            print(f"✅ Сделка {item_id} обработана.")
    else:
        print(f"❌ Сделка {item_id} не найдена.")



# Основной процесс обработки сделок
def process_deals():
    deals = get_target_deals()

    if not deals:
        print("Нет сделок на стадии", TARGET_STAGE_ID)
        return

    for deal in deals:
        item_id = deal["id"]

        processed_flag = deal.get(BITRIX_PROCESSED_FIELD, "")  # Проверяем флаг

        if processed_flag == "1":
            print(f"⚠ Сделка {item_id} уже была обработана. Пропускаем...")
            continue  # Если флаг уже стоит, пропускаем сделку
        
        file_name = create_excel_file(deal, item_id)
        file_url, _ = upload_to_bitrix(file_name)

        if file_url:
            update_item_with_file_link(item_id, file_url)
            set_processed_flag(item_id)  # Устанавливаем "1" после обработки

def set_processed_flag(item_id):
    """ Устанавливаем флаг "1" в текстовое поле, чтобы сделка не обрабатывалась повторно """
    response = requests.post(BITRIX_ITEM_UPDATE_URL, json={
        "entityTypeId": BITRIX_SMART_PROCESS_ID,
        "id": item_id,
        "fields": {BITRIX_PROCESSED_FIELD: "1"}  # Записываем "1" в текстовое поле
    })

    if response.json().get("result"):
        print(f"✅ Флаг '1' установлен для сделки {item_id}")
    else:
        print(f"❌ Ошибка установки флага для сделки {item_id}:", response.json())


# Flask-сервер для запуска скрипта
app = Flask(__name__)

from flask import request  # Добавляем импорт request

@app.route("/", methods=["GET", "POST"])
def run_script():
    item_id = request.args.get("item_id")  # Получаем ID из GET-запроса
    if request.method == "POST":
        data = request.get_json()  # Получаем данные из POST-запроса
        if data and "item_id" in data:
            item_id = data["item_id"]  # Извлекаем ID сделки из тела запроса
    
    if item_id:
        process_deal(item_id)  # Запускаем обработку только этой сделки
        return f"Обработана сделка {item_id}"
    else:
        process_deals()  # Обрабатываем все сделки, если ID не передан
        return "Обработка завершена."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
