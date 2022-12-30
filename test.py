from type_checker import typecheck
import timeit
import typing
from functools import singledispatch


def add_without_type_check(a, b):
    return a + b


@typecheck
@singledispatch
def add_with_type_check(a: int | str, b: int | str) -> int | str: ...

@add_with_type_check.register(int)
@typecheck
def _add_with_type_check_int(a: int, b: int) -> int:
    return a + b;

@add_with_type_check.register(str)
@typecheck
def _add_with_type_check_str(a: str, b: str) -> int:
    return a + b;


if __name__ == '__main__':
    duration1 = timeit.timeit(lambda: add_without_type_check("114514", "1919810"), number=114514)
    duration2 = timeit.timeit(lambda: add_with_type_check("114514", "1919810"), number=114514)
    print(duration1, duration2),
    print(add_with_type_check.__doc__)
