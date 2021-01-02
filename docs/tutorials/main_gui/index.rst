Main GUI
========

The Main GUI for mcetl contains options for processing data, fitting data, plotting data,
writing data to Excel, and moving files. Before using the Main GUI, DataSource and Function
objects must be created.

Each DataSource object contains the information for reading files for that DataSource
(such as what separator to use, which rows and columns to use, labels for the columns, etc.),
the calculations that will be performed on the data, and the options for writing the data to
Excel (formatting, placement in the worksheet, etc.).

Function objects come in three types:

* PreprocessFunctions, which will process the data as soon as it is imported from the files.
  PreprocessFunctions can be used to
* CalculationFunctions,
* SummaryFunctions,

A note on nomenclature:


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   creating_functions
   creating_datasources
   main_gui
