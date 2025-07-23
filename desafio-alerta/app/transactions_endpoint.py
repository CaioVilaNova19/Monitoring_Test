import os
import sqlite3
import statistics
from datetime import datetime, timedelta
from threading import Thread
import subprocess
from flask import Flask, request, jsonify, g, send_from_directory # Import send_from_directory

# Configuration
APP_DIR = os.path.dirname(__file__) # Adicionado para referência de caminho
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'transactions.db'))
STD_MULTIPLIER = float(os.environ.get('STD_MULTIPLIER', 3))
HISTORY_LIMIT = int(os.environ.get('HISTORY_LIMIT', 7))
MIN_HISTORY_POINTS = int(os.environ.get('MIN_HISTORY_POINTS', 3))
FALLBACK_DAYS = int(os.environ.get('FALLBACK_DAYS', 7))
ALERT_STATUSES = {'approved', 'failed', 'denied', 'reversed'}

# Flask app factory
def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        DB_PATH=DB_PATH,
        STD_MULTIPLIER=STD_MULTIPLIER,
        HISTORY_LIMIT=HISTORY_LIMIT,
        MIN_HISTORY_POINTS=MIN_HISTORY_POINTS,
        FALLBACK_DAYS=FALLBACK_DAYS,
        ALERT_STATUSES=ALERT_STATUSES,
    )

    @app.before_request
    def get_db():
        if 'db' not in g:
            g.db = sqlite3.connect(app.config['DB_PATH'], timeout=10)
            g.db.row_factory = sqlite3.Row # Permite acesso por nome de coluna

    @app.teardown_appcontext
    def close_db(exception=None):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    def fetch_history(status: str, timestamp: datetime, exclude_current: bool = True) -> list[int]:
        # Same-day, same-hour history
        hour_start = timestamp.replace(minute=0, second=0, microsecond=0).isoformat()
        day = timestamp.strftime('%Y-%m-%d')
        query = (
            "SELECT count FROM transactions "
            "WHERE status = ? "
            "AND strftime('%Y-%m-%dT%H:00:00', timestamp) = ? "
            "AND strftime('%Y-%m-%d', timestamp) = ? "
        )
        params = [status, hour_start, day]
        if exclude_current:
            query += "AND timestamp < ? "
            params.append(timestamp.isoformat())
        query += "ORDER BY timestamp DESC LIMIT ?"
        params.append(app.config['HISTORY_LIMIT'])
        cur = g.db.execute(query, tuple(params))
        return [row['count'] for row in cur.fetchall()]

    def fetch_history_across_days(status: str, timestamp: datetime) -> list[int]:
        # Same hour across previous days
        hour = timestamp.strftime('%H')
        cutoff = timestamp.isoformat()
        query = (
            "SELECT count FROM transactions "
            "WHERE status = ? "
            "AND strftime('%H', timestamp) = ? "
            "AND timestamp < ? "
            "ORDER BY timestamp DESC LIMIT ?"
        )
        # allow up to HISTORY_LIMIT * FALLBACK_DAYS to gather enough
        limit = app.config['HISTORY_LIMIT'] * app.config['FALLBACK_DAYS']
        cur = g.db.execute(query, (status, hour, cutoff, limit))
        counts = [row['count'] for row in cur.fetchall()]
        return counts[:app.config['HISTORY_LIMIT']]

    def check_anomaly(status: str, current_ts: str, count: int) -> tuple[bool, float, float, float]:
        ts = datetime.fromisoformat(current_ts)
        history = fetch_history(status, ts)
        if len(history) < app.config['MIN_HISTORY_POINTS']:
            history = fetch_history_across_days(status, ts)
        if len(history) < app.config['MIN_HISTORY_POINTS']:
            return False, None, None, None

        mean = statistics.mean(history)
        std = statistics.stdev(history)
        threshold = mean + app.config['STD_MULTIPLIER'] * std
        return count > threshold, mean, std, threshold

    def calculate_severity(count: int, mean: float, std: float) -> str:
        if std == 0 or mean is None: # Adicionado 'mean is None' para caso não haja histórico
            return "unknown"
        z = (count - mean) / std
        if z >= 3:
            return "high"
        if z >= 2:
            return "medium"
        return "low"

    def trigger_alerts(status: str, timestamp: str, count: int):
        try:
            # Assumindo que email_alert.py e telegram_alert.py estão na mesma pasta do endpoint
            email_script_path = os.path.join(APP_DIR, 'email_alert.py')
            telegram_script_path = os.path.join(APP_DIR, 'telegram_alert.py')

            subprocess.Popen(["python", email_script_path, status, timestamp, str(count)])
            subprocess.Popen(["python", telegram_script_path, status, timestamp, str(count)])
            app.logger.info(f"Alert fired for {status} at {timestamp} ({count})")
        except Exception as err:
            app.logger.error(f"Failed to trigger alerts: {err}")

    # --- ROTA EXISTENTE: receive_transaction ---
    @app.route("/receive_transaction", methods=["POST"])
    def receive_transaction():
        data = request.get_json(force=True)
        timestamp = data.get('timestamp')
        status = data.get('status')
        count = data.get('count')

        # Input validation
        if not timestamp or not status or count is None:
            return jsonify(error="Missing 'timestamp', 'status', or 'count'"), 400
        if status not in app.config['ALERT_STATUSES'] and status != 'approved': # Incluir 'approved' para processamento, mesmo se não for alertável no trigger
            return jsonify(error=f"Unsupported status '{status}'"), 400
        try:
            count = int(count)
            datetime.fromisoformat(timestamp)
        except Exception as e:
            return jsonify(error=f"Invalid data format: {e}"), 400

        # Check anomaly before insertion
        alert, mean, std, threshold = check_anomaly(status, timestamp, count)
        severity = calculate_severity(count, mean, std) if mean is not None else "unknown"

        # Persist and respond
        g.db.execute(
            "INSERT INTO transactions(timestamp, status, count) VALUES (?, ?, ?)",
            (timestamp, status, count)
        )
        g.db.commit()

        # Trigger alerts ONLY for statuses in ALERT_STATUSES AND severity 'high'
        if status in app.config['ALERT_STATUSES'] and alert and severity == "high":
            trigger_alerts(status, timestamp, count)

        response = {
            "alert": alert,
            "status": status,
            "severity": severity,
            "expected_range": {
                "mean": round(mean, 2),
                "std": round(std, 2),
                "max_normal_value": round(threshold, 2)
            } if mean is not None else None,
            "message": (
                f"🚨 Anomaly detected (severity: {severity})"
                if alert else "Transaction within normal range"
            )
        }
        return jsonify(response)


    # --- NOVA ROTA: get_dashboard_data ---
    @app.route("/dashboard_data", methods=["GET"])
    def get_dashboard_data():
        try:
            conn = g.db # Usar a conexão do g.db
            cursor = conn.cursor()

            # Query para pegar os dados agregados por status e hora nos últimos 24 horas
            # Usando datetime.now() e timedelta para o fuso horário correto (Brasil -03)
            current_time_utc = datetime.utcnow() # Pega o tempo UTC
            current_time_local = datetime.now() # Pega o tempo local (Brasil -03)

            # Para os dados do dashboard, queremos ver as horas locais.
            # Ajustamos a janela de 24h para terminar na hora atual local.
            twenty_four_hours_ago_local = current_time_local - timedelta(hours=24)
            # A string para a query precisa ser em ISO format
            twenty_four_hours_ago_str = twenty_four_hours_ago_local.isoformat(sep=' ', timespec='seconds')


            # Nota sobre STDEV no SQLite: Ele não é uma função padrão.
            # Precisamos obter todos os 'counts' e calcular no Python.
            # STDEV no SQLite é geralmente uma função agregada personalizada ou necessita de uma biblioteca.
            # Aqui, vou manter a abordagem de GROUP_CONCAT e cálculo em Python, que é mais portátil.
            
            cursor.execute("""
                SELECT
                    strftime('%Y-%m-%dT%H:00:00', timestamp) as hour_window,
                    status,
                    GROUP_CONCAT(count) as counts_list
                FROM transactions
                WHERE timestamp >= ?
                GROUP BY hour_window, status
                ORDER BY hour_window ASC, status ASC;
            """, (twenty_four_hours_ago_str,))
            
            rows_metrics = cursor.fetchall()

            dashboard_metrics = []
            for row in rows_metrics:
                # row é um sqlite3.Row, então podemos acessar por nome
                hour_window = row['hour_window']
                status = row['status']
                counts_list_str = row['counts_list']
                
                counts = [float(c) for c in counts_list_str.split(',')]
                
                avg = statistics.mean(counts)
                std = statistics.stdev(counts) if len(counts) > 1 else 0.0
                threshold = avg + app.config['STD_MULTIPLIER'] * std

                dashboard_metrics.append({
                    "hour_window": hour_window,
                    "status": status,
                    "mean_count": round(avg, 2),
                    "std_count": round(std, 2),
                    "max_normal_value": round(threshold, 2),
                    "num_points": len(counts)
                })

            # Pega as transações recentes E RECALCULA SEU STATUS DE ALERTA para o dashboard
            # Não filtrando por status aqui, para o dashboard poder mostrar todos
            cursor.execute("""
                SELECT timestamp, status, count FROM transactions
                ORDER BY timestamp DESC
                LIMIT 50;
            """)
            raw_recent_transactions = cursor.fetchall()
            
            processed_recent_transactions = []
            for r in raw_recent_transactions:
                timestamp = r['timestamp']
                status = r['status']
                count = r['count']

                # Reusa a lógica de detecção de anomalia para cada transação recente
                # A função check_anomaly e calculate_severity são as mesmas usadas para /receive_transaction
                alert, mean, std, threshold = check_anomaly(status, timestamp, count)
                severity = calculate_severity(count, mean, std) if mean is not None else "unknown"
                
                processed_recent_transactions.append({
                    "timestamp": timestamp,
                    "status": status,
                    "count": count,
                    "alert": alert,
                    "severity": severity # Retorna o nível de severidade
                })

            return jsonify({
                "metrics_by_hour_status": dashboard_metrics,
                "recent_transactions": processed_recent_transactions
            })

        except sqlite3.Error as e:
            app.logger.error(f"Erro no endpoint /dashboard_data: {e}")
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        except Exception as e:
            app.logger.error(f"Erro inesperado no endpoint /dashboard_data: {e}")
            return jsonify({'error': f'Internal server error: {str(e)}'}), 500
    
    # --- Rota para servir o dashboard.html ---
    @app.route('/')
    def index():
        return send_from_directory(APP_DIR, 'dashboard.html')

    return app


if __name__ == '__main__':
    # Garante que a pasta 'data' existe e inicializa o DB
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            timestamp TEXT,
            status TEXT,
            count INTEGER
        )
        """
    )
    conn.commit()
    conn.close()

    app = create_app()
    # Adicionando um logger básico para ver as mensagens no console
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    app.logger.setLevel(logging.INFO)

    # Usa app.run() diretamente para simplificar, mas use gunicorn/waitress em produção
    app.run(port=5000, debug=False, use_reloader=False)

    # O bloco input() e Thread.daemon não são mais necessários com app.run() direto para desenvolvimento
    # Para produção, você usaria um WSGI server (Gunicorn, Waitress) para rodar o app.
    # print("Flask server running on port 5000")
    # input("Press Enter to stop...")