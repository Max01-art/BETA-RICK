"""
Models package
Модели данных для работы с БД
"""
from .subject import Subject
from .test import Test
from .homework import Homework
from .news import News
from .user import User
from .update import Update
from .terms import Terms

__all__ = [
    'Subject',
    'Test',
    'Homework',
    'News',
    'User',
    'Update',
    'Terms'
]