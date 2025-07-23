import os
import sqlite3
import pandas as pd

DATA_DIR = os.path.abspath(os.path.join("..", "..", "desafio-alerta", "data"))

auth_codes_csv = os.path.join(DATA_DIR, 'transactions_auth_codes.csv')
transactions_csv = os.path.join(DATA_DIR, 'transactions.csv')

df_auth_codes = pd.read_csv(auth_codes_csv, sep=",")
df_transactions = pd.read_csv(transactions_csv, sep=",")

db_path = os.path.join(DATA_DIR, 'transactions.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS auth_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    auth_code TEXT,
    count INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    status TEXT,
    count INTEGER
)
""")

df_auth_codes.to_sql('auth_codes', conn, if_exists='append', index=False)
df_transactions.to_sql('transactions', conn, if_exists='append', index=False)

conn.commit()
conn.close()

print("Database successfully initialized")