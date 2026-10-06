from shutil import copy2
from pathlib import Path


DIR = Path(__file__).resolve().parents[1] # Путь к папке /data/.


class DefaultData: # Создание файлов при их отсутствии.
    def __init__(self, template_dir: Path = DIR/"default_data", data_dir: Path = DIR):
        self.template_dir = template_dir
        self.data_dir = data_dir

    def init_files(self) -> None:
        for source in self.template_dir.rglob("*"):
            if not source.is_file():
                continue

            relative = source.relative_to(self.template_dir)
            destination = self.data_dir / relative

            if destination.exists():
                continue

            destination.parent.mkdir(parents=True, exist_ok=True)
            copy2(source, destination)

default_data = DefaultData()