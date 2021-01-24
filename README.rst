=====
mcetl
=====

.. image:: https://github.com/derb12/mcetl/raw/main/docs/images/logo.png
    :alt: mcetl Logo
    :align: center

.. image:: https://img.shields.io/pypi/v/mcetl.svg
    :target: https://pypi.python.org/pypi/mcetl
    :alt: Most Recent Version

.. image:: https://readthedocs.org/projects/mcetl/badge/?version=latest
    :target: https://mcetl.readthedocs.io
    :alt: Documentation Status

.. image:: https://img.shields.io/pypi/pyversions/mcetl.svg
    :target: https://pypi.python.org/pypi/mcetl
    :alt: Supported Python versions

.. image:: https://img.shields.io/badge/license-BSD%203--Clause-blue.svg
    :target: https://github.com/derb12/mcetl/tree/main/LICENSE.txt
    :alt: BSD 3-clause license


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


.. contents:: **Contents**
    :depth: 1


Introduction
------------

Purpose
~~~~~~~

The aim of mcetl is to ease the repeated processing of data files. Contrary to its name, mcetl
can process any tabulated files (txt, csv, tsv, xlsx, etc.), and does not require that the files originate
from materials characterization. However, the focus on materials characterization was selected because:

* Most data files from materials characterization are relatively small in size (a few kB or MB).
* Materials characterization files are typically cleanly tabulated and do not require handling
  messy or missing data.
* It was the author's area of usage and naming things is hard...

mcetl requires only a very basic understanding of Python to use, and allows a single person to
create a tool that their entire group can use to process data and produce Excel files with a
consistent style. mcetl can create new Excel files when processing data or saving peak fitting
results, or it can append to an existing Excel file to easily work with already created files.

Limitations
~~~~~~~~~~~

* Since mcetl uses the `pandas <https://pandas.pydata.org>`_ library to load data
  from files into memory for processing, it is not suited for processing files whose
  total memory size is large (e.g. cannot load a 10 GB file on a computer with
  only 8 GB of RAM).
* mcetl does not provide any resources for processing data files directly from
  characterization equipment (such as .XRDML, .PAR, etc.). Other libraries such
  as `xylib <https://github.com/wojdyr/xylib>`_ already exist and are capable of
  converting many such files to a format mcetl can use (txt, csv, etc.).
* The peak fitting and plotting modules in mcetl are not as feature-complete as
  other alternatives such as `Origin <https://originlab.com>`_,
  `fityk <https://fityk.nieto.pl>`_, `SciDAVis <https://sourceforge.net/projects/scidavis/>`_,
  etc. The modules are included in mcetl in case those better alternatives are not
  available, and the author highly recommends using those alternatives over mcetl if available.


Installation
------------

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

mcetl is easily installed using `pip <https://pip.pypa.io>`_, simply by running
the following command in your terminal:

.. code-block:: console

    pip install --upgrade mcetl

This is the preferred method to install mcetl, as it will always install the
most recent stable release.


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


Quick Start
-----------

The sections below give a quick introduction to using mcetl, requiring no setup.
For a more detailed introduction, refer to the `tutorials section`_ of mcetl's
documentation.

.. _tutorials section: https://mcetl.readthedocs.io/en/latest/tutorials.html

Note: on Windows operating systems, the GUIs can appear blurry due to how dpi
scaling is handled. To fix, simply do:

.. code-block:: python

    import mcetl
    mcetl.set_dpi_awareness()

The above code **must** be called before opening any GUIs, or else the dpi scaling
will be incorrect.


Main GUI
~~~~~~~~

The main GUI for mcetl contains options for processing data, fitting, plotting,
writing data to Excel, and moving files.

Before using the main GUI, DataSource objects must be created. Each DataSource
contains the information for reading files for that DataSource (such as what
separator to use, which rows and columns to use, labels for the columns, etc.),
the calculations that will be performed on the data, and the options for writing
the data to Excel (formatting, placement in the worksheet, etc.).

The following will create a DataSource named 'tutorial' with the default settings,
and will then open the main GUI.

.. code-block:: python

    import mcetl

    simple_datasource = mcetl.DataSource(name='tutorial')
    mcetl.launch_main_gui([simple_datasource])


Fitting Data
~~~~~~~~~~~~

To use the fitting module in mcetl, simply do:

.. code-block:: python

    from mcetl import fitting
    fitting.launch_peak_fitting_gui()


A window will then appear to select the data file(s) to be fit and the Excel file for saving the results.
No other setup is required for doing fitting.

After doing the fitting, the fit results and plots will be saved to Excel.


Plotting
~~~~~~~~

To use the plotting module in mcetl, simply do:

.. code-block:: python

    from mcetl import plotting
    plotting.launch_plotting_gui()


Similar to fitting, a window will then appear to select the data file(s) to be plotted,
and no other setup is required for doing plotting.

When plotting, the image of the plots can be saved to all formats supported by
`Matplotlib <https://matplotlib.org>`_, including tiff, jpg, png, svg, and pdf.

In addition, the layout of the plots can be saved to apply to other figures later, and the data
for the plots can be saved so that the entire plot can be recreated.

To reopen a figure saved through mcetl, do:

.. code-block:: python

    plotting.load_previous_figure()


Generating Example Data
~~~~~~~~~~~~~~~~~~~~~~~

Files for example data from characterization techniques can be created using:

.. code-block:: python

    from mcetl import raw_data
    raw_data.generate_raw_data()


Data produced by the generate_raw_data function covers the following characterization techniques:

* X-ray diffraction (XRD)
* Fourier-transform infrared spectroscopy (FTIR)
* Raman spectroscopy
* Thermogravimetric analysis (TGA)
* Differential scanning calorimetry (DSC)
* Rheometry
* Uniaxial tensile tests
* Pore size measurements


Example Programs
~~~~~~~~~~~~~~~~

`Example programs`_  are available to show basic usage of mcetl. The examples include:

* Generating raw data
* Using the main GUI
* Using the fitting GUI
* Using the plotting GUI
* Reopening a figure saved with the plotting GUI


The example program for using the main GUI contains all necessary inputs for processing the
example raw data generated by the generate_raw_data function as described above and is an
excellent resource for creating new DataSource objects.


.. _Example programs: https://github.com/derb12/mcetl/tree/main/examples


Future Plans
------------

Planned features for later releases:

* Develop tests for all modules in the package.
* Switch from print statements to logging.
* Switch GUI backend from PySimpleGUI to wxPython or something web-based.
* Add more plot types to the plotting gui, including bar charts, categorical plots, and 3d plots.
* Make fitting more flexible by allowing more options or user inputs.
* Potentially add support for importing data from more file types.
* Improve overall look and usability of all GUIs.


Contributing
------------

Contributions are welcomed and greatly appreciated. For information on submitting bug reports,
pull requests, or general feedback, please refer to the `contributing guide`_.

.. _contributing guide: https://github.com/derb12/mcetl/tree/main/docs/contributing.rst


Changelog
---------

Refer to the changelog_ for information on mcetl's changes.

.. _changelog: https://github.com/derb12/mcetl/tree/main/CHANGELOG.rst


License
-------

mcetl is open source and available under the BSD 3-clause license.
For more information, refer to the license_.

.. _license: https://github.com/derb12/mcetl/tree/main/LICENSE.txt


Author
------

* Donald Erb <donnie.erb@gmail.com>


Gallery
-------

Images of the various GUIs can be found on the `gallery section`_ of
mcetl's documentation.

.. _gallery section: https://mcetl.readthedocs.io/en/latest/gallery.html
