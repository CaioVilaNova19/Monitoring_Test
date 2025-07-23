import os
import time
import pandas as pd
import requests
from datetime import datetime, timedelta
import random
import sqlite3 # Importação mantida, mas sqlite3 não será usado neste script


ENDPOINT_URL = os.environ.get('ENDPOINT_URL', 'http://127.0.0.1:5000/receive_transaction')
# CSV_PATH não será usado para escrita, apenas para referência (se aplicável)
CSV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'transactions.csv'))
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'transactions.db')) # Não será usado para limpar o DB aqui
STREAM_SPEED = float(os.environ.get('STREAM_SPEED', 0.5))
-
data = []

target_anomaly_hour = datetime(2025, 7, 22, 21, 0, 0) # Exemplo: 22 de Julho de 2025, 21:00:00

# 1. Gerar dados "normais" antes e depois da hora da anomalia, simulando tráfego contínuo.
# Estes não são essenciais para a detecção da anomalia, mas simulam um fluxo real.
# Geraremos dados por 30 minutos, abrangendo a hora da anomalia.
start_time = target_anomaly_hour - timedelta(minutes=15)

for i in range(30):
    ts = start_time + timedelta(minutes=i)
    
    # Garantir que os 'approved' tenham contagens mais altas, e outros baixas, como no seu CSV
    if ts.minute % 5 == 0: # A cada 5 minutos, um approved
        status = 'approved'
        count = random.randint(100, 150) # Contagens altas para approved
    else:
        status = random.choice(['failed', 'denied', 'reversed'])
        count = random.randint(1, 5) # Contagens baixas para outros status
    
    data.append({
        'timestamp': ts.isoformat(),
        'status': status,
        'count': count
    })

# 2. Injetar a transação anômala para 'denied' em um minuto específico dentro da hora alvo.
# Escolha um minuto que o `transactions_endpoint.py` possa calcular a baseline.
# Por exemplo, no minuto 6 da hora (21:06:00), após alguns minutos de dados "normais" dessa mesma hora.
anomaly_ts = target_anomaly_hour + timedelta(minutes=6) # 2025-07-22T21:06:00
data.append({
    'timestamp': anomaly_ts.isoformat(),
    'status': 'denied',
    'count': 5000 # A anomalia! Valor bem alto para garantir o disparo.
})

# Opcional: Para garantir que a anomalia seja processada por último, você pode reordenar a lista:
# data.sort(key=lambda x: datetime.fromisoformat(x['timestamp']))

# --- End of data generation logic ---

# Criar o DataFrame
df = pd.DataFrame(data)

# As linhas que salvariam no CSV CONTINUAM REMOVIDAS/COMENTADAS para não sobrescrever o histórico:
# df.to_csv(CSV_PATH, index=False)
# print(f"✔️ Test data saved to {CSV_PATH}")

# Envia dados para o endpoint
print(f"🔄 Starting data stream to {ENDPOINT_URL} (sleep {STREAM_SPEED}s)...\n")
for idx, row in df.iterrows():
    payload = {
        'timestamp': row['timestamp'],
        'status': row['status'],
        'count': int(row['count'])
    }
    try:
        resp = requests.post(ENDPOINT_URL, json=payload, timeout=5)
        print(f"[{row['timestamp']}] Sent {payload} -> {resp.status_code} {resp.json()}")
    except Exception as e:
        print(f"Failed to send {payload}: {e}")
    time.sleep(STREAM_SPEED)

print("Stream finished.")
