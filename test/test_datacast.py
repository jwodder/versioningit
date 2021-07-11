from dataclasses import dataclass, field
from datetime import date, datetime, time
import logging
from typing import Any, Dict, List, Optional, Union
import pytest
from versioningit.datacast import BaseModel, is_instance, type_name
from versioningit.errors import ConfigError


@dataclass
class Structure(BaseModel):
    KEY = "tool.structure"

    required: Union[str, int]
    opt_int: Optional[int] = None
    lst: List[str] = field(default_factory=list)
    truth: bool = False
    sub_strs: Dict[str, str] = field(default_factory=dict)
    sub_map: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Keyless(BaseModel):
    required: Union[str, int]
    opt_int: Optional[int] = None


@pytest.mark.parametrize(
    "data,r,warnings",
    [
        (
            {"required": "foo"},
            Structure(
                required="foo",
                opt_int=None,
                lst=[],
                truth=False,
                sub_strs={},
                sub_map={},
            ),
            [],
        ),
        (
            {"required": 42},
            Structure(
                required=42,
                opt_int=None,
                lst=[],
                truth=False,
                sub_strs={},
                sub_map={},
            ),
            [],
        ),
        (
            {"required": "foo", "opt-int": 42},
            Structure(
                required="foo",
                opt_int=42,
                lst=[],
                truth=False,
                sub_strs={},
                sub_map={},
            ),
            [],
        ),
        (
            {"required": "foo", "opt_int": 42},
            Structure(
                required="foo",
                opt_int=None,
                lst=[],
                truth=False,
                sub_strs={},
                sub_map={},
            ),
            [
                "Ignoring unknown parameter 'opt_int' in tool.structure"
                " (Did you mean: opt-int?)"
            ],
        ),
        (
            {"required": "foo", "mystery": 42},
            Structure(
                required="foo",
                opt_int=None,
                lst=[],
                truth=False,
                sub_strs={},
                sub_map={},
            ),
            ["Ignoring unknown parameter 'mystery' in tool.structure"],
        ),
        (
            {"required": "foo", "opt-int": None},
            Structure(
                required="foo",
                opt_int=None,
                lst=[],
                truth=False,
                sub_strs={},
                sub_map={},
            ),
            [],
        ),
        (
            {"required": "foo", "lst": []},
            Structure(
                required="foo",
                opt_int=None,
                lst=[],
                truth=False,
                sub_strs={},
                sub_map={},
            ),
            [],
        ),
        (
            {"required": "foo", "lst": ["foo", "bar"]},
            Structure(
                required="foo",
                opt_int=None,
                lst=["foo", "bar"],
                truth=False,
                sub_strs={},
                sub_map={},
            ),
            [],
        ),
        (
            {"required": "foo", "truth": True},
            Structure(
                required="foo",
                opt_int=None,
                lst=[],
                truth=True,
                sub_strs={},
                sub_map={},
            ),
            [],
        ),
        (
            {"required": "foo", "sub-strs": {}},
            Structure(
                required="foo",
                opt_int=None,
                lst=[],
                truth=False,
                sub_strs={},
                sub_map={},
            ),
            [],
        ),
        (
            {"required": "foo", "sub-strs": {"foo": "bar", "gnusto": "cleesh"}},
            Structure(
                required="foo",
                opt_int=None,
                lst=[],
                truth=False,
                sub_strs={"foo": "bar", "gnusto": "cleesh"},
                sub_map={},
            ),
            [],
        ),
        (
            {"required": "foo", "sub-map": {"foo": "bar", "gnusto": "cleesh"}},
            Structure(
                required="foo",
                opt_int=None,
                lst=[],
                truth=False,
                sub_strs={},
                sub_map={"foo": "bar", "gnusto": "cleesh"},
            ),
            [],
        ),
        (
            {"required": "foo", "sub-map": {"foo": 42, "gnusto": None}},
            Structure(
                required="foo",
                opt_int=None,
                lst=[],
                truth=False,
                sub_strs={},
                sub_map={"foo": 42, "gnusto": None},
            ),
            [],
        ),
    ],
)
def test_parse_obj(
    caplog: pytest.LogCaptureFixture, data: dict, r: Structure, warnings: List[str]
) -> None:
    assert Structure.parse_obj(data) == r
    assert [
        msg
        for logger, lvl, msg in caplog.record_tuples
        if logger == "versioningit" and lvl == logging.WARNING
    ] == warnings


