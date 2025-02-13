import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
import os

# Указываем путь к файлу
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
XLSX_PATH = os.path.join(BASE_DIR, "../data/output.xlsx")

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
