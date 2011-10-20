marimo template tag
===================

The template tag is currently only useful for ``request_widget``.

The tag requires marimo.js (and any marimo js dependencies) to be included in
your template's ``<head>``. You also need to place a hideous sigil somewhere
within a ``<script>`` somewhere in your template. This allows the template tag
to automagically register widgets with marimo's ``add_widget`` method.

Usage::

    {% marimo comments request_widget objectpk=23 %}

will become

.. code-block:: xml

    <div id="comments_widget_123"></div>

and generate the following call to ``add_widget``:

.. code-block:: javascript

    marimo.add_widget({
        id: 'comments_widget_123',
        widget_prototype: 'request_widget',
        kwargs: {
            objectpk:23
        },
        args: []
    });