@pytest.mark.parametrize(
    "data,errmsg",
    [
        ({}, "tool.structure.required is required"),
        ({"required": 3.14}, "tool.structure.required must be a string or an integer"),
        (
            {"required": "foo", "opt-int": "42"},
            "tool.structure.opt-int must be an integer",
        ),
        (
            {"required": "foo", "lst": "list,of,things"},
            "tool.structure.lst must be a list of strings",
        ),
        (
            {"required": "foo", "lst": ["foo", 42]},
            "tool.structure.lst must be a list of strings",
        ),
        (
            {"required": "foo", "truth": "yes"},
            "tool.structure.truth must be a boolean",
        ),
        (
            {"required": "foo", "sub-strs": {"foo": 42}},
            "tool.structure.sub-strs must be a table of strings -> strings",
        ),
        (
            {"required": "foo", "sub-strs": {42: "foo"}},
            "tool.structure.sub-strs must be a table of strings -> strings",
        ),
        (
            {"required": "foo", "sub-map": {42: "foo"}},
            "tool.structure.sub-map must be a table of strings -> anything",
        ),
        (
            {"required": "foo", "sub-map": "foo"},
            "tool.structure.sub-map must be a table of strings -> anything",
        ),
        (
            {"required": "foo", "sub-map": ["foo"]},
            "tool.structure.sub-map must be a table of strings -> anything",
        ),
    ],
)
def test_parse_obj_error(data: dict, errmsg: str) -> None:
    with pytest.raises(ConfigError) as excinfo:
        Structure.parse_obj(data)
    assert str(excinfo.value) == errmsg


def test_parse_obj_unknown_param_keyless(caplog: pytest.LogCaptureFixture) -> None:
    assert Keyless.parse_obj({"required": 42, "opt_int": 23}) == Keyless(
        required=42, opt_int=None
    )
    assert [
        msg
        for logger, lvl, msg in caplog.record_tuples
        if logger == "versioningit" and lvl == logging.WARNING
    ] == ["Ignoring unknown parameter 'opt_int' (Did you mean: opt-int?)"]


@pytest.mark.parametrize(
    "data,errmsg",
    [
        ({}, "required is required"),
        ({"required": 3.14}, "required must be a string or an integer"),
        ({"required": "foo", "opt-int": "42"}, "opt-int must be an integer"),
    ],
)
def test_parse_obj_error_keyless(data: dict, errmsg: str) -> None:
    with pytest.raises(ConfigError) as excinfo:
        Keyless.parse_obj(data)
    assert str(excinfo.value) == errmsg


@pytest.mark.parametrize(
    "data,errmsg",
    [
        ({}, "stuff.table.required is required"),
        ({"required": 3.14}, "stuff.table.required must be a string or an integer"),
        (
            {"required": "foo", "opt-int": "42"},
            "stuff.table.opt-int must be an integer",
        ),
    ],
)
@pytest.mark.parametrize("klass", [Structure, Keyless])
def test_parse_obj_error_custom_key(klass: BaseModel, data: dict, errmsg: str) -> None:
    with pytest.raises(ConfigError) as excinfo:
        klass.parse_obj(data, key="stuff.table")
    assert str(excinfo.value) == errmsg


