.. highlight:: shell

============
Installation
============


Dependencies
~~~~~~~~~~~~

mcetl requires `Python <https://python.org>`_ version 3.7 or later and the following libraries:

* `asteval <https://github.com/newville/asteval>`_
* `lmfit <https://lmfit.github.io/lmfit-py/>`_ (>= 1.0)
* `Matplotlib <https://matplotlib.org>`_ (>= 3.1)
* `NumPy <https://numpy.org>`_ (>= 1.8)
* `openpyxl <https://openpyxl.readthedocs.io/en/stable/>`_ (>= 2.4)
* `pandas <https://pandas.pydata.org>`_ (>= 0.25)
* `PySimpleGUI <https://github.com/PySimpleGUI/PySimpleGUI>`_ (>= 4.29)
* `SciPy <https://www.scipy.org/scipylib/index.html>`_


All of the required libraries should be automatically installed when installing mcetl
using either of the two installation methods below.

Additionally, mcetl can optionally use `Pillow <https://python-pillow.org/>`_
to allow for additional options when saving figures in the plotting GUI.


Stable Release
~~~~~~~~~~~~~~

mcetl is easily installed from `pypi <https://pypi.org/project/mcetl>`_
using `pip <https://pip.pypa.io>`_, simply by running the following command in your terminal:

.. code-block:: console

    pip install --upgrade mcetl

This is the preferred method to install mcetl, as it will always install the most
recent stable release. Note that the ``--upgrade`` tag is used to ensure that the
most recent version of mcetl is downloaded and installed, even if an older version
is currently installed.


Development Version
~~~~~~~~~~~~~~~~~~~

The sources for mcetl can be downloaded from the `Github repo <https://github.com/derb12/mcetl>`_.

The public repository can be cloned using:

.. code-block:: console

    git clone https://github.com/derb12/mcetl.git


Once the repository is downloaded, it can be installed with:

.. code-block:: console

    cd mcetl
    python setup.py install
