==================
Using the Main GUI
==================

Once all of the desired DataSource objects are created, simply group the DataSource
objects together in a list or tuple, and then call :func:`.launch_main_gui`. For
example, using the two DataSource objects created from the last section gives:

.. code-block:: python

    import mcetl

    all_datasources = (xrd, tensile)
    mcetl.launch_main_gui(all_datasources)

The main GUI has the following steps:

* Main Menu (Choosing the DataSource and Processing Steps)
* File Selection
* Importing Data from Files
* Naming Samples & Columns
* Processing

Main Menu
---------

In the main menu, the desired DataSource, the file selection method, and
any processing steps are selected.

The possible processing steps are:

* Process the data using the Function objects for the selected DataSource
* Fit the data
* Plot the data
* Save the data to Excel
* Move files

Note that if the only selected processing step is moving files, then no data is actually
imported.

File Selection
--------------

Manually Selecting Files
~~~~~~~~~~~~~~~~~~~~~~~~

Manual selection of files is easy and fast. To start, the number of datasets
needs to be entered, and then the number of samples per dataset. Each dataset
will be one sheet when writing to Excel.

Next, a window will appear to select the files for each sample in each dataset
(see the file selection window in the :doc:`gallery section <../../gallery>` of
the documentation). Simply press 'Add Files', and select all of the files for
each sample. To remove a file, just select it and press 'Del Files'.

Searching Using Keywords
~~~~~~~~~~~~~~~~~~~~~~~~

Files can also be searched for using keywords. However, this is usually
more difficult than manually selecting the files and should only be
used if searching for files within a deeply nested folder structure.
Further explanation of keyword searching for files is given when
actually using within the main GUI, and will not be covered here since
its usage is discouraged.

.. note::
   After selecting files, a file called "previous_files_{DataSource.name}.json" is
   locally saved, where {DataSource.name} is the name of the selected DataSource. This
   allows quickly bypassing file selection in case of repeated processing of the same files.

   To get the file path where the files are saved, simply do:

   .. code-block:: python

        print(str(mcetl.main_gui.SAVE_FOLDER))


Importing Data from Files
-------------------------

See the :doc:`Importing Data section <../importing_data>` of the tutorial
for the explanation of how mcetl imports raw data.

Note that numeric data after importing is downcast to the lowest
possible representation (for example float is converted to numpy.float32)
to reduce memory usage. If this would be an issue, be sure to include
appropriate Function objects to convert to the desired dtype.

Naming Samples & Columns
------------------------

The name of each sample for each dataset can be specified, as
well as the column name for each column in the dataset. Column names
are generated using the ``column_names`` input for the selected DataSource.
The :doc:`gallery section <../../gallery>` of the documentation shows an
example of the sample and column naming window.

Processing
----------

Processing includes any processing steps selected in the main menu, including
processing the data using the Function objects for the selected DataSource,
fitting the data, plotting the data, writing to Excel, or moving files. Each
step should be self-explanatory.

The output of the launch_main_gui function will be a single dictionary with
the following keys and values:

    'dataframes': list or None
        A list of lists of pandas.DataFrame, with each dataframe containing the
        data imported from a raw data file; will be None if the function
        fails before importing data, or if the only processing step taken
        was moving files.
    'fit_results': list or None
        A nested list of lists of lmfit ModelResult objects, with each
        ModelResult pertaining to the fitting of a data entry, each list of
        ModelResults containing all of the fits for a single sample,
        and east list of lists pertaining to the data within one dataset.
        Will be None if fitting is not done, or only partially filled
        if the fitting process ends early.
    'plot_results': list or None
        A list of lists, with one entry per dataset. Each interior
        list is composed of a matplotlib.Figure object and a
        dictionary of matplotlib.Axes objects. Will be None if
        plotting is not done, or only partially filled if the plotting
        process ends early.
    'writer': pandas.ExcelWriter or None
        The pandas ExcelWriter used to create the output Excel file; will
        be None if the output results were not saved to Excel.
