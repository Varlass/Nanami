from functools import wraps
from warnings import warn
from collections.abc import Callable
from types import MethodType

from .config import SYNTAX, CHECKING_KEY, CHECKING_VALUE


class Object:
    def __init__(self, items = None):
        self._items = items

    def __getitem__(self, key):
        if self._items is None:
            raise TypeError(f"'{type(self).__name__}' does not support indexing")

        return self._items[key]

    def __getattr__(self, attribute):
        if self._items is not None:
            return getattr(self._items, attribute)

        raise AttributeError(f"{type(self).__name__} object has no attribute {attribute}")

    def _add(self, function: Callable) -> None:
        """Adds a function to the object."""

        if not callable(function):
            raise TypeError(f"'_add' expects a callable, got {type(function).__name__}")

        setattr(self, function.__name__, MethodType(function, self))

class_cache: dict[str, type] = {}

class EmptyKeyWarning(UserWarning):
    pass

class EmptyValueWarning(UserWarning):
    pass


def normaliser(function):
    """Normalises input text into a sequence of ligical lines."""

    @wraps(function)
    def wrapper(text: str) -> list[tuple[str, int]]:
        lines = text.splitlines()
        result = []
        current_line = None
        current_number = 0

        for number, raw_line in enumerate(lines):
            line = raw_line.strip()

            if not line or line.startswith(SYNTAX["commentary"]):
                continue

            if SYNTAX["separator"] in line or line.startswith(tuple(marker for marker in SYNTAX["types"])):
                if current_line is not None:
                    result.append((current_line, current_number))

                current_line = line
                current_number = number + 1

            else:
                if current_line is None:
                    raise KeyError(f"The key is missing from the string.\n{number}: {line}.")

                current_line += "\n" + line

        if current_line is not None:
            result.append((current_line, current_number))

        return function(result)
    return wrapper

def checking(tokens: list) -> None:
    """Checks tokens for non-critical errors."""

    for token in tokens:
        if token["key"] in CHECKING_KEY:
            warn(f"Emply key at {token["path"]}", EmptyKeyWarning)

        if token["value"] in CHECKING_VALUE:
            warn(f"Emply value at {token["path"]}", EmptyValueWarning)


@normaliser
def text_tokeniser(text: str) -> list[dict]:
    """Converts logical lines into tokens."""

    result = []

    for line, path in text:
        token = {"key": None,
                 "value": None,
                 "high": None,
                 "path": f"line {path}"}

        if SYNTAX["separator"] in line:
            token["key"], token["value"] = map(str.strip, line.split(SYNTAX["separator"], 1))

        for marker in SYNTAX["types"]:
            if line.startswith(marker):
                token["key"] = line.strip(f"{marker} ")

                token["value"] = SYNTAX["types"][marker]

                high = 0
                while high < len(line) and line[high] == marker:
                    high += 1
                token["high"] = high

        result.append(token)

    return result

def collection_tokeniser(collection: dict|list|tuple|set) -> list[dict]:
    """Converts a collections into tokens."""

    result = []
    maximum_depth = 0

    def _walk(collection: dict|list|tuple|set, depth: int = 1, path: str = "collection"):
        nonlocal maximum_depth

        if isinstance(collection, dict):
            items = collection.items()

        else:
            items = enumerate(collection, 1)

        for key, value in items:
            if isinstance(collection, dict):
                current_path = f'{path}["{key}"]'

            elif isinstance(collection, set):
                current_path = f'{path}[{value!r}]'

            else:
                current_path = f'{path}[{key - 1}]'

            token = {"key": key,
                    "value": value,
                    "high": None,
                    "path": current_path}

            if isinstance(value, (dict, list, tuple, set)):
                token["value"] = type(value)
                token["high"] = depth
                maximum_depth = max(maximum_depth, depth)

                result.append(token)
                _walk(value, depth + 1, current_path)

            else:
                result.append(token)

    _walk(collection)

    for token in result:
        if token["high"] is not None:
            token["high"] = maximum_depth - token["high"] + 1

    return result

def object_tokeniser(obj: object) -> list[dict]:
    """Converts objects into tokens."""

    result = []
    maximum_depth = 0

    def _walk(obj: object, depth: int = 1, path: str = "obj"):
        nonlocal maximum_depth

        if isinstance(obj, dict):
            items = obj.items()

        elif isinstance(obj, (list, tuple, set)):
            items = enumerate(obj, 1)

        else:
            items = vars(obj).items()

        for key, value in items:
            if hasattr(value, "__dict__"):
                current_path = f'{path}.{key}'

            elif isinstance(obj, dict):
                current_path = f'{path}["{key}"]'

            elif isinstance(obj, set):
                current_path = f'{path}[{value!r}]'

            else:
                current_path = f'{path}[{key - 1}]'

            token = {"key": key,
                    "value": value,
                    "high": None,
                    "path": current_path}


            if isinstance(value, (dict, list, tuple, set)):
                token["value"] = type(value)

            elif hasattr(value, "__dict__"):
                token["value"] = dict

            else:
                result.append(token)
                continue

            token["high"] = depth
            maximum_depth = max(maximum_depth, depth)

            result.append(token)
            _walk(value, depth + 1, current_path)

    _walk(obj)

    for token in result:
        if token["high"] is not None:
            token["high"] = maximum_depth - token["high"] + 1

    return result


def text_builder(tokens: list[dict]) -> str:
    """Builds a formated text from tokens."""

    result = []

    for token in tokens:
        if token["value"] in SYNTAX["types"].values():
            marker = next(marker for marker, collection in SYNTAX["types"].items() if collection is token["value"])

            result.append(f"{marker * token["high"]} {token["key"]} {marker * token["high"]}")

        else:
            result.append(f"{token["key"]}{SYNTAX["separator"]} {token["value"]}")

    return "\n".join(result)

def collection_builder(tokens: list[dict], collection: dict|list|set) -> dict|list|set:
    """Builds a collection from tokens."""

    stack = []

    for token in tokens:
        if token["high"]:
            while stack and stack[-1]["high"] <= token["high"]:
                stack.pop()

        parent = stack[-1]["node"] if stack else collection
        value = token["value"]

        if value in (dict, list, set):
            value = value()

        if isinstance(parent, dict):
            parent[token["key"]] = value

        elif isinstance(parent, list):
            parent.append(value)

        elif isinstance(parent, set):
            parent.add(value)

        if token["high"]:
            stack.append({"node": value,
                          "high": token["high"]})

    return collection

def object_builder(tokens: list[dict], functions: list[Callable]|None, class_name: str) -> Object:
    """Builds an Object from tokens."""

    if class_name not in class_cache.keys():
        class_cache[class_name] = type(class_name, (Object,), {})
    ClassObject = class_cache[class_name]
    obj = ClassObject()

    stack = []

    for token in tokens:
        if token["high"]:
            while stack and stack[-1]["high"] <= token["high"]:
                stack.pop()

        parent = stack[-1]["node"] if stack else obj
        value = token["value"]

        if value is dict:
            value = ClassObject()

        elif value in (list, set):
            value = ClassObject(value())

        if parent._items is None:
            key = token["key"].replace(" ", "_")
            setattr(parent, key, value)

        elif isinstance(parent._items, list):
            parent._items.append(value)

        elif isinstance(parent._items, set):
            parent._items.add(value)

        if token["high"]:
            stack.append({"node": value,
                          "high": token["high"]})

    if functions is not None:
        for function in functions:
            obj._add(function)

    return obj