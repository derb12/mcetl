=====
mcetl
=====

.. image:: https://github.com/derb12/mcetl/raw/master/docs/images/logo.png
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
* Documentation available at: https://mcetl.readthedocs.io.


mcetl is focused on easing the time required to process data files. It does this
by allowing the user to define DataSource objects which contain the information
for reading files specfic to that DataSource, the calculations that will be performed on
the data, and the options for writing the data to Excel.

In addition, mcetl provides peak fitting and plotting user interfaces that
can be used without creating any DataSource objects. Peak fitting is done using
lmfit, and plotting is done with matplotlib.


.. contents:: **Table of Contents**
    :depth: 1


Description
-----------

Purpose
~~~~~~~

The aim of mcetl is to ease the repeated processing of data files. Contrary to its name, mcetl
can process any tabulated files (txt, csv, tsv, etc.), and does not require that the files originate
from materials characterization (abbreviated as MC). However, the focus on MC was selected because:

* Most data files from MC are relatively small in size (a few kB or MB).
* MC files are typically cleanly tabulated and do not require handling messy or missing data.
* Shamelessly improving my SEO :)


mcetl requires only a very basic understanding of python to use, and allows a single person to
create a tool that their entire group can use to process data and produce Excel files with a
consistent style. mcetl can create new Excel files when processing data or saving peak fitting
results, or it can append to an existing Excel file to easily work with already created files.


Screenshots
~~~~~~~~~~~

Main GUI
^^^^^^^^

.. figure:: https://github.com/derb12/mcetl/raw/master/docs/images/main_menu.png
   :align: center
   :width: 972 px
   :height: 632 px
   :scale: 45 %

   Selection of processing steps and DataSource.

.. figure:: https://github.com/derb12/mcetl/raw/master/docs/images/excel_output.png
   :align: center
   :width: 1475 px
   :height: 616 px
   :scale: 35 %

   The output Excel file after processing all the raw data files.


Peak Fitting
^^^^^^^^^^^^

.. figure:: https://github.com/derb12/mcetl/raw/master/docs/images/fitting_1.png
   :align: center
   :width: 1640 px
   :height: 757 px
   :scale: 35 %

   Peak fitting GUI and manual selection of peaks.

.. figure:: https://github.com/derb12/mcetl/raw/master/docs/images/fitting_2.png
   :align: center
   :width: 1740 px
   :height: 630 px
   :scale: 35 %

   Fit results with best fit and individual peaks.


Plotting
^^^^^^^^

.. figure:: https://github.com/derb12/mcetl/raw/master/docs/images/plotting_gui.png
   :align: center
   :width: 1702 px
   :height: 938 px
   :scale: 30 %

   The plotting GUI.


Limitations
~~~~~~~~~~~

* Since mcetl uses the pandas library to load files into memory for processing, it is not suited
  for processing files whose total memory size is large (> ~10% of total RAM). mcetl attempts to reduce
  the required memory by downcasting types to their smallest representation (eg. converting float64 to float32),
  but this can only do so much.

* mcetl does not provide any built-in resources for cleaning data, although the user can easily
  manually implement this into the processing pipeline for a DataSource.

* mcetl does not provide any resources for processing data files directly from characterization equipment (such as
  .XRDML, .PAR, etc.). Other libraries such as xylib already exist and are capable of converting many such files
  to a format mcetl can use (txt, csv, etc.).

* The peak fitting and plotting modules in mcetl are not as feature-complete as other alternatives such as
  Origin, fityk, SciDAVis, etc. The modules are included in mcetl in case those better alternatives are not
  available, and the author highly recommends using those alternatives over mcetl if available.


Installation
------------

Stable Release
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


Peak Fitting
~~~~~~~~~~~~

To use the peak fitting module in mcetl, simply do::

    mcetl.launch_peak_fitting_gui()


A window will then appear to select the data file(s) to be fit and the Excel file for saving the results.
No other setup is required for doing peak fitting.

After doing peak fitting, the peak fitting results and plots will be saved to Excel.


Plotting
~~~~~~~~

To use the plotting module in mcetl, simply do::

    mcetl.launch_plotting_gui()


Similar to peak fitting, a window will appear to select the data file(s) to be plotted, and no other setup
is required for doing plotting.

When plotting, the image of the figure can be saved to all formats supported by matplotlib,
including tiff, jpg, png, svg, and pdf.

In addition, the layout of the figure can be saved to apply to other figures later, and the data for the figure
can be saved so that the entire figure can be recreated.

To reopen a figure saved through mcetl, do::

    mcetl.load_previous_figure()


Main GUI
~~~~~~~~

The main GUI for mcetl contains options for processing data, peak fitting, plotting, writing data to Excel,
and moving files.

Before using the main GUI, DataSource objects must be created. Each DataSource object contains the information
for reading files for that DataSource (such as what separator to use, which rows and columns to use, labels
for the columns, etc.), the calculations that will be performed on the data, and the options for writing the
data to Excel (formatting, placement in the worksheet, etc.).

