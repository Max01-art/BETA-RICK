"""
Инициализация модуля models
"""
from .database import get_db_connection, init_database, is_postgresql_connection
from .subjects import load_subjects, save_subject, delete_subject
from .tests import load_tests, save_test, delete_test
from .homework import load_homework, save_homework, delete_homework

__all__ = [
    'get_db_connection',
    'init_database',
    'is_postgresql_connection',
    'load_subjects',
    'save_subject',
    'delete_subject',
    'load_tests',
    'save_test',
    'delete_test',
    'load_homework',
    'save_homework',
    'delete_homework',
]