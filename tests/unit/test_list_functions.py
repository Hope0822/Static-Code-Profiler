import ast

from cyclocalc.cli import list_functions


def test_list_functions_basic_and_nested():
    source = """
class A:
    def method(self):
        def inner():
            pass
        return inner

def top_level():
    pass
"""
    tree = ast.parse(source)
    funcs = list_functions(tree)
    func_names = sorted(name for name, _ in funcs)

    expected = sorted(
        [
            "A.method",
            "A.method.inner",
            "top_level",
        ]
    )
    assert func_names == expected


def test_list_functions_async_and_nested_classes():
    source = """
async def async_func():
    pass

class Outer:
    def method(self):
        pass

    class Inner:
        async def inner_async(self):
            pass
"""
    tree = ast.parse(source)
    funcs = list_functions(tree)
    func_names = sorted(name for name, _ in funcs)

    expected = sorted(
        [
            "async_func",
            "Outer.method",
            "Outer.Inner.inner_async",
        ]
    )
    assert func_names == expected
