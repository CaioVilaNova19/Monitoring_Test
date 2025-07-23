import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys # Importa o módulo sys para acessar argumentos de linha de comando

def send_email_alert(status, detected_at, current_count):
    """
    Envia um e-mail de alerta para uma anomalia detectada.
    Recebe o status, timestamp da detecção e a contagem atual como argumentos.
    """
   
    smtp_server = 'smtp.example.com' 
    smtp_port = 587                  
    sender_email = 'your_email@example.com'
    receiver_email = 'destinatary_alerta@example.com'
    
    password = 'your_password' 


    subject = f'ALERTA DE ANOMALIA: Status {status.upper()}'
    body = (
        f"Anomaly detected!\n\n"
        f"Transaction Status: {status}\n"
        f"Detected at: {detected_at}\n"
        f"Current count: {current_count}\n\n"
        f"Verify Monitoring System for more details"
    )

    # Constrói a mensagem de e-mail
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Conecta ao servidor SMTP e envia o e-mail
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls() # Inicia a segurança TLS
            server.login(sender_email, password)
            server.send_message(msg)
        print(f"📧 Email alert send to {receiver_email} por status: {status}")
    except Exception as e:
        print(f"❌ Fail to send email alert for status {status}: {e}")

if __name__ == '__main__':
    
    if len(sys.argv) != 4:
        print("Uso: python email_alert.py <status> <detected_at> <current_count>")
        sys.exit(1)

    
    status_arg = sys.argv[1]
    detected_at_arg = sys.argv[2]
    current_count_arg = int(sys.argv[3])

    
    send_email_alert(status_arg, detected_at_arg, current_count_arg)