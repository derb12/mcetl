API Reference
=============

.. warning::
   mcetl is going to switch GUI backends in a later version (v0.5 or v0.6), so
   any api that is not referenced in the Quick Start or Tutorial sections should
   be used with caution since it is liable to be changed or removed.

.. toctree::
   :titlesonly:

   {% for page in pages %}
   {% if page.top_level_object and page.display %}
   {{ page.include_path }}
   {% endif %}
   {% endfor %}


API reference documentation was auto-generated using `sphinx-autoapi <https://github.com/readthedocs/sphinx-autoapi>`_.
