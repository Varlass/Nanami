from types import MethodType, FunctionType


SYNTAX = {"types": {"=": dict,
                    "-": list},
          "comment": "#",
          "separ": ":"}

class Object:
    def __init__(self, items = None):
        self._items = items
        self._my_getitem = None

    def __getitem__(self, key):
        if self._my_getitem is not None:
            return self._my_getitem(self, key)

        if self._items is None:
            raise TypeError(f"{type(self).__name__} не поддерживает индексацию")

        return self._items[key]

    def _add(self, func):
        if not callable(func):
            raise TypeError(f"Функция ожидает callable, а не {type(func)}")

        if func.__name__ == "__getitem__":
            self._my_getitem = func

        setattr(self, func.__name__, MethodType(func, self))


def text_to_container(text: str, container: dict|list = None) -> tuple[dict|list, list]:
    if container is None:
        container = []

    result = container
    bugs = []

    if not isinstance(text, str):
        raise TypeError(f"Функция ожидает str, а не {type(text)}")

    if not isinstance(container, (dict, list)):
        raise TypeError(f"Функция ожидает dict или list, а не {type(container)}") 

    lines, bugs =  _normaliser(text)
    tokens = _tokeniser(lines)
    notices = _checking(tokens, lines)

    if not bugs:
        result = _ast_builder(tokens, container)

    return result, notices + bugs

def container_to_object(container: dict|list|tuple, functions: list[FunctionType]|None = None) -> Object:
    if isinstance(container, dict):
        obj = Object()

        for key, value in container.items():
            if isinstance(value, (dict, list, tuple)):
                value = container_to_object(value)

            setattr(obj, key, value)

    elif isinstance(container, (list, tuple)):
        obj = Object([container_to_object(value) if isinstance(value, (dict, list, tuple)) else value for value in container])

    else:
        raise TypeError(f"Функция ожидает dict, list или tuple, а не {type(container)}")

    if functions is not None:
        for func in functions:
            obj._add(func)

    return obj

def object_to_container(obj: object) -> dict:
    if isinstance(obj, dict):
        return {key: object_to_container(value) for key, value in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [object_to_container(value) for value in obj]

    if hasattr(obj, "__dict__"):
        return {key: object_to_container(value) for key, value in obj.__dict__.items()}

    return obj


def _normaliser(text: str) -> list:
    lines = text.splitlines()

    result = []
    bugs = []
    current_line = None
    current_number = 0

    for number, raw in enumerate(lines):
        line = raw.strip()

        if not line or line.startswith(SYNTAX["comment"]):
            continue

        if SYNTAX["separ"] in line or line.startswith(tuple(marker for marker in SYNTAX["types"])):
            if current_line is not None:
                result.append((current_line, current_number))

            current_line = line
            current_number = number + 1

        else:
            if current_line is None:
                bugs.append({"error_type": "MISSING_KEY",
                             "error_text": "отсутствует ключ",
                             "text_content": line,
                             "text_line": number + 1})
                continue

            current_line += "\n" + line

    if current_line is not None:
        result.append((current_line, current_number))

    return result, bugs

def _tokeniser(lines: list) -> list:
    result = []

    for index, line in enumerate(lines):
        line = line[0]

        token = {"key": None,
                 "value": None,
                 "high": None,
                 "index": index}

        if SYNTAX["separ"] in line:
            token["key"], token["value"] = map(str.strip, line.split(SYNTAX["separ"], 1))

        for marker in SYNTAX["types"]:
            if line.startswith(marker):
                token["key"] = line.strip(f"{marker} ")

                token["value"] = SYNTAX["types"][marker]()

                high = 0
                while high < len(line) and line[high] == marker:
                    high += 1
                token["high"] = high

        result.append(token)

    return result

def _checking(tokens: list, lines: list) -> list:
    notices = []

    for token in tokens:
        if token["key"] == "":
            notices.append({"error_type": "EMPTY_KEY",
                            "error_text": "пустой ключ",
                            "text_content": lines[token["index"]][0],
                            "text_line": lines[token["index"]][1]})

        if token["value"] == "":
            notices.append({"error_type": "EMPTY_VALUE",
                            "error_text": "пустое значение",
                            "text_content": lines[token["index"]][0],
                            "text_line": lines[token["index"]][1]})

    return notices

def _ast_builder(tokens: list, container: dict|list) -> dict:
    stack = []

    for token in tokens:
        if token["high"]:
            while stack and stack[-1]["high"] <= token["high"]:
                stack.pop()

        parent = stack[-1]["node"] if stack else container

        if isinstance(parent, dict):
            parent[token["key"]] = token["value"]

        else:
            parent.append(token["value"])

        if token["high"]:
            stack.append({"node": token["value"],
                          "high": token["high"]})

    return container