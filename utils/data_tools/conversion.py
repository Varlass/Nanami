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

_class_cache: dict[str, type] = {}


def text_to_collection(text: str, container: dict|list = None, notices_handler: bool = False) -> dict|list|tuple[dict|list, list]:
    if container is None:
        container = []

    notices = []

    if not isinstance(text, str):
        raise TypeError(f"Функция ожидает str, а не {type(text)}")

    if not isinstance(container, (dict, list)):
        raise TypeError(f"Функция ожидает dict или list, а не {type(container)}") 

    lines, bugs =  _normaliser(text)
    tokens = _tokeniser(lines)

    if not bugs and not notices_handler:
        return _ast_builder(tokens, container)

    if notices_handler:
        notices = _checking(tokens, lines)

    return container, bugs + notices

def collection_to_object(container: dict|list|tuple|set, functions: set[FunctionType]|None = None, class_name: str = "Object") -> Object:
    if class_name not in _class_cache.keys():
        _class_cache[class_name] = type(class_name, (Object,), {})
    ClassObject = _class_cache[class_name]

    if isinstance(container, dict):
        obj = ClassObject()

        for key, value in container.items():
            if isinstance(value, dict):
                value = collection_to_object(value, str(key))

            elif isinstance(value, (list, tuple, set)):
                value = collection_to_object(value)

            setattr(obj, key, value)

    elif isinstance(container, (list, tuple, set)):
        obj = ClassObject([collection_to_object(value) if isinstance(value, (dict, list, tuple, set)) else value for value in container])

    else:
        raise TypeError(f"Функция ожидает dict, list, tuple или set, а не {type(container)}")

    if functions is not None:
        for function in functions:
            obj._add(function)

    return obj

def object_to_collection(obj: object) -> dict:
    if not hasattr(obj, "__dict__"):
        raise TypeError(f"Функция ожидает object, а не {type(obj)}")

    def convert(value):
        if hasattr(value, "__dict__"):
            return {key: convert(value) for key, value in value.__dict__.items()}

        if isinstance(value, dict):
            return {key: convert(value) for key, value in value.items()}

        if isinstance(value, (list, tuple, set)):
            return [convert(value) for value in value]

        return value

    return convert(obj)


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