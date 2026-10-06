import sqlite3
from pathlib import Path

from .data_manager import DIR


class SQLiteManager: # Работа с db.
    TYPE_MAP: dict[type, str] = {str: "TEXT",
                                 int: "INTEGER",
                                 float: "REAL",
                                 bool: "INTEGER",
                                 bytes: "BLOB"}

    def __init__(self):
        self.connections = {}

    def table_create(self, file_name: str, table_name: str|None = None, *, dir: Path = DIR, **schemes): # Создание таблицы в db.
        table_name = table_name or file_name

        columns = []
        for column_name, py_type in schemes.items():
            if not isinstance(py_type, type):
                py_type = type(py_type)

            sql_type = self.TYPE_MAP[py_type]
            columns.append(f"{column_name} {sql_type}")

        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({", ".join(columns)})"

        self.execute(file_name, query, dir = dir)

    def fetch(self, file_name: str, query: str, params: list|tuple = (), *, dir: Path = DIR): # Чтение db.
        _, cursor = self._connect(file_name, dir = dir)

        cursor.execute(query, params)

        return cursor.fetchall()

    def execute(self, file_name: str, query: str, params: list|tuple = (), *, dir: Path = DIR): # Запись в db.
        conn, cursor = self._connect(file_name, dir = dir)

        if isinstance(params, (list, tuple)) and params and isinstance(params[0], (list, tuple, dict)):
            cursor.executemany(query, params)

        else:
            cursor.execute(query, params)

        conn.commit()

    def _connect(self, file_name: str, *, dir: Path = DIR): # Низкоуровневая функция подключения к db.
        if file_name not in self.connections:
            self.connections[file_name] = sqlite3.connect(dir/f"{file_name}.db")

        return self.connections[file_name], self.connections[file_name].cursor()

    def close(self, file_name: str) -> None: # Закрытие 1 db подключения.
        conn = self.connections.pop(file_name, None)
        if conn:
            try:
                conn.close()
            except Exception:
                pass

    def close_all(self) -> None: # Закрытие всех db подключений.
        for conn in self.connections.values():
            conn.close()
        self.connections.clear()

sqlitemanager = SQLiteManager()