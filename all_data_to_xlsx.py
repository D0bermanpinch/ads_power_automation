import pandas as pd

# Читаем первый файл (data.txt)
with open("data.txt", "r", encoding="utf-8") as file:
    email_lines = file.readlines()

# Читаем второй файл (data2.txt)
with open("data2.txt", "r", encoding="utf-8") as file:
    twitter_lines = file.readlines()

# Обрабатываем строки из первого файла (data.txt)
entries = []
for line in email_lines:
    parts = line.strip().split("|")
    if len(parts) >= 3:
        email = parts[0]
        password = parts[1]
        token = parts[2]  # Токен из первого файла
        entries.append([email, password, token])  # Записываем Email, Password, Token

# Обрабатываем строки из второго файла (data2.txt)
for i, line in enumerate(twitter_lines):
    parts = line.strip().split(":")
    if len(parts) >= 3:  # Минимум 3 части (логин, пароль, почта)
        twitter_login = parts[0]
        twitter_password = parts[1]
        twitter_email = parts[2]

        # Если есть соответствующий Email из первого файла, добавляем данные
        if i < len(entries):
            entries[i].extend([twitter_login, twitter_password, twitter_email])
        else:
            entries.append(["", "", "", twitter_login, twitter_password, twitter_email])

# Создаём DataFrame
df = pd.DataFrame(entries, columns=["Email", "Password", "Token", "Twitter Login", "Twitter Password", "Twitter Email"])

# Сохраняем в Excel по указанному пути
output_path = "data/output.xlsx"
df.to_excel(output_path, index=False)

print(f"Файл сохранён по пути: {output_path}")