@pytest.mark.parametrize("klass", [Structure, Keyless])
def test_parse_obj_unknown_param_custom_key(
    caplog: pytest.LogCaptureFixture, klass: BaseModel
) -> None:
    assert klass.parse_obj({"required": 42, "opt_int": 23}, key="stuff.table") == klass(  # type: ignore[operator]  # noqa: B950
        required=42, opt_int=None
    )
    assert [
        msg
        for logger, lvl, msg in caplog.record_tuples
        if logger == "versioningit" and lvl == logging.WARNING
    ] == [
        "Ignoring unknown parameter 'opt_int' in stuff.table (Did you mean: opt-int?)"
    ]


@pytest.mark.parametrize(
    "value,ftype,r",
    [
        (42, int, True),
        ("42", int, False),
        ("42", str, True),
        (42, str, False),
        (["42"], str, False),
        (None, type(None), True),
        (None, Any, True),
        (42, Any, True),
        ("42", Any, True),
        (["42", 42], Any, True),
        (["42", 42], list, True),
        (["42", 42], List, True),
        (["42", 42], List[str], False),
        (["42", 42], List[int], False),
        (["42"], List[str], True),
        ([42], List[int], True),
        ([], List[str], True),
        ([], List[int], True),
        ({}, dict, True),
        ({}, Dict, True),
        ({}, Dict[Any, Any], True),
        ({42: "foo", "gnusto": "cleesh"}, Dict[Any, Any], True),
        ({}, Dict[Any, str], True),
        ({42: "foo", "gnusto": "cleesh"}, Dict[Any, str], True),
        ({}, Dict[str, Any], True),
        ({"foo": 42, "gnusto": "cleesh"}, Dict[str, Any], True),
        ({"foo": 42, "gnusto": "cleesh"}, Dict[str, str], False),
        ({"foo": "42", "gnusto": "cleesh"}, Dict[str, str], True),
        ({"foo": 42, "gnusto": 23}, Dict[str, int], True),
        ({42: "foo", "23": "gnusto"}, Dict[int, str], False),
        ({42: "foo", 23: "gnusto"}, Dict[int, str], True),
        (42, Union[int, str, None], True),
        ("42", Union[int, str, None], True),
        (None, Union[int, str, None], True),
        (3.14, Union[int, str, None], False),
        ([], Union[int, str, None], False),
        ({}, Union[int, str, None], False),
    ],
)
def test_is_instance(value: Any, ftype: Any, r: bool) -> None:
    assert is_instance(value, ftype) is r


def test_is_instance_unsupported() -> None:
    with pytest.raises(RuntimeError) as excinfo:
        is_instance((1, 2, 3), tuple)
    assert str(excinfo.value) == "Unsupported type in field annotation: <class 'tuple'>"


@pytest.mark.parametrize(
    "ftype,name",
    [
        (int, "an integer"),
        (str, "a string"),
        (float, "a float"),
        (bool, "a boolean"),
        (date, "a date"),
        (time, "a time"),
        (datetime, "a datetime"),
        (Any, "anything"),
        (List[int], "a list of integers"),
        (List[str], "a list of strings"),
        (List[List[int]], "a list of lists of integers"),
        (list, "a list"),
        (List, "a list"),
        (List[Any], "a list"),
        (dict, "a table"),
        (Dict, "a table"),
        (Dict[Any, Any], "a table"),
        (Dict[Any, str], "a table of anything -> strings"),
        (Dict[str, Any], "a table of strings -> anything"),
        (Dict[str, int], "a table of strings -> integers"),
        (List[Dict[str, date]], "a list of tables of strings -> dates"),
        (Optional[int], "an integer"),
        (Union[int, str], "an integer or a string"),
        (Union[int, str, date], "an integer, a string, or a date"),
    ],
)
def test_type_name(ftype: Any, name: str) -> None:
    assert type_name(ftype) == name


def test_type_name_unsupported() -> None:
    with pytest.raises(RuntimeError) as excinfo:
        type_name(tuple)
    assert str(excinfo.value) == "Unsupported type in field annotation: <class 'tuple'>"
