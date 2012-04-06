from django.utils.importlib import import_module

def smart_import(mpath):
    """ Given a path smart_import will import the module and return the attr reffered to """
    try:
        rest = import_module(mpath)
    except ImportError:
        split = mpath.split('.')
        rest = smart_import('.'.join(split[:-1]))
        rest = getattr(rest, split[-1])
    return rest

def composition_decorator(decfn):
    '''Decorator. Declares its decorated function to be itself a decorator,
    which instead of receiving the arguments of the functions it decorates,
    will instead be composed with the function as if in a pipeline. Example:

    >>> @composition_decorator
    >>> def add_two(x):
    ...    return x+2

    >>> @add_two
    >>> def five():
    ...    return 5

    >>> five()
    7

    '''
    return lambda fn: lambda *a, **kw: decfn(fn(*a, **kw))
