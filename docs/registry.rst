marimo widgets registry
=======================

the registry is a file that contains a dictionary. This dictionary maps widget
names to an importable path for a callable that can handle a request for widget
data and templates.

.. code-block:: python

    registry = {
        'test_widget':'mtest.views.TestWidget',
    }

We've been calling this widgets.py, but it can be identified in any way via the MARIMO_REGISTRY setting.
