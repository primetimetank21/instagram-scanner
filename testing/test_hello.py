"""Pytests for hello()"""
from typing import cast
import hello
import mock  # type:ignore
from hello import hello as hello_func, main


def test_hello() -> None:
    """Tests for `hello()`"""
    assert hello_func() == "Hello John!"
    assert hello_func("Jill") == "Hello Jill!"
    assert hello_func(name="Jill") == "Hello Jill!"
    assert isinstance(hello_func(), str)


def test_main() -> None:
    with mock.patch.object(hello, attribute="main", return_value=None):
        with mock.patch.object(hello, "__name__", "__main__"):
            return_val = cast(None, main())

            assert return_val is None
