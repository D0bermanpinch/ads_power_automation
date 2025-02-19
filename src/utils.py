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

    account = df.iloc[0].to_dict()

    wb = load_workbook(XLSX_PATH)
    ws = wb.active

    first_row = 2  # Первая строка - заголовки, данные с 2-й строки

    fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
    for cell in ws[first_row]:
        cell.fill = fill

    wb.save(XLSX_PATH)

    return account
