===========
Quick Start
===========

The sections below give a quick introduction to using mcetl, requiring no setup.
For a more detailed introduction, refer to the :doc:`tutorials section </tutorials/index>`
of the documentation.

.. note::
   On Windows operating systems, the GUIs can appear blurry due to how dpi
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
    fitting.launch_fitting_gui()

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
