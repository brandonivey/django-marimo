django-marimo settings
======================

.. code-block:: python

    MARIMO_URL='/marimo/' # this should map to marimo.views.Router.as_view()
    MARIMO_REGISTRY='mtest.widgets.registry' # this is a mapping of widget names to handlers
    # where marimo will look for mustache templates.
    MARIMO_TEMPLATE_DIRS = (
         '%s/templates/marimo' % BASE_DIR,
    )
