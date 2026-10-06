from __future__ import annotations
from functools import wraps
from warnings import warn
from collections.abc import Iterable, Callable
from types import MethodType
from typing import Any
from dataclasses import dataclass

from .config import SYNTAX, DEFAULT_NAME, CHECKING_KEY, CHECKING_VALUE


Collection = dict|list|tuple|set
Value = str|int|float|bool
COLLECTIONS = (dict, list, tuple, set)
VALUES = (str, int, float, bool)


class EmptyKeyWarning(UserWarning):
    pass

class EmptyValueWarning(UserWarning):
    pass


class Object:
    def __init__(self, items = None) -> Any:
        self._items = items

    def __getitem__(self, key):
        if self._items is None:
            raise TypeError(f"'{type(self).__name__}' does not support indexing")

        return self._items[key]

    def __getattr__(self, attribute) -> Any:
        if self._items is None:
            raise AttributeError(f"{type(self).__name__} object has no attribute {attribute}")

        return getattr(self._items, attribute)

    def _add(self, function: Callable|Iterable[Callable]) -> None:
        """Adds a function to the object."""

        if isinstance(function, (list, tuple, set)):
            for func in function:
                setattr(self, function.__name__, MethodType(func, self))

        elif isinstance(function, dict):
            for name, func in function:
                setattr(self, name, MethodType(func, self))

        elif callable(function):
            setattr(self, function.__name__, MethodType(function, self))

        else:
            raise TypeError(f"'_add' expects a callable, got {type(function).__name__}")

class_cache: dict[str, object] = {}


@dataclass(slots = True, eq = False)
class Token:
    parent: Token|type = None

    key: Any = None
    value: Any = None

    high: int|None = None

    path: str = ""


def normaliser(function):
    """Normalises input text into a sequence of logical lines."""

    @wraps(function)
    def wrapper(text: str, root_type: type[Collection]) -> list[tuple[str, str]]:
        lines: list[str] = text.splitlines()

        result: list[tuple[str, str]] = []

        current_line: str|None = None
        current_number: int = 0

        for number, raw_line in enumerate(lines, 1):
            line = raw_line.strip()

            if not line or line.startswith(SYNTAX["commentary"]):
                continue

            if SYNTAX["separator"] in line or line.startswith(tuple(marker for marker in SYNTAX["types"])):
                if current_line is not None:
                    result.append((current_line, "line " + str(current_number)))

                current_line = line
                current_number = number

            else:
                if current_line is None:
                    raise KeyError(f"The key is missing from the string.\n{number}: {line}.")

                current_line += "\n" + line

        if current_line is not None:
            result.append((current_line, "line " + str(current_number)))

        return function(result, root_type)
    return wrapper

def checking(tokens: list[Token]) -> None:
    """Checks tokens for non-critical errors."""

    for token in tokens:
        if token.key in CHECKING_KEY:
            warn(f"Emply key at {token.path}", EmptyKeyWarning)

        if token.value in CHECKING_VALUE:
            warn(f"Emply value at {token.path}", EmptyValueWarning)


@normaliser
def text_tokeniser(text: str, root_type: type[Collection]) -> list[Token]:
    """Converts logical lines into tokens."""

    result: list[Token] = []
    parents: list[Token] = []

    for line, path in text:
        token = Token(path = path)

        if SYNTAX["separator"] in line:
            token.parent = parents[-1] if parents else root_type
            token.key, token.value = map(str.strip, line.split(SYNTAX["separator"], 1))

        else:
            for marker in SYNTAX["types"]:
                if line.startswith(marker):
                    token.key = line.strip(f"{marker} ")
                    token.value = SYNTAX["types"][marker]
                    token.high = len(line) - len(line.lstrip(marker))

                    while parents and parents[-1].high >= token.high:
                        parents.pop()
                    token.parent = parents[-1] if parents else root_type

                    parents.append(token)

                    break

        result.append(token)

    return result

