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
    if len(parts) >= 2:  # Берём только Email и Password (без токена из data.txt)
        email = parts[0]
        password = parts[1]
        entries.append([email, password, "", "", "", "", ""])  # Добавляем пустой токен, Twitter-данные и Used

# Обрабатываем строки из второго файла (data2.txt)
for i, line in enumerate(twitter_lines):
    parts = line.strip().split(":")
    if len(parts) >= 4:  # Минимум 4 части (логин, пароль, почта, токен)
        twitter_login = parts[0]
        twitter_password = parts[1]
        twitter_email = parts[2]
        token = parts[3]  # Теперь токен берётся из второго файла

        # Если есть соответствующий Email из первого файла, дополняем данные
        if i < len(entries):
            entries[i][2:] = [token, twitter_login, twitter_password, twitter_email, ""]  # `Used` пока пустая
        else:
            entries.append(["", "", token, twitter_login, twitter_password, twitter_email, ""])  # Добавляем без Email

# Создаём DataFrame с колонкой `Used` в конце
df = pd.DataFrame(entries, columns=["Email", "Password", "Token", "Twitter Login", "Twitter Password", "Twitter Email", "Used"])

# Сохраняем в Excel по указанному пути
output_path = "data/output.xlsx"
df.to_excel(output_path, index=False)

print(f"Файл сохранён по пути: {output_path}")
