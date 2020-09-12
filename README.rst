=====
mcetl
=====

.. image:: https://github.com/derb12/mcetl/raw/master/docs/logo.png
   :align: center


.. image:: https://img.shields.io/pypi/v/mcetl.svg
        :target: https://pypi.python.org/pypi/mcetl

.. image:: https://readthedocs.org/projects/mcetl/badge/?version=latest
        :target: https://mcetl.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://img.shields.io/badge/License-BSD%203--Clause-blue.svg
        :target: https://github.com/derb12/mcetl/tree/master/LICENSE.txt



mcetl is a simple Extract-Transform-Load framework focused on materials characterization.

* For python 3.7+
* Open Source: BSD 3-clause license
* Documentation: https://mcetl.readthedocs.io.


.. contents:: **Table of Contents**
    :depth: 1


Summary
-------

* TODO


Installation
------------

Stable release
~~~~~~~~~~~~~~

To install mcetl, run this command in your terminal:

.. code-block:: console

    $ pip install mcetl

This is the preferred method to install mcetl, as it will always install the most recent stable release.


From Github
~~~~~~~~~~~

The sources for mcetl can be downloaded from the `Github repo`_.

You can clone the public repository:

.. code-block:: console

    $ git clone git://github.com/derb12/mcetl


Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ python setup.py install


.. _Github repo: https://github.com/derb12/mcetl


Usage
-----

To use mcetl in a project::

    import mcetl


To use the peak fitting or plotting modules in mcetl, simply do::

    mcetl.launch_peak_fitting_gui()
    mcetl.launch_plotting_gui()


A window will then appear to select the data file(s) to be fitted or plotted.


Files for example data from characterization techniques can be created using::

    from mcetl import raw_data
    raw_data.generate_raw_data()


Data produced by the generate_raw_data function covers the following characterization techniques:

* X-ray diffraction (XRD)
* Fourier-transform infrared spectroscopy (FTIR)
* Raman spectroscopy
* Thermogravimetric analysis (TGA)
* Differential scanning calorimetry (DSC)


`Example programs`_  are available to show basic usage of mcetl. The examples include:

* Generating raw data
* Using the main GUI
* Using the peak fitting GUI
* Using the plotting GUI
* Reopening a figure saved with the plotting GUI


.. _Example programs: https://github.com/derb12/mcetl/tree/master/examples


Future Plans
------------

Planned features for later releases:

Short term
~~~~~~~~~~

* Develop tests for all modules in the package.
* Switch from print statements to logging.
* Transfer documentation from PDF/Word files to automatic documentation with Sphinx.
* Improve usage when opening existing Excel files.


Long term
~~~~~~~~~

* Add more plot types to the plotting gui, including bar charts, categorical plots, and 3d plots.
* Make peak fitting more flexible by allowing more options or user inputs.
* Improve overall look and usability of all GUIs.


Contributing
------------

Contributions are welcome, and they are greatly appreciated.

You can contribute in many ways:

Bugs Reports
~~~~~~~~~~~~

Report bugs at https://github.com/derb12/mcetl/issues.

If you are reporting a bug, please include:

* Your operating system name, python version, and mcetl version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Feedback
~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/derb12/mcetl/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.

Pull Requests
~~~~~~~~~~~~~

Pull requests are welcomed for this project. When submitting a pull request, follow similar procedures for feedback, namely:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.


Changelog
--------------

`Changelog`_

.. _Changelog: https://github.com/derb12/mcetl/tree/master/CHANGELOG.rst


Author
------

* Donald Erb <donnie.erb@gmail.com>


Credits
-------

The layout of this package was initially created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.


.. _Cookiecutter: https://github.com/audreyr/cookiecutter

.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

