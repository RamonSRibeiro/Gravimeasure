"""
Middleware para habilitar Foreign Key constraints no SQLite
"""

from django.db.backends.sqlite3.base import DatabaseWrapper
from django.db.backends.signals import connection_created
from django.dispatch import receiver


@receiver(connection_created)
def enable_sqlite_fk_constraints(sender, connection, **kwargs):
    """
    Habilita constraints de foreign key no SQLite quando a conexão é criada
    """
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA foreign_keys = ON;')
        cursor.close()
