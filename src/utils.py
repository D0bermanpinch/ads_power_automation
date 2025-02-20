import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
import os
import json

# Указываем путь к файлу
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
XLSX_PATH = os.path.join(BASE_DIR, "../data/output.xlsx")


def get_unverified_profile():
    """Возвращает первый профиль из profiles.json, у которого bought = false"""
    profiles_path = os.path.join(os.path.dirname(__file__), "..", "data", "profiles.json")

    if not os.path.exists(profiles_path):
        return None

    with open(profiles_path, "r", encoding="utf-8") as f:
        profiles = json.load(f)

    for profile in profiles:
        if not profile.get("bought", False):
            return profile["serial_number"], profile["user_id"]

    return None  # Если таких профилей нет


def get_next_account():
    df = pd.read_excel(XLSX_PATH)

    if df.empty:
        print("Файл пустой, аккаунты закончились.")
        return None

    # Проверяем, есть ли колонка 'used'
    if 'used' not in df.columns:
        print("Ошибка: колонка 'used' не найдена.")
        return None

    # Перебираем строки и ищем первую не использованную строку
    for index, row in df.iterrows():
        if pd.notna(row["Email"]) and pd.notna(row["Password"]) and (pd.isna(row["used"]) or row["used"] != "used"):
            # Если данные не использованы, забираем аккаунт
            account = row.to_dict()

            # Помечаем строку как использованную
            df.at[index, "used"] = "used"  # Заполняем колонку "used" значением "used"

            # Сохраняем изменения в Excel
            df.to_excel(XLSX_PATH, index=False)

            return account

    print("Ошибка: Не удалось найти неиспользованные данные.")
    return None


def get_email_password_from_xlsx():
    """Получает email и пароль из первой неиспользованной строки output.xlsx"""
    #xlsx_path = os.path.join(os.path.dirname(__file__), "..", "data", "output.xlsx")

    if not os.path.exists(XLSX_PATH):
        print("Ошибка: output.xlsx не найден.")
        return None, None

    df = pd.read_excel(XLSX_PATH)

    if df.empty:
        print("Ошибка: output.xlsx пустой.")
        return None, None

    # Берём первую строку с данными
    email = df.iloc[1, 0]  # Вторая строка, первая колонка (Email)
    password = df.iloc[1, 1]  # Вторая строка, вторая колонка (Password)

    return email, password


def get_twitter_credentials_from_xlsx():
    """Получает Twitter Login, Twitter Password и Twitter Email из output.xlsx по строкам"""
    if not os.path.exists(XLSX_PATH):
        print("Ошибка: output.xlsx не найден.")
        return None, None, None

    df = pd.read_excel(XLSX_PATH)

    if df.empty:
        print("Ошибка: output.xlsx пустой.")
        return None, None, None

    twitter_logins = []
    twitter_passwords = []
    twitter_emails = []

    # Получаем значения из 4-й, 5-й и 6-й колонок
    for i in range(1, len(df)):  # начинаем с 1, чтобы пропустить заголовок
        twitter_logins.append(df.iloc[i, 3])  # Twitter Login
        twitter_passwords.append(df.iloc[i, 4])  # Twitter Password
        twitter_emails.append(df.iloc[i, 5])  # Twitter Email

    return twitter_logins, twitter_passwords, twitter_emails
