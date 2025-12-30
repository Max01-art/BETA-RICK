"""
WebSocket Service - Real-time updates
"""

from flask_socketio import emit, join_room, leave_room
from datetime import datetime


def register_socketio_handlers(socketio):
    """
    Регистрирует все WebSocket обработчики
    
    Args:
        socketio: SocketIO instance
    """
    
    @socketio.on('connect')
    def handle_connect():
        """Клиент подключился"""
        print(f'Client connected: {datetime.now()}')
        emit('connected', {'message': 'Connected to Classmate'})
    
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Клиент отключился"""
        print(f'Client disconnected: {datetime.now()}')
    
    
    @socketio.on('join_room')
    def handle_join_room(data):
        """Присоединиться к комнате"""
        room = data.get('room')
        if room:
            join_room(room)
            emit('joined_room', {'room': room}, room=room)
    
    
    @socketio.on('leave_room')
    def handle_leave_room(data):
        """Покинуть комнату"""
        room = data.get('room')
        if room:
            leave_room(room)
            emit('left_room', {'room': room}, room=room)
    
    
    @socketio.on('work_added')
    def handle_work_added(data):
        """Новая работа добавлена"""
        emit('work_update', {
            'action': 'added',
            'work': data
        }, broadcast=True)
    
    
    @socketio.on('work_deleted')
    def handle_work_deleted(data):
        """Работа удалена"""
        emit('work_update', {
            'action': 'deleted',
            'work_id': data.get('work_id')
        }, broadcast=True)
    
    
    @socketio.on('work_updated')
    def handle_work_updated(data):
        """Работа обновлена"""
        emit('work_update', {
            'action': 'updated',
            'work': data
        }, broadcast=True)
    
    
    @socketio.on('timer_session')
    def handle_timer_session(data):
        """Сессия таймера завершена"""
        emit('timer_update', data, broadcast=True)
    
    
    @socketio.on('ping')
    def handle_ping():
        """Проверка соединения"""
        emit('pong', {'timestamp': datetime.now().isoformat()})


def broadcast_work_added(socketio, work_data):
    """
    Отправить уведомление о новой работе всем клиентам
    
    Args:
        socketio: SocketIO instance
        work_data: Данные о работе
    """
    socketio.emit('work_update', {
        'action': 'added',
        'work': work_data
    })


def broadcast_work_deleted(socketio, work_id):
    """
    Отправить уведомление об удалении работы
    
    Args:
        socketio: SocketIO instance
        work_id: ID работы
    """
    socketio.emit('work_update', {
        'action': 'deleted',
        'work_id': work_id
    })


def broadcast_work_updated(socketio, work_data):
    """
    Отправить уведомление об обновлении работы
    
    Args:
        socketio: SocketIO instance
        work_data: Данные о работе
    """
    socketio.emit('work_update', {
        'action': 'updated',
        'work': work_data
    })