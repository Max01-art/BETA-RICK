"""
Core package initialization
"""

from .database import (
    get_db_connection,
    is_postgresql,
    init_db,
    execute_query
)

__all__ = [
    'get_db_connection',
    'is_postgresql',
    'init_db',
    'execute_query'
]