import pandas as pd

data = {
    "Дата": ["2026-04-01", "2026-04-02"],
    "Тип": ["Доход", "Расход"],
    "Категория": ["Зарплата", "Еда"],
    "Сумма": [2000, -50]
}

df = pd.DataFrame(data)

df.to_excel("finance.xlsx", index=False)

print("Excel файл создан")