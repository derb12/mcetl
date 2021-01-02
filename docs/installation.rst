.. highlight:: shell

============
Installation
============


Dependencies
~~~~~~~~~~~~

mcetl requires `Python <https://python.org>`_ version 3.7 or later and the following libraries:

* `asteval <https://github.com/newville/asteval>`_
* `lmfit <https://lmfit.github.io/lmfit-py/>`_ (>= 1.0)
* `matplotlib <https://matplotlib.org>`_ (>= 3.1)
* `NumPy <https://numpy.org>`_ (>= 1.8)
* `openpyxl <https://openpyxl.readthedocs.io/en/stable/>`_ (>= 2.4)
* `pandas <https://pandas.pydata.org>`_ (>= 0.24)
* `PySimpleGUI <https://github.com/PySimpleGUI/PySimpleGUI>`_ (>= 4.29)
* `SciPy <https://www.scipy.org/scipylib/index.html>`_


All of the required libraries should be automatically installed when installing mcetl
using either of the two installation methods below.

Additionally, mcetl can optionally use `xlrd <https://github.com/python-excel/xlrd>`_
to read .xls files, and `Pillow <https://python-pillow.org/>`_
to allow for additional options when saving figures in the plotting GUI.


Stable Release
~~~~~~~~~~~~~~

mcetl is easily installed using `pip`_, simply by running the following command in your terminal:

.. code-block:: console

    pip install --upgrade mcetl

This is the preferred method to install mcetl, as it will always install the most recent stable release.

To install mcetl, as well as its optional dependencies, use:

.. code-block:: console

    pip install --upgrade mcetl[extras]


.. _pip: https://pip.pypa.io


Development Version
~~~~~~~~~~~~~~~~~~~

The sources for mcetl can be downloaded from the `Github repo`_.

The public repository can be cloned using:

.. code-block:: console

    git clone https://github.com/derb12/mcetl.git


Once the repository is downloaded, it can be installed with:

.. code-block:: console

    cd mcetl
    python setup.py install


.. _Github repo: https://github.com/derb12/mcetl

