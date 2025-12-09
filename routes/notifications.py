"""
Управление email уведомлениями
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from models.subject import Subject
from core.database import get_db_connection, is_postgresql

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/', methods=['GET', 'POST'])
def notifications_page():
    """Страница подписки на уведомления"""
    subjects = Subject.get_all()
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        # Валидация email
        if not email or '@' not in email or '.' not in email:
            flash('Nederīgs e-pasta adrese!', 'error')
            return render_template('pages/notifications.html', subjects=subjects)
        
        # Сохранение подписки
        try:
            save_subscription(email, request.form, subjects)
            flash(f'✅ Veiksmīgi reģistrēts! Paziņojumi tiks sūtīti uz: {email}', 'success')
        except Exception as e:
            print(f"❌ Ошибка сохранения подписки: {e}")
            flash('Kļūda saglabājot iestatījumus!', 'error')
    
    return render_template('pages/notifications.html', subjects=subjects)


def save_subscription(email, form_data, subjects):
    """Сохранить подписку на уведомления"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        notify_1_day = 'notify_1_day' in form_data
        notify_3_days = 'notify_3_days' in form_data
        
        # Сохраняем основную подписку
        if is_postgresql(conn):
            cursor.execute('''
                INSERT INTO email_subscriptions (email, notify_1_day, notify_3_days, is_active)
                VALUES (%s, %s, %s, TRUE)
                ON CONFLICT (email) 
                DO UPDATE SET 
                    notify_1_day = EXCLUDED.notify_1_day,
                    notify_3_days = EXCLUDED.notify_3_days,
                    is_active = TRUE
            ''', (email, notify_1_day, notify_3_days))
        else:
            # SQLite - сначала проверяем существование
            cursor.execute('SELECT id FROM email_subscriptions WHERE email = ?', (email,))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute('''
                    UPDATE email_subscriptions 
                    SET notify_1_day = ?, notify_3_days = ?, is_active = 1
                    WHERE email = ?
                ''', (1 if notify_1_day else 0, 1 if notify_3_days else 0, email))
            else:
                cursor.execute('''
                    INSERT INTO email_subscriptions (email, notify_1_day, notify_3_days, is_active)
                    VALUES (?, ?, ?, 1)
                ''', (email, 1 if notify_1_day else 0, 1 if notify_3_days else 0))
        
        # Деактивируем все старые подписки на предметы
        if is_postgresql(conn):
            cursor.execute('''
                UPDATE email_subject_subscriptions 
                SET is_active = FALSE 
                WHERE email = %s
            ''', (email,))
        else:
            cursor.execute('''
                UPDATE email_subject_subscriptions 
                SET is_active = 0 
                WHERE email = ?
            ''', (email,))
        
        # Сохраняем выбранные предметы
        for subject in subjects:
            subject_checked = form_data.get(f'subject_{subject.name}')
            
            if subject_checked:
                if is_postgresql(conn):
                    cursor.execute('''
                        INSERT INTO email_subject_subscriptions (email, subject_name, is_active)
                        VALUES (%s, %s, TRUE)
                        ON CONFLICT (email, subject_name) 
                        DO UPDATE SET is_active = TRUE
                    ''', (email, subject.name))
                else:
                    # SQLite
                    cursor.execute('''
                        SELECT id FROM email_subject_subscriptions 
                        WHERE email = ? AND subject_name = ?
                    ''', (email, subject.name))
                    existing = cursor.fetchone()
                    
                    if existing:
                        cursor.execute('''
                            UPDATE email_subject_subscriptions 
                            SET is_active = 1 
                            WHERE email = ? AND subject_name = ?
                        ''', (email, subject.name))
                    else:
                        cursor.execute('''
                            INSERT INTO email_subject_subscriptions (email, subject_name, is_active)
                            VALUES (?, ?, 1)
                        ''', (email, subject.name))
        
        conn.commit()
        print(f"✅ Подписка сохранена для {email}")
        
    except Exception as e:
        print(f"❌ Ошибка сохранения подписки: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()


@notifications_bp.route('/unsubscribe/<email>')
def unsubscribe(email):
    """Отписаться от уведомлений"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if is_postgresql(conn):
            cursor.execute('''
                UPDATE email_subscriptions 
                SET is_active = FALSE 
                WHERE email = %s
            ''', (email,))
        else:
            cursor.execute('''
                UPDATE email_subscriptions 
                SET is_active = 0 
                WHERE email = ?
            ''', (email,))
        
        conn.commit()
        flash('✅ Tu esi veiksmīgi atrakstījies no paziņojumiem!', 'success')
        
    except Exception as e:
        print(f"❌ Ошибка отписки: {e}")
        flash('Kļūda atrakstīšanā!', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('main.index'))


@notifications_bp.route('/api/stats')
def api_notification_stats():
    """API статистика уведомлений"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Количество подписчиков
        cursor.execute('SELECT COUNT(*) FROM email_subscriptions WHERE is_active = TRUE')
        active_subs = cursor.fetchone()[0]
        
        # Количество подписок на предметы
        cursor.execute('SELECT COUNT(*) FROM email_subject_subscriptions WHERE is_active = TRUE')
        subject_subs = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'registered_emails': active_subs,
                'active_subscriptions': subject_subs
            }
        })
        
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)})


@notifications_bp.route('/test_email')
def test_email():
    """Тестирование отправки email (только для хоста)"""
    from flask import session
    
    if not session.get('is_host'):
        flash('Nav tiesību!', 'error')
        return redirect(url_for('auth.login'))
    
    from core.email_service import EmailService
    
    email_service = EmailService()
    
    if not email_service.enabled:
        return """
        <h2>❌ Email сервис не настроен</h2>
        <p>Добавьте SMTP_USERNAME и SMTP_PASSWORD в environment variables</p>
        <a href="/">← Назад</a>
        """
    
    # Отправка тестового письма
    test_email = "test@example.com"
    subject = "Classmate Test Email"
    content = "<h1>✅ Test Email</h1><p>Email система работает!</p>"
    
    success = email_service.send_email(test_email, subject, content)
    
    if success:
        return """
        <h2>✅ Тестовое письмо отправлено!</h2>
        <p>Проверьте логи сервера для подтверждения</p>
        <a href="/">← Назад</a>
        """
    else:
        return """
        <h2>❌ Ошибка отправки</h2>
        <p>Проверьте настройки SMTP и логи сервера</p>
        <a href="/">← Назад</a>
        """