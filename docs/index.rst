Welcome to mcetl's documentation!
=================================

.. image:: images/logo.png
   :align: center



mcetl is an Extract-Transform-Load framework focused on materials characterization.

* For python 3.7+
* Open source: BSD 3-clause license
* GitHub: https://github.com/derb12/mcetl
* Documentation: https://mcetl.readthedocs.io.


mcetl is focused on easing the time required to process data files. It does this
by allowing the user to define DataSource objects which contain the information
for reading files, the calculations that will be performed on the data, and the
options for writing the data to Excel.

In addition, mcetl provides peak fitting and plotting user interfaces that
can be used without creating any DataSource objects. Peak fitting is done using
lmfit, and plotting is done with matplotlib.



.. toctree::
   :maxdepth: 2
   :caption: Contents:

   description
   installation
   usage
   contributing
   changes
   license
   authors


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
