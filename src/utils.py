import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
import os
import json
import random

# Определяем абсолютный путь к файлу profiles.json
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # Путь к корню проекта
PROFILES_PATH = os.path.join(BASE_DIR, "data", "profiles.json")
XLSX_PATH = os.path.join(BASE_DIR, "data", "output.xlsx")
NAMES_PATH=os.path.join(BASE_DIR, "1", "names.json")
AVATAR_PATH=os.path.join(BASE_DIR, "1", "avatars")


def get_unverified_profile():
    """Возвращает serial_number и user_id первого профиля, у которого bought=False"""
    if not os.path.exists(PROFILES_PATH):
        print(f"Ошибка: profiles.json не найден по пути {PROFILES_PATH}.")
        return None

    try:
        with open(PROFILES_PATH, "r", encoding="utf-8") as f:
            profiles = json.load(f)
    except json.JSONDecodeError:
        print(f"Ошибка: profiles.json содержит некорректные данные.")
        return None

    if not profiles:
        print("Ошибка: profiles.json пуст.")
        return None

    for profile in profiles:
        if not profile.get("bought", False):  # Если bought=False
            serial_number = profile.get("serial_number")
            user_id = profile.get("user_id")

            if serial_number and user_id:
                print(f"Найден подходящий профиль: serial_number={serial_number}, user_id={user_id}")
                return serial_number, user_id
            else:
                print("Ошибка: В профиле отсутствуют serial_number или user_id.")

    print("Ошибка: Не найдено доступных профилей (все куплены или повреждены).")
    return None


def get_email_password_from_json(user_id):
    """Получает email и password из profiles.json по user_id"""
    if not os.path.exists(PROFILES_PATH):
        print("Ошибка: profiles.json не найден.")
        return None, None

    try:
        with open(PROFILES_PATH, "r", encoding="utf-8") as f:
            profiles = json.load(f)
    except json.JSONDecodeError:
        print("Ошибка: не удалось прочитать profiles.json.")
        return None, None

    # Ищем профиль по user_id
    for profile in profiles:
        if user_id == profile.get('user_id'):
            email = profile.get("email")
            password = profile.get("password")
            return email, password

def get_twitter_credentials_from_json(user_id):
    """Получает email и password из profiles.json по user_id"""
    if not os.path.exists(PROFILES_PATH):
        print("Ошибка: profiles.json не найден.")
        return None, None

    try:
        with open(PROFILES_PATH, "r", encoding="utf-8") as f:
            profiles = json.load(f)
    except json.JSONDecodeError:
        print("Ошибка: не удалось прочитать profiles.json.")
        return None, None

    # Ищем профиль по user_id
    for profile in profiles:
        if user_id == profile.get('user_id'):
            twitter_login = profile.get("twitter_login")
            twitter_email = profile.get("twitter_email")
            twitter_password = profile.get("twitter_password")
            return twitter_login, twitter_email, twitter_password


def get_credentials():
    """Получает все данные из output.xlsx и передает их в create_profile"""
    df = pd.read_excel(XLSX_PATH)

    if df.empty:
        print("Файл пустой, аккаунты закончились.")
        return None

    # Проверяем, есть ли колонка 'Used'
    if 'Used' not in df.columns:
        print("Ошибка: колонка 'Used' не найдена.")
        return None

    # Перебираем строки и ищем первую не использованную строку
    for index, row in df.iterrows():
        if pd.notna(row["Email"]) and pd.notna(row["Password"]) and (pd.isna(row["Used"]) or row["Used"] != "used"):
            # Если данные не использованы, забираем аккаунт
            email = row["Email"]
            password = row["Password"]
            token = row["Token"]
            twitter_login = row["Twitter Login"]
            twitter_password = row["Twitter Password"]
            twitter_email = row["Twitter Email"]

            # Помечаем строку как использованную
            df["Used"] = df["Used"].astype(str)  # Принудительное приведение типа
            df.at[index, "Used"] = "used"  # Теперь запись будет корректной
            df.to_excel(XLSX_PATH, index=False)  # Сохраняем изменения
            return {
                "Email": email,
                "Password": password,
                "Token": token,
                "Twitter Login": twitter_login,
                "Twitter Password": twitter_password,
                "Twitter Email": twitter_email
            }

    print("Ошибка: Не удалось найти неиспользованные данные.")
    return None

def get_random_name():
    with open(NAMES_PATH, "r", encoding="utf-8") as f:
        names = json.load(f)
    return random.choice(names)

def get_random_avatar():
    avatars = [f for f in os.listdir(AVATAR_PATH) if f.lower().endswith(".jpg")]
    if not avatars:
        raise FileNotFoundError("Нет доступных JPG-аватарок в папке.")
    return os.path.join(AVATAR_PATH, random.choice(avatars))

def set_result_for_email(email, result_text, excel_path=XLSX_PATH):
    """Записывает результат (успех/ошибка) в колонку 'Result' по email"""
    try:
        if not os.path.exists(excel_path):
            print(f"[Result] Файл не найден: {excel_path}")
            return

        df = pd.read_excel(excel_path)
        updated = 0

        for idx, row in df.iterrows():
            if row.get("Email") == email:
                df.at[idx, "Result"] = result_text
                updated += 1

        if updated:
            df.to_excel(excel_path, index=False)
            print(f"[Result] Обновлён результат для {email}: '{result_text}'")
        else:
            print(f"[Result] Email {email} не найден в таблице.")
    except Exception as e:
        print(f"[Result] Ошибка при записи результата: {e}")

def mark_payment_success(email):
    set_result_for_email(email, "Успешно")

def mark_payment_failed(email):
    set_result_for_email(email, "Ошибка оплаты")

def mark_card_declined(email):
    set_result_for_email(email, "Карта отклонена")

