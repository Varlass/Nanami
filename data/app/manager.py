import json, sqlite3
import copy
from pathlib import Path


DIR = Path(__file__).resolve().parents[1] # Путь к текущей папке.

class Init: # Создание файлов при их отсутствии.
    def __init__(self):
        self.files: dict[Path, str] = {DIR/"quiz_data/list.json": "{}"}

    def init_files(self) -> None:
        for path, data in self.files.items():
            if path.exists():
                continue

            path.parent.mkdir(parents = True, exist_ok = True)
            path.write_text(data, encoding = "utf-8")


class JsonManage: # Работа с .json
    def temp(self, file_name: str, temp: dict, *, root_keys: list|None = None, dir: Path = DIR) -> dict: # Высокоуровневая функция создания шаблона в json.
        data = self.read(file_name, dir = dir)
        
        target = data
        if root_keys:
            for key in root_keys:
                target = target.setdefault(key, {})
        
        self._apply_template(target, temp)
        self.json_write(file_name, data)

        return data

    def _apply_template(self, target: dict, temp: dict) -> dict: # Низкоуровневая функция создания шаблона в json.
        for key, value in temp.items():
            if key not in target:
                target[key] = copy.deepcopy(value)

            elif isinstance(value, dict) and isinstance(target[key], dict):
                self._apply_template(target[key], value)

        return target

    def read(self, file_name: str, *, dir: Path = DIR) -> dict: # Чтение с json.
        path = dir/f"{file_name}.json"


        with open(path, "r", encoding = "utf-8") as file:
            return json.load(file)

    def write(self, file_name: str, data: dict, *, dir: Path = DIR) -> None: # Запись в json.
        path = dir/f"{file_name}.json"

        with open(path, "w", encoding = "utf-8") as file:
            json.dump(data, file, indent = 4, ensure_ascii = False)


json_manage = JsonManage()



class DataBaseManage: # Работа с db.
    TYPE_MAP = {str: "TEXT",
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


db_manage = DataBaseManage()