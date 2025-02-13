import pandas as pd

# Читаем первый файл
with open("data.txt", "r", encoding="utf-8") as file:
    lines = file.readlines()

# Читаем второй файл
with open("data2.txt", "r", encoding="utf-8") as file:
    token_lines = file.readlines()

tokens = []
for line in token_lines:
    parts = line.strip().split(":")
    if len(parts) >= 4:
        tokens.append(parts[-1])  # Берём последний элемент после последнего :

# Обрабатываем строки
entries = []
for i, line in enumerate(lines):
    parts = line.strip().split("|")
    if len(parts) >= 2:
        email = parts[0]
        password = parts[1]
        token = tokens[i] if i < len(tokens) else ""  # Добавляем токен, если он есть
        entries.append([email, password, token])

# Создаём DataFrame
df = pd.DataFrame(entries, columns=["Email", "Password", "Token"])

# Сохраняем в Excel
df.to_excel("output.xlsx", index=False)

print("Файл сохранён как output.xlsx")