For more information on creating a DataSource object, refer to the `example program`_ that shows how to use
the main gui. Once DataSource objects are created, simply put them into a list or tuple and do::

    mcetl.launch_main_gui(list_of_DataSources)


which will run the main GUI and allow selection of all the processing steps to perform.


.. _example program: https://github.com/derb12/mcetl/tree/master/examples


Generating Example Data
~~~~~~~~~~~~~~~~~~~~~~~

Example raw data files for various characterization techniques can be created using::

    from mcetl import raw_data
    raw_data.generate_raw_data()


Data produced by the generate_raw_data function covers the following characterization techniques:

* X-ray diffraction (XRD)
* Fourier-transform infrared spectroscopy (FTIR)
* Raman spectroscopy
* Thermogravimetric analysis (TGA)
* Differential scanning calorimetry (DSC)


Example Programs
~~~~~~~~~~~~~~~~

`Example programs`_  are available to show basic usage of mcetl. The examples include:

* Generating raw data
* Using the main GUI
* Using the peak fitting GUI
* Using the plotting GUI
* Reopening a figure saved with the plotting GUI


The example program for using the main GUI contains all necessary inputs for processing the example raw
data generated by the generate_raw_data function as described above and is an excellent resource for
creating new DataSource objects.


.. _Example programs: https://github.com/derb12/mcetl/tree/master/examples


Changing GUI Colors
~~~~~~~~~~~~~~~~~~~

All user interfaces are created using PySimpleGUI, which allows easily changing the theme of the GUIs.
For example, the following code will change the GUI theme to use PySimpleGUI's 'darkblue10' theme::

    import PySimpleGUI as sg
    sg.theme('darkblue10')


Additionally, mcetl uses a unique coloring for the button that advances to the next window.
To change this button's colors (for example to use white text on a green background), do::

    from mcetl import utils
    utils.PROCEED_COLOR = ('white', 'green')


Valid inputs for PROCEED_COLOR are color strings supported by PySimpleGUI, such as 'green',
or hex colors such as '#F9B381'.


Future Plans
------------

Planned features for later releases:

Short Term
~~~~~~~~~~

* Develop tests for all modules in the package.
* Switch from print statements to logging.
* Simplify file searching and make it more flexible.
* Transfer documentation from PDF/Word files to automatic documentation with Sphinx.
* Improve usage when opening existing Excel files.
* Add automatic and manual peak labeling for the plotting gui.


Long Term
~~~~~~~~~

* Add more plot types to the plotting gui, including bar charts, categorical plots, and 3d plots.
* Make peak fitting more flexible by allowing more options or user inputs.
* Improve overall look and usability of all GUIs.


Contributing
------------

Contributions are welcomed and greatly appreciated. For information on submitting bug reports,
pull requests, or general feedback, please refer to the `contributing guide`_.

.. _contributing guide: https://github.com/derb12/mcetl/tree/master/docs/contributing.rst


Changelog
---------

Refer to the changelog_ for information on mcetl's changes.

.. _changelog: https://github.com/derb12/mcetl/tree/master/CHANGELOG.rst


License
-------

mcetl is available under the BSD 3-clause license. For more information, refer to the license_.

.. _license: https://github.com/derb12/mcetl/tree/master/LICENSE.txt


Author
------

* Donald Erb <donnie.erb@gmail.com>


Credits
-------

The layout of this package was initially created with Cookiecutter_ and the
`audreyr/cookiecutter-pypackage`_ project template.


.. _Cookiecutter: https://github.com/audreyr/cookiecutter

.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage


Screenshots
-----------

Main GUI
~~~~~~~~


.. figure:: https://github.com/derb12/mcetl/raw/master/docs/images/main_menu_1.PNG
   :align: center
   :scale: 40 %

   The main menu.

.. figure:: https://github.com/derb12/mcetl/raw/master/docs/images/main_menu_2.PNG
   :align: center
   :scale: 40 %

   Selection of the DataSource object to use.

.. figure:: https://github.com/derb12/mcetl/raw/master/docs/images/excel_output.PNG
   :align: center
   :scale: 40 %

   The output Excel file after processing all the raw data files.


Peak Fitting
~~~~~~~~~~~~

.. figure:: https://github.com/derb12/mcetl/raw/master/docs/images/fitting_gui_1.png
   :align: center
   :scale: 40 %

   The peak fitting GUI.

.. figure:: https://github.com/derb12/mcetl/raw/master/docs/images/fitting_gui_2.png
   :align: center
   :scale: 40 %

   Manual selection of peaks is enabled using matplotlib.

.. figure:: https://github.com/derb12/mcetl/raw/master/docs/images/fitting_gui_3.png
   :align: center
   :scale: 40 %

   The initial fit and best fit after peak fitting.

.. figure:: https://github.com/derb12/mcetl/raw/master/docs/images/fitting_gui_4.png
   :align: center
   :scale: 40 %

   Individual peaks from the best fit.


Plotting
~~~~~~~~

.. figure:: https://github.com/derb12/mcetl/raw/master/docs/images/plotting_gui.PNG
   :align: center
   :scale: 40 %

   The plotting GUI.

