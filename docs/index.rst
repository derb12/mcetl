Welcome to mcetl's documentation!
=================================

.. image:: logo.png
   :align: center



mcetl is a simple Extract-Transform-Load framework focused on materials characterization.

mcetl is focused on easing the time required to process data files. It does this
by allowing the user to define DataSource objects which contains the information
for reading files for that DataSource, the calculations that will be performed on 
the data, and the options for writing the data to Excel.

In addition, mcetl provides peak fitting and plotting user interfaces that
can be used without creating any DataSource objects. Peak fitting is done using
lmfit, and plotting is done with matplotlib.


* For python 3.7+
* Open source: BSD 3-clause license
* GitHub: https://github.com/derb12/mcetl
* Documentation: https://mcetl.readthedocs.io.



.. toctree::
   :maxdepth: 2
   :caption: Contents:

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
