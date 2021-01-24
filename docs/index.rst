mcetl Documentation
===================

.. image:: images/logo.png
   :align: center
   :scale: 35 %


mcetl is a small-scale Extract-Transform-Load framework focused on materials characterization.

* For Python 3.7+
* Open Source: BSD 3-Clause License
* Source Code: https://github.com/derb12/mcetl
* Documentation: https://mcetl.readthedocs.io.


mcetl is focused on easing the time required to process data files and write the
results to Excel. It does this by allowing the user to define DataSource objects
for each separate source of data. Each DataSource contains information such as the
options needed to import data from files, the calculations that will be performed
on the data, and the options for writing the data to Excel.

In addition, mcetl provides fitting and plotting user interfaces that
can be used without any prior setup.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   introduction
   installation
   quickstart
   tutorials/index
   api/index
   gallery
   contributing
   changes
   license
   authors


Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
