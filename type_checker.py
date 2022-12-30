'''
NOTE: This function currently not support function overloading
Example:
    @typecheck
    def add(a: int | str, b: int | str) -> int | str:
        return a + b

    # In this situation add(0, 'a') or add('a', 0) is both legal, but I don't think 
    #   this is what you want to see
    
Solution:
    Change the function definition like below:
    
    from functools import singledispatch

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

    Then call add('string', 1) will cause an error
''' 

'''
BUG: The decorator will make your function slower 1.5 to 10 times than the original function
So don't use it on some funcs which will be frequently called
I will try to make some optimizations in the next version 
'''


from typing import Any, Callable
from functools import wraps

import sys

if sys.version_info < (3, 7):
    raise Exception(
        'Python under 3.7 is not supported'
    )


def typecheck(func: Callable[..., Any]) -> Callable[..., Any]:
    '''

    A simple tool to check the argument type for your function calls
    If you have multiple decorations, the @typecheck should always be in the bottom
    NOTICE: This decorator will rewrite the document of your function
    WARNING: If you use @typecheck on a function where there're some arguments have not been annotated, you'll got an error
            So if you want to discard a specified type checking on a argument, please use :typing.Any
    '''
    # Locally import libs to read function signature
    from inspect import signature, isfunction, Parameter
    if not isfunction(func):
        raise TypeError(
            f'Not a function: {func}'
        )

    # Definition of these characters will be easier to insert them in f-strings
    endl = '\n'
    tab = '    '
    
    # Convert typename from <class 'int'> to int
    def get_clear_type_name(raw_type_name: str) -> str:
        return raw_type_name.strip("<class ") \
                            .strip("'")      \
                            .strip("'>")

    # Format an inspect.Argument type object to an readable string
    def get_clear_argument_signature(argument_signature: Parameter) -> str:
        parameter_name = argument_signature.name
        parameter_kind = argument_signature.kind
        parameter_type = get_clear_type_name(str(argument_signature.annotation))
        parameter_default = get_clear_type_name(str(argument_signature.default))
        if parameter_default == 'inspect._empty':
            parameter_default = '?'

        return f'{parameter_kind}    {parameter_name} = {parameter_default}'

    # Get type annotations and generates the function signature string
    type_annotations = func.__annotations__
    function_signature_info = signature(func)
    function_param_signature = f"(\n{tab}{f', {endl}{tab}'.join([get_clear_argument_signature(p) for p in list(function_signature_info.parameters.values())])}\n  )"
    function_signature = f'def {func.__name__}{function_param_signature}: ...'
    
    # Generates the positioanal arguments list
    function_positional_argument_list = [name for name in tuple(function_signature_info.parameters.keys())]

    # Then format the __doc__ attribute of it
    if func.__doc__ is None:
        func.__doc__ = f'\n  *** There\'s no documentation for function ***\n'
    func.__doc__ = f'Documentation for function "{func.__name__}":\n{func.__doc__}\nSignature:\n  {function_signature}\n\nParameters & Returns:\n'
    # Insert the parameters and the annotations of parameters into documentation
    for index, (param_name, param_type) in enumerate(type_annotations.items()):
        suffix = f'{"," + endl if index + 1 < len(type_annotations) else endl}'
        func.__doc__ += f'  {param_name}: {get_clear_type_name(str(param_type))}{suffix}'

    # Below are the real function to do type chckings
    @wraps(func)
    def check_type(*args, **kwargs):
        if len(type_annotations) == 0:
            raise TypeError(
                f'Type hint required for function \'{func.__name__}\''
            )

        # Check for keyword arguments
        function_positional_arguments = args
        function_keyword_arguments = kwargs
        for real_param_name, param_value in function_keyword_arguments.items():
            required_type: type = None
            # Check if the parameter exists in signature
            try:
                required_type = type_annotations[real_param_name]
            except KeyError:
                raise TypeError(
                    f'Function \'{func.__name__}\' got an unexpected keyword argument \'{real_param_name}\', perhaps it doesn\'t have type hint ?'
                )

            actual_type = type(param_value)

            # Continue if the annotation is just string
            if not isinstance(required_type, type): continue

            if actual_type != required_type:
                raise TypeError(
                    f'Keyword argument \'{real_param_name}\' requires type '
                    f'{get_clear_type_name(str(required_type))}, '
                    f'but got {get_clear_type_name(str(actual_type))}'
                )
        
        # Define a function which can get a name of a positional argument
        def get_positioanal_argument_name(index: int) -> str:
            return function_positional_argument_list[index] 

        # Check for positional arguments, depends on function signature we've got above
        for index, param_value in enumerate(function_positional_arguments):
            param_name = get_positioanal_argument_name(index)
            required_type: type = None
            try:
                required_type = type_annotations[param_name]
            except KeyError:
                raise TypeError(
                   f'No type information for positional argument at {index}, possibly name \'{param_name}\', '
                   'consider add a type hint for it'
                )

            actual_type = type(param_value)
            if not isinstance(required_type, type): continue

            if actual_type != required_type:
                raise TypeError(
                    f'Positional argument at pos {index}, possibly name \'{param_name}\', '
                    f'requires type \'{get_clear_type_name(str(required_type))}\', '
                    f'but got \'{get_clear_type_name(str(actual_type))}\''
                )

        # If nothing was error, call the function with original arguments and return its value back
        return func(*function_positional_arguments, **function_keyword_arguments)
    return check_type
    