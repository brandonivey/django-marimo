import os
from django.conf import settings

class TemplateNotFound(Exception):
    """ An exception for when a template can't be found """
    pass

class TemplateLoader(object):
    """ 
    Loads and caches templates from files 
    searches MARIMO_TEMPLATE_DIRS in order
    loads and caches the first template matching the path
    """

    def __init__(self):
        """ template_dirs is set at __init__ don't try to change them in settings."""
        self.template_dirs = getattr(settings, 'MARIMO_TEMPLATE_DIRS', [])
        self._templates = {}

    def load(self, path):
        """ 
        load a template
        :param path: The path to the template you want to load from a dir in template_dirs
        """
        try:
            return self._templates[path]
        except KeyError:
            for directory in self.template_dirs:
                full = os.path.join(directory, path)
                try:
                    fh = open(full)
                except IOError:
                    pass
                else:
                    self._templates[path] = fh.read()
                    fh.close()
                    return self._templates[path]
        raise TemplateNotFound('No such template: %s' % path)

template_loader = TemplateLoader()
