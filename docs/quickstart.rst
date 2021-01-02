==========
Quickstart
==========

The sections below show a quick introduction of mcetl, requiring little to no setup.
For a more detailed introduction, refer to the `tutorials section`_ of mcetl's
documentation.

.. _tutorials section: https://mcetl.readthedocs.io/en/stable/tutorials.html


Main GUI
~~~~~~~~

The main GUI for mcetl contains options for processing data, fitting, plotting,
writing data to Excel, and moving files.

Before using the main GUI, DataSource objects must be created. Each DataSource
contains the information for reading files for that DataSource (such as what
separator to use, which rows and columns to use, labels for the columns, etc.),
the calculations that will be performed on the data, and the options for writing
the data to Excel (formatting, placement in the worksheet, etc.).

For more information on creating a DataSource object, refer to the `example program`_
that shows how to use the main gui.

.. code-block:: python

    import mcetl

    simple_datasource = mcetl.DataSource('tutorial')
    mcetl.launch_main_gui([simple_datasource])


which will run the main GUI and allow selection of all the processing steps to perform.

.. _example program: https://github.com/derb12/mcetl/tree/master/examples


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

When plotting, the image of the plots can be saved to all formats supported by matplotlib,
including tiff, jpg, png, svg, and pdf.

In addition, the layout of the plots can be saved to apply to other figures later, and the data
for the plots can be saved so that the entire plot can be recreated.

To reopen a figure saved through mcetl, do:

.. code-block:: python

    plotting.load_previous_figure()

