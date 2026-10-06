import json, yaml
from pathlib import Path
from typing import Protocol, Any, TextIO

from .data_manager import DIR


class Format(Protocol):
    @staticmethod
    def read(file: TextIO) -> str:
        pass

    @staticmethod
    def write(data: Any, file: TextIO) -> None:
        pass

    @staticmethod
    def update(data: Any, file: Path) -> None:
        pass


class TxtFormat:
    @staticmethod
    def read(file: TextIO) -> str:
        return file.read()

    @staticmethod
    def write(data: Any, file: TextIO) -> None:
        file.write(str(data))

    @staticmethod
    def update(data: Any, file: Path) -> None:
        with open(file, mode = "a", encoding = "utf-8") as f:
            f.write(str(data))


class JsonFormat:
    @staticmethod
    def read(file: TextIO) -> dict|None:
        return json.load(file)

    @staticmethod
    def write(data: dict, file: TextIO) -> None:
        json.dump(data, file, ensure_ascii = False, indent = 4)

    @staticmethod
    def update(new_data: dict, file: Path) -> None:
        with open(file, mode =  "r", encoding = "utf-8") as f:
            data = json.load(f) or {}

        data.update(new_data)

        with open(file, mode = "w", encoding = "utf-8") as f:
            json.dump(data, f, ensure_ascii = False, indent = 4)


class YamlFormat:
    @staticmethod
    def read(file: TextIO) -> dict|None:
        return yaml.safe_load(file)

    @staticmethod
    def write(data, file: TextIO) -> None:
        yaml.safe_dump(data, file, allow_unicode = True, sort_keys = False)

    @staticmethod
    def update(new_data: dict, file: Path) -> None:
        with open(file, mode =  "r", encoding = "utf-8") as f:
            data = yaml.safe_load(f) or {}

        data.update(new_data)

        with open(file, mode = "w", encoding = "utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode = True, sort_keys = False)


class FileManager:
    FORMATS: dict[str, type[Format]] = {".txt": TxtFormat,
                                        ".log": TxtFormat,
                                        ".json": JsonFormat,
                                        ".yaml": YamlFormat}

    def __init__(self, file_path: Path|str):
        self.file: Path = self._get_path(file_path)
        self.format: Format = self._get_format(self.file)


    def read(self) -> Any:
        with open(self.file, mode =  "r", encoding = "utf-8") as file:
            return self.format.read(file)

    def write(self, data: Any) -> None:
        with open(self.file, mode = "w", encoding = "utf-8") as file:
            self.format.write(data, file)

    def update(self, data: Any) -> None:
        self.format.update(data, self.file)


    @staticmethod
    def _get_path(file_path: Path|str) -> Path:
        if isinstance(file_path, Path):
            return file_path

        if isinstance(file_path, str):
            return DIR/file_path

        else:
            raise TypeError(f"argument 'file_path' must be a Path or str, got {type(file_path).__name__}")

    def _get_format(self, file_path: Path) -> Format:
        file_format = file_path.suffix.lower()

        if file_format in self.FORMATS:
            return self.FORMATS[file_format]()

        else:
            raise ValueError(f"Unsupported file format: {file_format}")