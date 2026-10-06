from collections.abc import Iterable, Callable

from .conversion_internal import (Object, Collection, checking,
                                  text_tokeniser, tokeniser,
                                  text_builder, collection_builder, object_builder)
from .config import DEFAULT_NAME


def text_to_collection(text: str, collection: Collection) -> Collection:
    """
    Parse formatted text into a collection.

    The input text must follow the library's markup rules. The resulting
    collection has the type specefied by the collection argument.
    """

    if isinstance(collection, type):
        collection = collection()

    if not isinstance(text, str):
        raise TypeError(f"argument 'text' must be a str, got {type(text).__name__}")

    if not isinstance(collection, Collection):
        raise TypeError(f"argument 'collection' must be a dict, list, tuple, set or None, got {type(collection).__name__}") 

    tokens = text_tokeniser(text, type(collection))
    checking(tokens)
    result = collection_builder(tokens, collection)

    return result


def text_to_object(text: str, root_type: Collection, functions: Iterable[Callable]|None = None, class_name: str = DEFAULT_NAME) -> Object:
    """
    Parse formatted text into an Object.

    The input text must follow the library's markup rules. The resulting
    object reflects the structure and murkup of the input.
    """

    if functions is not None:
        functions = list(functions)

    if not isinstance(text, str):
        raise TypeError(f"argument 'text' must be a str, got {type(text).__name__}")

    if not isinstance(root_type, Collection):
        raise TypeError(f"argument 'root_type' must be a dict, list, tuple or set, got {type(root_type).__name__}")

    if functions is not None and not all(callable(function) for function in functions):
        raise TypeError(f"argument 'functions' must contain only callable objects, got {type(functions).__name__}")

    if not isinstance(class_name, str):
        raise TypeError(f"argument 'class_name' must be a str, got {type(class_name).__name__}")

    if not isinstance(root_type, type):
        root_type = type(root_type)

    tokens = text_tokeniser(text, root_type)
    checking(tokens)
    result = object_builder(tokens, functions, class_name)

    return result


def collection_to_text(collection: Collection) -> str:
    """
    Convert a collection into formatted text.

    The resulting text follows the library's markup rules and reflects
    the structure and type of the input collection.
    """

    if not isinstance(collection, Collection):
        raise TypeError(f"argument 'collection' must be a dict, list, tuple or set, got {type(collection).__name__}")

    tokens = tokeniser(collection, "collection")
    checking(tokens)
    result = text_builder(tokens)

    return result


def collection_to_object(collection: Collection, functions: Callable|Iterable[Callable]|None = None, class_name: str = DEFAULT_NAME) -> Object:
    """
    Convert a collection into an Object.

    The resulting object reflects the structure and type of the input
    collection.
    """

    if functions is not None:
        functions = list(functions)

    if not isinstance(collection, Collection):
        raise TypeError(f"argument 'collection' must be a dict, list, tuple or set, got {type(collection).__name__}")

    if functions and not all(callable(function) for function in functions):
        raise TypeError(f"argument 'functions' must be a callable objects, got {type(functions).__name__}")

    if not isinstance(class_name, str):
        raise TypeError(f"argument 'class_name' must be a str, got {type(class_name).__name__}")

    tokens = tokeniser(collection, "collection")
    checking(tokens)
    result = object_builder(tokens, functions, class_name)

    return result


def object_to_text(obj: object) -> str:
    """
    Convert an object into formatted text.

    The resulting text follows the library's markup rules and reflects
    the structure and attributes of the input object.
    """

    if not (isinstance(obj, type) or hasattr(obj, "__dict__")):
        raise TypeError(f"argument 'obj' must be an object, got {type(obj).__name__}")

    tokens = tokeniser(obj, "object")
    checking(tokens)
    result = text_builder(tokens)

    return result


def object_to_collection(obj: object, collection: Collection|None = None) -> Collection:
    """
    Convert an object into a collection.

    The resulting collection reflects the structure and attributes of the
    input object. If no collection is specified, a dictionary is used.
    """

    if isinstance(collection, type):
        collection = collection()

    if collection is None:
        collection = {}

    if not (isinstance(obj, type) or hasattr(obj, "__dict__")):
        raise TypeError(f"argument 'obj' must be an object, got {type(obj).__name__}")

    if not isinstance(collection, Collection):
        raise TypeError(f"argument 'collection' must be a dict, list, tuple, set or None, got {type(collection).__name__}")

    tokens = tokeniser(obj, "object")
    checking(tokens)
    result = collection_builder(tokens, collection)

    return result