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
