"""
Like pydantic, but only for dataclasses and only for types that exist in TOML
files, and also with fewer features in general.

Not related (though similar) to the datacast package on PyPI
"""

import dataclasses
from datetime import date, datetime, time
import sys
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_type_hints,
)
from .errors import ConfigError
from .logging import didyoumean, log

if sys.version_info[:2] >= (3, 8):
    from typing import get_args, get_origin
elif sys.version_info[:2] >= (3, 7):
    from typing_extensions import get_args, get_origin
else:

    def get_origin(t: Type[Any]) -> Optional[Type[Any]]:
        return getattr(t, "__origin__", None)

    def get_args(t: Type[Any]) -> Tuple[Any, ...]:
        return getattr(t, "__args__", ())


T = TypeVar("T")

PRIMITIVES = {
    int: "integer",
    str: "string",
    float: "float",
    bool: "boolean",
    date: "date",
    time: "time",
    datetime: "datetime",
}


class BaseModel:
    @classmethod
    def parse_obj(cls: Type[T], data: dict, key: Optional[str] = None) -> T:
        data = data.copy()
        attrs: Dict[str, Any] = {}
        if key is not None:
            keyprefix = f"{key}."
        else:
            try:
                key = cls.KEY  # type: ignore[attr-defined]
            except AttributeError:
                key = None
                keyprefix = ""
            else:
                keyprefix = f"{key}."
        fieldkeys: List[str] = []
        fieldtypes = get_type_hints(cls)
        for f in dataclasses.fields(cls):
            fkey = f.name.replace("_", "-")
            fieldkeys.append(fkey)
            try:
                value = data.pop(fkey)
            except KeyError:
                if (
                    f.default is dataclasses.MISSING
                    and f.default_factory is dataclasses.MISSING  # type: ignore
                ):
                    raise ConfigError(f"{keyprefix}{fkey} is required")
            else:
                ftype = fieldtypes[f.name]
                # if issubclass(ftype, BaseModel):
                #    attrs[f.name] = ftype.parse_obj(data, key=f"{keyprefix}{fkey}")
                if is_instance(value, ftype):
                    attrs[f.name] = value
                else:
                    raise ConfigError(f"{keyprefix}{fkey} must be {type_name(ftype)}")
        for extra in data.keys():
            suggestions = didyoumean(extra, fieldkeys)
            log.warning(
                "Ignoring unknown parameter %r%s%s",
                extra,
                f" in {key}" if key is not None else "",
                suggestions,
            )
        return cls(**attrs)  # type: ignore[call-arg]


def is_instance(value: Any, ftype: Any) -> bool:
    if ftype in PRIMITIVES:
        return isinstance(value, ftype)
    elif ftype is type(None):  # noqa: E721
        return value is None
    elif ftype is Any:
        return True
    elif ftype is list or get_origin(ftype) is list:
        if not isinstance(value, list):
            return False
        try:
            (arg,) = get_args(ftype)
        except ValueError:
            arg = Any
        return all(is_instance(v, arg) for v in value)
    elif ftype is dict or get_origin(ftype) is dict:
        if not isinstance(value, dict):
            return False
        try:
            ktype, vtype = get_args(ftype)
        except ValueError:
            ktype, vtype = Any, Any
        return all(
            is_instance(k, ktype) and is_instance(v, vtype) for k, v in value.items()
        )
    elif get_origin(ftype) is Union:
        return any(is_instance(value, a) for a in get_args(ftype))
    else:
        raise RuntimeError(f"Unsupported type in field annotation: {ftype!r}")


def type_name(ftype: Any, plural: bool = False) -> str:
    if ftype in PRIMITIVES:
        return determine(PRIMITIVES[ftype], plural=plural)
    elif ftype is type(None):  # noqa: E721
        return ""  # Weeded out by Union case
    elif ftype is Any:
        return "anything"
    elif ftype is list or get_origin(ftype) is list:
        try:
            (arg,) = get_args(ftype)
        except ValueError:
            arg = Any
        s = determine("list", plural=plural)
        if arg is not Any:
            s += " of " + type_name(arg, plural=True)
        return s
    elif ftype is dict or get_origin(ftype) is dict:
        try:
            ktype, vtype = get_args(ftype)
        except ValueError:
            ktype, vtype = Any, Any
        s = determine("table", plural=plural)
        if ktype is not Any or vtype is not Any:
            s += (
                " of "
                + type_name(ktype, plural=True)
                + " -> "
                + type_name(vtype, plural=True)
            )
        return s
    elif get_origin(ftype) is Union:
        choices = list(
            filter(None, (type_name(a, plural=plural) for a in get_args(ftype)))
        )
        assert len(choices) > 0, f"{ftype!r} has no non-None args"
        if len(choices) == 1:
            return choices[0]
        elif len(choices) == 2:
            return f"{choices[0]} or {choices[1]}"
        else:
            choices[-1] = "or " + choices[-1]
            return ", ".join(choices)
    # elif hasattr(ftype, "TYPE_DESC"):
    #    return cast(str, ftype.TYPE_DESC)
    else:
        raise RuntimeError(f"Unsupported type in field annotation: {ftype!r}")


def determine(word: str, plural: bool) -> str:
    if plural:
        return word + "s"
    elif word.lower().startswith(("a", "e", "i", "o", "u", "y")):
        return "an " + word
    else:
        return "a " + word
