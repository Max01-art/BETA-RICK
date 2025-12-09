"""
Email service for notifications
Сервис для отправки email уведомлений
"""
import smtplib
import queue
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os


# Email queue for async sending
email_queue = queue.Queue()
email_thread = None


class EmailService:
    """Email service class"""
    
    def __init__(self):
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', 587))
        self.smtp_username = os.environ.get('SMTP_USERNAME')
        self.smtp_password = os.environ.get('SMTP_PASSWORD')
        self.enabled = bool(self.smtp_username and self.smtp_password)
    
    def send_email(self, to_email, subject, html_content):
        """
        Отправить email (синхронно)
        
        Args:
            to_email: Email получателя
            subject: Тема письма
            html_content: HTML содержимое
        
        Returns:
            bool: True если успешно
        """
        if not self.enabled:
            print("❌ Email не настроен (нет SMTP_USERNAME/PASSWORD)")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(html_content, 'html'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email отправлен: {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка отправки email: {e}")
            return False
    
    def send_notification_email(self, to_email, work, days_until):
        """
        Отправить уведомление о работе
        
        Args:
            to_email: Email получателя
            work: Словарь с данными работы
            days_until: Дней до работы (1 или 3)
        
        Returns:
            bool: True если успешно
        """
        subject = f"🔔 Напоминание: {work['subject']} - {work.get('type', 'Работа')}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    line-height: 1.6; 
                    color: #333; 
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 0;
                }}
                .container {{ 
                    max-width: 600px; 
                    margin: 20px auto; 
                    padding: 0;
                    background: white;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{ 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; 
                    padding: 30px 20px; 
                    text-align: center;
                }}
                .header h2 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .content {{ 
                    padding: 30px 20px;
                }}
                .badge {{ 
                    display: inline-block; 
                    padding: 10px 20px; 
                    background: #ff3b30; 
                    color: white; 
                    border-radius: 20px; 
                    font-weight: bold;
                    font-size: 18px;
                    margin: 20px 0;
                }}
                .info {{ 
                    background: #f9f9f9; 
                    padding: 20px; 
                    margin: 20px 0; 
                    border-radius: 8px; 
                    border-left: 4px solid #2E5BFF;
                }}
                .info p {{
                    margin: 10px 0;
                }}
                .info strong {{
                    color: #2E5BFF;
                }}
                .footer {{ 
                    margin-top: 30px; 
                    padding-top: 20px; 
                    border-top: 1px solid #ddd; 
                    text-align: center; 
                    color: #777; 
                    font-size: 12px;
                }}
                .cta-button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background: #2E5BFF;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>📚 Classmate Напоминание</h2>
                </div>
                
                <div class="content">
                    <div style="text-align: center;">
                        <span class="badge">
                            {'🚨 ЗАВТРА' if days_until == 1 else '⏰ Через 3 дня'}
                        </span>
                    </div>
                    
                    <div class="info">
                        <p><strong>📚 Предмет:</strong> {work['subject']}</p>
                        <p><strong>📝 Тип:</strong> {work.get('type', 'Работа')}</p>
                        <p><strong>📅 Дата:</strong> {work['date']}</p>
                        {f"<p><strong>🕐 Время:</strong> {work['time']}</p>" if work.get('time') and work['time'] != '23:59' else ''}
                        {f"<p><strong>📋 Описание:</strong> {work['description']}</p>" if work.get('description') else ''}
                    </div>
                    
                    <p style="text-align: center; font-size: 16px;">
                        Не забудь подготовиться! 💪
                    </p>
                    
                    <div style="text-align: center;">
                        <a href="#" class="cta-button">Открыть Classmate</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Это автоматическое уведомление от Classmate</p>
                    <p><small>Чтобы отписаться, перейди в настройки уведомлений</small></p>
                    <p><small>&copy; {datetime.now().year} Classmate. Все права защищены.</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)


def email_worker():
    """
    Фоновый процесс для отправки email
    Работает в отдельном потоке
    """
    email_service = EmailService()
    
    while True:
        try:
            task = email_queue.get(timeout=300)  # 5 минут таймаут
            if task is None:  # Stop signal
                break
            
            to_email, subject, html_content = task
            print(f"📧 Отправка email из очереди: {to_email}")
            email_service.send_email(to_email, subject, html_content)
            email_queue.task_done()
            
        except queue.Empty:
            continue
        except Exception as e:
            print(f"❌ Ошибка в email worker: {e}")


def start_email_worker():
    """
    Запустить фоновый процесс email
    """
    global email_thread
    
    if email_thread is None or not email_thread.is_alive():
        email_thread = threading.Thread(target=email_worker, daemon=True)
        email_thread.start()
        print("✅ Email worker запущен")


def send_email_async(to_email, subject, html_content):
    """
    Отправить email асинхронно (через очередь)
    
    Args:
        to_email: Email получателя
        subject: Тема письма
        html_content: HTML содержимое
    
    Returns:
        bool: True если добавлено в очередь
    """
    try:
        email_queue.put((to_email, subject, html_content))
        print(f"✅ Email добавлен в очередь: {to_email}")
        return True
    except Exception as e:
        print(f"❌ Ошибка добавления в очередь: {e}")
        return False


def send_email(to_email, subject, html_content):
    """
    Отправить email синхронно
    
    Args:
        to_email: Email получателя
        subject: Тема письма
        html_content: HTML содержимое
    
    Returns:
        bool: True если успешно
    """
    email_service = EmailService()
    return email_service.send_email(to_email, subject, html_content)


# Запускаем worker при импорте модуля
start_email_worker()