def tokeniser(data: object|Collection, core_path: str = DEFAULT_NAME) -> list[Token]:
    """Converts object and collecgion into tokens."""

    result: list[Token] = []

    def _walk(data: object|Collection, parent: Token|type = type(data), max_depth: int = 1, depth: int = 1, path: str = "", ) -> int:
        if isinstance(data, dict):
            items = data.items()
            temp_path = lambda key, _: f'{path}["{key}"]'

        elif isinstance(data, (list, tuple)):
            items =  enumerate(data, 1)
            temp_path = lambda key, _: f'{path}[{key - 1}]'

        elif isinstance(data, set):
            items =  enumerate(data, 1)
            temp_path = lambda _, value: f'{path}{{{value!r}}}'

        else:
            items = vars(data).items()
            temp_path = lambda key, _: f'{path}.{key}'

        for key, value in items:
            current_path = temp_path(key, value)

            if isinstance(data, set): # Проверка текста.
                print(current_path)

            token = Token(parent = parent, key = key, value = value, path = current_path)

            if isinstance(value, Collection):
                token.value = type(value)

            elif hasattr(value, "__dict__"):
                token.value = dict

            else:
                result.append(token)
                continue

            token.high = depth
            max_depth = max(max_depth, depth)

            result.append(token)
            max_depth = _walk(value, token, max_depth, depth + 1, current_path)

        return max_depth


    max_depth = _walk(data = data, path = core_path)

    for token in result:
        if token.high is not None:
            token.high = max_depth - token.high + 1

    return result


def text_builder(tokens: list[Token]) -> str:
    """Builds a formatted text from tokens."""

    result: list[tuple[str, Token]] = []

    for token in tokens:
        if token.value in SYNTAX["types"].values():
            marker = next(marker for marker, collection in SYNTAX["types"].items() if collection is token.value)

            result.append((f"{marker * token.high} {token.key} {marker * token.high}", token))

        else:
            parent_index = next(item for item, (_, parent_token) in enumerate(result) if parent_token is token.parent) if isinstance(token.parent, Token) else -1

            result.insert(parent_index + 1, (f"{token.key}{SYNTAX["separator"]} {token.value}", token))

    return "\n".join(line for line, _ in result)

def collection_builder(tokens: list[Token], collection: Collection|None = None) -> Collection:
    """Builds a collection from tokens."""

    if collection is None:
        collection = next(token.parent() for token in tokens if not isinstance(token.parent, Token))

    parents: list[Token] = [parent for parent in tokens if parent.value in COLLECTIONS]

    while parents:
        min_high = min(parent.high for parent in parents)

        for parent in [parent for parent in parents if parent.high == min_high]:
            children: list[Token] = [child for child in tokens if child.parent is parent]

            collection_type = parent.value

            if collection_type is dict:
                parent.value = {child.key: child.value  for child in children}

            else:
                value = [child.value for child in children]
                parent.value = parent.value(value)

            parents.remove(parent)

    result: list[Token] = [token for token in tokens if not isinstance(token.parent, Token)]

    if isinstance(collection, dict):
        collection.update((token.key, token.value) for token in result)

    elif isinstance(collection, list):
        collection.extend(token.value for token in result)

    elif isinstance(collection, tuple):
        collection += tuple(token.value for token in result)

    elif isinstance(collection, set):
        collection.update(token.value for token in result)

    return collection

def object_builder(tokens: list[Token], functions: list[Callable]|None, class_name: str) -> Object:
    """Builds an Object from tokens."""

    if class_name not in class_cache.keys():
        class_cache[class_name] = type(class_name, (Object,), {})
    ClassObject = class_cache[class_name]
    obj = ClassObject()

    parents: list[Token] = [parent for parent in tokens if parent.value in COLLECTIONS]

    while parents:
        min_high = min(parent.high for parent in parents)

        for parent in [parent for parent in parents if parent.high == min_high]:
            children: list[Token] = [child for child in tokens if child.parent is parent]

            collection_type = parent.value

            if collection_type is dict:
                class_object = ClassObject()
                
                for child in children:
                    setattr(class_object, child.key, child.value)

            else:
                value = [child.value for child in children]
                class_object = ClassObject(collection_type(value))

            parent.value = class_object
            parents.remove(parent)

    result: list[Token] = [token for token in tokens if not isinstance(token.parent, Token)]
    root_type = result[0].parent

    if root_type is dict:
        for token in tokens:
            setattr(obj, token.key, token.value)

    else:
        value = [token.value for token in result]
        obj._items = root_type(value)

    if functions is not None:
        for function in functions:
            obj._add(function)

    return obj