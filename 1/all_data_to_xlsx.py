import os
import pandas as pd
import random
from datetime import datetime
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_TXT = os.path.join(BASE_DIR, "1", "data.txt")
DATA2_TXT = os.path.join(BASE_DIR, "1", "data2.txt")
CARD_XLSX = os.path.join(BASE_DIR, "1", "cards.xlsx")
NAMES_JSON = os.path.join(BASE_DIR, "1", "names.json")
OUTPUT_XLSX = os.path.join(BASE_DIR, "data", "output.xlsx")

def get_random_cardholder(names):
    return random.choice(names)

def main():
    if not os.path.exists(NAMES_JSON):
        print("Файл names.json не найден.")
        return

    with open(NAMES_JSON, "r", encoding="utf-8") as f:
        names = json.load(f)

    if not os.path.exists(CARD_XLSX):
        print("Файл с картами не найден:", CARD_XLSX)
        return

    card_df = pd.read_excel(CARD_XLSX)
    card_df.columns = ["Card Number", "Expiry", "CVC"]
    card_df["Cardholder"] = [get_random_cardholder(names) for _ in range(len(card_df))]

    if os.path.exists(OUTPUT_XLSX):
        df = pd.read_excel(OUTPUT_XLSX)
    else:
        df = pd.DataFrame(columns=[
            "Created At", "AdsPower ID",
            "Email", "Password", "Token", "Twitter Login", "Twitter Password", "Twitter Email",
            "Card Number", "Expiry", "CVC", "Cardholder",
            "Used", "Result"
        ])

    if not os.path.exists(DATA_TXT) or not os.path.exists(DATA2_TXT):
        print("Файлы data.txt или data2.txt не найдены.")
        return

    with open(DATA_TXT, "r", encoding="utf-8") as f:
        email_lines = f.readlines()

    with open(DATA2_TXT, "r", encoding="utf-8") as f:
        twitter_lines = f.readlines()

    entries = []

    for i, (email_line, twitter_line) in enumerate(zip(email_lines, twitter_lines)):
        email_parts = email_line.strip().split("|")
        twitter_parts = twitter_line.strip().split(":")

        if len(email_parts) < 2 or len(twitter_parts) < 4:
            continue

        email = email_parts[0]
        password = email_parts[1]
        token = twitter_parts[3]
        twitter_login = twitter_parts[0]
        twitter_password = twitter_parts[1]
        twitter_email = twitter_parts[2]

        if i < len(card_df):
            card_number = card_df.iloc[i]["Card Number"]
            expiry = card_df.iloc[i]["Expiry"]
            cvc = str(card_df.iloc[i]["CVC"]).zfill(3)
            cardholder = card_df.iloc[i]["Cardholder"]
        else:
            card_number = expiry = cvc = cardholder = ""

        entry = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "",
            email, password, token, twitter_login, twitter_password, twitter_email,
            card_number, expiry, cvc, cardholder,
            "", ""
        ]
        entries.append(entry)

    new_df = pd.DataFrame(entries, columns=df.columns)
    df = pd.concat([df, new_df], ignore_index=True)
    df.to_excel(OUTPUT_XLSX, index=False)
    print(f"Файл успешно обновлён: {{OUTPUT_XLSX}}")

if __name__ == "__main__":
    main()
